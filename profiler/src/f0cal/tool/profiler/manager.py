import os
import glob
import json
import pandas as pd
from datetime import datetime
import multiprocessing as mp

import pandas as pd

class MultiprocRunner:
    _ACK = 0

    def __init__(self):
        self._proc = None
        self._pipe = None

    def _run_multiproc(self, *args, **dargs):
        self._pipe, child_pipe = mp.Pipe()
        target = self._multiproc_worker
        _args = (child_pipe, args, dargs)
        proc = mp.Process(target=target, args=_args)
        proc.start()
        pid = self._pipe.recv()
        assert pid == proc.pid
        return proc

    @staticmethod
    def _multiproc_worker(pipe, args, dargs):
        pipe.send(os.getpid())
        assert pipe.recv() == MultiprocRunner._ACK
        assert len(args) == 1
        cmd_list = args[0]
        exe = cmd_list.pop(0)
        # LOG.debug(f"{exe_str} {cmd_list} {args} {dargs}")
        env = dargs.pop("env", {})
        for k, v in env.items():
            os.putenv(k, v)
        os.execlp(exe, exe, *cmd_list)

    def start(self, *args, **dargs):
        assert self._proc is None
        self._proc = self._run_multiproc(*args, **dargs)

    def run(self, block=True):
        assert self._proc is not None
        assert self._pipe is not None
        self._pipe.send(self._ACK)
        if block:
            self._proc.join()

    @property
    def pid(self):
        assert self._proc is not None
        return self._proc.pid

    @property
    def exitcode(self):
        assert self._proc is not None
        return self._proc.exitcode

    @classmethod
    def from_config(cls, config):
        return cls()

class Manifest:
    @property
    def _manifest_iter(self):
        _field = self._BLOB_FIELD
        manifest_list = glob.glob(self._manifest_glob)
        for manifest_file in manifest_list:
            blob = json.load(open(manifest_file))
            for a_dict in blob[_field]:
                yield a_dict

    @property
    def manifest_df(self):
        _len = len(list(self._manifest_iter))
        _df = pd.DataFrame.from_records(self._manifest_iter, nrows=_len)
        return _df[["hash", "return_type", "prefix", "suffix"]].drop_duplicates()


class ProfileManager:
    SESSION_CLS = None
    METADATA_FILE_NAME = 'profile_data.json'



    @classmethod
    def from_config(cls, config):
        assert cls.SESSION_CLS is not None
        profiler_dir = config["profiler"]["profiler_dir"]
        manifest_glob = config["profiler"]["manifest_glob"]
        preload_glob = config["lttng"]["preload_glob"]
        return cls(profiler_dir, manifest_glob, preload_glob)

    def __init__(self, profiler_dir, manifest_glob, preload_glob, session_id=None):
        self._profiler_dir = profiler_dir
        self.trace_metadata_file = os.path.join(self._profiler_dir, self.METADATA_FILE_NAME)

        if not os.path.exists(self.trace_metadata_file):
            os.makedirs(self._profiler_dir, exist_ok=True)
            json.dump({}, open(self.trace_metadata_file, 'w'))

        self._manifest_glob = manifest_glob
        self._preload_glob = preload_glob
        self.session_id = session_id

    @property
    def trace_metadata(self):
        return json.load(open(self.trace_metadata_file))

    def save_metadata(self, metadata_blob):
        json.dump(metadata_blob, open(self.trace_metadata_file, 'w'))
    @property
    def ld_preload_list(self):
        return glob.glob(self._preload_glob)

    @property
    def ld_preload_str(self):
        preload_list = self.ld_preload_list
        assert len(preload_list) > 0
        return ":".join(preload_list)

    @property
    def traces_df(self):
        # TODO this could be done way faster
        traces_dicts = []
        for _id, val in self.trace_metadata.items():
            val['id'] = _id
            traces_dicts.append(val)

        df = pd.DataFrame.from_records(traces_dicts)
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['start_time'])

        return df

    def record_session_start(self, trace_path):
        trace_dir = os.path.split(trace_path)[-1]
        # _parts = trace_dir.split('-')
        # session_id = _parts[1] if len(_parts) > 1 else _parts[0]
        session_id = trace_dir
        self.session_id = session_id
        metadata = self.trace_metadata
        metadata[session_id] = {'start_time': str(datetime.now())}
        metadata[session_id]['trace_path'] = trace_path
        self.save_metadata(metadata)

    def record_run(self, executable):
        metadata = self.trace_metadata
        metadata[self.session_id]['executable'] = executable
        self.save_metadata(metadata)

    def record_session_stop(self):
        metadata = self.trace_metadata
        metadata[self.session_id]['end_time'] = str(datetime.now())
        self.save_metadata(metadata)

    def session_factory(self, config):

        class ManagerMixin:
            def _start_session(_self, *args, **kwargs):
                ret = super()._start_session(*args, **kwargs)
                self.record_session_start(_self.trace_path)
                return ret

            def run (_self, *args, **kwargs):
                if len(args) > 0:
                    _exe = args[0]
                    self.record_run(_exe)
                return super().run(*args, **kwargs)



            def _end_session(_self, *args, **kwargs):
                ret = super()._end_session(*args, **kwargs)
                self.record_session_stop()

                return ret

        new_class = type("ManagedSession", (ManagerMixin,self.SESSION_CLS ), {})
        return new_class.from_config(config)

    def create_hdf_path(self, trace_id):
        metadata = self.trace_metadata
        assert trace_id in metadata
        output_file = os.path.join(self._profiler_dir, '{}.hdf5'.format(trace_id))

        metadata[trace_id]['hdf_path'] = output_file
        self.save_metadata(metadata)
        return output_file
