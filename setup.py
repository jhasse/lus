from pathlib import Path
import setuptools
import toml

pyproject = toml.load("pyproject.toml")
project = pyproject["project"]

README = Path(__file__).parent / "README.md"
long_description = README.read_text(encoding="utf-8")

setuptools.setup(
    name=project["name"],
    version=project["version"],
    author="Jan Niklas Hasse",
    author_email="jhasse@bixense.com",
    url="https://github.com/jhasse/lus",
    download_url="https://github.com/jhasse/lus/archive/v{}.tar.gz".format(
        project["version"]
    ),
    description="A simple task-runner using KDL for configuration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["lus"],
    entry_points={
        "console_scripts": ["lus = lus:main"],
    },
    install_requires=[
        "kdl-py",
        "expandvars",
    ],
)
