'''
Created on Jan 10, 2014

@author: sean
'''
import sys
import struct
from rpmfile.errors import RPMError
import re
import io
import rpmdefs

RPM_LEAD_MAGIC_NUMBER = '\xed\xab\xee\xdb'
RPM_HEADER_MAGIC_NUMBER = '\x8e\xad\xe8'
HEADER_MAGIC_NUMBER = re.compile('(\x8e\xad\xe8)')

RPMTAGS = {rpmdefs.RPMTAG_NAME: 'name',
           rpmdefs.RPMTAG_VERSION: 'version',
           rpmdefs.RPMTAG_RELEASE: 'release',
           rpmdefs.RPMTAG_DESCRIPTION: 'description',
           rpmdefs.RPMTAG_COPYRIGHT: 'copyright',
           rpmdefs.RPMTAG_URL: 'url',
           rpmdefs.RPMTAG_ARCH: 'arch'}

class Entry(object):
    ''' RPM Header Entry
    '''
    def __init__(self, entry, store):
        self.entry = entry
        self.store = store

        self.switch = { rpmdefs.RPM_DATA_TYPE_CHAR:            self.__readchar,
                        rpmdefs.RPM_DATA_TYPE_INT8:            self.__readint8,
                        rpmdefs.RPM_DATA_TYPE_INT16:           self.__readint16,
                        rpmdefs.RPM_DATA_TYPE_INT32:           self.__readint32,
                        rpmdefs.RPM_DATA_TYPE_INT64:           self.__readint64,
                        rpmdefs.RPM_DATA_TYPE_STRING:          self.__readstring,
                        rpmdefs.RPM_DATA_TYPE_BIN:             self.__readbin,
                        rpmdefs.RPM_DATA_TYPE_I18NSTRING_TYPE: self.__readstring}

        self.store.seek(entry[2])
        self.value = self.switch[entry[1]]()
        self.tag = entry[0]

    def __str__(self):
        return "(%s, %s)" % (self.tag, self.value, )

    def __repr__(self):
        return "(%s, %s)" % (self.tag, self.value, )

    def __readchar(self, offset=1):
        ''' store is a pointer to the store offset
        where the char should be read
        '''
        data = self.store.read(offset)
        fmt = '!'+str(offset)+'c'
        value = struct.unpack(fmt, data)
        return value

    def __readint8(self, offset=1):
        ''' int8 = 1byte
        '''
        return self.__readchar(offset)

    def __readint16(self, offset=1):
        ''' int16 = 2bytes
        '''
        data = self.store.read(offset*2)
        fmt = '!'+str(offset)+'i'
        value = struct.unpack(fmt, data)
        return value

    def __readint32(self, offset=1):
        ''' int32 = 4bytes
        '''
        data = self.store.read(offset*4)
        fmt = '!'+str(offset)+'i'
        value = struct.unpack(fmt, data)
        return value

    def __readint64(self, offset=1):
        ''' int64 = 8bytes
        '''
        data = self.store.read(offset*4)
        fmt = '!'+str(offset)+'l'
        value = struct.unpack(fmt, data)
        return value

    def __readstring(self):
        ''' read a string entry
        '''
        string = ''
        while True:
            char = self.__readchar()
            if char[0] == '\x00': # read until '\0'
                break
            string += char[0]
        return string

    def __readbin(self):
        ''' read a binary entry
        '''
        if self.entry[0] == rpmdefs.RPMSIGTAG_MD5:
            data = self.store.read(rpmdefs.MD5_SIZE)
            value = struct.unpack('!'+rpmdefs.MD5_SIZE+'s', data)
            return value
        elif self.entry[0] == rpmdefs.RPMSIGTAG_PGP:
            data = self.store.read(rpmdefs.PGP_SIZE)
            value = struct.unpack('!'+rpmdefs.PGP_SIZE+'s', data)
            return value

class Header(object):
    ''' RPM Header Structure
    '''
    def __init__(self, header, entries , store):
        '''
        '''
        self.header = header
        self.entries = entries
        self.store = store
        self.pentries = []
        self.rentries = []

        self.__readentries()


    def __readentry(self, entry):
        ''' [4bytes][4bytes][4bytes][4bytes]
               TAG    TYPE   OFFSET  COUNT
        '''
        entryfmt = '!llll'
        entry = struct.unpack(entryfmt, entry)
        if entry[0] < rpmdefs.RPMTAG_MIN_NUMBER or\
                entry[0] > rpmdefs.RPMTAG_MAX_NUMBER:
            return None
        return entry

    def __readentries(self):
        ''' read a rpm entry
        '''
        for entry in self.entries:
            entry = self.__readentry(entry)
            if entry:
                if entry[0] in rpmdefs.RPMTAGS:
                    self.pentries.append(entry)

        for pentry in self.pentries:
            entry = Entry(pentry, self.store)
            if entry:
                self.rentries.append(entry)


def _readheader(header):
    ''' reads the header-header section
    [3bytes][1byte][4bytes][4bytes][4bytes]
      MN      VER   UNUSED  IDXNUM  STSIZE
    '''
    headerfmt = '!3sc4sll'
    if not len(header) == 16:
        raise RPMError('invalid header size')

    header = struct.unpack(headerfmt, header)
    magic_num = header[0]
    if magic_num != RPM_HEADER_MAGIC_NUMBER:
        raise RPMError('invalid RPM header')
    return header


def _readheaders(fileobj, offset):
    ''' read information headers
    '''
    # lets find the start of the header
    fileobj.seek(offset)
    start = find_magic_number(HEADER_MAGIC_NUMBER, fileobj)
    # go back to the begining of the header
    fileobj.seek(start)
    header = fileobj.read(16)
    header = _readheader(header)
    entries = []
    _headers = []
    for entry in range(header[3]):
        _entry = fileobj.read(16)
        entries.append(_entry)
    store = io.BytesIO(fileobj.read(header[4]))
    _headers.append(Header(header, entries, store))

    _entries = {}
    for header in _headers:
        for entry in header.rentries:
            key = RPMTAGS.get(entry.tag, entry.tag)
            _entries[key] = entry.value 
    return _entries

def find_magic_number(regexp, data):
    ''' find a magic number in a buffer
    '''
    string = data.read(1)
    while True:
        match = regexp.search(string)
        if match:
            return data.tell() - 3
        byte = data.read(1)
        if not byte:
            return None
        else:
            string += byte

def _readlead(fileobj):
    ''' reads the rpm lead section

        struct rpmlead {
           unsigned char magic[4];
           unsigned char major, minor;
           short type;
           short archnum;
           char name[66];
           short osnum;
           short signature_type;
           char reserved[16];
           } ;
    '''
    lead_fmt = '!4sBBhh66shh16s'
    data = fileobj.read(96)
    value = struct.unpack(lead_fmt, data)

    magic_num = value[0]
    ptype = value[3]

    if magic_num != RPM_LEAD_MAGIC_NUMBER:
        raise RPMError('wrong magic number this is not a RPM file')

    if ptype not in [0, 1]:
        raise RPMError('wrong package type this is not a RPM file')

def _read_sigheader(fileobj):
    ''' read signature header

        ATN: this will not return any usefull information
        besides the file offset
    '''
    start = find_magic_number(HEADER_MAGIC_NUMBER, fileobj)
    if not start:
        raise RPMError('invalid RPM file, signature header not found')
    # return the offsite after the magic number
    return start + 3

def get_headers(fileobj):
    _readlead(fileobj)
    offset = _read_sigheader(fileobj)
    return _readheaders(fileobj, offset)
    
def main():
    with open(sys.argv[1]) as fileobj:
        print get_headers(fileobj)

if __name__ == '__main__':
    main() 
