import os
import argparse

import rpmfile


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", type=argparse.FileType("rb"))
    parser.add_argument(
        "-x",
        "--extract",
        dest="extract",
        action="store_true",
        help="Extract the input RPM",
    )
    parser.add_argument(
        "-C",
        "--directory",
        type=str,
        dest="dest",
        help="Extract to this directory when extracting files",
        default=".",
    )
    parser.add_argument(
        "-l",
        "--list",
        dest="list",
        action="store_true",
        help="List files in RPM without extracting",
    )
    args = parser.parse_args(argv)

    if args.list:
        with rpmfile.open(fileobj=args.infile) as rpm:
            for rpminfo in rpm.getmembers():
                print(rpminfo.name)
    elif args.extract:
        dest = os.path.abspath(args.dest)
        if not os.path.isdir(dest):
            raise FileNotFoundError(dest + " is not a directory")
        with rpmfile.open(fileobj=args.infile) as rpm:
            for rpminfo in rpm.getmembers():
                with rpm.extractfile(rpminfo.name) as rpmfileobj:
                    target = os.path.abspath(os.path.join(dest, rpminfo.name))
                    if not target.startswith(dest):
                        raise ValueError("Attempted path traveral: " + target)
                    with open(target, "wb") as outfile:
                        outfile.write(rpmfileobj.read())
                        print(target)
    else:
        raise Exception("Nothing to do")
