#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the add required service command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand

archetype_required = {
    'aquilon': ["dns", "aqd", "ntp", "bootserver", "support-group", "lemon",
                "syslogng"],
    'esx_cluster': ["esx_management_server"],
    'vmhost': ["dns", "ntp", "syslogng"],
}


class TestAddRequiredService(TestBrokerCommand):

    def test_100_add_afs(self):
        command = "add required service --service afs --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def test_105_verify_afs(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Required for Archetype: aquilon", command)

    def test_110_add_defaults(self):
        # Setup required services, as expected by the templates.
        for archetype, servicelist in archetype_required.items():
            for service in servicelist:
                self.noouttest(["add_required_service", "--service", service,
                                "--archetype", archetype,
                                "--justification", "tcm=12345678"])

    def test_115_verify_defaults(self):
        all_services = set()
        for archetype, servicelist in archetype_required.items():
            all_services.update(servicelist)

        for archetype, servicelist in archetype_required.items():
            command = ["show_archetype", "--archetype", archetype]
            out = self.commandtest(command)
            for service in servicelist:
                self.matchoutput(out, "Service: %s" % service, command)

            for service in all_services - set(servicelist):
                self.matchclean(out, "Service: %s" % service, command)

    def test_120_add_choosers(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["add_required_service", "--service", service,
                       "--archetype=aquilon", "--personality=unixeng-test"]
            self.noouttest(command)

    def test_125_show_personality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=unixeng-test"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: chooser1", command)
        self.matchoutput(out, "Service: chooser2", command)
        self.matchoutput(out, "Service: chooser3", command)

    def test_125_show_service(self):
        command = "show service --service chooser1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Required for Personality: unixeng-test "
                         "Archetype: aquilon Stage: current",
                         command)

    def test_130_add_utsvc(self):
        command = ["add_required_service", "--personality=compileserver",
                   "--service=utsvc", "--archetype=aquilon"]
        self.noouttest(command)

    def test_135_verify_utsvc(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: utsvc", command)

    def test_140_add_netmap(self):
        command = ["add_required_service", "--personality=eaitools",
                   "--service=netmap", "--archetype=aquilon"]
        self.noouttest(command)

    def test_145_verify_netmap(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=eaitools"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: netmap", command)

    def test_150_copy_personality(self):
        self.noouttest(["add_personality", "--personality", "required_svc_test",
                        "--eon_id", "2", "--archetype", "aquilon",
                        "--copy_from", "eaitools",
                        "--host_environment", "dev"])

        command = ["show_personality", "--archetype=aquilon",
                   "--personality=required_svc_test"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: netmap", command)

        self.successtest(["del_personality", "--personality", "required_svc_test",
                          "--archetype", "aquilon"])

    def test_160_add_badservice(self):
        command = ["add_required_service", "--service=badservice",
                   "--personality=badpersonality2", "--archetype=aquilon"]
        self.noouttest(command)

    def test_165_verify_badservice(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=badpersonality2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: badservice", command)

    def test_200_archetype_duplicate(self):
        command = "add required service --service afs --archetype aquilon"
        command += " --justification tcm=12345678"
        self.badrequesttest(command.split(" "))

    def test_200_personality_duplicate(self):
        command = ["add_required_service", "--service", "chooser1",
                   "--archetype", "aquilon", "--personality", "unixeng-test"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Service chooser1 is already required by "
                         "personality aquilon/unixeng-test@current.",
                         command)

    def test_200_no_justification(self):
        command = "add required service --service afs --archetype aquilon"
        out = self.unauthorizedtest(command.split(" "), auth=True,
                                    msgcheck=False)
        self.matchoutput(out,
                         "Changing the required services of an archetype "
                         "requires --justification.",
                         command)

    def test_200_missing_service(self):
        command = ["add_required_service", "--service",
                   "service-does-not-exist", "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service service-does-not-exist not found.",
                         command)

    def test_200_missing_personality(self):
        command = ["add_required_service", "--service", "afs",
                   "--personality", "personality-does-not-exist",
                   "--archetype", "aquilon"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality personality-does-not-exist, "
                         "archetype aquilon not found.",
                         command)

    def test_200_missing_personality_stage(self):
        command = ["add_required_service", "--service", "afs",
                   "--personality", "nostage", "--archetype", "aquilon",
                   "--personality_stage", "previous"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality aquilon/nostage does not have stage "
                         "previous.",
                         command)

    def test_200_bad_personality_stage(self):
        command = ["add_required_service", "--service", "afs",
                   "--personality", "nostage", "--archetype", "aquilon",
                   "--personality_stage", "no-such-stage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'no-such-stage' is not a valid personality "
                         "stage.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRequiredService)
    unittest.TextTestRunner(verbosity=2).run(suite)
