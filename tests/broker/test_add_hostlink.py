#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011-2018  Contributor
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
"""Module for testing the add hostlink command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddHostlink(TestBrokerCommand):

    def test_100_add_hostlink(self):
        command = ["add_hostlink", "--hostlink=app1",
                   "--target=/var/spool/hostlinks/app1",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user1",
                   "--mode=775",
                   "--comments=Some hostlink comments"]
        self.successtest(command)

    def test_103_add_hostlink_with_mode(self):
        command = ["add_hostlink", "--hostlink=app2",
                   "--target=/var/spool/hostlinks/app2",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user1",
                   "--mode=1777",
                   "--comments=Some hostlink comments"]
        self.successtest(command)

    def test_103_add_hostlink_with_bad_mode(self):
        command = ["add_hostlink", "--hostlink=app3",
                   "--target=/var/spool/hostlinks/app3",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user1",
                   "--mode=3775",
                   "--comments=Some hostlink comments"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "mode is out of range (0-1777 octal)", command)

    def test_103_add_hostlink_with_bad_string_mode(self):
        command = ["add_hostlink", "--hostlink=app4",
                   "--target=/var/spool/hostlinks/app4",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user1",
                   "--mode=rwxrwxrwx",
                   "--comments=Some hostlink comments"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "mode does not convert to base 8 integer", command)

    def test_105_make(self):
        command = ["make", "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_110_show_hostlink(self):
        command = ["show_hostlink", "--hostlink=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Hostlink: app1
              Comments: Some hostlink comments
              Bound to: Host server1.aqd-unittest.ms.com
              Target Path: /var/spool/hostlinks/app1
              Owner: user1
              Mode: 775
            """, command)

    def test_110_show_hostlink_with_mode(self):
        command = ["show_hostlink", "--hostlink=app2",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.output_equals(out, """
            Hostlink: app2
              Comments: Some hostlink comments
              Bound to: Host server1.aqd-unittest.ms.com
              Target Path: /var/spool/hostlinks/app2
              Owner: user1
              Mode: 1777
            """, command)

    def test_112_check_plenary_with_mode(self):
        self.check_plenary_contents("resource", "host",
                                    "server1.aqd-unittest.ms.com", "hostlink",
                                    "app2", "config", contains=['"perm" = "1777";'])

    def test_110_show_host(self):
        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hostlink: app1", command)

    def test_110_show_host_proto(self):
        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com",
                   "--format=proto"]
        host = self.protobuftest(command, expect=1)[0]
        hostlinkfound = False
        for resource in host.resources:
            if resource.name == "app1" and resource.type == "hostlink":
                self.assertEqual(resource.hostlink.target,
                                 "/var/spool/hostlinks/app1")
                self.assertEqual(resource.hostlink.owner_user, "user1")
                self.assertEqual(resource.hostlink.owner_group, "")
                self.assertEqual(resource.hostlink.mode, "775")
                hostlinkfound = True
        self.assertTrue(hostlinkfound,
                        "Hostlink app1 not found in the resources. "
                        "Existing resources: %s" %
                        ", ".join("%s %s" % (res.type, res.name)
                                  for res in host.resources))

    def test_110_cat_host(self):
        command = ["cat", "--hostname", "server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/resources/hostlink" = append(create("resource/host/server1.aqd-unittest.ms.com/hostlink/app1/config"))', command)

    def test_120_add_camelcase(self):
        command = ["add_hostlink", "--hostlink=CaMeLcAsE",
                   "--target=/var/spool/hostlinks/CaMeLcAsE",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user1"]
        self.successtest(command)

        self.check_plenary_exists("resource", "host",
                                  "server1.aqd-unittest.ms.com", "hostlink",
                                  "camelcase", "config")
        self.check_plenary_gone("resource", "host",
                                "server1.aqd-unittest.ms.com", "hostlink",
                                "CaMeLcAsE", "config")

    def test_200_add_existing(self):
        command = ["add_hostlink", "--hostlink=app1",
                   "--target=/var/spool/hostlinks/app1",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_200_notfound(self):
        command = ["show_hostlink", "--hostlink", "hostlink-does-not-exist",
                   "--hostname", "server1.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_200_badowner(self):
        command = ["add_hostlink", "--hostlink", "badlink",
                   "--target", "/dev/zero", "--owner", "unittest:unitgroup",
                   "--hostname", "server1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "owner_user cannot contain the ':' character",
                         command)

    def test_200_badgroup(self):
        command = ["add_hostlink", "--hostlink", "badlink",
                   "--target", "/dev/zero", "--owner", "unittest",
                   "--group", "unit:group",
                   "--hostname", "server1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "owner_group cannot contain the ':' character",
                         command)

    def test_320_add_hostlink_grn(self):
        command = [
            'add_hostlink', '--hostlink', 'app_grn',
            '--target', '/var/spool/hostlinks/app_grn',
            '--grn', 'grn:/ms/ei/aquilon/ut2',
            '--host_environment', 'dev',
            '--city', 'ln',
            '--owner', 'testuser3',
            '--group', 'testgroup3',
            '--comments', 'A hostlink set at the GRN level',
        ]
        self.successtest(command)

    def test_322_show_hostlink_grn(self):
        command = [
            'show_hostlink',
            '--hostlink', 'app_grn',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Hostlink: app_grn',
                       '  Comments: A hostlink set at the GRN level',
                       '  Bound to: GRN grn:/ms/ei/aquilon/ut2, '
                       'Host Environment dev, City ln',
                       '  Target Path: /var/spool/hostlinks/app_grn',
                       '  Owner: testuser3',
                       '  Group: testgroup3'))
        self.output_equals(out, expected_out, command)

    def test_324_cat_grn(self):
        command = [
            'cat',
            '--grn', 'grn:/ms/ei/aquilon/ut2',
            '--host_environment', 'dev',
            '--city', 'ln',
        ]
        out = self.commandtest(command)
        expected_out = ['\n'.join(n) for n in [
            ('"/system/resources/hostlink" = append(create("resource'
             '/eon_id/4'
             '/dev'
             '/city/ln'
             '/hostlink/app_grn'
             '/config"));',),
        ]]
        self.output_unordered_equals(out, expected_out, command,
                                     match_all=False)

    def test_330_add_hostlink_eon_id(self):
        command = [
            'add_hostlink', '--hostlink', 'app_eon_id',
            '--target', '/var/spool/hostlinks/app_eon_id',
            '--eon_id', 3,
            '--host_environment', 'dev',
            '--organization', 'ms',
            '--owner', 'testuser4',
            '--group', 'testgroup4',
            '--comments', 'A hostlink set at the GRN level (eon_id)',
        ]
        self.successtest(command)

    def test_332_show_hostlink_eon_id(self):
        command = [
            'show_hostlink',
            '--hostlink', 'app_eon_id',
        ]
        out = self.commandtest(command)
        expected_out = \
            '\n'.join(('Hostlink: app_eon_id',
                       '  Comments: A hostlink set at the GRN level (eon_id)',
                       '  Bound to: GRN grn:/ms/ei/aquilon/unittest, '
                       'Host Environment dev, Organization ms',
                       '  Target Path: /var/spool/hostlinks/app_eon_id',
                       '  Owner: testuser4',
                       '  Group: testgroup4'))
        self.output_equals(out, expected_out, command)

    def test_334_cat_eon_id(self):
        command = [
            'cat',
            '--eon_id', 3,
            '--host_environment', 'dev',
            '--organization', 'ms',
        ]
        out = self.commandtest(command)
        expected_out = ['\n'.join(n) for n in [
            ('"/system/resources/hostlink" = append(create("resource'
             '/eon_id/3'
             '/dev'
             '/organization/ms'
             '/hostlink/app_eon_id'
             '/config"));',),
        ]]
        self.output_unordered_equals(out, expected_out, command,
                                     match_all=False)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHostlink)
    unittest.TextTestRunner(verbosity=2).run(suite)
