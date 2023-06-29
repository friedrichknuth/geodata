#!/usr/bin/env python

from distutils.core import setup
import setuptools

setup(
    name="geodata",
    version="0.1",
    description="Python library and client for public geospatial data retrieval",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": ["download_3DEP_DSM=geodata.cli.download_3DEP_DSM:main"]
    },
)
