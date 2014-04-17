'''
Created on Jan 11, 2014

@author: sean
'''
import io
def _doc(from_func):
    '''copy doc from one function to another
    use as a decorator eg::
        
        @_doc(file.tell)
        def tell(..):
            ...
    '''
    def decorator(to_func):
        to_func.__doc__ = from_func.__doc__
        return to_func
    return decorator

class _SubFile(object):
    """A thin wrapper around an existing file object that
       provides a part of its data as an individual file
       object.
    """

    def __init__(self, fileobj, start=0, size=None):
        self._fileobj = fileobj
        self._start = start
        if size is None:
            fileobj.seek(0, 2)
            pos = fileobj.tell()
            self._size = pos - start
        else:
            self._size = size
        self._pos = 0

    def __getattr__(self, attr):
        return getattr(self._fileobj, attr)

    @_doc(io.FileIO.tell)
    def tell(self):
        return self._pos

    @_doc(io.FileIO.seek)
    def seek(self, offset, whence=0):
        if whence == 0:
            self._pos = offset
        elif whence == 1:
            self._pos += offset
        else:
            self._pos = self._size + offset

        self._pos = max(0, self._pos)

    def _n(self, size=None):
        if not size:
            size = self._size
        return min(size, self._size - self._pos)

    @_doc(io.FileIO.read)
    def read(self, size=None):
        self._fileobj.seek(self._pos + self._start, 0)

        n = self._n(size)
        self._pos += n

        return self._fileobj.read(n)

    @_doc(io.FileIO.readline)
    def readline(self, size=None):
        self._fileobj.seek(self._pos + self._start, 0)
        n = self._n(size)
        line = self._fileobj.readline(n)
        self._pos += len(line)
        return line

    @_doc(io.FileIO.readlines)
    def readlines(self, size=None):
        n = self._n(size)
        line = self.readline(n)
        n -= len(line)
        while line:
            yield line
            line = self.readline(n)
            n -= len(line)

