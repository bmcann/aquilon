#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016-2018  Contributor
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
"""Module for testing the del hostlink command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelHostlink(TestBrokerCommand):

    def test_100_del_hostlink(self):
        path = ["resource", "host", "server1.aqd-unittest.ms.com",
                "hostlink", "app1", "config"]
        self.check_plenary_exists(*path)

        command = ["del_hostlink", "--hostlink=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        self.check_plenary_gone(*path, directory_gone=True)

    def test_101_del_hostlink_with_mode(self):
        path = ["resource", "host", "server1.aqd-unittest.ms.com",
                "hostlink", "app2", "config"]
        self.check_plenary_exists(*path)

        command = ["del_hostlink", "--hostlink=app2",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        self.check_plenary_gone(*path, directory_gone=True)

    def test_105_del_camelcase(self):
        path = ["resource", "host", "server1.aqd-unittest.ms.com",
                "hostlink", "camelcase", "config"]
        self.check_plenary_exists(*path)
        self.successtest(["del_hostlink", "--hostlink", "CaMeLcAsE",
                          "--hostname", "server1.aqd-unittest.ms.com"])
        self.check_plenary_gone(*path)

    def test_110_verify_del(self):
        command = ["show_host", "--hostname", "server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Hostlink", command)

    def test_300_del_hostlink_personality(self):
        path = [
            'resource',
            'personality', 'compileserver',
            'country', 'us',
            'hostlink', 'app_personality',
            'config',
        ]
        self.check_plenary_exists(*path)

        command = [
            'del_hostlink',
            '--hostlink', 'app_personality',
            '--personality', 'compileserver',
            '--country', 'us',
        ]
        self.successtest(command)

        self.check_plenary_gone(*path, directory_gone=True)

    def test_300_del_hostlink_archetype(self):
        path = [
            'resource',
            'archetype', 'aquilon',
            'dev',
            'hub', 'ny',
            'hostlink', 'app_archetype',
            'config',
        ]
        self.check_plenary_exists(*path)

        command = [
            'del_hostlink',
            '--hostlink', 'app_archetype',
            '--archetype', 'aquilon',
            '--host_environment', 'dev',
            '--hub', 'ny',
        ]
        self.successtest(command)

        self.check_plenary_gone(*path, directory_gone=True)

    def test_300_del_hostlink_grn(self):
        path = [
            'resource',
            'eon_id', '4',
            'dev',
            'city', 'ln',
            'hostlink', 'app_grn',
            'config',
        ]
        self.check_plenary_exists(*path)

        command = [
            'del_hostlink',
            '--hostlink', 'app_grn',
            '--grn', 'grn:/ms/ei/aquilon/ut2',
            '--host_environment', 'dev',
            '--city', 'ln',
        ]
        self.successtest(command)

        self.check_plenary_gone(*path, directory_gone=True)

    def test_300_del_hostlink_eon_id(self):
        path = [
            'resource',
            'eon_id', '3',
            'dev',
            'organization', 'ms',
            'hostlink', 'app_eon_id',
            'config',
        ]
        self.check_plenary_exists(*path)

        command = [
            'del_hostlink',
            '--hostlink', 'app_eon_id',
            '--eon_id', 3,
            '--host_environment', 'dev',
            '--organization', 'ms',
        ]
        self.successtest(command)

        self.check_plenary_gone(*path, directory_gone=True)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelHostlink)
    unittest.TextTestRunner(verbosity=2).run(suite)
