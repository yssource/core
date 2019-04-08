import sys
import argparse
import venusian


class ParserTree(object):
    _dest_prefix = "cmd"

    def __init__(self, base=None):
        if base is None:
            base = argparse.ArgumentParser()
        self._base_parser = base
        self.subparsers = {}
        self.parsers = {}

    def _make_tuple(self, item):
        if isinstance(item, str):
            return (item,)
        return tuple(item)

    def __getitem__(self, item):
        _parsers = self.parsers
        _subparsers = self.subparsers
        item = self._make_tuple(item)
        if len(item) == 0:
            return self._base_parser
        if item in _parsers:
            return _parsers[item]
        parent_item = item[:-1]
        parent_parser = self[parent_item]
        if parent_item not in _subparsers:
            _d = "{}{}".format(self._dest_prefix, len(parent_item))
            _subparsers[parent_item] = parent_parser.add_subparsers(dest=_d)
            _subparsers[parent_item].required = True
        if item not in _parsers:
            _parsers[item] = _subparsers[parent_item].add_parser(item[-1])
        return _parsers[item]


class ParserFactory(object):
    def __init__(self, base=None, target=None):
        if base is None:
            base = argparse.ArgumentParser()
        if target is None:
            target = "func"
        self._tree = ParserTree(base)
        self._captured_parse_args = base.parse_args
        self._captured_parse_known_args = base.parse_known_args
        base.parse_args = self._parse_args
        base.parse_known_args = self._parse_known_args
        self._base = base
        self._target = target
        self._scanned_list = []

    @property
    def tree(self):
        return self._tree

    def read_annotated_class(self, cls):
        for attr in dir(cls):
            if not attr.startswith("cli_"):
                continue
            cmds = attr.replace("cli_", "").split("_")
            self._tree[cmds].set_defaults(func=attr)

    def scan_error_handler(self, name):
        if not issubclass(sys.exc_info()[0], ImportError):
            raise  # reraise the last exception

    def read_package(self, package, require=None):
        if package in self._scanned_list:
            return
        # TODO (br) Make 'entrypoints' global
        scanner = venusian.Scanner(entrypoints=[], modifiers=[])
        scanner.scan(
            package, categories=["plugnparse"], onerror=self.scan_error_handler
        )
        self._add_entrypoints(scanner.entrypoints)
        self._add_modifiers(scanner.modifiers)
        self._scanned_list.append(package)

    def _add_entrypoints(self, entrypoint_list):
        assert len(entrypoint_list) > 0, "You MUST supply at least one @entrypoint"
        for cmds, arg_factory, fn in entrypoint_list:
            parser = self._tree[cmds]
            _dargs = {self._target: fn}
            parser.set_defaults(**_dargs)
            arg_factory(parser)

    def _add_modifiers(self, modifier_list):
        for cmds, arg_factory in modifier_list:
            parser = self._tree[cmds]
            arg_factory(parser)

    def _parse_args(self, *args, **dargs):
        prefix = self.tree._dest_prefix
        ns = self._captured_parse_args(*args, **dargs)
        cmd_dict = {k: v for k, v in vars(ns).items() if k.startswith(prefix)}
        # ns.cmds = [v for k, v in sorted(cmd_dict.items())]
        for k in cmd_dict:
            delattr(ns, k)
        func = ns.func
        delattr(ns, "func")
        return ns, func

    def _parse_known_args(self, *args, **dargs):
        return self._captured_parse_known_args(*args, **dargs)

    def make_parser(self):
        return self._base
