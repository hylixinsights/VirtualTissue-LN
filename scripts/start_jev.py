#!/usr/bin/env python3
"""Start the illustrated LN directly with Jev; secrets stay in this process."""
import argparse
import getpass
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from scripts import record_reactive


def request_cap(value):
    try:
        cap = int(value)
    except (ValueError, TypeError):
        raise ValueError('Enter an integer request limit between 1 and 100000.') from None
    if not 1 <= cap <= 100000:
        raise ValueError('Enter an integer request limit between 1 and 100000.')
    return cap


def main(argv=None):
    parser = argparse.ArgumentParser(description='Illustrated LN with individual Jev decisions.')
    parser.add_argument('--port', type=int, default=8022)
    parser.add_argument('--cells', type=int, choices=range(100,150), default=120)
    parser.add_argument('--max-decisions', type=request_cap, default=10)
    parser.add_argument('--max-requests', type=request_cap)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--preview', action='store_true',help='Use the earlier manually stepped ten-decision preview.')
    parser.add_argument('--policy',choices=record_reactive.POLICIES,default='development')
    parser.add_argument('--seed',type=int,default=21)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--resume',action='store_true',help='Verify and continue an existing complete checkpoint with the same total call cap.')
    args = parser.parse_args(argv)
    server.load_env()
    if not os.environ.get('TYPESAFE_API_KEY', '').strip():
        if not sys.stdin.isatty():
            parser.error('Set TYPESAFE_API_KEY locally or open Start Jev.cmd to enter the key through hidden input.')
        key = getpass.getpass('TypeSafe / Jev key (hidden; kept only in this session): ').strip()
        if not key:
            parser.error('A TypeSafe key is required to start Jev.')
        os.environ['TYPESAFE_API_KEY'] = key
    cap = args.max_requests
    if cap is None:
        if not sys.stdin.isatty():
            parser.error('Specify --max-requests to set the per-run call limit.')
        print('This cap counts HTTP requests, not dollars. Quiet cells make no requests; only local responders are queried.')
        try:
            cap = request_cap(input('Maximum paid Jev calls for this run: ').strip())
        except ValueError as error:
            parser.error(str(error))
    if not args.preview:
        print(f'Starting an LN recording with {args.cells} resident cells and a hard cap of {cap} Jev calls.')
        print(record_reactive.POLICIES[args.policy])
        print('The run continues after division and antibody output. Ctrl+C saves and stops it. Replaying the recording is free of inference calls.')
        options=['--port',str(args.port),'--cells',str(args.cells),'--seed',str(args.seed),'--policy',args.policy,'--max-requests',str(cap)]
        if args.output:options+=['--output',str(args.output)]
        if args.resume:options.append('--resume')
        if not args.no_browser:options.append('--open-browser')
        record_reactive.main(options)
        return
    print(f'LN with Jev: {args.cells} cells, cap of {cap} requests. Opening the tissue makes no calls.')
    print(f'Introduce the dendritic cell, then run the tissue. This experiment allows at most {args.max_decisions} individual decisions.')
    options = ['--port', str(args.port), '--cells', str(args.cells), '--provider', 'jev', '--enable-jev', '--max-requests', str(cap), '--max-decisions', str(args.max_decisions)]
    if not args.no_browser:
        options.append('--open-browser')
    server.main(options)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nStartup cancelled.')
