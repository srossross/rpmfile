# rpmfile

[![Build Status](https://travis-ci.org/srossross/rpmfile.svg?branch=master)](https://travis-ci.org/srossross/rpmfile)
[![Actions Status](https://github.com/srossross/rpmfile/workflows/Tests/badge.svg?branch=master&event=push)](https://github.com/srossross/rpmfile/actions)
[![PyPI version](https://img.shields.io/pypi/v/rpmfile.svg)](https://pypi.org/project/rpmfile)

Tools for inspecting RPM files in python. This module is modeled after the
[tarfile](https://docs.python.org/3/library/tarfile.html) module.

## Install

```console
$ python -m pip install -U rpmfile
```

If you want to use `rpmfile` with `zstd` compressed rpms, you'll need to install
the  [zstandard](https://pypi.org/project/zstandard/) module.

`zstd` also requires that you are using Python >= 3.5

```console
$ python -m pip install -U zstandard
```

## Example

```python
import rpmfile

with rpmfile.open('file.rpm') as rpm:

    # Inspect the RPM headers
    print(rpm.headers.keys())
    print(rpm.headers.get('arch', 'noarch'))

    # Extract a fileobject from the archive
    fd = rpm.extractfile('./usr/bin/script')
    print(fd.read())

    for member in rpm.getmembers():
        print(member)
```


## Classes

* rpmfile.RPMFile: The RPMFile object provides an interface to a RPM archive
* rpmfile.RPMInfo: An RPMInfo object represents one member in a RPMFile.

## Contributing

The [black](https://github.com/psf/black) formater should be used on all files
before submitting a contribution.

```console
$ black .
```

## Code in this module was borrowed from:

* https://bitbucket.org/krp/cpiofile
* https://github.com/mjvm/pyrpm
