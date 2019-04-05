import re
import pandas as pd
import babeltrace as bt
import os
import wrapt
import cxxfilt
import time
import json
import glob

import f0cal

from .manager import ProfileManager
from .pandas_helpers import required_columns

@wrapt.decorator
def timing(fn, instance, args, dargs):
    ts = time.time()
    result = fn(*args, **dargs)
    te = time.time()
    print('func: %r args:[%r, %r] took: %2.4f sec' % (fn.__name__, args, dargs, te-ts))
    return result


class CtfTraceIterator:
    _SCOPES = dict(event_fields=bt.CTFScope.EVENT_FIELDS,
                   event_context=bt.CTFScope.EVENT_CONTEXT,
                   stream_event_context=bt.CTFScope.STREAM_EVENT_CONTEXT,
                   stream_event_header=bt.CTFScope.STREAM_EVENT_HEADER,
                   stream_packet_context=bt.CTFScope.STREAM_PACKET_CONTEXT,
                   trace_packet_header=bt.CTFScope.TRACE_PACKET_HEADER)

    def __init__(self, collection):
        self._trace_collection = collection
        self._len = None

    @property
    def events_iter(self):
        return self._trace_collection.events

    @classmethod
    def from_path(cls, trace_path):
        assert cls.is_valid_ctf_path(trace_path)
        trace_collection = bt.TraceCollection()
        trace_collection.add_traces_recursive(trace_path, "ctf")
        return cls(trace_collection)

    @classmethod
    def is_valid_ctf_path(cls, trace_path):
        assert os.path.exists(trace_path), trace_path
        assert os.path.isdir(trace_path), trace_path
        return True

    @property
    @required_columns(["name", "cycles", "timestamp"])
    def events_df(self):
        _e_dict = lambda e: dict(name=e.name, cycles=e.cycles, timestamp=e.timestamp)
        return pd.DataFrame.from_records(_e_dict(e) for e in self.events_iter)

    @property
    @required_columns(["payload"])
    def event_fields_json_df(self):
        it = self._value_iter("event_fields")
        return pd.DataFrame.from_records(dict(payload=json.dumps(k)) for k in it)

    @property
    @required_columns(['perf_thread_cpu_clock', 'perf_thread_cycles', 'pthread_id', 'vpid'])
    def stream_event_context_df(self):
        return self._df("stream_event_context")

    @property
    @required_columns(['content_size', 'cpu_id', 'events_discarded', 'packet_seq_num',
       'packet_size', 'timestamp_begin', 'timestamp_end'])
    def stream_packet_context_df(self):
        return self._df("stream_packet_context")

    def _df(self, scope):
        return pd.DataFrame.from_records(self._value_iter(scope))

    def _value_iter(self, scope):
        scope_enum = self._SCOPES[scope]
        for event in self.events_iter:
            fields = event.field_list_with_scope(scope_enum)
            yield {k: event.field_with_scope(k, scope_enum) for k in fields}

    def __len__(self):
        if self._len is not None:
            return self._len
        count = 0
        for event in self.events_iter:
            count += 1
        self._len = count
        return self._len


@wrapt.decorator
def cached(fn, instance, args, dargs):
    self = args[0]
    fn_name = fn.__name__
    if fn_name in self._cache:
        return self._cache[fn_name]
    result = fn(*args, **dargs)
    self._cache[fn_name] = result
    return result

class TraceParser:
    _CACHE_FACTORY = dict
    _F0CAL_REGEX = re.compile(
        "^(?P<provider>\w*):(?P<pkg>\w*)_(?P<io>[io])(?P<hash>\w*)$"
    )
    _BLOB_FIELD='shims'

    def __init__(self, trace_iter, config,  cache=None):
        self._trace_iter = trace_iter
        self._cache = self._CACHE_FACTORY() if cache is None else cache

        manifest_glob = config['profiler']['manifest_glob']
        self.shims_dicts = []
        for file in glob.glob(manifest_glob):
            blob = json.load(open(file))
            self.shims_dicts.extend(blob[self._BLOB_FIELD])

    @classmethod
    def from_iter(cls, some_iter, config):
        return cls(some_iter, config)

    @classmethod
    def from_lttng_trace(cls, trace_path, config, trace_format="ctf"):
        it = CtfTraceIterator.from_path(trace_path)
        return cls.from_iter(it, config)

    @property
    @required_columns(['cycles', 'name', 'timestamp'])
    @cached
    def raw_events_df(self):
        return self._trace_iter.events_df

    @property
    @required_columns(['name'])
    @cached
    def f0cal_events_df(self):
        return self.raw_events_df.query(
            "name.str.startswith('f0cal')", engine="python"
        )[["name"]]

    @property
    @required_columns(['provider',  'pkg', 'io',  'hash'])
    @cached
    def parsed_f0cal_events_df(self):
        return self.f0cal_events_df["name"].str.extract(self._F0CAL_REGEX)

    @property
    @cached
    def payload_df(self):
        def _make_series(_a_dict):
            _a_dict = json.loads(_a_dict)
            return pd.Series(_a_dict)
        events = self._trace_iter.event_fields_json_df
        return events.payload.apply(_make_series)

    @property
    @required_columns(['provider', 'pkg', 'io',  'hash',  'pid', 'thid'])
    @cached
    def threaded_f0cal_events_df(self):
        _df = self._trace_iter.stream_event_context_df
        _pid = _df["vpid"].astype(int)
        _thid = _df["pthread_id"].astype(int)
        return self.parsed_f0cal_events_df.assign(pid=_pid, thid=_thid)

    @property
    @required_columns(['entry', 'exit'])
    @cached
    def pairs_df(self):
        _stacker = lambda _df: Stacker(_df).pairs_df
        df = (
            self.threaded_f0cal_events_df.groupby(["pid", "thid"])
            .apply(_stacker)
            .reset_index()
        )
        df = df[["entry", "exit"]]
        return df

    @property
    @required_columns(["entry", "exit", "dt"])
    @cached
    def dt_df(self):
        merger_df = self.pairs_df
        payload_df = self._trace_iter.stream_event_context_df[["perf_thread_cpu_clock"]]
        _df = pd.merge(payload_df, merger_df, left_index=True, right_on="entry")
        _df = pd.merge(
            payload_df, _df, left_index=True, right_on="exit", suffixes=("_o", "_i")
        )
        _df["dt"] = _df["perf_thread_cpu_clock_o"] - _df["perf_thread_cpu_clock_i"]
        return _df[["entry", "exit", "dt"]]

    @property
    @required_columns(['event_id', 'arg_num', 'width', 'height'])
    @cached
    def shape_df(self):
        df = self.payload_df
        _test = lambda _c: _c.startswith("v") and _c.endswith("_shape")
        cols = [_col for _col in df.columns if _test(_col)]
        df = df[cols]
        all_dfs = []
        for col in df.columns:
            _df = df[[col]].query(f"{col}.notnull()", engine="python")
            _df["width"] = _df[col].str.get(0)  # HACK (br) This shouldn't work
            _df["height"] = _df[col].str.get(1)  # HACK (br)
            _df["arg_num"] = int(col.split("_")[0][1:])
            _df["event_id"] = _df.index
            all_dfs.append(_df)
        df = pd.concat(all_dfs, axis="index", ignore_index=True)
        return df[["event_id", "arg_num", "width", "height"]]

    @property
    @required_columns(['event_id', 'arg_num', 'ptr'])
    @cached
    def ptr_df(self):
        df = self.payload_df
        _test = lambda _c: _c.startswith("v") and _c.endswith("_ptr")
        cols = [_col for _col in df.columns if _test(_col)]
        df = df[cols]
        all_dfs = []
        for col in df.columns:
            _df = df[[col]].query(f"{col}.notnull()", engine="python")
            _df["ptr"] = _df[col]
            _df["arg_num"] = int(col.split("_")[0][1:])
            _df["event_id"] = _df.index
            all_dfs.append(_df)
        df = pd.concat(all_dfs, axis="index", ignore_index=True)
        return df[["event_id", "arg_num", "ptr"]]

    @property
    @required_columns(['event_id', 'arg_num', 'width', 'height', 'ptr'])
    @cached
    def arg_fields_df(self):
        shp_df = self.shape_df
        ptr_df = self.ptr_df
        return pd.merge(shp_df, ptr_df, on=["event_id", "arg_num"])

    @property
    @required_columns(['mangled_name'])
    @cached
    def event_mangled_names_df(self):
        _renames = dict(mangled_name_field="mangled_name")
        return self.payload_df[["mangled_name_field"]].rename(columns=_renames)


    @property
    @required_columns(['index', 'mangled_name', 'demangled_name'])
    @cached
    def mangling_lookup_df(self):
        _df = self.event_mangled_names_df.drop_duplicates().reset_index()
        _demangle = lambda _str: cxxfilt.demangle(_str)
        _df["demangled_name"] = _df["mangled_name"].apply(_demangle)
        return _df


    @property
    @required_columns(['hash', 'prefix'])
    @cached
    def hash_to_callable_df(self):
        df = pd.DataFrame.from_records(self.shims_dicts)
        return df[['hash', 'prefix']]

    @property
    @required_columns(['hash', 'prefix'])
    @cached
    def unique_callables_df(self):
        df = self.hash_to_callable_df
        events_hashes = self.parsed_f0cal_events_df['hash'].unique()
        events_hashes_df = pd.DataFrame({'hash':events_hashes})
        df = events_hashes_df.merge(df)
        return df

    @property
    @required_columns(['hash', 'arg_num', 'arg_type'])
    @cached
    def unique_callable_args_df(self):
        # Todo there is a faster way to do this
        args_dicts = []
        for item in self.shims_dicts:
            for arg in item['arg_list']:
                args_dicts.append({'hash':item['hash'], **arg})

        args_df = pd.DataFrame.from_records(args_dicts)
        return args_df[['hash', 'arg_num', 'arg_type']]

    @property
    @cached
    def big_table_df(self):
        dt_df = self.dt_df
        fe_df = self.parsed_f0cal_events_df
        fe_df["event_id"] =fe_df.index

        _df1 = pd.merge(fe_df, dt_df, left_index=True, right_on="entry")
        uc_df = self.unique_callables_df
        ua_df = self.unique_callable_args_df
        _df2 = pd.merge(uc_df, ua_df)
        _df = pd.merge(_df1, _df2, right_index=True, on="hash")
        f_df = self.arg_fields_df
        return pd.merge(_df, f_df, on=["event_id", "arg_num"], how="left")

class Stacker:
    def __init__(self, df):
        self._df = df
        self._df["is_entry"] = df["io"] == "i"
        self._stack = []

    @property
    def pairs_df(self):
        _worker = lambda _s: self._worker(_s["hash"], _s["is_entry"], _s.name)
        return self._df.apply(_worker, axis="columns").query(
            "entry.notnull()", engine="python"
        )

    def _worker(self, name_hash, is_entry, index):
        prev_index = pd.np.nan
        if is_entry:
            self._stack.append((name_hash, index))
        else:
            prev_hash, prev_index = self._stack.pop()
            assert name_hash == prev_hash
        return pd.Series(dict(entry=prev_index, exit=index), name=index)

class HDFCache:
    def __init__(self, store):
        self._store = store

    def __setitem__(self, item, value):
        assert isinstance(item, str), item
        assert isinstance(value, pd.DataFrame), value
        self._store[item] = value

    def __getitem__(self, item):
        assert isinstance(item, str), item
        df = self._store[item]
        return df

    def __contains__(self, item):
        return self._store.__contains__(item)

    @classmethod
    def from_path(cls, path):
        # assert os.path.exists(path)
        return cls(pd.HDFStore(path))

def _pr_list_args(parser):
    parser.add_argument('--query', default=None)

@f0cal.entrypoint(['pr', 'list'], args=_pr_list_args)
def _pr_list_entrypoint(parser, core, query):
    ProfileManager.SESSION_CLS = object() # (br) HACK
    mgr = ProfileManager.from_config(core.config)
    df = mgr.traces_df
    if query is not None:
        df = df.query(query)
    print(df)

def _pr_view_args(parser):
    parser.add_argument('--query', default=None)

@f0cal.entrypoint(['pr', 'view'], args=_pr_view_args)
def _pr_view_entrypoint(parser, core, query):
    ProfileManager.SESSION_CLS = object() # (br) HACK
    mgr = ProfileManager.from_config(core.config)
    df = mgr.traces_df

    # Either get the most recent trace or select via the query
    if query is not None:
        trace = df.query(query)
        assert len(df) == 1, df
    else:
        df = df.sort_values(by=['start_time'], ascending=False)
        trace = df.iloc[0]

    if pd.isnull(trace.get('hdf_path')):
        trace_id = trace['id']
        hdf_path = mgr.create_hdf_path(trace_id)
    else:
        hdf_path = trace.get('hdf_path')

    TraceParser._CACHE_FACTORY = lambda _: HDFCache.from_path(hdf_path)
    tp = TraceParser.from_lttng_trace(trace.get('trace_path'), core.config)
    _df = tp.big_table_df

    _df = _df.query("width.notnull() and width>0", engine="python")
    _df[["width", "height"]] = _df[["width", "height"]].astype(int)

    _df.dt = _df.dt * 1e-6

    _grp = _df.groupby(["prefix", "width", "height"])
    _df1 = _grp.agg(dict(dt=["count"]))
    _df2 = _grp.agg(dict(dt=["min", "max", "mean"]))
    _df3 = (1000.0 / _df2[["dt"]])

    _df1 = _df1.rename(dict(dt=""), axis="columns")
    _df2 = _df2.rename(dict(dt="Latency (ms)"), axis="columns")
    _df3 = _df3.rename(dict(min="max", max="min"), axis="columns") \
               .rename(dict(dt="Throughput (fps)"), axis="columns")
    print(pd.concat([_df1, _df2, _df3], axis='columns').round(2))
