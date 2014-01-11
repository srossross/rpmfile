

from headers import get_headers
import sys
import io
import gzip
import struct
from rpmfile import cpiofile

pad = lambda fileobj: (4 - (fileobj.tell() % 4)) % 4

class RPMInfo(object):
    
    _new_coder = struct.Struct(b'8s8s8s8s8s8s8s8s8s8s8s8s8s')
    
    def __init__(self, name, file_start, file_size, initial_offset, isdir):
        self.name = name
        self.file_start = file_start
        self.size = file_size
        self.initial_offset = initial_offset
        self._isdir = isdir
        
    @property
    def isdir(self):
        return self._isdir
         
        
    def __repr__(self):
        return '<RPMMember %r>' % self.name
    
    @classmethod
    def _read(cls, magic, fileobj):
        if magic == '070701':
            return cls._read_new(fileobj, magic=magic)
        else:
            raise Exception('bad magic number %r' % magic)
    
    @classmethod
    def _read_new(cls, fileobj, magic=None):
        coder = cls._new_coder 
        
        initial_offset = fileobj.tell()
        d = coder.unpack_from(fileobj.read(coder.size))
        
        namesize = int(d[11], 16)
        name = fileobj.read(namesize)[:-1]
        fileobj.seek(pad(fileobj), 1)
        file_start = fileobj.tell()
        file_size = int(d[6], 16)
        fileobj.seek(file_size, 1)
        fileobj.seek(pad(fileobj), 1)
        nlink = int(d[4], 16)
        isdir = nlink == 2 and file_size == 0  
        return cls(name, file_start, file_size, initial_offset, isdir)
    
class RPMFile(object):
    def __init__(self, name=None, mode='rb', fileobj=None):
        self._fileobj = fileobj or io.open(name, mode)
        self._headers = get_headers(self._fileobj)
        self.data_offset = self._fileobj.tell()
    
    @property
    def headers(self):
        return self._headers
    
    def __enter__(self):
        return self
    
    def __exit__(self, *excinfo):
        self._fileobj.close()
        
    def getmembers(self):
        g = self.raw()
        magic = g.read(2)
        _members = []
        while magic: 
            if magic == '07':
                magic += g.read(4)
                member = RPMInfo._read(magic, g)
                
                if member.name == 'TRAILER!!!':
                    break
                
                if not member.isdir:
                    _members.append(member)
                
            magic = g.read(2)
        return _members
            
    def extract(self, name):
        import tarfile
        tarfile.TarFile.extract(self, member, path)
    
    def raw(self):
        
        self._fileobj.seek(self.data_offset, 0)
        return gzip.GzipFile(fileobj=self._fileobj)
    
    def read(self, member):
        g = self.raw()
        g.seek(member.file_start, 1)
        return g.read(member.size)

def open(name=None, mode='rb', fileobj=None):
    return RPMFile(name, mode, fileobj)

def main():
    print sys.argv[1]
    with open(sys.argv[1]) as rpm:
        print rpm.headers
        for m in rpm.getmembers():
            print m
            

if __name__ == '__main__':
    main()
