"""Tests for the rpmfile command-line interface."""

import os
import pathlib
import shutil
import sys
import tempfile
import time
import unittest

from rpmfile.cli import main

sys.path.append(str(pathlib.Path(__file__).parent.resolve()))
from test_extract import make_rpm


class TempCLI(unittest.TestCase):
    """CLI tests that operate on a gopacket-license–like RPM.

    The RPM is generated once for the entire class in :meth:`setUpClass` with
    metadata that matches the original gopacket-license package so that the
    expected strings in the test assertions remain stable.
    """

    GOPACKET_LICENSE_DIRS = [".", "usr", "share", "doc", "gopacket-license"]
    GOPACKET_LICENSE_FILES = ["AUTHORS", "LICENSE"]
    # Metadata fields that the CLI ``-i`` output must contain.
    # buildtime=1554800116 → "Tue Apr  9 08:55:16 2019" when TZ=UTC, LC_ALL=C.
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

    # AUTHORS (1668 B) + LICENSE (1555 B) = 3223 B, matching GOPACKET_LICENSE_INFO.
    _AUTHORS_CONTENT = b"A" * 1668
    _LICENSE_CONTENT = b"L" * 1555

    gopacket_rpm = None  # path to the generated RPM, set by setUpClass

    @classmethod
    def setUpClass(cls):
        cls._rpm_dir = tempfile.mkdtemp()
        rpm_bytes = make_rpm(
            name="gopacket-license",
            version="2019_04_08T07_36_42Z",
            release="1",
            arch="noarch",
            summary="License for gopacket-license",
            description="License for gopacket-license",
            group="default",
            license_text="BSD",
            url="http://example.com/no-uri-given",
            sourcerpm="gopacket-license-2019_04_08T07_36_42Z-1.src.rpm",
            buildtime=1554800116,
            buildhost="jenkins-slave-fat-cloud-nlbzt",
            files=[
                (
                    "./usr/share/doc/gopacket-license/AUTHORS",
                    cls._AUTHORS_CONTENT,
                    0o100644,
                    0,
                ),
                (
                    "./usr/share/doc/gopacket-license/LICENSE",
                    cls._LICENSE_CONTENT,
                    0o100644,
                    0,
                ),
            ],
            compression="gzip",
        )
        cls.gopacket_rpm = os.path.join(cls._rpm_dir, "gopacket.rpm")
        with open(cls.gopacket_rpm, "wb") as fh:
            fh.write(rpm_bytes)

    @classmethod
    def tearDownClass(cls):
        if cls._rpm_dir:
            shutil.rmtree(cls._rpm_dir)
            cls._rpm_dir = None
            cls.gopacket_rpm = None

    def setUp(self):
        self.prevdir = os.getcwd()
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        os.environ["LC_ALL"] = "C"
        os.environ["TZ"] = "UTC"
        time.tzset()

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        os.chdir(self.prevdir)

    def test_extract(self):
        """The command line extracts files to the correct directory tree."""
        dest = os.path.join(self.tempdir, "mydir")
        os.mkdir(dest)

        _args, output = main("-xC", dest, self.gopacket_rpm)

        extracted_files = os.listdir(
            os.path.join(self.tempdir, "mydir", *self.GOPACKET_LICENSE_DIRS)
        )
        self.assertEqual(self.GOPACKET_LICENSE_FILES, sorted(extracted_files))

        self.assertEqual(len(output["extracted"]), len(self.GOPACKET_LICENSE_FILES))
        for filename in self.GOPACKET_LICENSE_FILES:
            self.assertIn(self.GOPACKET_LICENSE_DIRS + [filename], output["extracted"])

    def test_list(self):
        """The command line lists the correct file paths."""
        _args, output = main("-l", self.gopacket_rpm)

        self.assertEqual(len(output["list"]), len(self.GOPACKET_LICENSE_FILES))
        for filename in self.GOPACKET_LICENSE_FILES:
            self.assertIn(self.GOPACKET_LICENSE_DIRS + [filename], output["list"])

    def test_info(self):
        """The command line displays RPM metadata correctly."""
        _args, output = main("-i", self.gopacket_rpm)
        self.assertEqual(output["info"], self.GOPACKET_LICENSE_INFO)
