#!/usr/bin/python3
#
# Clean action implementation.
#
# Copyright (c) 2018 Xevo Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import errno
import logging
import os
import shutil

from wst import (
    dry_run,
    WSError
)
from wst.conf import (
    get_build_dir,
    get_build_env,
    get_build_props,
    get_ws_config,
    invalidate_checksum,
    parse_manifest,
    update_config
)


def args(parser):
    '''Populates the argument parser for the clean subcmd.'''
    parser.add_argument(
        'projects',
        action='store',
        nargs='*',
        help='Clean project(s)')
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        default=False,
        help='Force-clean (remove the build directory')


def force_clean(ws, proj):
    '''Performs a force-clean of a project, removing all files instead of
    politely calling the clean function of the underlying build system.'''
    build_dir = get_build_dir(ws, proj)
    logging.debug('removing %s' % build_dir)
    if dry_run():
        return
    try:
        shutil.rmtree(build_dir)
    except OSError as e:
        if e.errno == errno.ENOENT:
            logging.debug('%s already removed' % build_dir)
        else:
            raise

    config = get_ws_config(ws)
    config['taint'] = False
    update_config(ws, config)


def polite_clean(ws, proj, d):
    '''Performs a polite-clean of a project, calling the underlying build
    system of a project and asking it to clean itself.'''
    build_props = get_build_props(proj, d)
    build_dir = get_build_dir(ws, proj)
    if not os.path.exists(build_dir):
        return

    build_env = get_build_env(ws, proj, d)
    build_props['clean'](proj, build_dir, build_env)


def clean(ws, proj, force, d):
    '''Cleans a project, forcefully or not.'''
    invalidate_checksum(ws, proj)

    if force:
        force_clean(ws, proj)
    else:
        polite_clean(ws, proj, d)


def handler(ws, args):
    '''Executes the clean subcmd.'''
    # Validate.
    d = parse_manifest(args.root)
    for project in args.projects:
        if project not in d:
            raise WSError('unknown project %s' % project)

    if len(args.projects) == 0:
        projects = d.keys()
    else:
        projects = args.projects

    for project in projects:
        clean(ws, project, args.force, d)