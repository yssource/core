#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = ["venusian", "pandas"]

test_requirements = []

setup(
    name="plugnparse",
    version="0.0.1",
    description="Venusian decorators and argparse support for quickly building 'plugable' command line applications.",
    long_description=readme + "\n\n" + history,
    author="Brian Rossa",
    author_email="br@f0cal.com",
    url="https://github.com/brianthelion/plugnparse",
    packages=["plugnparse"],
    package_dir={"plugnparse": "plugnparse"},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords="plugnparse",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    test_suite="tests",
    tests_require=test_requirements,
)
