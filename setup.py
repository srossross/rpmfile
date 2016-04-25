'''
@author: sean
'''

from setuptools import setup, find_packages
from os.path import isfile

if isfile('README.md'):
    long_description = open('README.md').read()
else:
    long_description = '???'

setup(
    name='rpmfile',
    description='Read rmp archive files',
    version="0.1.5",
    author='Sean Ross-Ross',
    author_email='srossross@gmail.com',
    url='https://github.com/srossross/rpmfile',
    license='MIT',
    long_description=long_description,
    packages=find_packages(),
    install_requires=[
        'backports.lzma>=0.0.3',
    ],
)
