import os
import io
import sys
import types
import functools
import distutils.spawn
import logging
import shlex
import subprocess
import configparser

import plugnparse

from .helpers import Jinja2Renderer

HERE = os.path.dirname(__file__)
LOG = logging.getLogger(__name__)


def _render_jinja(template_name, blob):
    j2r = Jinja2Renderer.from_template_path(os.path.join(HERE, template_name))
    return j2r.render_blob(blob)


# class classproperty:
#     def __init__(self, f):
#         self.f = f
#     def __get__(self, obj, owner):
#         return self.f(owner)


class Config(configparser.ConfigParser):
    _INTERPOLATION = configparser.ExtendedInterpolation()

    def __init__(self, *args, **dargs):
        assert "interpolation" not in dargs
        dargs["interpolation"] = self._INTERPOLATION
        super().__init__(*args, **dargs)

    @classmethod
    def from_file(cls, path):
        self = cls()
        if not os.path.exists(path):
            return self
        with open(path) as cfile:
            self.read_file(cfile)
        return self

    def write_file(self, path):
        with open(path, "w") as f:
            self.write(f)

    def to_buffer(self):
        buff = io.StringIO()
        self.write(buff)
        buff.seek(0)
        return buff

    def to_str(self):
        return self.to_buffer().read()

    @classmethod
    def merge(cls, obj_list):
        assert all(isinstance(_x, cls) for _x in obj_list)
        cfg = cls()
        for old_cfg in obj_list:
            cfg.read_string(old_cfg.to_str())
        return cfg

    @staticmethod
    def optionxform(option):
        return option


class StateManager:
    # ACTIVATE_F0CAL_SCRIPT_NAME = "activate_f0cal"
    ACTIVATE_F0CAL_SCRIPT_TEMPLATE = "activate.jinja2"
    ACTIVATE_VENV_SCRIPT_NAME = "activate"
    ENV_CONFIG_SECTION = "env"

    def __init__(self):
        self.scanner = plugnparse.PluginScanner()
        self.log = logging.getLogger("f0cal")

    @property
    def prefix(self):
        assert (
            sys.prefix != sys.base_prefix
        ), "f0cal requires a virtual environment! Aborting."
        return sys.prefix

    @property
    def config_path(self):
        _dir = os.path.join(self.prefix, "etc")
        if not os.path.exists(_dir):
            LOG.debug(f"Creating config dir {_dir}")
            os.makedirs(_dir)
        path = os.path.join(_dir, "f0cal.conf")
        return path

    @property
    @functools.lru_cache()
    def _plugin_config(self):
        config_obj = Config()
        plugin_funcs = self.scanner.query("sets=='config_file'")
        for _func in plugin_funcs.values():
            config_obj.read_string(_func())
        return config_obj

    @property
    def _file_config(self):
        return Config.from_file(self.config_path)

    @property
    @functools.lru_cache()
    def config(self):
        _c = Config.merge([self._plugin_config, self._file_config])
        _c.write_file(self.config_path)
        return _c

    @property
    def _env(self):
        return dict(self.config.items("env"))

    @property
    def cli(self):
        return types.SimpleNamespace(entrypoint=plugnparse.entrypoint)

    @property
    @functools.lru_cache()
    def env_activate_str(self):
        blob = {"env_var_list": self._env.items()}
        return _render_jinja(self.ACTIVATE_F0CAL_SCRIPT_TEMPLATE, blob)

    @property
    @functools.lru_cache()
    def venv_activate_script_path(self):
        return os.path.join(self.prefix, "bin", self.ACTIVATE_VENV_SCRIPT_NAME)

    def append_to_venv_activate(self):
        command_str = "eval $(f0cal env activate)"
        with open(self.venv_activate_script_path, "a+") as f:
            file_str = f.read()
            if command_str in file_str:
                return
            f.write(command_str)

    def run_all_ini(self):
        plugin_funcs = self.scanner.query("sets=='ini'")
        for plugin_name, ini_func in plugin_funcs.items():
            config_dict = self.config[plugin_name]
            ini_func(**config_dict)

    @staticmethod
    def subprocess_run(exe_str, *args, **dargs):
        LOG.debug(f"{exe_str} {args} {dargs}")
        cmd_list = shlex.split(exe_str)
        env = os.environ
        if "env" in dargs:
            env.update(dargs.pop("env"))
        return subprocess.run(cmd_list, *args, env=env, stdout=subprocess.PIPE, **dargs)


def from_file(self, path):
    raise NotImplementedError
