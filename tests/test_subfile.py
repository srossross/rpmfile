"""
Created on Jan 11, 2014

@author: sean
"""
import unittest

import rpmfile
import io


class Test(unittest.TestCase):
    def test_seek(self):
        fd = io.BytesIO(b"Hello world")
        sub = rpmfile._SubFile(fd, start=2, size=4)

        sub.seek(0)
        self.assertEqual(sub.tell(), 0)

        sub.seek(1)
        self.assertEqual(sub.tell(), 1)

        sub.seek(1, 1)
        self.assertEqual(sub.tell(), 2)

        sub.seek(-1, 1)
        self.assertEqual(sub.tell(), 1)

        sub.seek(-10, 1)
        self.assertEqual(sub.tell(), 0)

    def test_read(self):
        fd = io.BytesIO(b"Hello world")
        sub = rpmfile._SubFile(fd, start=2, size=4)

        self.assertEqual(sub.read(), b"llo ")
        self.assertEqual(sub.read(), b"")

        sub.seek(0)
        self.assertEqual(sub.read(2), b"ll")

        sub.seek(0)
        self.assertEqual(sub.read(10), b"llo ")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testSeek']
    unittest.main()
