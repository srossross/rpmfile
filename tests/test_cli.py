import os
import shutil
import tempfile
import unittest

from rpmfile.cli import main

from .test_extract import download


class TempCLI(unittest.TestCase):
    GOPACKET_LICENSE_DIRS = [".", "usr", "share", "doc", "gopacket-license"]
    GOPACKET_LICENSE_FILES = ["AUTHORS", "LICENSE"]

    def setUp(cls):
        cls.prevdir = os.getcwd()
        cls.tempdir = tempfile.mkdtemp()
        os.chdir(cls.tempdir)

    def tearDown(cls):
        shutil.rmtree(cls.tempdir)
        os.chdir(cls.prevdir)

    @download(
        "https://github.com/srossross/rpmfile/files/3150016/gopacket-license.noarch.rpm.gz",
        "gopacket.rpm",
    )
    def test_extract(self, rpmpath):
        """That the command line extracts correctly"""
        dest = os.path.join(self.tempdir, "mydir")
        os.mkdir(dest)

        _args, output = main("-xC", dest, rpmpath)

        extracted_files = os.listdir(
            os.path.join(self.tempdir, "mydir", *self.GOPACKET_LICENSE_DIRS)
        )
        self.assertEqual(self.GOPACKET_LICENSE_FILES, sorted(extracted_files))

        self.assertEqual(len(output["extracted"]), len(self.GOPACKET_LICENSE_FILES))
        for filename in self.GOPACKET_LICENSE_FILES:
            self.assertIn(self.GOPACKET_LICENSE_DIRS + [filename], output["extracted"])

    @download(
        "https://github.com/srossross/rpmfile/files/3150016/gopacket-license.noarch.rpm.gz",
        "gopacket.rpm",
    )
    def test_list(self, rpmpath):
        """That the command line lists correctly"""
        _args, output = main("-l", rpmpath)

        self.assertEqual(len(output["list"]), len(self.GOPACKET_LICENSE_FILES))
        for filename in self.GOPACKET_LICENSE_FILES:
            self.assertIn(self.GOPACKET_LICENSE_DIRS + [filename], output["list"])
