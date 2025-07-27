from setuptools import setup

VERSION='0.1.0' # also see __init__.py

setup(
    name='los',
    version=VERSION,
    author="Jan Niklas Hasse",
    author_email="jhasse@bixense.com",
    url="https://bixense.com/los",
    download_url='https://github.com/jhasse/los/archive/v{}.tar.gz'.format(VERSION),
    description="A simple task-runner using KDL for configuration",
    packages=['los'],
    entry_points={
        'console_scripts': ['los = los:__main__'],
    },
    install_requires=[
        'ckdl',
    ],
)
