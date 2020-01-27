#!/usr/bin/env python3
import argparse
import logging
from .client import Client


def standalone():
    '''Standalone command for LSST Argo Workflow API Client
    '''
    allowed = ['list', 'create', 'delete', 'inspect', 'logs', 'pod',
               'details', 'version']
    parser = argparse.ArgumentParser(
        description="LSST Argo Workflow API Client")
    parser.add_argument("operation",
                        default="list",
                        help=("Operation (one of 'list', 'new', 'delete', " +
                              "'inspect', 'logs', 'pods', 'details', or " +
                              "'version')"))
    parser.add_argument("-u", "--url", help="Workflow API Server URL",
                        default="http://localhost:8080/")
    parser.add_argument("-j", "--json", "--json-post-file",
                        help=("File containing POST body in JSON format " +
                              "(required for 'create')"))
    parser.add_argument("-w", "--workflow_id",
                        default='',
                        help=("Workflow ID (required for 'delete', " +
                              "'inspect', 'logs', 'pods', 'details')"))
    parser.add_argument("-p", "--pod_id",
                        default='',
                        help="Pod ID (required for 'details')")
    parser.add_argument("-d", "--debug", action='store_true',
                        help="Enable debug logging.")
    args = parser.parse_args()
    op = args.operation
    if op not in allowed:
        raise ValueError("Operation must be one of '{}'".format(allowed))
    for needs_wf in ['delete', 'inspect', 'pods', 'log', 'details']:
        if needs_wf == op:
            if not args.workflow_id:
                raise ValueError("Operation '{}' requires workflow ID".format(
                    op))
    if op == "details":
        if not args.pod_id:
            raise ValueError(
                "Operation '{}' requires pod ID".format(op))
    if op == "create" and not args.json:
        raise ValueError(
            "Operation '{}' requires input JSON".format(op))
    client = Client(api_url=args.url, post_json_file=args.json)
    if args.debug:
        client.log.setLevel(logging.DEBUG)
    if op == "list":
        client.list()
    elif op == "create":
        client.new()
    elif op == "version":
        client.version()
    wf = args.workflow_id
    if op == "delete":
        client.delete(wf)
    elif op == "inspect":
        client.inspect(wf)
    elif op == "logs":
        client.logs(wf)
    elif op == "pods":
        client.pods(wf)
    elif op == "details":
        client.details(wf, args.pod_id)
    client.show_response()


if __name__ == '__main__':
    standalone()
