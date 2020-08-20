#!/usr/bin/env python3
import argparse
from .generator import Generator


def standalone():
    """Standalone command for generating header and body input files
    """
    parser = argparse.ArgumentParser(
        description="Generate header and body files for WF Dispatcher"
    )
    parser.add_argument(
        "-b", "--bodyfile", help="File for post data", default="postbody.json"
    )
    parser.add_argument(
        "-r", "--headerfile", help="Auth header file", default="authheader.txt"
    )
    parser.add_argument(
        "-m",
        "--mock",
        help="Make mock user, not from env",
        action="store_true",
    )
    args = parser.parse_args()
    generator = Generator(
        bodyfile=args.bodyfile, headerfile=args.headerfile, _mock=args.mock
    )
    generator.go()


if __name__ == "__main__":
    standalone()
