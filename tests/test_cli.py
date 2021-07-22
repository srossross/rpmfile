import os
import shutil
import tempfile
import time
import unittest

from rpmfile.cli import main

from .test_extract import download


class TempCLI(unittest.TestCase):
    GOPACKET_LICENSE_DIRS = [".", "usr", "share", "doc", "gopacket-license"]
    GOPACKET_LICENSE_FILES = ["AUTHORS", "LICENSE"]
    GOPACKET_LICENSE_INFO = (
        "Name        : gopacket-license\n"
        "Version     : 2019_04_08T07_36_42Z\n"
        "Release     : 1\n"
        "Architecture: noarch\n"
        "Group       : default\n"
        "Size        : 3223\n"
        "License     : BSD\n"
        "Signature   : None\n"
        "Source RPM  : gopacket-license-2019_04_08T07_36_42Z-1.src.rpm\n"
        "Build Date  : Tue Apr  9 08:55:16 2019\n"
        "Build Host  : jenkins-slave-fat-cloud-nlbzt\n"
        "URL         : http://example.com/no-uri-given\n"
        "Summary     : License for gopacket-license\n"
        "Description : \n"
        "License for gopacket-license\n"
    )

    def setUp(cls):
        cls.prevdir = os.getcwd()
        cls.tempdir = tempfile.mkdtemp()
        os.chdir(cls.tempdir)
        os.environ["LC_ALL"] = "C"
        os.environ["TZ"] = "UTC"
        time.tzset()

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

    @download(
        "https://github.com/srossross/rpmfile/files/3150016/gopacket-license.noarch.rpm.gz",
        "gopacket.rpm",
    )
    def test_info(self, rpmpath):
        """That the command line get RPM infomation correctly"""
        _args, output = main("-i", rpmpath)
        self.assertEqual(output["info"], self.GOPACKET_LICENSE_INFO)
