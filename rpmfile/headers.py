'''
Created on Jan 10, 2014

@author: sean
'''
import sys
import struct
from pprint import pprint

tags = {'name': 1000
    , 'version': 1001
    , 'release': 1002
    , 'serial': 1003
    , 'summary': 1004
    , 'description': 1005
    , 'buildtime': 1006
    , 'buildhost': 1007
    , 'installtime': 1008
    , 'size': 1009
    , 'distribution': 1010
    , 'vendor': 1011
    , 'gif': 1012
    , 'xpm': 1013
    , 'copyright': 1014
    , 'packager': 1015
    , 'group': 1016
    , 'changelog': 1017
    , 'source': 1018
    , 'patch': 1019
    , 'url': 1020
    , 'os': 1021
    , 'arch': 1022
    , 'prein': 1023
    , 'postin': 1024
    , 'preun': 1025
    , 'postun': 1026
    , 'filenames': 1027
    , 'filesizes': 1028
    , 'filestates': 1029
    , 'filemodes': 1030
    , 'fileuids': 1031
    , 'filegids': 1032
    , 'filerdevs': 1033
    , 'filemtimes': 1034
    , 'filemd5s': 1035
    , 'filelinktos': 1036
    , 'fileflags': 1037
    , 'root': 1038
    , 'fileusername': 1039
    , 'filegroupname': 1040
    , 'exclude': 1041
    , 'exclusive': 1042
    , 'icon': 1043
    , 'sourcerpm': 1044
    , 'fileverifyflags': 1045
    , 'archivesize': 1046
    , 'provides': 1047
    , 'requireflags': 1048
    , 'requirename': 1049
    , 'requireversion': 1050
    , 'nosource': 1051
    , 'nopatch': 1052
    , 'conflictflags': 1053
    , 'conflictname': 1054
    , 'conflictversion': 1055
    , 'defaultprefix': 1056
    , 'buildroot': 1057
    , 'installprefix': 1058
    , 'excludearch': 1059
    , 'excludeos': 1060
    , 'exclusivearch': 1061
    , 'exclusiveos': 1062
    , 'autoreqprov': 1063
    , 'rpmversion': 1064
    , 'triggerscripts': 1065
    , 'triggername': 1066
    , 'triggerversion': 1067
    , 'triggerflags': 1068
    , 'triggerindex': 1069
    , 'verifyscript': 1079
    
    , 'basenames': 1117
     
    , 'archive_format': 1124 
    , 'archive_compression': 1125 
    , 'target': 1132 
    
    , 'authors':1081
    , 'comments':1082

}

rtags = {value:key for (key, value) in tags.items()}


def extract_string(offset, count, store):
    assert count == 1
    idx = store[offset:].index('\x00')
    return store[offset:offset + idx]

def extract_array(offset, count, store):
    a = []
    for _ in range(count):
        idx = store[offset:].index('\x00')
        value = store[offset:offset + idx]
        a.append(value)
        offset = offset + idx + 1
    return a

def extract_bin(offset, count, store):
    return store[offset:offset + count]
    
def extract_int32(offset, count, store):
    values = struct.unpack('!' + 'i' * count, store[offset:offset + 4 * count])
    if count == 1: values = values[0]
    return values
    
def extract_int16(offset, count, store):
    values = struct.unpack('!' + 'h' * count, store[offset:offset + 2 * count])
    if count == 1: values = values[0]
    return values
    
    
ty_map = {
          
          3: extract_int16,
          4: extract_int32,
          6: extract_string,
          7: extract_bin,
          8: extract_array,
          9: extract_string,
          }

def extract_data(ty, offset, count, store):
    extract = ty_map.get(ty)
    if extract:
        return extract(offset, count, store)
    else:
        return 'could not extract %s' % ty


def _readheader(fileobj):
    char = fileobj.read(1)
    while char != '\x8e':
        char = fileobj.read(1)
    magic = '\x8e' + fileobj.read(2)
    assert magic.encode('hex') == '8eade8'
    version = ord(fileobj.read(1))
    
    header_start = fileobj.tell() - 4 # -4 for magic
    
    _ = fileobj.read(4)
    
    num_entries, = struct.unpack('!i', fileobj.read(4))
    header_structure_size, = struct.unpack('!i', fileobj.read(4))
    
    header = struct.Struct('!iiii')
    
    entries = []
    for _ in range(num_entries):
        entry = header.unpack(fileobj.read(header.size))
        entries.append(entry)
    
    store = fileobj.read(header_structure_size)
    store
    
    headers = {}
    for tag, ty, offset, count in entries:
        key = rtags.get(tag, tag)
        value = extract_data(ty, offset, count, store)
        headers[key] = value
    header_end = fileobj.tell()
    return (header_start, header_end), headers
    
def get_headers(fileobj):
    lead = struct.Struct('!4sBBhh66shh16s')
    data = fileobj.read(lead.size)
    value = lead.unpack(data)

    #Not sure what the first set of headers are for
    _readheader(fileobj)
    return _readheader(fileobj)

    
def main():
    
    with open(sys.argv[1]) as fileobj:
        headers = get_headers(fileobj)
        print pprint(headers)

if __name__ == '__main__':
    main() 
