# -*- coding: utf-8 -*-
__import__("pkg_resources").declare_namespace(__name__)

import wrapt

from .state import StateManager

CORE = StateManager()
plugin = CORE.scanner.make_plugin_decorator
entrypoint = CORE.cli.entrypoint

@wrapt.decorator
def api_entrypoint(fn, _, args, dargs):
    CORE.scanner.scan("f0cal")
    return fn(CORE, *args, **dargs)


@plugin(name="f0cal", sets="config_file")
def config():
    prefix = CORE.prefix
    return (
        f"""
    [f0cal]
    prefix={prefix}
    """
        + """
    [env]
    LD_LIBRARY_PATH=${f0cal:prefix}/lib
    """
    )
