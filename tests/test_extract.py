"""
Tests for rpmfile extraction and header-reading functionality.

All test RPMs are generated on-the-fly by :func:`make_rpm` using only the
Python standard library (plus the optional ``zstandard`` package for zstd
tests).  No pre-built binary files and no network access are required.
"""

import gzip
import hashlib
import io
import os
import shutil
import stat
import struct
import sys
import tempfile
import unittest

import rpmfile

# ---------------------------------------------------------------------------
# Optional-dependency capability flags used by skipUnless decorators
# ---------------------------------------------------------------------------

try:
    import lzma as _lzma  # noqa: F401 - stdlib since Python 3.3

    _HAVE_LZMA = True
except ImportError:
    _HAVE_LZMA = False

try:
    import zstandard as _zstandard  # noqa: F401 - optional third-party package

    _HAVE_ZSTD = True
except ImportError:
    _HAVE_ZSTD = False


# ---------------------------------------------------------------------------
# Pure-Python minimal RPM builder
# ---------------------------------------------------------------------------

def _cpio_entry(name, content, mode=0o100644, mtime=0, ino=1, nlink=1):
    """Return a single CPIO *newc* entry as bytes."""
    name_bytes = name.encode() + b"\x00"
    header = (
        b"070701"
        + "{:08x}".format(ino).encode()
        + "{:08x}".format(mode).encode()
        + b"00000000"  # uid
        + b"00000000"  # gid
        + "{:08x}".format(nlink).encode()
        + "{:08x}".format(mtime).encode()
        + "{:08x}".format(len(content)).encode()
        + b"00000008"  # devmajor
        + b"00000005"  # devminor
        + b"00000000"  # rdevmajor
        + b"00000000"  # rdevminor
        + "{:08x}".format(len(name_bytes)).encode()
        + b"00000000"  # check
    )
    # header is exactly 110 bytes
    entry = header + name_bytes
    entry += b"\x00" * ((4 - len(entry) % 4) % 4)  # pad header+name to 4 bytes
    entry += content
    entry += b"\x00" * ((4 - len(content) % 4) % 4)  # pad data to 4 bytes
    return entry


def _cpio_archive(files):
    """Return a complete CPIO *newc* archive containing *files*.

    *files* is a list of ``(path, content_bytes, mode_octal, mtime_epoch)``
    tuples.
    """
    data = b"".join(
        _cpio_entry(name, content, mode=mode, mtime=mtime, ino=i + 1)
        for i, (name, content, mode, mtime) in enumerate(files)
    )
    data += _cpio_entry("TRAILER!!!", b"", mode=0, nlink=1, ino=0)
    return data


def _rpm_header(entries_and_data):
    """Serialise an RPM header section.

    *entries_and_data* is a list of ``(tag, type, count, raw_bytes)`` tuples.
    Types 3 (INT16) and 4 (INT32) are automatically aligned in the store.
    """
    store = b""
    index_entries = []
    for tag, ty, count, raw in entries_and_data:
        if ty == 4:  # INT32 – align to 4 bytes
            store += b"\x00" * ((4 - len(store) % 4) % 4)
        elif ty == 3:  # INT16 – align to 2 bytes
            store += b"\x00" * ((2 - len(store) % 2) % 2)
        index_entries.append((tag, ty, len(store), count))
        store += raw
    nindex = len(index_entries)
    hsize = len(store)
    index_data = b"".join(struct.pack("!iiii", *e) for e in index_entries)
    return (
        b"\x8e\xad\xe8\x01"  # magic + version
        + b"\x00\x00\x00\x00"  # reserved
        + struct.pack("!II", nindex, hsize)
        + index_data
        + store
    )


def make_rpm(
    name,
    version,
    release,
    arch,
    summary,
    description,
    group,
    license_text,
    url,
    sourcerpm,
    buildtime,
    buildhost,
    files,
    compression="gzip",
):
    """Create a minimal, valid RPM file and return its raw bytes.

    Parameters
    ----------
    files:
        A list of ``(path, content_bytes, mode_octal, mtime_epoch)`` tuples
        that will be packed into the CPIO payload.
    compression:
        ``'gzip'``, ``'xz'``, or ``'zstd'``.
    """
    cpio_data = _cpio_archive(files)

    if compression == "gzip":
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
            gz.write(cpio_data)
        compressed, compress_tag = buf.getvalue(), b"gzip"
    elif compression == "xz":
        import lzma  # stdlib since Python 3.3

        compressed = lzma.compress(cpio_data, format=lzma.FORMAT_XZ)
        compress_tag = b"xz"
    elif compression == "zstd":
        import zstandard  # optional third-party package

        compressed = zstandard.ZstdCompressor().compress(cpio_data)
        compress_tag = b"zstd"
    else:
        raise ValueError("Unknown compression: {}".format(compression))

    def _s(v):
        return (v.encode() if isinstance(v, str) else v) + b"\x00"

    def _i32(v):
        return struct.pack("!I", v)

    def _i32a(seq):
        return struct.pack("!" + str(len(seq)) + "I", *seq)

    def _i16a(seq):
        return struct.pack("!" + str(len(seq)) + "H", *seq)

    def _stra(lst):
        return b"".join(
            (s.encode() if isinstance(s, str) else s) + b"\x00" for s in lst
        )

    total_size = sum(len(c) for _, c, _, _ in files)
    basenames, dirnames, dirindexes = [], [], []
    for path, _, _, _ in files:
        if "/" in path:
            d, b = path.rsplit("/", 1)
            d += "/"
        else:
            d, b = "./", path
        basenames.append(b)
        if d not in dirnames:
            dirnames.append(d)
        dirindexes.append(dirnames.index(d))

    main_entries = [
        (100, 8, 1, b"C\x00"),  # headeri18ntable
        (1000, 6, 1, _s(name)),  # name
        (1001, 6, 1, _s(version)),  # version
        (1002, 6, 1, _s(release)),  # release
        (1004, 9, 1, _s(summary)),  # summary
        (1005, 9, 1, _s(description)),  # description
        (1006, 4, 1, _i32(buildtime)),  # buildtime
        (1007, 6, 1, _s(buildhost)),  # buildhost
        (1009, 4, 1, _i32(total_size)),  # size
        (1014, 6, 1, _s(license_text)),  # copyright (license)
        (1016, 9, 1, _s(group)),  # group
        (1020, 6, 1, _s(url)),  # url
        (1021, 6, 1, _s("linux")),  # os
        (1022, 6, 1, _s(arch)),  # arch
        (1028, 4, len(files), _i32a([len(c) for _, c, _, _ in files])),  # filesizes
        (1030, 3, len(files), _i16a([m for _, _, m, _ in files])),  # filemodes
        (1033, 3, len(files), _i16a([0] * len(files))),  # filerdevs
        (1034, 4, len(files), _i32a([t for _, _, _, t in files])),  # filemtimes
        (1035, 8, len(files), _stra([""] * len(files))),  # filemd5s
        (1036, 8, len(files), _stra([""] * len(files))),  # filelinktos
        (1044, 6, 1, _s(sourcerpm)),  # sourcerpm
        (1095, 4, len(files), _i32a([0] * len(files))),  # filedevices
        (1096, 4, len(files), _i32a(list(range(1, len(files) + 1)))),  # fileinodes
        (1097, 8, len(files), _stra([""] * len(files))),  # filelangs
        (1116, 4, len(files), _i32a(dirindexes)),  # dirindexes
        (1117, 8, len(files), _stra(basenames)),  # basenames
        (1118, 8, len(dirnames), _stra(dirnames)),  # dirnames
        (1124, 6, 1, b"cpio\x00"),  # archive_format
        (1125, 6, 1, compress_tag + b"\x00"),  # archive_compression
    ]
    main_header = _rpm_header(main_entries)

    sig_entries = [
        (1000, 4, 1, _i32(len(main_header) + len(compressed))),  # size
        (1004, 7, 16, hashlib.md5(main_header + compressed).digest()),  # sigmd5
        (1007, 4, 1, _i32(len(cpio_data))),  # payloadsize
    ]
    sig_header = _rpm_header(sig_entries)
    # Pad signature section to 8-byte boundary
    sig_header += b"\x00" * ((8 - len(sig_header) % 8) % 8)

    archnum = 255 if arch == "noarch" else 1
    lead = struct.pack(
        "!4sBBhh66shh16s",
        b"\xed\xab\xee\xdb",  # magic
        3,
        0,  # major, minor
        0,  # type (binary)
        archnum,
        "{}-{}-{}".format(name, version, release)[:65].encode().ljust(66, b"\x00"),
        1,  # osnum (linux)
        5,  # sig_type
        b"\x00" * 16,  # reserved
    )

    return lead + sig_header + main_header + compressed


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------


class TestExtract(unittest.TestCase):
    """Tests for RPMFile extraction with different compression algorithms.

    All RPMs used in the test suite are generated once in :meth:`setUpClass`
    and stored in a temporary directory that is cleaned up in
    :meth:`tearDownClass`.  No network access and no pre-built binary files
    are required.
    """

    tempdir = None

    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls._build_test_rpms()

    @classmethod
    def tearDownClass(cls):
        if cls.tempdir:
            shutil.rmtree(cls.tempdir)
            cls.tempdir = None

    @classmethod
    def _build_test_rpms(cls):
        """Generate all RPM fixtures used by the test methods."""

        def write(filename, **kwargs):
            path = os.path.join(cls.tempdir, filename)
            with open(path, "wb") as fh:
                fh.write(make_rpm(**kwargs))

        _common = dict(
            version="1.0",
            release="1",
            arch="noarch",
            group="default",
            license_text="MIT",
            url="http://example.com",
            buildtime=0,
            buildhost="localhost",
        )

        # --- gzip RPM ---------------------------------------------------------
        # Shared fixture for tests that only need a basic gzip-compressed RPM.
        # Contains two files so that multi-value header fields (e.g. filemodes)
        # are stored as arrays rather than scalars.
        write(
            "test-gzip.rpm",
            name="test-gzip",
            summary="Gzip test package",
            description="Gzip compression test",
            sourcerpm="test-gzip-1.0-1.src.rpm",
            files=[
                (
                    "./usr/share/doc/test-gzip/AUTHORS",
                    b"A" * 1668,
                    0o100644,
                    0,
                ),
                (
                    "./usr/share/doc/test-gzip/LICENSE",
                    b"L" * 1555,
                    0o100644,
                    0,
                ),
            ],
            compression="gzip",
            **_common,
        )

        # --- xz RPM -----------------------------------------------------------
        # Used by test_lzma.  Only built when lzma is available (_HAVE_LZMA).
        if _HAVE_LZMA:
            write(
                "test-xz.rpm",
                name="test-xz",
                summary="XZ test package",
                description="XZ (lzma) compression test",
                sourcerpm="test-xz-1.0-1.src.rpm",
                files=[
                    (
                        "./usr/share/test-package/hello.txt",
                        b"Hello, World!\n",
                        0o100644,
                        0,
                    ),
                    (
                        "./usr/share/test-package/goodbye.txt",
                        b"Goodbye, World!\n",
                        0o100644,
                        0,
                    ),
                ],
                compression="xz",
                **_common,
            )

        # --- zstd RPM ---------------------------------------------------------
        # Used by test_zstd.  Only built when zstandard is available (_HAVE_ZSTD).
        if _HAVE_ZSTD:
            write(
                "test-zstd.rpm",
                name="test-zstd",
                summary="Zstd test package",
                description="Zstd compression test",
                sourcerpm="test-zstd-1.0-1.src.rpm",
                files=[
                    (
                        "./usr/bin/test-zstd",
                        b"This is a test binary for zstd.\n",
                        0o100755,
                        0,
                    ),
                    (
                        "./usr/share/doc/test-zstd/ChangeLog",
                        b"\n",
                        0o100644,
                        0,
                    ),
                ],
                compression="zstd",
                **_common,
            )

        # --- unsigned-ints RPM ------------------------------------------------
        # Used by test_unsigned_ints: verifies that uint32 header fields are
        # read correctly (filemtimes[0]=1689811200, mode=0o100755).
        # Two files are needed so the header fields are stored as arrays
        # rather than scalars, matching real-world RPM behaviour.
        write(
            "test-unsigned.rpm",
            name="test-unsigned",
            summary="Unsigned-ints test package",
            description="Unsigned integer header fields test",
            sourcerpm="test-unsigned-1.0-1.src.rpm",
            files=[
                (
                    "./usr/bin/hello",
                    b"hello\n",
                    stat.S_IFREG | 0o755,
                    1689811200,
                ),
                (
                    "./usr/share/doc/test-unsigned/README",
                    b"readme\n",
                    stat.S_IFREG | 0o644,
                    0,
                ),
            ],
            compression="gzip",
            **_common,
        )

    # ------------------------------------------------------------------
    # Individual test methods
    # ------------------------------------------------------------------

    @unittest.skipUnless(_HAVE_LZMA, "lzma module not available")
    def test_lzma(self):
        """Test that xz/lzma-compressed RPMs can be read and extracted."""
        rpmpath = os.path.join(self.tempdir, "test-xz.rpm")
        with rpmfile.open(rpmpath) as rpm:
            self.assertIn("name", rpm.headers.keys())
            self.assertEqual(rpm.headers.get("arch", "noarch"), b"noarch")

            members = list(rpm.getmembers())
            self.assertEqual(len(members), 2)

            with rpm.extractfile("./usr/share/test-package/hello.txt") as fd:
                calculated = hashlib.md5(fd.read()).hexdigest()
                self.assertEqual("bea8252ff4e80f41719ea13cdf007273", calculated)

    @unittest.skipUnless(_HAVE_ZSTD, "zstandard module not available")
    def test_zstd(self):
        """Test that zstd-compressed RPMs can be read and extracted."""
        rpmpath = os.path.join(self.tempdir, "test-zstd.rpm")
        with rpmfile.open(rpmpath) as rpm:
            self.assertIn("name", rpm.headers.keys())
            self.assertEqual(rpm.headers.get("arch", "noarch"), b"noarch")

            members = list(rpm.getmembers())
            self.assertEqual(len(members), 2)

            with rpm.extractfile("./usr/bin/test-zstd") as fd:
                calculated = hashlib.md5(fd.read()).hexdigest()
                self.assertEqual(calculated, "0debacccbf83d0d3849e8487ce5de2e9")

            with rpm.extractfile("./usr/share/doc/test-zstd/ChangeLog") as fd:
                calculated = hashlib.md5(fd.read()).hexdigest()
                self.assertEqual(calculated, "68b329da9893e34099c7d8ad5cb9c940")

    def test_autoclose(self):
        """Test that RPMFile.open context manager properly closes the file."""
        rpmpath = os.path.join(self.tempdir, "test-gzip.rpm")

        rpm_ref = None
        with rpmfile.open(rpmpath) as rpm:
            rpm_ref = rpm

            self.assertIn("name", rpm.headers.keys())
            self.assertEqual(rpm.headers.get("arch", "noarch"), b"noarch")

            members = list(rpm.getmembers())
            self.assertEqual(len(members), 2)

            # Test that extractfile does not close the parent file; close the
            # sub-file and then extract another member successfully.
            fd = rpm.extractfile("./usr/share/doc/test-gzip/AUTHORS")
            calculated = hashlib.md5(fd.read()).hexdigest()
            self.assertEqual(calculated, "beb5588f8c8be1365297cdb7045f71b3")
            fd.close()

            fd = rpm.extractfile("./usr/share/doc/test-gzip/LICENSE")
            calculated = hashlib.md5(fd.read()).hexdigest()
            self.assertEqual(calculated, "efb958d6031d2e92100eef119fb52449")
            fd.close()

        # The context manager must have closed the underlying file descriptor.
        self.assertTrue(rpm_ref._fileobj.closed)
        self.assertTrue(rpm_ref._ownes_fd)

    def test_issue_19(self):
        """Regression test: getmembers() returns the correct count."""
        rpmpath = os.path.join(self.tempdir, "test-gzip.rpm")
        with rpmfile.open(rpmpath) as rpm:
            self.assertEqual(len(list(rpm.getmembers())), 2)

    def test_unsigned_ints(self):
        """Test that unsigned-integer header fields are parsed correctly."""
        rpmpath = os.path.join(self.tempdir, "test-unsigned.rpm")
        with rpmfile.open(rpmpath) as rpm:
            self.assertEqual(1689811200, rpm.headers["filemtimes"][0])
            mode = rpm.headers["filemodes"][0]
            st_type = stat.S_IFMT(mode)
            st_mode = stat.S_IMODE(mode)
            self.assertTrue(stat.S_ISREG(st_type))
            self.assertEqual(
                stat.S_IRUSR
                | stat.S_IWUSR
                | stat.S_IXUSR
                | stat.S_IRGRP
                | stat.S_IXGRP
                | stat.S_IROTH
                | stat.S_IXOTH,
                st_mode,
            )
