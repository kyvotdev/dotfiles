#!/usr/bin/env python3
"""Themed clipboard history; original bytes never pass through menu labels."""
import argparse
import subprocess
from common import choose, confirm, guarded, notify, run, IC


def entries():
    return run('cliphist', 'list').stdout.splitlines()


def select(title):
    records = entries()
    if not records:
        notify('Clipboard', 'History is empty. Copy text or an image first.')
        return None
    rows = []
    for record in records:
        _, separator, preview = record.partition('\t')
        if not separator:
            continue
        icon = IC['image'] if 'binary' in preview.lower() else IC['copy']
        rows.append((icon + '  ' + preview, record))
    return choose(title, rows, message='Type to search · Enter to select · Esc to close')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', default='pick', choices=['pick', 'menu', 'delete', 'clear'])
    action = parser.parse_args().action
    if action == 'menu':
        action = choose('Clipboard', [(IC['copy']+'  Clipboard history', 'pick'),
                                     (IC['trash']+'  Delete entry', 'delete'),
                                     (IC['trash']+'  Clear history', 'clear')])
    if action == 'clear':
        if confirm('Clear clipboard history?'):
            run('cliphist', 'wipe')
            run('wl-copy', '--clear')
            notify('Clipboard', 'History and current clipboard cleared')
        return
    if action not in ('pick', 'delete'):
        return
    record = select('Delete clipboard entry' if action == 'delete' else 'Clipboard history')
    if record is None:
        return
    if action == 'delete':
        subprocess.run(['cliphist', 'delete'], input=record.encode(), check=True, capture_output=True)
        return
    data = subprocess.run(['cliphist', 'decode'], input=record.encode(), capture_output=True, check=True).stdout
    subprocess.run(['wl-copy'], input=data, check=True, capture_output=True)


if __name__ == '__main__':
    guarded(main)
