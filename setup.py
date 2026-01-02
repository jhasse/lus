from pathlib import Path

from setuptools import setup

VERSION = "0.2.1"  # also see __init__.py

README = Path(__file__).parent / "README.md"
long_description = README.read_text(encoding="utf-8")

setup(
    name="lus",
    version=VERSION,
    author="Jan Niklas Hasse",
    author_email="jhasse@bixense.com",
    url="https://github.com/jhasse/lus",
    download_url="https://github.com/jhasse/lus/archive/v{}.tar.gz".format(VERSION),
    description="A simple task-runner using KDL for configuration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["lus"],
    entry_points={
        "console_scripts": ["lus = lus:main"],
    },
    install_requires=[
        "ckdl",
        "expandvars",
    ],
)
