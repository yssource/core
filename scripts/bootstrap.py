#! /usr/bin/env python3
import sys
assert sys.version_info >= (3, 6), "Sorry, this script relies on v3.6+ language features."

import argparse
import os
import logging
import venv
import site
import distutils.spawn
import distutils.dir_util
import shlex
import glob
import string
import shutil

LOG = logging.getLogger(__file__)
PKG_REQS = ["python3-venv", "gcc", "python3-dev"]
TAB = " " * 5
TOP_PKG = "profiler"
PKGS = ["plugnparse", "f0cal", TOP_PKG]
SENTINEL = "--"
DEFAULT_GIT_URL = "https://github.com/f0cal/f0cal.git"

def run_exe(exe_unk):
    if isinstance(exe_unk, str):
        exe_unk = shlex.split(exe_unk)
    assert isinstance(exe_unk, list)
    return distutils.spawn.spawn(exe_unk)

DISTRO_INSTALLER = shutil.which("apt")
assert DISTRO_INSTALLER, "Sorry, this script currently supports Debian derivatives only."

class VenvActivator:
    def run(self, arg_dict):
        venv_dir = arg_dict["venv_dir"]
        LOG.debug(
            TAB + "source {venv_dir}/bin/activate -- RUN".format(venv_dir=venv_dir)
        )
        self.activicate_env(venv_dir)
        return True

    @staticmethod
    def activicate_env(env_dir):
        """Activate virtualenv for current interpreter:

        Use exec(open(this_file).read(), {'__file__': this_file}).

        This can be used when you must use an existing Python interpreter, not the virtualenv bin/python.
        """

        try:
            __file__
        except NameError:
            raise AssertionError(
                "You must use exec(open(this_file).read(), {'__file__': this_file}))"
            )

        # prepend bin to PATH (this file is inside the bin directory)
        bin_dir = os.path.join(env_dir, "bin")
        os.environ["PATH"] = os.pathsep.join(
            [bin_dir] + os.environ.get("PATH", "").split(os.pathsep)
        )

        base = os.path.dirname(bin_dir)

        # virtual env is right above bin directory
        os.environ["VIRTUAL_ENV"] = base

        # add the virtual environments site-package to the host python import mechanism
        IS_PYPY = hasattr(sys, "pypy_version_info")
        IS_JYTHON = sys.platform.startswith("java")
        if IS_JYTHON:
            site_packages = os.path.join(base, "Lib", "site-packages")
        elif IS_PYPY:
            site_packages = os.path.join(base, "site-packages")
        else:
            IS_WIN = sys.platform == "win32"
            if IS_WIN:
                site_packages = os.path.join(base, "Lib", "site-packages")
            else:
                site_packages = os.path.join(
                    base, "lib", "python{}".format(sys.version[:3]), "site-packages"
                )

        prev = set(sys.path)
        site.addsitedir(site_packages)
        sys.real_prefix = sys.prefix
        sys.prefix = base

        # Move the added items to the front of the path, in place
        new = list(sys.path)
        sys.path[:] = [i for i in new if i not in prev] + [i for i in new if i in prev]


class FileWriter:
    LINE_TEMPLATE = "-e file://{clone_dir}/{pkg}#egg={pkg}\n"

    def run(self, arg_dict):
        clone_dir = arg_dict["clone_dir"]
        path = os.path.join(clone_dir, "constraints.txt")
        with open(path, "w") as constraints_file:
            for pkg in PKGS:
                line_str = self.LINE_TEMPLATE.format(pkg=pkg, **arg_dict)
                constraints_file.write(line_str)
        return True


class Copier:
    def run(self, argdict):
        src_dir = argdict["path"]
        dst_dir = argdict["copy_dir"]
        distutils.dir_util.copy_tree(src_dir, dst_dir)
        return True


class Cmd:
    def __init__(self, cmd_str, **dargs):
        self._dargs = dargs
        self._cmd_str = cmd_str

    @classmethod
    def _format(cls, a_str, available_dict):
        LOG.debug(TAB + a_str)
        required_fields = [
            fname for _, fname, _, _ in string.Formatter().parse(a_str) if fname
        ]
        available_fields = [k for k, v in available_dict.items() if v is not None]
        if set(required_fields) - set(available_fields) != set():
            return ""
        result = a_str.format(**available_dict)
        return result

    def _run(self, cmd_str):
        if len(cmd_str.strip()) == 0:
            LOG.debug(TAB + self._cmd_str + " -- SKIP")
            return False
        LOG.debug(TAB + cmd_str + " -- RUN")
        run_exe(cmd_str)
        return True

    def run(self, arg_dict):
        LOG.debug(arg_dict)
        interp_list = list(reversed(list(self._dargs.items())))
        interp_list.append((None, self._cmd_str))
        for key, arg_str in interp_list:
            arg_dict[key] = self._format(arg_str, arg_dict)
            LOG.debug(TAB + TAB + arg_dict[key])
        return self._run(arg_dict[None])

APT_INSTALL = Cmd("{sudo} apt-get install {pkgs} -y")

MK_VENV = Cmd("python3 -m venv {venv_dir}")

GIT_CLONE = Cmd(
    "git clone {url} {branch} {clone_dir}",
    url=DEFAULT_GIT_URL,
    creds="{username}{password}@",
    password=":{password}",
    branch="-b {branch}",
)

PIP_INSTALL = Cmd(
    "pip install {editable} {pypkg} {requirements} {constraints}",
    editable="-e {editable}",
    requirements="-r {requirements_file}",
    constraints="-c {constraints_file}",
    constraints_file="{clone_dir}/constraints.txt",
)

VENV_ACTIVATE = VenvActivator()

WRITE_CONSTRAINTS = FileWriter()

RECURSIVE_COPY = Copier()

UPGRADE_PIP = Cmd("pip install --upgrade pip")


def git_install(ns_dict, parser):

    ns_dict["pkgs"] = " ".join(PKG_REQS + ["git"])
    if ns_dict.pop("test"):
        cmds.append(RUN_TESTS)
    if ns_dict.pop("skip_system_packages"):
        ns_dict["install"] = False
    else:
        ns_dict["install"] = True
    if ns_dict.pop("no_sudo"):
        ns_dict["sudo"] = ""
    else:
        ns_dict["sudo"] = "sudo"
    if ns_dict.pop("editable"):
        ns_dict["editable"] = ""
    else:
        ns_dict["editable"] = None
    ns_dict["pypkg"] = TOP_PKG
    if ns_dict["venv_dir"]:
        ns_dict["venv_dir"] = os.path.abspath(ns_dict["venv_dir"])

    assert APT_INSTALL.run(ns_dict) if ns_dict["install"] else True
    if ns_dict["clone_dir"] == "./" or ns_dict["clone_dir"] == ".":
        ns_dict["clone_dir"] = ""
    assert GIT_CLONE.run(ns_dict)
    assert MK_VENV.run(ns_dict) if ns_dict["venv_dir"] else True
    assert VENV_ACTIVATE.run(ns_dict) if ns_dict["venv_dir"] else True
    assert UPGRADE_PIP.run(ns_dict)
    if ns_dict["clone_dir"] == "":
        ns_dict["clone_dir"] = "./f0cal"
    ns_dict["clone_dir"] = os.path.abspath(ns_dict["clone_dir"])
    assert WRITE_CONSTRAINTS.run(ns_dict)
    assert PIP_INSTALL.run(ns_dict)


def local_install(ns_dict, parser):

    ns_dict["pkgs"] = " ".join(PKG_REQS)
    if ns_dict.pop("test"):
        cmds.append(RUN_TESTS)
    if ns_dict.pop("skip_system_packages"):
        ns_dict["install"] = False
    else:
        ns_dict["install"] = True
    if ns_dict.pop("no_sudo"):
        ns_dict["sudo"] = ""
    else:
        ns_dict["sudo"] = "sudo"
    if ns_dict.pop("editable"):
        ns_dict["editable"] = ""
    else:
        ns_dict["editable"] = None
    ns_dict["pypkg"] = TOP_PKG
    ns_dict["clone_dir"] = ns_dict["copy_dir"] or ns_dict["path"]
    if ns_dict["venv_dir"]:
        ns_dict["venv_dir"] = os.path.abspath(ns_dict["venv_dir"])

    assert APT_INSTALL.run(ns_dict) if ns_dict["install"] else True
    assert RECURSIVE_COPY.run(ns_dict) if ns_dict["copy_dir"] else True
    assert MK_VENV.run(ns_dict) if ns_dict["venv_dir"] else True
    assert VENV_ACTIVATE.run(ns_dict) if ns_dict["venv_dir"] else True
    assert UPGRADE_PIP.run(ns_dict)
    assert WRITE_CONSTRAINTS.run(ns_dict)
    assert PIP_INSTALL.run(ns_dict)


def pip_install(ns, parser):
    raise NotImplementedError()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        default=False,
        action="store_true",
        help="Enable debug " "logging",
    )
    parser.add_argument(
        "-v", "--venv-dir", default=None, help="Directory to create python venv in"
    )
    parser.add_argument(
        "--no-sudo", default=False, action="store_true", help="Install without " "sudo"
    )

    parser.add_argument(
        "--skip-system-packages",
        default=False,
        action="store_true",
        help="Do not install system wide packages such as compilers",
    )
    # parser.add_argument("-l", "--log", default=None)

    subs = parser.add_subparsers(dest="mode")

    git_parser = subs.add_parser("git", help="Install from github")
    git_parser.add_argument("-u", "--username", default=None, help="Github username")
    git_parser.add_argument("-p", "--password", default=None, help="Github password")
    git_parser.add_argument("-b", "--branch", default="master", help="Git branch")
    git_parser.add_argument(
        "-c", "--clone-dir", default="./", help="Location to clone source code into"
    )
    git_parser.add_argument(
        "-t", "--test", default=False, action="store_true", help="Run tests"
    )
    git_parser.add_argument(
        "-e",
        "--editable",
        default=False,
        action="store_true",
        help="Install in editable mode",
    )
    git_parser.add_argument(
        "executable",
        nargs=argparse.REMAINDER,
        default=None,
        help="Executable to run after install",
    )

    local_parser = subs.add_parser("local")
    local_parser.add_argument(
        "-p", "--path", default=os.getcwd(), help="Path to source code directory"
    )
    local_parser.add_argument(
        "-c", "--copy-dir", default=None, help="Path to copy source code into"
    )
    local_parser.add_argument(
        "-t", "--test", default=False, action="store_true", help="Run tests"
    )
    local_parser.add_argument(
        "-e",
        "--editable",
        default=False,
        action="store_true",
        help="Install in editable mode",
    )
    local_parser.add_argument(
        "executable", nargs=argparse.REMAINDER, help="Executable to run after install"
    )

    pip_parser = subs.add_parser("pip")

    ns_dict = vars(parser.parse_args())

    mode = ns_dict.pop("mode", None)
    if not mode:
        parser.error("Please choose an instal mode: ./bootstrap.py {git|pip|local} <options>")

    if ns_dict.pop("debug"):
        logging.basicConfig(level="DEBUG")

    exe = ns_dict.pop("executable")
    exe = (
        None if len(exe) == 0 else exe
    )  # because default=None doesn't work for nargs=REMAINDER
    assert exe is None or exe.pop(0) == SENTINEL

    if mode == "git":
        git_install(ns_dict, parser)
    elif mode == "pip":
        pip_install(ns_dict, parser)
    elif mode == "local":
        local_install(ns_dict, parser)
    else:
        parser.error("")

    if exe is None:
        return

    print("#"*80)
    print("# BOOTSTRAP: Running " + " ".join(exe))
    print("#"*80)

    try:
        run_exe(exe)
    except distutils.errors.DistutilsExecError:
        exit(1)

if __name__ == "__main__":
    main()
