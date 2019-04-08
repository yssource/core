#! /usr/bin/env python3.5

import logging

logging.basicConfig(level=0)

import argparse
import os
import plugnparse

# import salt.client
# import salt.output
# import tempfile
# import yaml
# import shutil
# import os
# import glob
import getpass

# import plugnparse
# import f0cal
# import jinja2
# import jinja2.meta
# import contextlib
# import yaml
# import distutils.dir_util
# import glob
# import pprint
# import string

from .salt_helpers import SaltConfig

LOG = logging.getLogger(__name__)
LOG_LEVELS = ["critical", "error", "warning", "info", "debug", "notset"]

HERE = os.path.split(__file__)[0]
CONFIG_DIR = os.path.join(HERE, "_salt")

DEFAULT_MANIFEST_PATH = "./manifest"
DEFAULT_MANIFEST_URL = "https://github.com/f0cal/manifest"
DEFAULT_MANIFEST_BRANCH = "master"


def init_args(parser):
    parser.add_argument("-gu", "--github-user", default=None)
    parser.add_argument("-gp", "--github-pass", default=None)


@plugnparse.entrypoint(["init"], args=init_args)
def init_entrypoint(ns, parser):
    ns.manifest_path = os.path.abspath(ns.manifest_path)
    ns.github_user = ns.github_user or input("Github username: ")
    ns.github_pass = ns.github_pass or getpass.getpass("Github password: ")
    pillar = ns.__dict__
    print(pillar)

    with SaltConfig.from_root_dir(CONFIG_DIR, cleanup=False) as salt_config:
        client = salt_config.caller_client()
        result = client.cmd("saltutil.sync_all")
        salt.output.display_output(result, "", salt_config.minion_opts)
        result = client.cmd("state.sls", "manifest", pillar=pillar)
        salt.output.display_output(result, "", salt_config.minion_opts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbosity", "-v", default=None, choices=LOG_LEVELS)
    parser.add_argument("-mp", "--manifest-path", default=DEFAULT_MANIFEST_PATH)
    # parser.add_argument('-mu', '--manifest-url', default=DEFAULT_MANIFEST_URL)
    # parser.add_argument('-mb', '--manifest-branch', default=DEFAULT_MANIFEST_BRANCH)
    ns, remainder = parser.parse_known_args()

    if ns.verbosity is not None:
        logging.basicConfig(level=ns.verbosity.upper())

    factory = plugnparse.ParserFactory(base=parser)
    factory.read_package(__import__("f0cal"))
    parser = factory.make_parser()
    ns = parser.parse_args()

    ns.func(ns, parser)


if __name__ == "__main__":
    main()
