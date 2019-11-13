from __future__ import print_function, unicode_literals, absolute_import

import gzip
import io
import sys

from .headers import get_headers

try:
    import lzma
except ImportError:
    pass
import struct
from rpmfile import cpiofile
from rpmfile.io_extra import _SubFile

pad = lambda fileobj: (4 - (fileobj.tell() % 4)) % 4


class NoLZMAModuleError(NotImplementedError):
    pass


class RPMInfo(object):
    """
    Informational class which holds the details about an
    archive member given by an RPM entry block.
    RPMInfo objects are returned by RPMFile.getmember() and
    RPMFile.getmembers() and are
    usually created internally.
    """
    _new_coder = struct.Struct(b'8s8s8s8s8s8s8s8s8s8s8s8s8s')

    def __init__(self, name, file_start, file_size, initial_offset,
                 isdir, ino, is_elf):
        self.name = name
        self._file_start = file_start
        self._size = file_size
        self.initial_offset = initial_offset
        self._isdir = isdir
        self._ino = ino
        self._is_elf = is_elf
        self.link_target = None

    @property
    def file_start(self):
        if self.link_target is not None:
            assert self.link_target != self
            return self.link_target.file_start
        return self._file_start

    @property
    def size(self):
        if self.link_target is not None:
            assert self.link_target != self
            return self.link_target.size
        return self._size

    @property
    def is_elf(self):
        if self.link_target is not None:
            assert self.link_target != self
            return self.link_target.is_elf
        return self._is_elf

    @property
    def ino(self):
        return self._ino

    @property
    def isdir(self):
        return self._isdir

    @isdir.setter
    def isdir(self, value):
        # only allowing to change isdir from True to False,
        # and only when a target for the link is present
        if self._isdir and self.link_target is not None:
            self._isdir = value

    def __repr__(self):
        return '<RPMMember %r>' % self.name

    @classmethod
    def _read(cls, magic, fileobj):
        if magic == b'070701':
            return cls._read_new(fileobj, magic=magic)
        else:
            raise Exception('bad magic number %r' % magic)

    @classmethod
    def _read_new(cls, fileobj, magic=None):
        coder = cls._new_coder

        initial_offset = fileobj.tell()
        s = fileobj.read(coder.size)
        d = coder.unpack_from(s)
        namesize = int(d[11], 16)
        name = fileobj.read(namesize)[:-1].decode('utf-8')
        fileobj.seek(pad(fileobj), 1)
        file_start = fileobj.tell()
        is_elf = fileobj.read(4) == b'\x7fELF'
        file_size = int(d[6], 16)
        fileobj.seek(file_size - 4, 1)
        fileobj.seek(pad(fileobj), 1)
        nlink = int(d[4], 16)
        ino = d[0] + d[1]
        isdir = nlink == 2 and file_size == 0
        return cls(name, file_start, file_size, initial_offset, isdir, ino,
                   is_elf)


class RPMFile(object):
    """
    Open an RPM archive `name'. `mode' must be 'r' to
    read from an existing archive.

    If `fileobj' is given, it is used for reading or writing data. If it
    can be determined, `mode' is overridden by `fileobj's mode.
    `fileobj' is not closed, when TarFile is closed.

    """

    def __init__(self, name=None, mode='rb', fileobj=None):

        if mode != 'rb':
            raise NotImplementedError("currently the only supported mode is 'rb'")
        self._fileobj = fileobj or io.open(name, mode)
        self._header_range, self._headers = get_headers(self._fileobj)
        self._ownes_fd = fileobj is None
        self._ino_map = {}

    @property
    def data_offset(self):
        return self._header_range[1]

    @property
    def header_range(self):
        return self._header_range

    @property
    def headers(self):
        """RPM headers"""
        return self._headers

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        if self._ownes_fd:
            self._fileobj.close()

    _members = None

    @staticmethod
    def _resolve_links(ino_map):
        for _, _ino_members in ino_map.items():
            _links_or_dirs = []
            target_member = None
            for member in _ino_members:
                if member.size > 0 and not member.isdir:
                    target_member = member
                else:
                    _links_or_dirs.append(member)
            if target_member is None:
                continue
            for member in _links_or_dirs:
                member.link_target = target_member
                member.isdir = False

    def getmembers(self):
        """
        Return the members of the archive as a list of RPMInfo objects. The
        list has the same order as the members in the archive.
        """
        if self._members is None:
            _members = []
            from collections import defaultdict
            _ino_map = defaultdict(list)
            g = self.data_file
            magic = g.read(2)
            while magic:
                if magic == b'07':
                    magic += g.read(4)
                    member = RPMInfo._read(magic, g)

                    if member.name == 'TRAILER!!!':
                        break
                    _ino_map[member.ino].append(member)
                    _members.append(member)

                magic = g.read(2)
            self._resolve_links(_ino_map)
            self._members = list(filter(lambda x: not x.isdir, _members))
        return self._members

    def getmember(self, name):
        """
        Return an RPMInfo object for member `name'. If `name' can not be
        found in the archive, KeyError is raised. If a member occurs more
        than once in the archive, its last occurrence is assumed to be the
        most up-to-date version.
        """
        members = self.getmembers()

        for m in members[::-1]:
            if m.name == name:
                return m
        raise KeyError("member %s could not be found" % name)

    def extractfile(self, member):
        """
        Extract a member from the archive as a file object. `member' may be
        a filename or an RPMInfo object.
        The file-like object is read-only and provides the following
        methods: read(), readline(), readlines(), seek() and tell()
        """
        if not isinstance(member, RPMInfo):
            member = self.getmember(member)
        return _SubFile(self.data_file, member.file_start, member.size)

    _data_file = None

    def get_binaries(self):
        """
        Get a list all members that were identified as ELF
        :return: List of RPMInfo, each represent a member identified as ELF
        """

        return list(filter(lambda m: m.is_elf, self.getmembers()))

    @property
    def data_file(self):
        """Return the uncompressed raw CPIO data of the RPM archive."""

        if self._data_file is None:
            fileobj = _SubFile(self._fileobj, self.data_offset)

            if self.headers["archive_compression"] == b"xz":
                if not getattr(sys.modules[__name__], 'lzma', False):
                    raise NoLZMAModuleError('lzma module not present')
                self._data_file = lzma.LZMAFile(fileobj)
            else:
                self._data_file = gzip.GzipFile(fileobj=fileobj)

        return self._data_file


def open(name=None, mode='rb', fileobj=None):
    """
    Open an RPM archive for reading. Return
    an appropriate RPMFile class.
    """
    return RPMFile(name, mode, fileobj)


def main():
    print(sys.argv[1])
    with open(sys.argv[1]) as rpm:
        print(rpm.headers)
        for m in rpm.getmembers():
            print(m)
        print('done')


if __name__ == '__main__':
    main()
