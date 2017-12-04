"""
Created on Jan 10, 2014

@author: sean
"""
from __future__ import print_function, unicode_literals, absolute_import
import sys
import struct
from pprint import pprint
from .errors import RPMError

tags = {
    "headerimage": 61,
    "headersignatures": 62,
    "headerimmutable": 63,
    "headerregions": 64,
    "headeri18ntable": 100,
    "sig_base": 256,
    "sigsize": 257,
    "sigpgp": 259,
    "siggpg": 262,
    "pubkeys": 266,
    "signature": 267,
    "rsaheader": 268,
    "md5": 269,
    "longsigsize": 270,
    "longarchivesize": 271,
    "name": 1000,
    "version": 1001,
    "release": 1002,
    "serial": 1003,
    "summary": 1004,
    "description": 1005,
    "buildtime": 1006,
    "buildhost": 1007,
    "installtime": 1008,
    "size": 1009,
    "distribution": 1010,
    "vendor": 1011,
    "gif": 1012,
    "xpm": 1013,
    "copyright": 1014,
    "packager": 1015,
    "group": 1016,
    "changelog": 1017,
    "source": 1018,
    "patch": 1019,
    "url": 1020,
    "os": 1021,
    "arch": 1022,
    "prein": 1023,
    "postin": 1024,
    "preun": 1025,
    "postun": 1026,
    "filenames": 1027,
    "filesizes": 1028,
    "filestates": 1029,
    "filemodes": 1030,
    "fileuids": 1031,
    "filegids": 1032,
    "filerdevs": 1033,
    "filemtimes": 1034,
    "filemd5s": 1035,
    "filelinktos": 1036,
    "fileflags": 1037,
    "root": 1038,
    "fileusername": 1039,
    "filegroupname": 1040,
    "exclude": 1041,
    "exclusive": 1042,
    "icon": 1043,
    "sourcerpm": 1044,
    "fileverifyflags": 1045,
    "archivesize": 1046,
    "provides": 1047,
    "requireflags": 1048,
    "requirename": 1049,
    "requireversion": 1050,
    "nosource": 1051,
    "nopatch": 1052,
    "conflictflags": 1053,
    "conflictname": 1054,
    "conflictversion": 1055,
    "defaultprefix": 1056,
    "buildroot": 1057,
    "installprefix": 1058,
    "excludearch": 1059,
    "excludeos": 1060,
    "exclusivearch": 1061,
    "exclusiveos": 1062,
    "autoreqprov": 1063,
    "rpmversion": 1064,
    "triggerscripts": 1065,
    "triggername": 1066,
    "triggerversion": 1067,
    "triggerflags": 1068,
    "triggerindex": 1069,
    "verifyscript": 1079,
    "changelogtime": 1080,
    "authors": 1081,
    "comments": 1082,
    "prereq": 1084,
    "preinprog": 1085,
    "postinprog": 1086,
    "preunprog": 1087,
    "postunprog": 1088,
    "buildarchs": 1089,
    "obsoletes": 1090,
    "verifyscriptprog": 1091,
    "triggerscriptprog": 1092,
    "docdir": 1093,
    "cookie": 1094,
    "filedevices": 1095,
    "fileinodes": 1096,
    "filelangs": 1097,
    "prefixes": 1098,
    "instprefixes": 1099,
    "triggerin": 1100,
    "triggerun": 1101,
    "triggerpostun": 1102,
    "autoreq": 1103,
    "autoprov": 1104,
    "capability": 1105,
    "sourcepackage": 1106,
    "oldorigfilenames": 1107,
    "buildprereq": 1108,
    "buildrequires": 1109,
    "buildconflicts": 1110,
    "buildmacros": 1111,
    "provideflags": 1112,
    "provideversion": 1113,
    "obsoleteflags": 1114,
    "obsoleteversion": 1115,
    "dirindexes": 1116,
    "basenames": 1117,
    "dirnames": 1118,
    "origdirindexes": 1119,
    "origbasenames": 1120,
    "origdirnames": 1121,
    "optflags": 1122,
    "disturl": 1123,
    "archive_format": 1124,
    "archive_compression": 1125,
    "payloadflags": 1126,
    "installcolor": 1127,
    "installtid": 1128,
    "removetid": 1129,
    "rhnplatform": 1131,
    "target": 1132,
    "patchesname": 1133,
    "patchesflags": 1134,
    "patchesversion": 1135,
    "cachectime": 1136,
    "cachepkgpath": 1137,
    "cachepkgsize": 1138,
    "cachepkgmtime": 1139,
    "filecolors": 1140,
    "fileclass": 1141,
    "classdict": 1142,
    "filedependsx": 1143,
    "filedependsn": 1144,
    "dependsdict": 1145,
    "sourcepkgid": 1146,
    "filecontexts": 1147,
    "fscontexts": 1148,
    "recontexts": 1149,
    "policies": 1150,
    "pretrans": 1151,
    "posttrans": 1152,
    "pretransprog": 1153,
    "posttransprog": 1154,
    "disttag": 1155,
    "oldsuggestsname": 1156,
    "oldsuggestsversion": 1157,
    "oldsuggestsflags": 1158,
    "oldenhancesname": 1159,
    "oldenhancesversion": 1160,
    "oldenhancesflags": 1161,
    "priority": 1162,
    "cvsid": 1163,
    "blinkpkgid": 1164,
    "blinkhdrid": 1165,
    "blinknevra": 1166,
    "flinkpkgid": 1167,
    "flinkhdrid": 1168,
    "flinknevra": 1169,
    "packageorigin": 1170,
    "triggerprein": 1171,
    "buildsuggests": 1172,
    "buildenhances": 1173,
    "scriptstates": 1174,
    "scriptmetrics": 1175,
    "buildcpuclock": 1176,
    "filedigestalgos": 1177,
    "variants": 1178,
    "xmajor": 1179,
    "xminor": 1180,
    "repotag": 1181,
    "keywords": 1182,
    "buildplatforms": 1183,
    "packagecolor": 1184,
    "packageprefcolor": 1185,
    "xattrsdict": 1186,
    "filexattrsx": 1187,
    "depattrsdict": 1188,
    "conflictattrsx": 1189,
    "obsoleteattrsx": 1190,
    "provideattrsx": 1191,
    "requireattrsx": 1192,
    "buildprovides": 1193,
    "buildobsoletes": 1194,
    "dbinstance": 1195,
    "nvra": 1196,
    "filenames": 5000,
    "fileprovide": 5001,
    "filerequire": 5002,
    "fsnames": 5003,
    "fssizes": 5004,
    "triggerconds": 5005,
    "triggertype": 5006,
    "origfilenames": 5007,
    "longfilesizes": 5008,
    "longsize": 5009,
    "filecaps": 5010,
    "filedigestalgo": 5011,
    "bugurl": 5012,
    "evr": 5013,
    "nvr": 5014,
    "nevr": 5015,
    "nevra": 5016,
    "headercolor": 5017,
    "verbose": 5018,
    "epochnum": 5019,
    "preinflags": 5020,
    "postinflags": 5021,
    "preunflags": 5022,
    "postunflags": 5023,
    "pretransflags": 5024,
    "posttransflags": 5025,
    "verifyscriptflags": 5026,
    "triggerscriptflags": 5027,
    "collections": 5029,
    "policynames": 5030,
    "policytypes": 5031,
    "policytypesindexes": 5032,
    "policyflags": 5033,
    "vcs": 5034,
    "ordername": 5035,
    "orderversion": 5036,
    "orderflags": 5037,
    "mssfmanifest": 5038,
    "mssfdomain": 5039,
    "instfilenames": 5040,
    "requirenevrs": 5041,
    "providenevrs": 5042,
    "obsoletenevrs": 5043,
    "conflictnevrs": 5044,
    "filenlinks": 5045,
    "recommendname": 5046,
    "recommendversion": 5047,
    "recommendflags": 5048,
    "suggestname": 5049,
    "suggestversion": 5050,
    "suggestflags": 5051,
    "supplementname": 5052,
    "supplementversion": 5053,
    "supplementflags": 5054,
    "enhancename": 5055,
    "enhanceversion": 5056,
    "enhanceflags": 5057,
    "recommendnevrs": 5058,
    "suggestnevrs": 5059,
    "supplementnevrs": 5060,
    "enhancenevrs": 5061,
    "encoding": 5062,
    "filetriggerin": 5063,
    "filetriggerun": 5064,
    "filetriggerpostun": 5065,
    "filetriggerscripts": 5066,
    "filetriggerscriptprog": 5067,
    "filetriggerscriptflags": 5068,
    "filetriggername": 5069,
    "filetriggerindex": 5070,
    "filetriggerversion": 5071,
    "filetriggerflags": 5072,
    "transfiletriggerin": 5073,
    "transfiletriggerun": 5074,
    "transfiletriggerpostun": 5075,
    "transfiletriggerscripts": 5076,
    "transfiletriggerscriptprog": 5077,
    "transfiletriggerscriptflags": 5078,
    "transfiletriggername": 5079,
    "transfiletriggerindex": 5080,
    "transfiletriggerversion": 5081,
    "transfiletriggerflags": 5082,
    "removepathpostfixes": 5083,
    "filetriggerpriorities": 5084,
    "transfiletriggerpriorities": 5085,
    "filetriggerconds": 5086,
    "filetriggertype": 5087,
    "transfiletriggerconds": 5088,
    "transfiletriggertype": 5089,
    "filesignatures": 5090,
    "filesignaturelength": 5091,
    "payloaddigest": 5092,
    "payloaddigestalgo": 5093,
    "autoinstalled": 5094,
    "identity": 5095,
    "modularitylabel": 5096,
}

rtags = dict([(value, key) for (key, value) in tags.items()])


def extract_string(offset, count, store):
    if count > 1:
        return extract_array(offset, count, store)
    assert count == 1
    idx = store[offset:].index(b"\x00")
    return store[offset : offset + idx]


def extract_i18nstring(offset, count, store):
    # rpm string header entries can have multiple versions, one for each locale.
    # the locale names are defined in the i18n table header entry. For the sake of
    # simplicity, take only one locale to use
    return store[offset:].split(b"\x00", count)[0]


def extract_array(offset, count, store):
    return store[offset:].split(b"\x00", count)[:-1]


def extract_bin(offset, count, store):
    return store[offset : offset + count]


def extract_int32(offset, count, store):
    values = struct.unpack(b"!" + b"i" * count, store[offset : offset + 4 * count])
    if count == 1:
        values = values[0]
    return values


def extract_int16(offset, count, store):
    values = struct.unpack(b"!" + b"h" * count, store[offset : offset + 2 * count])
    if count == 1:
        values = values[0]
    return values


ty_map = {
    3: extract_int16,
    4: extract_int32,
    6: extract_string,
    7: extract_bin,
    8: extract_array,
    9: extract_i18nstring,
}


def extract_data(ty, offset, count, store):
    extract = ty_map.get(ty)
    if extract:
        return extract(offset, count, store)
    else:
        return "could not extract %s" % ty


def _readheader(fileobj):
    char = fileobj.read(1)
    while char != b"\x8e":
        char = fileobj.read(1)

        if char is None or char == b"":
            raise RPMError("reached end of file without finding magic char \x8e")

    magic = b"\x8e" + fileobj.read(2)
    from binascii import hexlify

    assert hexlify(magic) == b"8eade8", hexlify(magic)
    version = ord(fileobj.read(1))

    header_start = fileobj.tell() - 4  # -4 for magic

    _ = fileobj.read(4)

    (num_entries,) = struct.unpack(b"!i", fileobj.read(4))
    (header_structure_size,) = struct.unpack(b"!i", fileobj.read(4))

    header = struct.Struct(b"!iiii")

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
    lead = struct.Struct(b"!4sBBhh66shh16s")
    data = fileobj.read(lead.size)
    value = lead.unpack(data)

    # Not sure what the first set of headers are for
    first_range, first_headers = _readheader(fileobj)
    second_range, second_headers = _readheader(fileobj)

    first_headers.update(second_headers)

    return second_range, first_headers


def main():
    with open(sys.argv[1]) as fileobj:
        headers = get_headers(fileobj)
        pprint(headers)


if __name__ == "__main__":
    main()
