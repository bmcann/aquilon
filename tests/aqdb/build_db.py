#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2019  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" The way to populate an aqdb instance """

from __future__ import print_function

import argparse
import importlib
import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger('aqdb.populate')

import utils
utils.load_classpath()

from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers

from aquilon.config import Config
config = Config()

from aquilon.aqdb.model import *  # pylint: disable=W0401,W0614
from aquilon.aqdb.db_factory import DbFactory
from aquilon.aqdb.utils import constraints as cnst
from loader import load_from_file


BINDIR = os.path.dirname(os.path.realpath(__file__))


def importName(modulename, name):
    """ Import a named object from a module in the context of this function.
    """
    try:
        module = __import__(modulename, globals(), locals(), [name])
    except ImportError:
        return None
    try:
        return getattr(module, name)
    except AttributeError:
        print('getattr(%s, %s) failed (modulename = %s)' % (module,
                                                            name, modulename))


def parse_cli(*args, **kw):
    parser = argparse.ArgumentParser(
        description='rebuilds the aquilon data store (aqdb) from scratch')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='makes metadata bind.echo = True')

    parser.add_argument('-D', '--delete', action='store_true', dest='delete_db',
                        help='delete database without confirmation')

    parser.add_argument('-d', '--debug', action='store_true',
                        help='write debug info on stdout')

    parser.add_argument('-p', '--populate',
                        help='run functions to prepopulate data from the named file',
                        default=os.path.join(BINDIR, "data", "unittest.dump"))

    parser.add_argument('--no-populate', action='store_false', dest='populate',
                        help='disable populate')

    parser.add_argument('--dump',
                        help='dump the SQL commands instead of running them',
                        type=str)

    return parser.parse_args()


def main(*args, **kw):
    opts = parse_cli(args, kw)

    if opts.debug:
        log.setLevel(logging.DEBUG)

    db = DbFactory(verbose=opts.verbose)
    assert db, "No db_factory in build_db"

    if opts.dump:
        dialect = importlib.import_module(
            'sqlalchemy.dialects.{}'.format(opts.dump))
        dialect_inst = dialect.dialect()

        def metadata_dump(sql, *multiparams, **params):
            # We will print the data that passes by here using the
            # dialect that was requested
            print(sql.compile(dialect=dialect_inst))

        db.engine = create_engine(
            "sqlite:///:memory:",
            strategy='mock',
            executor=metadata_dump)

    Base.metadata.bind = db.engine

    if opts.delete_db:
        log.debug('Dropping database')
        # Let SQLAlchemy try first - it may not clean everything, e.g. if there
        # was a schema change
        Base.metadata.drop_all(checkfirst=True)
        # Clean up the rest
        db.drop_all_tables_and_sequences()

    if opts.populate:
        s = db.Session()
        assert s, "No Session in build_db.py populate"

    # Need to call this explicitely to make the __extra_table_args__ hack work
    configure_mappers()

    # Create all tables upfront
    Base.metadata.create_all(checkfirst=True)

    if opts.populate:
        load_from_file(s, opts.populate)

        env = os.environ.copy()
        env['AQDCONF'] = config.baseconfig
        rc = subprocess.call([os.path.join(os.path.dirname(os.path.dirname(BINDIR)), 'sbin', 'aqdb_set_role.py'),
                              '--role', 'aqd_admin'],
                             env=env, stdout=1, stderr=2)
        if rc != 0:
            log.warn("Failed to add current user as administrator.")

    # CONSTRAINTS
    if db.engine.dialect.name == 'oracle':
        # TODO: rename should be able to dump DDL to a file
        log.debug('renaming constraints...')
        cnst.rename_non_null_check_constraints(db)

    log.info('database built and populated')

if __name__ == '__main__':
    main(sys.argv)
