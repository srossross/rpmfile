from __future__ import print_function

from datetime import datetime
import os
import io
import sys
import argparse

import rpmfile


def console_script_entry_point():
    main(*sys.argv[1:])


def main(*argv):
    parser = argparse.ArgumentParser(prog="rpmfile")
    parser.add_argument("infile")
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
    parser.add_argument(
        "-i",
        "--info",
        dest="info",
        action="store_true",
        help="Display RPM information without extracting",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Print filenames when extracting",
    )
    args = parser.parse_args(argv)

    if args.infile == "-":
        args.infile = sys.stdin
        if sys.version_info.major >= 3:
            args.infile = args.infile.buffer
    else:
        args.infile = open(args.infile, "rb")

    # NOTE Not sure why but piping to rpmfile doesn't work unless we read
    # everything first into a buffer. Probably because of seek().
    buf = io.BytesIO(args.infile.read())

    output = {}

    if args.list:
        output["list"] = []
        with rpmfile.open(fileobj=buf) as rpm:
            for rpminfo in rpm.getmembers():
                print(rpminfo.name)
                output["list"].append(rpminfo.name.split("/"))
    elif args.info:
        output["info"] = ""
        with rpmfile.open(fileobj=buf) as rpm:
            headers_titles = {
                "name": "Name",
                "version": "Version",
                "release": "Release",
                "arch": "Architecture",
                "group": "Group",
                "size": "Size",
                "copyright": "License",
                "signature": "Signature",
                "sourcerpm": "Source RPM",
                "buildtime": "Build Date",
                "buildhost": "Build Host",
                "url": "URL",
                "summary": "Summary",
                "description": "Description",
            }
            for header in headers_titles:
                value = rpm.headers.get(header)
                if isinstance(value, bytes):
                    value = value.decode()
                if header == "buildtime":
                    value = datetime.fromtimestamp(value).strftime("%c")
                if header == "description":
                    value = "\n" + value
                line = "%s: %s" % (headers_titles.get(header).ljust(12), value)
                print(line)
                output["info"] += line + "\n"
    elif args.extract:
        output["extracted"] = []
        dest = os.path.abspath(args.dest)
        if not os.path.isdir(dest):
            raise FileNotFoundError(dest + " is not a directory")
        with rpmfile.open(fileobj=buf) as rpm:
            for rpminfo in rpm.getmembers():
                with rpm.extractfile(rpminfo.name) as rpmfileobj:
                    dirs = rpminfo.name.split("/")
                    filename = dirs.pop()
                    if dirs:
                        dirs_path = os.path.abspath(os.path.join(dest, *dirs))
                        if not dirs_path.startswith(dest):
                            raise ValueError("Attempted path traveral: " + dirs_path)
                        if not os.path.isdir(dirs_path):
                            os.makedirs(dirs_path)
                    target = os.path.abspath(os.path.join(dest, *(dirs + [filename])))
                    if not target.startswith(dest):
                        raise ValueError("Attempted path traveral: " + target)
                    outfile = open(target, "wb")
                    try:
                        outfile.write(rpmfileobj.read())
                    finally:
                        outfile.close()
                    if args.verbose:
                        print(target)
                    output["extracted"].append(rpminfo.name.split("/"))
    else:
        raise Exception("Nothing to do")

    buf.close()
    args.infile.close()

    return args, output
