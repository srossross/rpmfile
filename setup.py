"""
@author: sean
"""

from setuptools import setup, find_packages
from os.path import isfile

if isfile("README.md"):
    with open("README.md") as readme:
        long_description = readme.read()
else:
    long_description = "???"

setup(
    name="rpmfile",
    description="Read rpm archive files",
    version="1.0.4",
    author="Sean Ross-Ross",
    author_email="srossross@gmail.com",
    url="https://github.com/srossross/rpmfile",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    tests_require=["zstandard>=0.13.0"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
