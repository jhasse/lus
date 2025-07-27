from setuptools import setup

VERSION='0.1.0' # also see __init__.py

setup(
    name='lus',
    version=VERSION,
    author="Jan Niklas Hasse",
    author_email="jhasse@bixense.com",
    url="https://bixense.com/lus",
    download_url='https://github.com/jhasse/lus/archive/v{}.tar.gz'.format(VERSION),
    description="A simple task-runner using KDL for configuration",
    packages=['lus'],
    entry_points={
        'console_scripts': ['lus = lus:__main__'],
    },
    install_requires=[
        'ckdl',
    ],
)
