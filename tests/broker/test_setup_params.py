#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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
"""Module for testing parameter support."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from broker.brokertest import TestBrokerCommand

# validation parameters by templates
AQUILON_PARAM_DEFS = {
    "access": [
        {
            "path": "access/netgroup",
            "value_type": "list",
            "description": "netgroups access"
        },
        {
            "path": "access/users",
            "value_type": "list",
            "description": "users access"
        },
    ],
    "actions": [
        {
            "path": r"action/\w+/user",
            "value_type": "string",
            "description": "action user"
        },
        {
            "path": r"action/\w+/command",
            "value_type": "string",
            "description": "action command"
        },
        {
            "path": r"action/\w+",
            "value_type": "json",
            "description": "per action block"
        },
        {
            "path": "action",
            "value_type": "json",
            "description": "per action block"
        },
    ],
    "startup": [
        {
            "path": "startup/actions",
            "value_type": "list",
            "description": "startup actions"
        },
    ],
    "shutdown": [
        {
            "path": "shutdown/actions",
            "value_type": "list",
            "description": "shutdown actions"
        },
    ],
    "maintenance": [
        {
            "path": "maintenance/actions",
            "value_type": "list",
            "description": "maintenance actions"
        },
    ],
    "monitoring": [
        {
            "path": "monitoring/alert",
            "value_type": "json",
            "description": "monitoring alert"
        },
        {
            "path": "monitoring/metric",
            "value_type": "json",
            "description": "monitoring metric"
        },
    ],
    "espinfo": [
        {
            "path": "espinfo/function",
            "value_type": "string",
            "description": "espinfo function",
            "required": True
        },
        {
            "path": "espinfo/class",
            "value_type": "string",
            "description": "espinfo class",
            "required": True
        },
        {
            "path": "espinfo/users",
            "value_type": "list",
            "description": "espinfo users",
            "required": True
        },
        {
            "path": "espinfo/description",
            "value_type": "string",
            "description": "espinfo desc"
        },
    ],
    "windows": [
        {
            "path": "windows/windows",
            "value_type": "json",
            "required": True,
            "default": '[{"duration": 8, "start": "08:00", "day": "Sun"}]'
        }
    ],
}

AURORA_PARAM_DEFS = {
    "espinfo": [
        {
            "path": "espinfo/class",
            "value_type": "string",
            "description": "espinfo class",
            "required": True
        },
        {
            "path": "espinfo/function",
            "value_type": "string",
            "description": "espinfo function",
            "required": True
        },
    ],
}

HACLUSTER_PARAM_DEFS = {
    "espinfo": [
        {
            "path": "espinfo/class",
            "value_type": "string",
            "description": "espinfo class",
            "required": True
        },
        {
            "path": "espinfo/description",
            "value_type": "string",
            "description": "espinfo desc"
        },
    ],
}

VMHOST_PARAM_DEFS = {
    "espinfo": [
        {
            "path": "espinfo/function",
            "value_type": "string",
            "description": "espinfo function",
            "required": True
        },
        {
            "path": "espinfo/class",
            "value_type": "string",
            "description": "espinfo class",
            "required": True
        },
        {
            "path": "espinfo/users",
            "value_type": "list",
            "description": "espinfo users",
            "required": True
        },
    ],
}


class TestSetupParams(TestBrokerCommand):

    def add_param_def(self, archetype, template, params):
        cmd = ["add_parameter_definition", "--archetype", archetype,
               "--path", params["path"], "--template", template,
               "--value_type", params["value_type"]]
        if "required" in params:
            cmd.append("--required")
        if "activation" in params:
            cmd.extend(["--activation", params["activation"]])
        if "default" in params:
            cmd.extend(["--default", params["default"]])

        self.noouttest(cmd)

    def test_100_add_parameter_definitions(self):
        for template, paramlist in AQUILON_PARAM_DEFS.items():
            for params in paramlist:
                self.add_param_def("aquilon", template, params)
        for template, paramlist in AURORA_PARAM_DEFS.items():
            for params in paramlist:
                self.add_param_def("aurora", template, params)
        for template, paramlist in HACLUSTER_PARAM_DEFS.items():
            for params in paramlist:
                self.add_param_def("hacluster", template, params)
        for template, paramlist in VMHOST_PARAM_DEFS.items():
            for params in paramlist:
                self.add_param_def("vmhost", template, params)

    def test_110_search_by_template(self):
        command = ["search_parameter_definition", "--archetype", "aquilon",
                   "--template", "espinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "espinfo/function", command)
        self.matchclean(out, "access", command)
        self.matchclean(out, "actions", command)
        self.matchclean(out, "windows", command)

    def test_110_search_by_template_bad(self):
        command = ["search_parameter_definition", "--archetype", "aquilon",
                   "--template", "does-not-exist"]
        self.noouttest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSetupParams)
    unittest.TextTestRunner(verbosity=2).run(suite)
