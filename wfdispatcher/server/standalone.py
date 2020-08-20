#!/usr/bin/env python3
import argparse
from wsgiserver import WSGIServer
from .server import Server


def standalone():
    """Standalone command for starting a server.
    """
    parser = argparse.ArgumentParser(
        description="Start Argo Workflow API Dispatch Server"
    )
    parser.add_argument(
        "-p", "--port", help="Server listening port", type=int, default=8080
    )
    parser.add_argument(
        "-b", "--bind-address", help="Server bind address", default="127.0.0.1"
    )
    parser.add_argument(
        "-m",
        "--mock",
        "--mock-authentication",
        action="store_true",
        help="Do not require a JWT; mock out authentication",
    )
    parser.add_argument(
        "--no-verify-signature",
        action="store_true",
        help="Do not verify JWT signature",
    )
    parser.add_argument(
        "--no-verify-audience",
        action="store_true",
        help="Do not verify JWT audience",
    )
    args = parser.parse_args()
    mock = args.mock
    v_s = True
    v_a = True
    if args.no_verify_signature:
        v_s = False
    if args.no_verify_audience:
        v_a = False
    server = Server(_mock=mock, verify_signature=v_s, verify_audience=v_a)
    httpd = WSGIServer(server.app, host=args.bind_address, port=args.port)
    httpd.start()


if __name__ == "__main__":
    standalone()
