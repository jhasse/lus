from setuptools import setup

VERSION='0.1.0' # also see __init__.py

setup(
    name='sly',
    version=VERSION,
    author="Jan Niklas Hasse",
    author_email="jhasse@bixense.com",
    url="https://bixense.com/sly",
    download_url='https://github.com/jhasse/sly/archive/v{}.tar.gz'.format(VERSION),
    description="A simple task-runner using KDL for configuration",
    packages=['sly'],
    entry_points={
        'console_scripts': ['sly = sly:__main__'],
    },
    install_requires=[
        'ckdl',
    ],
)
