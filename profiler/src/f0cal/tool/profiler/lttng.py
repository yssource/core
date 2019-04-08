import os
import argparse
import shlex
import contextlib
import multiprocessing as mp
import logging
import hashlib
import pandas as pd
import glob
import re
import shutil

import f0cal

from .manager import ProfileManager, MultiprocRunner

SENTINEL = "--"

"""LTTNG_ABORT_ON_ERROR -- Set to 1 to abort the process after the first error
is encountered.

LTTNG_HOME -- Overrides the $HOME environment variable. Useful when the user
running the commands has a non-writable home directory.

LTTNG_MAN_BIN_PATH -- Absolute path to the man pager to use for viewing help
information about LTTng commands (using lttng-help(1) or lttng COMMAND --help).

LTTNG_SESSION_CONFIG_XSD_PATH -- Path in which the session.xsd session
configuration XML schema may be found.

LTTNG_SESSIOND_PATH -- Full session daemon binary path. The --sessiond-path
option has precedence over this environment variable. Note that the
lttng-create(1) command can spawn an LTTng session daemon automatically if none
is running. See lttng-sessiond(8) for the environment variables influencing the
execution of the session daemon.

"""

"""$LTTNG_HOME/.lttngrc -- User LTTng runtime configuration. This is where the
per-user current tracing session is stored between executions of lttng(1). The
current tracing session can be set with lttng-set-session(1). See
lttng-create(1) for more information about tracing sessions.

$LTTNG_HOME/lttng-traces -- Default output directory of LTTng traces. This can
be overridden with the --output option of the lttng-create(1) command.

$LTTNG_HOME/.lttng -- User LTTng runtime and configuration directory.

$LTTNG_HOME/.lttng/sessions -- Default location of saved user tracing sessions
(see lttng-save(1) and lttng-load(1)).

/etc/lttng/sessions -- System-wide location of saved tracing sessions (see
lttng-save(1) and lttng-load(1)).

"""

LOG = logging.getLogger(__name__)

@f0cal.plugin(name="lttng", sets="config_file")
def config_file():
    return """
    [env]
    LTTNG_HOME=${lttng:home_dir}

    [lttng]
    home_dir=${f0cal:prefix}/home/lttng
    preload_glob=${f0cal:prefix}/lib/libf0cal-*.so
    modules_dir=${f0cal:prefix}/lib/modules/f0cal

    [profiler]
    profiler_dir=${f0cal:prefix}/home/f0cal
    manifest_glob=${f0cal:prefix}/etc/f0cal/*.json
    """

@f0cal.plugin(name="lttng", sets="ini")
def ini(home_dir, preload_glob, modules_dir):
    if not os.path.exists(home_dir):
        os.makedirs(home_dir)

class LTTngSession(contextlib.AbstractContextManager):
    SUBPROCESS_FACTORY = None

    _EVENT_PARANOID_FILE = "/proc/sys/kernel/perf_event_paranoid"
    _DEFAULT_EVENTS = ["'f0cal:*'"]
    _DEFAULT_CONTEXTS = [
        "perf:thread:cpu-clock",
        "perf:thread:cycles",
        "pthread_id",
        "vpid",
    ]

    def _verify_contexts(self):
        """There are some contexts that need additional setup. For one there seems to be some bug in
        lttng where if a flag is not set in a proc file no traces are written """
        contexts = self._contexts
        if any(map(lambda x: "perf" in x, contexts)):
            assert os.path.exists(self._EVENT_PARANOID_FILE)
            with open(self._EVENT_PARANOID_FILE) as f:
                val = f.read()
            if val.strip() != "1":
                if os.getuid() == 0:
                    with open(self._EVENT_PARANOID_FILE, "w") as f:
                        f.write("1")
                else:
                    raise Exception(
                        "{file} is not set to 1 and f0cal does not have root "
                        "permissions. Please set that flag to 1".format(
                            file=self._EVENT_PARANOID_FILE
                        )
                    )

    def __init__(self):
        self._trace_path = None
        self._events = None
        self._contexts = None

    @property
    def trace_path(self):
        return self._trace_path

    def wrap(self, child_proc, events=None, contexts=None):
        events = self._DEFAULT_EVENTS if events is None else events
        assert isinstance(events, list) and len(events) > 0
        contexts = self._DEFAULT_CONTEXTS if contexts is None else contexts
        assert isinstance(contexts, list) and len(contexts) > 0
        self._events = events
        self._contexts = contexts
        self._verify_contexts()
        self._child_proc = child_proc
        return self

    def run(self, *args, **dargs):
        events = " ".join(self._events)
        contexts = " ".join(f"-t {_c}" for _c in self._contexts)
        self._run("lttng enable-event --userspace {events}".format(events=events))
        self._run("lttng add-context --userspace {contexts}".format(contexts=contexts))
        self._child_proc.start(*args, **dargs)
        self._run("lttng track --userspace --pid={pid}".format(pid=self._child_proc.pid))
        self._run("lttng start")
        self._child_proc.run()
        assert self._child_proc.exitcode == 0, self._child_proc.exitcode

    def _subprocess_run(self, *args, **dargs):
        return self.__class__.SUBPROCESS_FACTORY(*args, **dargs)

    def _run(self, *args, **dargs):
        cp = self._subprocess_run(*args, **dargs)
        ret_code = cp.returncode
        assert ret_code == 0, ret_code
        return cp.stdout


    def _start_session(self):
        output = self._run("lttng create")
        regex = re.compile("Traces will be written in (.+)")
        m = regex.search(output.decode())
        assert m is not None
        self._trace_path = m.groups()[0]
        LOG.debug(self._trace_path)

    def _check_lttng_metadata(self):
        files = glob.glob(
            os.path.join(self.trace_path, "**", "metadata"), recursive=True
        )
        assert len(files) > 0

    def _end_session(self):
        try:
            self._run("lttng stop")
        except:
            pass
        finally:
            self._run("lttng destroy")
            self._check_lttng_metadata()

    def __enter__(self):
        self._start_session()
        return self

    def __exit__(self, *args):
        LOG.debug(args)
        self._end_session()

    @classmethod
    def from_config(cls, config):
        assert cls.SUBPROCESS_FACTORY is not None
        return cls()

def _pr_add_args(parser):
    parser.add_argument("--name", default=None)
    parser.add_argument("executable", default=None, nargs=argparse.REMAINDER)

@f0cal.entrypoint(["pr", "add"], args=_pr_add_args)
def _pr_add_entrypoint(parser, core, executable, name, **_):
    global LOG
    LOG = core.log
    _exe = executable
    if len(_exe) == 0 or _exe.pop(0) != SENTINEL:
        parser.error(
            "An executable is required. Please use '--' to demarcate the start of your executable."
        )
    _abs_exe_path = shutil.which(_exe[0])
    if _abs_exe_path is None:
        parser.error(f"Command not found: {_exe[0]}")
    _exe[0] = _abs_exe_path
    ProfileManager.SESSION_CLS = LTTngSession
    LTTngSession.SUBPROCESS_FACTORY = core.subprocess_run
    mgr = ProfileManager.from_config(core.config)
    _env = {'LD_PRELOAD': mgr.ld_preload_str}
    with mgr.session_factory(core.config) as session:
        runner = MultiprocRunner.from_config(core.config)
        runner = session.wrap(runner)
        runner.run(_exe, env=_env)
