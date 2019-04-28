'''
@author: sean
'''

from setuptools import setup, find_packages
from os.path import isfile

if isfile('README.md'):
    with open('README.md') as readme:
        long_description = readme.read()
else:
    long_description = '???'

setup(
    name='rpmfile',
    description='Read rpm archive files',
    version="1.0.0",
    author='Sean Ross-Ross',
    author_email='srossross@gmail.com',
    url='https://github.com/srossross/rpmfile',
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
)
