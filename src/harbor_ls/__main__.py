#!/usr/bin/env python3

import sys

if sys.version_info.major == 3 and sys.version_info.minor < 9:
    print("Python 3.9 or higher is required.", file=sys.stderr)
    sys.exit(1)

import json
import logging
import os
import sys
from argparse import ArgumentParser

from harbor_ls import HarborLs

import urllib.error
import urllib.request


def _activate_urllib_debug_logging() -> None:
    handlers = [urllib.request.HTTPHandler(debuglevel=1), urllib.request.HTTPSHandler(debuglevel=1)]
    opener = urllib.request.build_opener(*handlers)
    urllib.request.install_opener(opener)


def _print_results_json(results: dict, indent=4) -> None:
    print(json.dumps(results, indent=indent, sort_keys=True))


def _print_results_text(results: dict) -> None:
    for project, repos in results.items():
        print(f'{project}')
        for repo, artefacts in repos.items():
            print(f'\t{repo}')
            for a in sorted(artefacts, key=lambda x: x['time'], reverse=True):
                print(f'\t\t{a["time"]} {a["digest"]} {" ".join(sorted(a["tags"]))}')


def cli(argv: list[str] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    parser = ArgumentParser()
    parser.add_argument('-u', '--user', metavar='USER', default=os.environ.get('HARBOR_USER'))
    parser.add_argument('-p', '--password', metavar='PASS', default=os.environ.get('HARBOR_PASSWORD'))
    parser.add_argument('-r', '--registry', metavar='REG', default=os.environ.get('HARBOR_REGISTRY'))
    parser.add_argument('-l', '--level', choices=['debug', 'info', 'warning', 'error', 'critical'], default='warning')
    parser.add_argument('-f', '--format', choices=['text', 'json'], default='text')
    parser.add_argument('filters', nargs='*')
    args = parser.parse_args(argv)
    logging.basicConfig(format='%(levelname)s %(message)s', level=getattr(logging, args.level.upper()))
    if args.level == 'debug':
        _activate_urllib_debug_logging()

    try:
        scanner = HarborLs(registry_fqdn=args.registry, user=args.user, password=args.password, filters=args.filters)
    except ValueError as e:
        logging.error(f'Initialization failed: {e}')
        sys.exit(1)
    try:
        results = scanner.ls()
    except KeyboardInterrupt:
        logging.info(f'Interrupted. Exiting...')
        sys.exit(2)

    if args.format == 'json':
        _print_results_json(results)
    elif args.format == 'text':
        _print_results_text(results)
    else:
        logging.error(f'Unknown format: {args.format}')
        sys.exit(1)


if __name__ == '__main__':
    cli()
