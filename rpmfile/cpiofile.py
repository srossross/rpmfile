#!/usr/bin/env python -3
# -*- coding: utf-8 -*-
#
# Copyright Â© 2011, 2013 K Richard Pixley
#
# See LICENSE for details.
#
# Time-stamp: <30-Jun-2013 19:07:22 PDT by rich@noir.com>

"""
Cpiofile is a library which reads and writes unix style 'cpio' format
archives.

.. todo:: open vs context manager
.. todo:: make is_cpiofile work on fileobj
"""

from __future__ import unicode_literals, print_function

__docformat__ = 'restructuredtext en'

__all__ = [
    'CheckSumError',
    'CpioError',
    'CpioFile',
    'CpioMember',
    'HeaderError',
    'InvalidFileFormat',
    'InvalidFileFormatNull',
    'is_cpiofile',
    'valid_magic',
    ]

import abc
import io
import mmap
import os
import struct

class CpioError(Exception):
    """Base class for CpioFile exceptions"""
    pass

class CheckSumError(CpioError):
    """Exception indicating a check sum error"""
    pass

class InvalidFileFormat(CpioError):
    """Exception indicating a file format error"""
    pass

class InvalidFileFormatNull(InvalidFileFormat):
    """Exception indicating a null file"""
    pass

class HeaderError(CpioError):
    """Exception indicating a header error"""
    pass

def valid_magic(block):
    """predicate indicating whether *block* includes a valid magic number"""
    return CpioMember.valid_magic(block)

def is_cpiofile(name):
    """predicate indicating whether *name* is a valid cpiofile"""
    with io.open(name, 'rb') as fff:
        return valid_magic(fff.read(16))

class StructBase(object):
    """
    An abstract base class representing objects which are inherently
    based on a struct.
    """

    __metaclass__ = abc.ABCMeta

    coder = None
    """
    The :py:class:`struct.Struct` used to encode/decode this object
    into a block of memory.  This is expected to be overridden by
    subclasses.
    """  # pylint: disable=W0105

    @property
    def size(self):
        """
        Exact size in bytes of a block of memory into which is suitable
        for packing this instance.
        """
        return self.coder.size

    def unpack(self, block):
        """convenience function for unpacking"""
        return self.unpack_from(block)

    @abc.abstractmethod
    def unpack_from(self, block, offset=0):
        """
        Set the values of this instance from an in-memory
        representation of the struct.

        :param string block: block of memory from which to unpack
        :param int offset: optional offset into the memory block from
            which to start unpacking
        """
        raise NotImplementedError

    def pack(self):
        """convenience function for packing"""
        block = bytearray(self.size)
        self.pack_into(block)
        return block

    @abc.abstractmethod
    def pack_into(self, block, offset=0):
        """
        Store the values of this instance into an in-memory
        representation of the file.

        :param string block: block of memory into which to pack
        :param int offset: optional offset into the memory block into
            which to start packing
        """
        raise NotImplementedError

    __hash__ = None

    def __eq__(self, other):
        raise NotImplementedError

    def __ne__(self, other):
        return not self.__eq__(other)

    def close_enough(self, other):
        """
        This is a comparison similar to __eq__ except that here the
        goal is to determine whether two objects are "close enough"
        despite perhaps having been produced at different times in
        different locations in the file system.
        """
        return self == other

class CpioFile(StructBase):
    """Class representing an entire cpio file"""

    _members = []

    def __init__(self):
        self._members = []

    @property
    def members(self):
        """accessor for a list of the members of this cpio file"""
        return self._members

    @property
    def names(self):
        """accessor for a list of names of the members of this cpio file"""
        return [member.name for member in self.members]

    def __enter__(self):
        return self

    def __exit__(self, thingy, value, traceback):
        self.close()

    @classmethod
    def open(cls, name=None, mode=None):
        return cls._open(cls(), name)

    def _open(self, name=None, fileobj=None, mymap=None, block=None):
        """
        The _open function takes some form of file identifier and creates
        an :py:class:`CpioFile` instance from it.

        :param :py:class:`str` name: a file name
        :param :py:class:`file` fileobj: if given, this overrides *name*
        :param :py:class:`mmap.mmap` mymap: if given, this overrides *fileobj*
        :param :py:class:`bytes` block: file contents in a block of memory, (if given, this overrides *mymap*)

        The file to be used can be specified in any of four different
        forms, (in reverse precedence):

        #. a file name
        #. :py:class:`file` object
        #. :py:mod:`mmap.mmap`, or
        #. a block of memory
        """

        if block is not None:
            if not name:
                name = '<unknown>'

            self.unpack_from(block)

            if fileobj:
                fileobj.close()

            return self

        if mymap is not None:
            block = mymap

        elif fileobj:
            try:
                mymap = mmap.mmap(fileobj.fileno(), 0,
                                  mmap.MAP_SHARED, mmap.PROT_READ)

            # pylint: disable=W0702
            except:
                mymap = 0
                block = fileobj.read()

        elif name:
            fileobj = io.open(os.path.normpath(os.path.expanduser(name)), 'rb')

        else:
            assert False

        return self._open(name=name,
                         fileobj=fileobj,
                         mymap=mymap,
                         block=block)

    def close(self):
        """noop - here for completeness"""
        pass

    def unpack_from(self, block, offset=0):
        pointer = offset
        print("unpack_from")
        while 'TRAILER!!!' not in self.names:
            cmem = CpioMember.encoded_class(block, pointer)()
            print(type(cmem))
            self.members.append(cmem.unpack_from(block, pointer))
            pointer += cmem.size

        del self.members[-1]

    def pack_into(self, block, offset=0):
        pointer = offset

        for member in self.members:
            member.pack_into(block, pointer)
            pointer += member.size

        cmtype = type(self.members[0]) if self.members else CpioMemberNew
        cmt = cmtype()
        cmt.name = 'TRAILER!!!'
        cmt.pack_into(block, pointer)

    def get_member(self, name):
        """return a member by *name*"""
        for member in self.members:
            if member.name == name:
                return member

        return None

    def __eq__(self, other):
        raise NotImplementedError

class CpioMember(StructBase):
    """class representing a member of a cpio archive"""

    coder = None

    name = None
    magic = None
    devmajor = None
    devminor = None
    ino = None
    mode = None
    uid = None
    gid = None
    nlink = None
    rdevmajor = None
    rdevminor = None
    mtime = None
    filesize = None

    content = None

    @staticmethod
    def valid_magic(block, offset=0):
        """
        predicate indicating whether a block of memory has a valid magic number
        """
        try:
            return CpioMember.encoded_class(block, offset)
        except InvalidFileFormat:
            return False

    @staticmethod
    def encoded_class(block, offset=0):
        """
        predicate indicating whether a block of memory includes a magic number
        """
        if not block:
            raise InvalidFileFormatNull

        for key in __magicmap__:
            if block.find(key, offset, offset + len(key)) > -1:
                return __magicmap__[key]

        raise InvalidFileFormat

    def unpack_from(self, block, offset=0):
        (self.magic, dev, self.ino, self.mode,
         self.uid, self.gid, self.nlink, rdev,
         mtimehigh, mtimelow, namesize, filesizehigh,
         filesizelow) = self.coder.unpack_from(block, offset)

        self.devmajor = os.major(dev)
        self.devminor = os.minor(dev)
        self.rdevmajor = os.major(rdev)
        self.rdevminor = os.minor(rdev)

        self.mtime = (mtimehigh << 16) | mtimelow
        self.filesize = (filesizehigh << 16) | filesizelow

        namestart = offset + self.coder.size
        datastart = namestart + namesize

        self.name = block[namestart:datastart - 1]  # drop the null

        if isinstance(self, CpioMemberBin) and (namesize & 1):
            datastart += 1  # skip a pad byte if necessary

        self.content = block[datastart:datastart + self.filesize]

        return self

    def pack_into(self, block, offset=0):
        namesize = len(self.name)
        dev = os.makedev(self.devmajor, self.devminor)
        rdev = os.makedev(self.rdevmajor, self.rdevminor)

        mtimehigh = self.mtime >> 16
        mtimelow = self.mtime & 0xffff

        filesizehigh = self.filesize >> 16
        filesizelow = self.filesize & 0xffff

        self.coder.pack_into(block, offset, self.magic, dev,
                             self.ino, self.mode, self.uid, self.gid,
                             self.nlink, rdev, mtimehigh, mtimelow,
                             namesize, filesizehigh, filesizelow)
        
        namestart = offset + self.coder.size
        datastart = namestart + namesize + 1

        block[namestart:datastart - 1] = self.name
        block[datastart - 1] = '\x00'

        if isinstance(self, CpioMemberBin) and (namesize & 1):
            datastart += 1
            block[datastart - 1] = '\x00'

        block[datastart:datastart + self.filesize] = self.content

        if isinstance(self, CpioMemberBin) and (self.filesize & 1):
            block[datastart + self.filesize] = '\x00'

        return self

    @property
    def size(self):
        return (self.coder.size
                + len(self.name) + 1
                + self.filesize)

    def __repr__(self):
        return (b'<{0}@{1}: coder={2}, name=\'{3}\', magic=\'{4}\''
                + ', devmajor={5}, devminor={6}, ino={7}, mode={8}'
                + ', uid={9}, gid={10}, nlink={11}, rdevmajor={12}'
                + ', rdevmino={13}, mtime={14}, filesize={15}>'
                .format(self.__class__.__name__, hex(id(self)), self.coder,
                        self.name, self.magic, self.devmajor, self.devminor,
                        self.ino, self.mode, self.uid, self.gid, self.nlink,
                        self.rdevmajor, self.rdevminor, self.mtime,
                        self.filesize))

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.coder == other.coder
                and self.magic == other.magic
                and self.devmajor == other.devmajor
                and self.devminor == other.devminor
                and self.ino == other.ino
                and self.mode == other.mode
                and self.uid == other.uid
                and self.gid == other.gid
                and self.nlink == other.nlink
                and self.rdevmajor == other.rdevmajor
                and self.rdevminor == other.rdevminor
                and self.mtime == other.mtime
                and self.filesize == other.filesize)

    close_enough = __eq__

class CpioMemberBin(CpioMember):
    """intermediate class indicating binary members - for subclassing only"""

    @property
    def size(self):
        namesize = len(self.name) + 1  # add null

        retval = self.coder.size
        retval += namesize

        if isinstance(self, CpioMemberBin) and (namesize & 1):
            retval += 1

        retval += self.filesize

        if isinstance(self, CpioMemberBin) and (self.filesize & 1):
            retval += 1

        return retval

class CpioMember32b(CpioMemberBin):
    """
    .. todo:: need to pad after name and after content for old binary.
    """
    coder = struct.Struct(b'>2sHHHHHHHHHHHH')

class CpioMember32l(CpioMemberBin):
    """class representing a 32bit little endian binary member"""
    coder = struct.Struct(b'<2sHHHHHHHHHHHH')

class CpioMemberODC(CpioMember):
    """class representing an ODC member"""
    coder = struct.Struct(b'=6s6s6s6s6s6s6s6s11s6s11s')

    def unpack_from(self, block, offset=0):
        (self.magic, dev, ino, mode,
         uid, gid, nlink, rdev,
         mtime, namesize, filesize) = self.coder.unpack_from(block, offset)
        _namesize = namesize
        self.ino = int(ino, 8)
        self.mode = int(mode, 8)
        self.uid = int(uid, 8)
        self.gid = int(gid, 8)
        self.nlink = int(nlink, 8)

        dev = int(dev, 8)
        rdev = int(rdev, 8)
        self.devmajor = os.major(dev)
        self.devminor = os.minor(dev)
        self.rdevmajor = os.major(rdev)
        self.rdevminor = os.minor(rdev)

        self.mtime = int(mtime, 8)
        namesize = int(namesize, 8)
        self.filesize = int(filesize, 8)

        namestart = offset + self.coder.size
        datastart = namestart + namesize

        self.name = block[namestart:datastart - 1]  # drop the null
        print('+', _namesize, self.name)
        self.content = block[datastart:datastart + self.filesize]

        return self

    def pack_into(self, block, offset=0):
        dev = os.makedev(self.devmajor, self.devminor)
        ino = str(self.ino)
        mode = str(self.mode)
        uid = str(self.uid)
        gid = str(self.gid)
        nlink = str(self.nlink)
        rdev = os.makedev(self.rdevmajor, self.rdevminor)
        mtime = str(self.mtime)
        namesize = str(len(self.name) + 1)  # add a null
        filesize = str(self.filesize)

        self.coder.pack_into(block, offset, self.magic, dev,
                             ino, mode, uid, gid,
                             nlink, rdev, mtime, namesize,
                             filesize)
        
        namesize = len(self.name) + 1

        namestart = offset + self.coder.size
        datastart = namestart + namesize

        block[namestart:datastart - 2] = self.name
        block[datastart - 1] = '\x00'
        block[datastart:datastart + self.filesize] = self.content

        return self

class CpioMemberNew(CpioMember):
    """class representing a new member"""
    coder = struct.Struct(b'6s8s8s8s8s8s8s8s8s8s8s8s8s8s')

    # pylint: disable=W0613
    @staticmethod
    def _checksum(block, offset, length):
        """return a checksum for *block* at *offset* and *length*"""
        return 0
    # pylint: enable=W0613

    def unpack_from(self, block, offset=0):
        unpacks = self.coder.unpack_from(block, offset)

        self.magic = unpacks[0]

        self.ino = int(unpacks[1], 16)
        self.mode = int(unpacks[2], 16)
        self.uid = int(unpacks[3], 16)
        self.gid = int(unpacks[4], 16)
        self.nlink = int(unpacks[5], 16)

        self.mtime = int(unpacks[6], 16)
        self.filesize = int(unpacks[7], 16)

        self.devmajor = int(unpacks[8], 16)
        self.devminor = int(unpacks[9], 16)
        self.rdevmajor = int(unpacks[10], 16)
        self.rdevminor = int(unpacks[11], 16)

        namesize = int(unpacks[12], 16)
        check = int(unpacks[13], 16)

        namestart = offset + self.coder.size
        nameend = namestart + namesize
        datastart = nameend + ((4 - (nameend % 4)) % 4)  # pad
        dataend = datastart + self.filesize

        self.name = block[namestart:nameend - 1]  # drop the null
        print( "name", namesize, self.name) 
        print( 'pad', ((4 - (nameend % 4)) % 4)  )# pad
        self.content = block[datastart:dataend]

        if check != self._checksum(self.content, 0, self.filesize):
            raise CheckSumError

        return self

    def pack_into(self, block, offset=0):
        namesize = len(self.name) + 1
        # unused: rdev = os.makedev(self.rdevmajor, self.rdevminor)
        self.coder.pack_into(
            block, offset, self.magic, str(self.ino), str(self.mode),
            str(self.uid), str(self.gid), str(self.nlink),
            str(self.mtime), str(self.filesize), str(self.devmajor),
            str(self.devminor), str(self.rdevmajor),
            str(self.rdevminor), str(namesize),
            self._checksum(self.content, 0, self.filesize))
        
        namestart = offset + self.coder.size
        nameend = namestart + namesize
        datastart = nameend + ((4 - (nameend % 4)) % 4)  # pad
        dataend = datastart + self.filesize

        block[namestart:nameend] = self.name

        for i in range(nameend, datastart):
            block[i] = '\x00'

        block[datastart:dataend] = self.content

        padend = dataend + ((4 - (datastart % 4)) % 4)  # pad
        for i in range(dataend, padend):
            block[i] = '\x00'

        return self

    @property
    def size(self):
        retval = self.coder.size
        retval += len(self.name) + 1
        retval += ((4 - (retval % 4)) % 4)
        retval += self.filesize
        retval += ((4 - (retval % 4)) % 4)
        return retval

class CpioMemberCRC(CpioMemberNew):
    """class representing a cpio archive member with a CRC"""
    @staticmethod
    def _checksum(block, offset, length):
        csum = 0

        for i in range(length):
            csum += ord(block[offset + i])

        return csum & 0xffffffff

__magicmap__ = {
    b'\x71\xc7': CpioMember32b,
    b'\xc7\x71': CpioMember32l,
    b'070707': CpioMemberODC,
    b'070701': CpioMemberNew,
    b'070702': CpioMemberCRC,
    }


