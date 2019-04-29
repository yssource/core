import re
import os

import pandas as pd
import contextlib
import types

import f0cal


from .pandas_helpers import required_columns as require


@f0cal.plugin(name="ldd", sets="config_file")
def config_file():
    return """
    
    [ldd]
    log_dir=${f0cal:prefix}/home/f0cal/ldd_logs
"""

@f0cal.plugin(name="ldd", sets="ini")
def ini(log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)


class LDDebugSession(contextlib.AbstractContextManager):
    def __init__(self, config,  session_id):
        self.config = config
        self.session_id = session_id
    @property
    def ld_log(self):
        log_name = '{session_id}.ld_debug.log'.format(session_id=self.session_id)
        return os.path.join(self.log_dir, log_name)
    @property
    def log_dir(self):
        return self.config['ldd']['log_dir']
    @property
    def _env(self):
        return {"LD_DEBUG": "all", "LD_DEBUG_OUTPUT": self.ld_log}
    @classmethod
    def from_config(cls, config, session_id=None):
        return cls(session_id=session_id)




class LDDebugOutputParser:
    _REGEXES = dict(bind=re.compile("^\s+(?P<pid>[0-9]+):\sbinding file (?P<src>\S+) \[\d+\] to (?P<dst>\S+) \[\d+\]: normal symbol `(?P<symbol>\w+)'(?P<suffix>.*)?$"),)
    _FILTERS = dict(bind="binding file")

    def __init__(self, log_path, config):
        self._log_path = log_path
        symbols_file = config['profiler']['symbols_file']
        self.symbols_df = pd.read_csv(symbols_file)

    def _iter(self, regex_name):
        _regex = self._REGEXES[regex_name]
        with open(self._log_path) as f:
            for line in f:
                if re.search(_regex, line):
                    yield line

    def _fast_iter(self, regex_name):
        _filter = self._FILTERS[regex_name]
        with open(self._log_path) as f:
            for line in f:
                if _filter in line:
                    yield line

    @property
    @require(["pid", "src", "dst", "symbol"])
    def binds_df(self):
        regex = "bind"
        line_df = pd.DataFrame.from_records({"line": _l} for _l in self._fast_iter(regex))
        extracted_df = line_df["line"].str.extract(self._REGEXES[regex])
        _df = pd.merge(line_df, extracted_df, left_index=True, right_index=True)
        return _df.query("pid.notnull()", engine="python").reset_index(drop=True)

    @property
    @require(["pid", "src", "dst", "symbol", "prefix"])
    def calls_df(self):
        _df = self.binds_df
        _df = pd.merge(_df, self.symbols_df, left_on='symbol', right_on='sym_name')
        return _df[["pid", "src", "dst", "symbol", "prefix"]]

    @classmethod
    def from_path(cls, log_path, config):
        return cls(log_path, config)

    @classmethod
    def from_list(cls, list_of_paths, config):
        parsers = [cls(_p, config) for _p in list_of_paths]
        dargs = {}
        dargs["binds_df"] = pd.concat([_p.binds_df for _p in parsers], axis="index")
        dargs["calls_df"] = pd.concat([_p.calls_df for _p in parsers], axis="index")

        return types.SimpleNamespace(**dargs)

def magnify():
    return [dict(selector="th",
                 props=[("font-size", "4pt")]),
            dict(selector="td",
                 props=[('padding', "0em 0em")]),
            dict(selector="th:hover",
                 props=[("font-size", "12pt")]),
            dict(selector="tr:hover td:hover",
                 props=[('max-width', '200px'),
                        ('font-size', '12pt')])]


def _pr_ldd_args(parser):
    parser.add_argument("ld_debug_logs", nargs="+")

@f0cal.entrypoint(["pr", "ldd"], args=_pr_ldd_args)
def _pr_ldd_entrypoint(parser, core, ld_debug_logs):
    lp = LDDebugOutputParser.from_list(ld_debug_logs, core.config) # 0.69s
    _df = lp.binds_df

    print(_df.query("src.str.contains('opencv')", engine="python").groupby("src").agg("count"))
    print(_df.query("dst.str.contains('opencv')", engine="python").groupby("dst").agg("count"))


    all_files_s = _df["src"].append(_df["dst"], ignore_index=True).drop_duplicates()
    files_df = all_files_s.to_frame(name="path").reset_index(drop=True)
    _p = lambda _s: os.path.basename(_s["path"])
    files_df["basename"] = files_df.apply(_p, axis="columns")
    print(files_df.query("path.str.contains('opencv')", engine="python"))

