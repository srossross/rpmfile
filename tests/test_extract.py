import os
import sys
import gzip
import shutil
import hashlib
import tempfile
import unittest
from functools import wraps
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

import rpmfile

def download(url, rpmname):
    def _downloader(func):
        @wraps(func)
        def wrapper(*args, **kwds):
            args = list(args)
            rpmpath = os.path.join(args[0].tempdir, rpmname)
            gztemp = os.path.join(args[0].tempdir, "temp.gz")
            args.append(rpmpath)
            download = urlopen(url)
            if url[::-1].startswith('.gz'[::-1]):
                with open(gztemp, 'wb') as gztemp_file:
                    gztemp_file.write(download.read())
                download.close()
                download = gzip.open(gztemp, 'rb')
            with open(rpmpath, 'wb') as target_file:
                target_file.write(download.read())
            download.close()
            if url[::-1].startswith('.gz'[::-1]):
                os.unlink(gztemp)
            return func(*args, **kwds)
        return wrapper
    return _downloader

class TempDirTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.prevdir = os.getcwd()
        cls.tempdir = tempfile.mkdtemp()
        os.chdir(cls.tempdir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)
        os.chdir(cls.prevdir)

    @unittest.skipUnless(sys.version_info.major >= 3 \
                            and sys.version_info.minor >= 3,
                         'Need lzma module')
    @download('https://download.clearlinux.org/releases/10540/clear/x86_64/os/Packages/sudo-setuid-1.8.17p1-34.x86_64.rpm', 'sudo.rpm')
    def test_lzma_sudo(self, rpmpath):
        with rpmfile.open(rpmpath) as rpm:

            # Inspect the RPM headers
            self.assertIn('name', rpm.headers.keys())
            self.assertEqual(rpm.headers.get('arch', 'noarch'), b'x86_64')

            members = list(rpm.getmembers())
            self.assertEqual(len(members), 1)

            with rpm.extractfile('./usr/bin/sudo') as fd:
                calculated = hashlib.md5(fd.read()).hexdigest()
                self.assertEqual(calculated, 'a208f3d9170ecfa69a0f4ccc78d2f8f6')


    @download('https://download.fedoraproject.org/pub/fedora/linux/releases/30/Everything/source/tree/Packages/r/rpm-4.14.2.1-4.fc30.1.src.rpm', 'sample.rpm')
    def test_autoclose(self, rpmpath):
        """Test that RPMFile.open context manager properly closes rpm file"""

        rpm_ref = None
        with rpmfile.open(rpmpath) as rpm:
            rpm_ref = rpm

            # Inspect the RPM headers
            self.assertIn('name', rpm.headers.keys())
            self.assertEqual(rpm.headers.get('arch', 'noarch'), b'x86_64')

            members = list(rpm.getmembers())
            self.assertEqual(len(members), 13)

            # Test that subfile does not close parent file by calling close and
            # then extractfile again
            fd = rpm.extractfile('rpm-4.13.90-ldflags.patch')
            calculated = hashlib.md5(fd.read()).hexdigest()
            self.assertEqual(calculated, '4841553ad9276fffd83df33643839a57')
            fd.close()

            fd = rpm.extractfile('rpm.spec')
            calculated = hashlib.md5(fd.read()).hexdigest()
            self.assertEqual(calculated, 'ed96e23cf7f8dd17c459e0dd4618888c')
            fd.close()

        # Test that RPMFile owned file descriptor and that underlying file is really closed
        self.assertTrue(rpm_ref._fileobj.closed)
        self.assertTrue(rpm_ref._ownes_fd)

    @download('https://github.com/srossross/rpmfile/files/3150016/gopacket-license.noarch.rpm.gz', 'gopacket.rpm')
    def test_issue_19(self, rpmpath):
        with rpmfile.open(rpmpath) as rpm:
            self.assertEqual(len(list(rpm.getmembers())), 2)
