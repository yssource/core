# -*- coding: utf-8 -*-

__author__ = "Brian Rossa"
__email__ = "br@f0cal.com"
__version__ = "0.0.1"

from .decorators import *
from .parserfactory import ParserFactory
from .plugins import PluginScanner
import argcomplete

def scan_and_run(package_name, base_parser=None, use_dict=True, use_kwargs=True):
    return run(
        scan(package_name, base_parser), use_dict=use_dict, use_kwargs=use_kwargs
    )
    # parser = base_parser or __import__('argparse').ArgumentParser()
    # factory = ParserFactory(base=parser)
    # factory.read_package(__import__(package_name))
    # parser = factory.make_parser()
    # ns = parser.parse_args()
    # return ns.func(ns, parser)


def scan(package_name, base_parser=None):
    parser = base_parser or __import__("argparse").ArgumentParser()
    factory = ParserFactory(base=parser)
    factory.read_package(__import__(package_name))
    return factory


def run(factory, use_dict=True, use_kwargs=True):
    parser = factory.make_parser()
    argcomplete.autocomplete(parser)
    ns, _func = parser.parse_args()
    ns = vars(ns) if use_dict or use_kwargs else ns
    if use_kwargs:
        return _func(parser, **ns)
    return _func(parser, ns)
