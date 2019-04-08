import os.path
import sys
import logging
import configparser

LOG = logging.getLogger(__name__)

CONFIG_DEFAULT_PATH = os.path.join("{prefix}", "etc", "f0cal.conf")

F0CAL_CONFIG_TEMPLATE = """
[f0cal]
client_key =
client_secret =
cache_path = {prefix}/var/cache/f0cal

[conan]
config_path = {prefix}/etc/conan
f0cal_remote_url = http://salt.local:9300/

[lttng]
session_path = {prefix}/var/cache/lttng

[packages]
opencv = opencv/4.0.1@f0cal/stable

#The following are override for the corresponding sections in the conan profile ini
[settings]
[options]
[env]
[build_requires]
"""


class NonVirtaulEnvError(Exception):
    pass


def is_virtual():
    """ Return if we run in a virtual environtment. """
    # Check supports venv && virtualenv
    return getattr(sys, "base_prefix", sys.prefix) != sys.prefix or hasattr(
        sys, "real_prefix"
    )


class Config(configparser.ConfigParser):
    default_path = CONFIG_DEFAULT_PATH

    @classmethod
    def from_file(cls, conf_file_path):
        assert os.path.isfile(conf_file_path)
        with open(conf_file_path) as f:
            parser = cls()
            parser.read_file(f)
            return parser

    @classmethod
    def create_file(cls, config_file_path, **dargs):
        dirs = os.path.dirname(config_file_path)
        if not os.path.exists(dirs):
            os.makedirs(dirs)
        assert os.path.isdir(dirs)
        with open(config_file_path, "w") as f:
            f.write(F0CAL_CONFIG_TEMPLATE.format(**dargs))


class Venv:
    def __init__(self, prefix):
        self._prefix = prefix

    @classmethod
    def from_environment(cls):
        if not is_virtual():
            raise NonVirtaulEnvError
        return cls(sys.prefix)

    @property
    def prefix(self):
        return self._prefix


def load(path=None):
    venv = Venv.from_environment()
    if path is not None:
        return Config.from_file(path)
    path = Config.default_path.format(prefix=venv.prefix)
    if not os.path.exists(path):
        Config.create_file(path, prefix=venv.prefix)
    return load(path)


def get_config_path(path=None):
    if path is not None:
        return path
    venv = Venv.from_environment()
    return Config.default_path.format(prefix=venv.prefix)
