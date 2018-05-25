#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015,2016,2018  Contributor
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
"""Module for testing the add room command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRoom(TestBrokerCommand):

    def test_100_addutroom1(self):
        command = ['add_room', '--room=utroom1', '--building=ut', '--floor=42',
                   '--fullname=UT pod1']
        self.noouttest(command)

    def test_105_verifyaddutroom1(self):
        command = "show room --room utroom1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Room: utroom1", command)
        self.matchoutput(out, "Floor: 42", command)
        self.matchoutput(out, "Fullname: UT pod1", command)

    def test_110_addutroom2(self):
        command = ['add_room', '--room=utroom2', '--building=ut', '--floor=GF']
        self.noouttest(command)

    def test_115_verifyutroom2(self):
        command = "show room --room utroom2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Room: utroom2", command)
        self.matchoutput(out, "Fullname: utroom2", command)
        self.matchoutput(out, "Floor: gf", command)

    def test_120_verifyshowcsv(self):
        command = "show room --all --format=csv"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "room,utroom1,building,ut", command)
        self.matchoutput(out, "room,utroom2,building,ut", command)

    def test_125_addnplab1(self):
        self.noouttest(["add_room", "--room", "np-lab1", "--building", "np",
                        "--fullname", "NP lab1", '--floor=0', '--uri=TEST URI'])

    def test_130_verifynplab1(self):
        command = "show room --room np-lab1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Room: np-lab1", command)
        self.matchoutput(out, "Fullname: NP lab1", command)
        self.matchoutput(out, "Floor: 0", command)
        self.matchoutput(out, "Location URI: TEST URI", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRoom)
    unittest.TextTestRunner(verbosity=2).run(suite)
