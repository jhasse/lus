import re
from pathlib import Path
import setuptools


def get_project_metadata():
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        content = f.read()
    name_match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
    version_match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    name = name_match.group(1) if name_match else "lus"
    version = version_match.group(1) if version_match else "0.0.0"
    return name, version


NAME, VERSION = get_project_metadata()

setuptools.setup(
    name=NAME,
    version=VERSION,
    url="https://github.com/jhasse/lus",
    download_url=f"https://github.com/jhasse/lus/archive/v{VERSION}.tar.gz",
    packages=["lus"],
)
