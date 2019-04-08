#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Setup file for babeltrace.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 3.1.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
import sys
import os

from pkg_resources import require, VersionConflict
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import distutils.spawn
import shlex

try:
    require("setuptools>=38.3")
except VersionConflict:
    print("Error: version of setuptools is too old (<38.3)!")
    sys.exit(1)


class ConanExtension(Extension):
    def __init__(self, pkg, remotes=None, build=None):
        self.pkg = pkg
        self.remotes = {} if remotes is None else remotes
        self.build = build
        super().__init__(pkg, [])


class ConanBuild(build_ext):
    def run_command(seld, cmd):
        return distutils.spawn.spawn(shlex.split(cmd))

    def run(self):
        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        for remote_name, remote_url in ext.remotes.items():
            self.run_command("conan remote add {} {}".format(remote_name, remote_url))
        self.run_command("conan install {} --build=missing".format(ext.pkg))


if __name__ == "__main__":
    pkg = "lttng-suite/2.10@f0cal/testing"
    remotes = {"f0cal": "https://api.bintray.com/conan/f0cal/conan -f"}
    setup(
        use_pyscaffold=True,
        ext_modules=[ConanExtension(pkg, remotes)],
        cmdclass={"build_ext": ConanBuild},
    )
