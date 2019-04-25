# rpmfile

Tools for inspecting RPM files in python. This module is modeled after the
tarfile module.

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

## Code in this module was borrowed from:

* https://bitbucket.org/krp/cpiofile
* https://github.com/mjvm/pyrpm
