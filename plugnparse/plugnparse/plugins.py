import sys
import warnings
import importlib

import venusian
import pandas as pd


class PluginScanner(venusian.Scanner):
    def __init__(self):
        self._registry = pd.DataFrame()
        self._scan_attempts = []
        self._scan_fails = {}

    def scan_error_handler(self, name):
        exc = sys.exc_info()
        self._scan_fails[name] = exc
        if not issubclass(exc[0], ImportError):
            raise  # reraise the last exception
        # self._scan_fails.pop()

    def scan(self, pkg, **dargs):
        if isinstance(pkg, str):
            pkg = __import__(pkg)
        if pkg in self._scan_attempts:
            return
        self._scan_attempts.append(pkg)
        return super().scan(
            pkg, categories=[self._unique_id], onerror=self.scan_error_handler, **dargs
        )

    def register_plugin(self, **dargs):
        self._registry = self._registry.append(pd.Series(dargs), ignore_index=True)

    def make_plugin_decorator(self, **dargs):
        def _decorator(wrapped):
            def callback(scanner, name, obj):
                assert scanner is self
                scanner.register_plugin(found=obj, **dargs)

            venusian.attach(wrapped, callback, self._unique_id)
            return wrapped

        return _decorator

    @property
    def _unique_id(self):
        return id(self)

    def query(self, query_str, *args, **dargs):
        if self._scan_fails:
            warnings.warn(str(self._scan_fails))
        df = self._registry.query(query_str, *args, **dargs)
        list_of_dicts = df.to_records("records")
        return {d["name"]: d["found"] for d in list_of_dicts}

    # def get_first_plugin(self, plugin_type, **dargs):
    #     filter_df = self._registry.query("plugin_type==@plugin_type")
    #     assert len(filter_df) > 0
    #     result = filter_df.apply(lambda row_s: row_s["accepts_fn"](**dargs), axis=1)
    #     filter_df["accepted"] = result
    #     filter_df = filter_df.query("accepted==True")
    #     return filter_df["wrapped_fn"].iloc[0]

    # def get_all_plugins(self, plugin_type, **dargs):
    #     filter_df = self._registry.query("plugin_type==@plugin_type")
    #     assert len(filter_df) > 0
    #     result = filter_df.apply(lambda row_s: row_s["accepts_fn"](**dargs), axis=1)
    #     filter_df["accepted"] = result
    #     filter_df = filter_df.query("accepted==True")
    #     return filter_df["wrapped_fn"].to_list()
