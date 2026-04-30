import os
import sys
import gzip
import shutil
import hashlib
import stat
import tempfile
import unittest
from functools import wraps

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

import rpmfile

# Directory containing bundled RPM test fixtures.
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def download(url, rpmname):
    """Decorator that provides an RPM file path to the test method.

    Looks for *rpmname* inside the local ``tests/data/`` directory first so
    that the test suite can run without a network connection when the sdist
    ships with pre-built test data.  Falls back to downloading from *url*
    when the file is not available locally.
    """

    def _downloader(func):
        @wraps(func)
        def wrapper(*args, **kwds):
            args = list(args)
            local_file = os.path.join(DATA_DIR, rpmname)
            if os.path.exists(local_file):
                rpmpath = local_file
            else:
                rpmpath = os.path.join(args[0].tempdir, rpmname)
                gztemp = os.path.join(args[0].tempdir, "temp.gz")
                response = urlopen(url)
                if url.endswith(".gz"):
                    with open(gztemp, "wb") as gztemp_file:
                        gztemp_file.write(response.read())
                    response.close()
                    response = gzip.open(gztemp, "rb")
                with open(rpmpath, "wb") as target_file:
                    target_file.write(response.read())
                response.close()
                if url.endswith(".gz"):
                    os.unlink(gztemp)
            args.append(rpmpath)
            return func(*args, **kwds)

        return wrapper

    return _downloader


class TestExtract(unittest.TestCase):
    @unittest.skipUnless(
        sys.version_info.major >= 3 and sys.version_info.minor >= 3, "Need lzma module"
    )
    def test_lzma(self):
        """Test that xz/lzma-compressed RPMs can be read and extracted."""
        rpmpath = os.path.join(DATA_DIR, "test-rpm-xz.noarch.rpm")
        with rpmfile.open(rpmpath) as rpm:
            # Inspect the RPM headers
            self.assertIn("name", rpm.headers.keys())
            self.assertEqual(rpm.headers.get("arch", "noarch"), b"noarch")

            members = list(rpm.getmembers())
            self.assertEqual(len(members), 2)

            with rpm.extractfile("./usr/share/test-package/hello.txt") as fd:
                calculated = hashlib.md5(fd.read()).hexdigest()
                self.assertEqual("bea8252ff4e80f41719ea13cdf007273", calculated)

    @unittest.skipUnless(
        sys.version_info.major >= 3 and sys.version_info.minor >= 5, "Need io.BytesIO"
    )
    def test_zstd_xmlstarlet(self):
        """Test that zstd-compressed RPMs can be read and extracted."""
        rpmpath = os.path.join(DATA_DIR, "xmlstarlet.rpm")
        with rpmfile.open(rpmpath) as rpm:
            # Inspect the RPM headers
            self.assertIn("name", rpm.headers.keys())
            self.assertEqual(rpm.headers.get("arch", "noarch"), b"x86_64")

            members = list(rpm.getmembers())
            self.assertEqual(len(members), 12)

            with rpm.extractfile("./usr/bin/xmlstarlet") as fd:
                calculated = hashlib.md5(fd.read()).hexdigest()
                self.assertEqual(calculated, "c5e22d7e47751565b56e507cb6ee375e")

            with rpm.extractfile("./usr/share/doc/xmlstarlet/ChangeLog") as fd:
                calculated = hashlib.md5(fd.read()).hexdigest()
                self.assertEqual(calculated, "68b329da9893e34099c7d8ad5cb9c940")

    def test_autoclose(self):
        """Test that RPMFile.open context manager properly closes rpm file."""
        rpmpath = os.path.join(DATA_DIR, "gopacket.rpm")

        rpm_ref = None
        with rpmfile.open(rpmpath) as rpm:
            rpm_ref = rpm

            # Inspect the RPM headers
            self.assertIn("name", rpm.headers.keys())
            self.assertEqual(rpm.headers.get("arch", "noarch"), b"noarch")

            members = list(rpm.getmembers())
            self.assertEqual(len(members), 2)

            # Test that subfile does not close parent file by calling close and
            # then extractfile again
            fd = rpm.extractfile("./usr/share/doc/gopacket-license/AUTHORS")
            calculated = hashlib.md5(fd.read()).hexdigest()
            self.assertEqual(calculated, "3cfb2ca4a1dbc26b71e869ef66434705")
            fd.close()

            fd = rpm.extractfile("./usr/share/doc/gopacket-license/LICENSE")
            calculated = hashlib.md5(fd.read()).hexdigest()
            self.assertEqual(calculated, "b32b347fe7ed4541e05033e8b0b29001")
            fd.close()

        # Test that RPMFile owned file descriptor and that underlying file is really closed
        self.assertTrue(rpm_ref._fileobj.closed)
        self.assertTrue(rpm_ref._ownes_fd)

    def test_issue_19(self):
        """Regression test for issue #19 (member count)."""
        rpmpath = os.path.join(DATA_DIR, "gopacket.rpm")
        with rpmfile.open(rpmpath) as rpm:
            self.assertEqual(len(list(rpm.getmembers())), 2)

    def test_unsigned_ints(self):
        """Test that unsigned-integer header fields are parsed correctly."""
        rpmpath = os.path.join(DATA_DIR, "hello.rpm")
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
