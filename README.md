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

See the [tests](tests/test_extract.py) for more examples.

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

## Command line usage

You can use `rpmfile` via it's module invocation or via `rpmfile` command if
your `PATH` environment variable is configured correctly. Pass `--help` for all
options.

List RPM contents

```conosle
curl -sfL 'https://example.com/some.rpm.gz' | gzip -d - | python -m rpmfile -l -
./path/to/file
```

Extract files

```conosle
curl -sfL 'https://example.com/some.rpm.gz' | gzip -d - | rpmfile -xv -
./path/to/file
```

Extract files to directory

```conosle
curl -sfL 'https://example.com/some.rpm.gz' | gzip -d - | rpmfile -xvC /tmp -
/tmp/path/to/file
```

## Classes

* rpmfile.RPMFile: The RPMFile object provides an interface to a RPM archive
* rpmfile.RPMInfo: An RPMInfo object represents one member in a RPMFile.

## Contributing

The [black](https://github.com/psf/black) formater should be used on all files
before submitting a contribution. Version 19.10b0.

```console
$ pip install black==19.10b0
$ black .
```

## Code in this module was borrowed from:

* https://bitbucket.org/krp/cpiofile
* https://github.com/mjvm/pyrpm
