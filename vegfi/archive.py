#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import os

import requests

from .veg import SOURCE_API_URL


def get_new_data(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.content


def add_to_archive(target_name, data):
    """If the last line of `target` is not equal to `data`, append `data` to
    `target` and return True, otherwise do nothing and return False."""
    if not os.path.exists(target_name):
        open(target_name, 'w').close()

    with open(target_name, 'r+b') as target:
        prev_data = target.readlines()
        if not prev_data or data != prev_data[-1]:
            target.writelines([data])
            return True
    return False


def main():
    """Run main."""
    import argparse
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('target', metavar='FILE', help='The archive file.')
    args = parser.parse_args()

    data = get_new_data(SOURCE_API_URL)
    if add_to_archive(args.target, data):
        print("Archive updated")
    else:
        print("No new data")
    return 0

if __name__ == '__main__':
    main()
