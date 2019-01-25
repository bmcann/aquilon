#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2013,2015-2019  Contributor
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
"""Module for testing the add address command."""

import unittest

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

from ipaddress import IPv6Address, ip_address

from broker.brokertest import TestBrokerCommand
from eventstest import EventsTestMixin
from dnstest import inaddr_ptr, in6addr_ptr


class TestAddAddress(EventsTestMixin, TestBrokerCommand):

    def event_add_arecord(self, fqdn, ip, reverse=None, ttl=None,
                          dns_environment='internal',
                          network_environment='internal',
                          reverse_dns_environment=None):
        # Determine the IP type
        ip = ip_address(unicode(ip))
        if isinstance(ip, IPv6Address):
            inaddr = in6addr_ptr
            rrtype = 'AAAA'
        else:
            inaddr = inaddr_ptr
            rrtype = 'A'

        # Prepare the records
        a_record = {
            'target': str(ip),
            'targetNetworkEnvironmentName': network_environment,
            'rrtype': rrtype,
        }
        ptr_record = {
            'target': (
                fqdn
                if reverse is None
                else reverse
            ),
            'targetEnvironmentName': dns_environment,
            'rrtype': 'PTR',
        }

        if ttl is not None:
            a_record['ttl'] = ttl
            ptr_record['ttl'] = ttl

        # Add the records in the expected events
        self.event_add_dns(
            fqdn=[
                fqdn,
                inaddr(ip),
            ],
            dns_environment=[
                dns_environment,
                reverse_dns_environment or network_environment,
            ],
            dns_records=[
                [a_record, ],
                [ptr_record, ],
            ],
        )

    def test_100_basic(self):
        self.event_add_arecord(
            fqdn='arecord13.aqd-unittest.ms.com',
            ip=str(self.net['unknown0'].usable[13]),
            dns_environment='internal',
        )
        self.dsdb_expect_add("arecord13.aqd-unittest.ms.com",
                             self.net["unknown0"].usable[13])
        command = ["add_address", "--ip=%s" % self.net["unknown0"].usable[13],
                   "--fqdn=arecord13.aqd-unittest.ms.com"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "Please provide a GRN/EON_ID!", command)

    def test_101_basic_grn(self):
        self.event_add_arecord(
            fqdn='arecord13.aqd-unittest.ms.com',
            ip=str(self.net['unknown0'].usable[13]),
            dns_environment='internal',
        )
        self.dsdb_expect_add("arecord13.aqd-unittest.ms.com",
                             self.net["unknown0"].usable[13])
        command = ["add_address", "--ip=%s" % self.net["unknown0"].usable[13],
                   "--fqdn=arecord13.aqd-unittest.ms.com",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify()
        self.events_verify()

    def test_105_verifybasic(self):
        net = self.net["unknown0"]
        command = ["show_address", "--fqdn=arecord13.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord13.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % net.usable[13], command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchclean(out, "Reverse", command)
        self.matchclean(out, "TTL", command)

    def test_110_basic_ipv6(self):
        self.event_add_arecord(
            fqdn='ipv6test.aqd-unittest.ms.com',
            ip=str(self.net['ipv6_test'].usable[1]),
            dns_environment='internal',
        )
        command = ["add_address", "--ip", self.net["ipv6_test"].usable[1],
                   "--fqdn", "ipv6test.aqd-unittest.ms.com",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify(empty=True)
        self.events_verify()

    def test_115_verify_basic_ipv6(self):
        net = self.net["ipv6_test"]
        command = ["show_address", "--fqdn=ipv6test.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "IP: %s" % net.usable[1], command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net), command)

    def test_200_add_defaultenv(self):
        default = self.config.get("site", "default_dns_environment")
        self.event_add_arecord(
            fqdn='arecord14.aqd-unittest.ms.com',
            ip=str(self.net['unknown0'].usable[14]),
            reverse='arecord13.aqd-unittest.ms.com',
            dns_environment=default,
        )
        self.dsdb_expect_add("arecord14.aqd-unittest.ms.com",
                             self.net["unknown0"].usable[14])
        command = ["add_address", "--ip=%s" % self.net["unknown0"].usable[14],
                   "--fqdn=arecord14.aqd-unittest.ms.com",
                   "--reverse_ptr=arecord13.aqd-unittest.ms.com",
                   "--dns_environment=%s" % default,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify()
        self.events_verify()

    def test_210_add_utenv_noreverse(self):
        # The reverse does not exist in this environment
        command = ["add_address", "--ip", self.net["unknown1"].usable[14],
                   "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--reverse_ptr", "arecord13.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.notfoundtest(command)
        self.matchoutput(out, "Target FQDN arecord13.aqd-unittest.ms.com does "
                         "not exist in DNS environment ut-env.", command)

    def test_220_add_utenv(self):
        self.event_add_arecord(
            fqdn='arecord14.aqd-unittest.ms.com',
            ip=str(self.net['unknown1'].usable[14]),
            dns_environment='ut-env',
        )
        # Different IP in this environment
        command = ["add_address", "--ip", self.net["unknown1"].usable[14],
                   "--fqdn", "arecord14.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        self.events_verify()

    def test_230_verifydefaultenv(self):
        default = self.config.get("site", "default_dns_environment")
        command = ["show_address", "--fqdn=arecord14.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord14.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "DNS Environment: %s" % default, command)
        self.matchoutput(out, "IP: %s" % self.net["unknown0"].usable[14],
                         command)
        self.matchoutput(out, "Reverse PTR: arecord13.aqd-unittest.ms.com",
                         command)

    def test_230_verifyutenv(self):
        command = ["show_address", "--fqdn=arecord14.aqd-unittest.ms.com",
                   "--dns_environment", "ut-env"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord14.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "IP: %s" % self.net["unknown1"].usable[14],
                         command)
        self.matchclean(out, "Reverse", command)

    def test_300_ipfromip(self):
        self.event_add_arecord(
            fqdn='arecord15.aqd-unittest.ms.com',
            ip=str(self.net['unknown0'].usable[15]),
            dns_environment='internal',
        )
        self.dsdb_expect_add("arecord15.aqd-unittest.ms.com",
                             self.net["unknown0"].usable[15])
        command = ["add_address", "--ipalgorithm=max",
                   "--ipfromip=%s" % self.net["unknown0"].ip,
                   "--fqdn=arecord15.aqd-unittest.ms.com",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify()
        self.events_verify()

    def test_310_verifyipfromip(self):
        command = ["show_address", "--fqdn=arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord15.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % self.net["unknown0"].usable[15],
                         command)
        self.matchclean(out, "Reverse", command)

    def test_320_verifyaudit(self):
        command = ["search_audit", "--command", "add_address",
                   "--keyword", "arecord15.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "[Result: ip=%s]" % self.net["unknown0"].usable[15],
                         command)

    def test_330_add_name_with_digit_prefix(self):
        fqdn = "1record42.aqd-unittest.ms.com"
        ip = self.net["unknown0"].usable[42]
        dns_env = "external"
        self.event_add_arecord(
            fqdn=fqdn,
            ip=str(ip),
            dns_environment=dns_env,
        )
        command = ["add_address", "--ip", ip, "--fqdn", fqdn,
                   "--dns_environment", dns_env,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)

        command = ["show_address", "--fqdn", fqdn,
                   "--dns_environment", dns_env]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: %s" % fqdn, command)
        self.matchoutput(out, "IP: %s" % ip, command)
        self.matchclean(out, "Reverse", command)
        self.events_verify()

    def test_400_dsdbfailure(self):
        self.dsdb_expect_add("arecord16.aqd-unittest.ms.com",
                             self.net["unknown0"].usable[16], fail=True)
        command = ["add_address", "--ip", self.net["unknown0"].usable[16],
                   "--fqdn", "arecord16.aqd-unittest.ms.com",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not add address to DSDB", command)
        self.dsdb_verify()

    def test_410_verifydsdbfailure(self):
        command = ["search", "dns", "--fqdn", "arecord16.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_420_failnetaddress(self):
        ip = self.net["unknown0"].ip
        command = ["add", "address", "--fqdn", "netaddress.aqd-unittest.ms.com",
                   "--ip", ip,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is the address of network " % ip,
                         command)

    def test_420_failnetaddressv6(self):
        ip = self.net["ipv6_test"].network_address
        command = ["add_address", "--fqdn", "netaddress6.aqd-unittest.ms.com",
                   "--ip", ip,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is the address of network " % ip,
                         command)

    def test_425_failbroadcast(self):
        ip = self.net["unknown0"].broadcast_address
        command = ["add", "address", "--fqdn", "broadcast.aqd-unittest.ms.com",
                   "--ip", ip, "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is the broadcast address of "
                         "network " % ip, command)

    def test_425_failbroadcastv6(self):
        ip = self.net["ipv6_test"].broadcast_address
        command = ["add", "address", "--fqdn", "broadcast.aqd-unittest.ms.com",
                   "--ip", ip, "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is the broadcast address of "
                         "network " % ip, command)

    def test_426_failv6mapped(self):
        ipv4 = self.net["unknown0"].ip
        ipv6 = IPv6Address(u"::ffff:%s" % ipv4)
        command = ["add", "address", "--fqdn", "broadcast.aqd-unittest.ms.com",
                   "--ip", ipv6, "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "IPv6-mapped IPv4 addresses are not supported.", command)

    def test_440_failbadenv(self):
        ip = self.net["unknown0"].usable[16]
        command = ["add", "address", "--fqdn", "no-such-env.aqd-unittest.ms.com",
                   "--ip", ip, "--dns_environment", "no-such-env",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Environment no-such-env not found.", command)

    def test_450_add_too_long_name(self):
        ip = self.net["unknown0"].usable[16]
        cmd = ['add', 'address', '--fqdn',
               #         1         2         3         4         5         6
               's234567890123456789012345678901234567890123456789012345678901234' +
               '.aqd-unittest.ms.com', '--dns_environment', 'internal',
               '--ip', ip, "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(cmd)
        self.matchoutput(out, "is more than the maximum 63 allowed.", cmd)

    def test_455_add_invalid_name(self):
        ip = self.net["unknown0"].usable[16]
        command = ['add', 'address', '--fqdn', 'foo-.aqd-unittest.ms.com',
                   '--dns_environment', 'internal', '--ip', ip,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "Illegal DNS name format 'foo-'.", command)

    def test_460_restricted_domain(self):
        ip = self.net["unknown0"].usable[-1]
        command = ["add", "address", "--fqdn", "foo.restrict.aqd-unittest.ms.com",
                   "--ip", ip, "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Domain restrict.aqd-unittest.ms.com is "
                         "restricted, adding extra addresses is not allowed.",
                         command)

    def test_470_restricted_reverse(self):
        ip = self.net["unknown0"].usable[32]
        self.event_add_arecord(
            fqdn='arecord17.aqd-unittest.ms.com',
            ip=str(ip),
            reverse='reverse.restrict.aqd-unittest.ms.com',
            dns_environment='internal',
        )
        self.dsdb_expect_add("arecord17.aqd-unittest.ms.com", ip)
        command = ["add", "address", "--fqdn", "arecord17.aqd-unittest.ms.com",
                   "--reverse_ptr", "reverse.restrict.aqd-unittest.ms.com",
                   "--ip", ip, "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        err = self.statustest(command)
        self.matchoutput(err,
                         "WARNING: Will create a reference to "
                         "reverse.restrict.aqd-unittest.ms.com, but trying to "
                         "resolve it resulted in an error: Name or service "
                         "not known",
                         command)
        self.dsdb_verify()
        self.events_verify()

    def test_471_verify_reverse(self):
        command = ["search", "dns", "--fullinfo",
                   "--fqdn", "reverse.restrict.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Reserved Name: reverse.restrict.aqd-unittest.ms.com",
                         command)
        command = ["show", "address", "--fqdn", "arecord17.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Reverse PTR: reverse.restrict.aqd-unittest.ms.com",
                         command)

    def test_500_addunittest20eth1(self):
        ip = self.net["zebra_eth1"].usable[0]
        fqdn = "unittest20-e1.aqd-unittest.ms.com"
        self.event_add_arecord(
            fqdn=fqdn,
            ip=str(ip),
            dns_environment='internal',
        )
        self.dsdb_expect_add(fqdn, ip)
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify()
        self.events_verify()

    def test_600_addip_with_network_env(self):
        ip = "192.168.3.1"
        fqdn = "cardenvtest600.aqd-unittest.ms.com"
        self.event_add_arecord(
            fqdn=fqdn,
            ip=str(ip),
            dns_environment='ut-env',
            network_environment='cardenv',
            reverse_dns_environment='ut-env',
        )
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn,
                   "--network_environment", "cardenv",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

        command = ["show_address", "--fqdn=%s" % fqdn,
                   "--network_environment", "cardenv"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: %s" % fqdn,
                         command)
        self.matchoutput(out, "IP: %s" % ip,
                         command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Network Environment: cardenv", command)

        self.events_verify()

    def test_610_addipfromip_with_network_env(self):
        fqdn = "cardenvtest610.aqd-unittest.ms.com"
        self.event_add_arecord(
            fqdn=fqdn,
            ip='192.168.3.5',
            dns_environment='ut-env',
            network_environment='cardenv',
            reverse_dns_environment='ut-env',
        )
        command = ["add", "address", "--ipfromip", "192.168.3.0",
                   "--fqdn", fqdn, "--network_environment", "cardenv",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        # External IP addresses should not be added to DSDB
        self.dsdb_verify(empty=True)

        command = ["show_address", "--fqdn=%s" % fqdn,
                   "--network_environment", "cardenv"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: %s" % fqdn,
                         command)
        self.matchoutput(out, "IP: %s" % "192.168.3.5",
                         command)
        self.matchoutput(out, "DNS Environment: ut-env", command)
        self.matchoutput(out, "Network Environment: cardenv", command)

        self.events_verify()

    def test_620_addexternalip_in_interanldns(self):
        ip = "192.168.3.4"
        fqdn = "cardenvtest620.aqd-unittest.ms.com"
        default = self.config.get("site", "default_dns_environment")
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn,
                   "--dns_environment", default,
                   "--network_environment", "cardenv",
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "Entering external IP addresses to the internal DNS environment is not allowed", command)

    def test_700_ttl(self):
        self.event_add_arecord(
            fqdn='arecord40.aqd-unittest.ms.com',
            ip=str(self.net['unknown0'].usable[40]),
            ttl=300,
            dns_environment='internal',
        )
        self.dsdb_expect_add("arecord40.aqd-unittest.ms.com",
                             self.net["unknown0"].usable[40])
        command = ["add_address", "--ip=%s" % self.net["unknown0"].usable[40],
                   "--fqdn=arecord40.aqd-unittest.ms.com",
                   "--ttl", 300,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify()
        self.events_verify()

    def test_720_verifyttl(self):
        net = self.net["unknown0"]
        command = ["show_address", "--fqdn=arecord40.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord40.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % net.usable[40], command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchoutput(out, "TTL: 300", command)
        self.matchclean(out, "Reverse", command)

    def test_730_badttl(self):
        command = ["add_address", "--ip=%s" % self.net["unknown0"].usable[41],
                   "--fqdn=arecord41.aqd-unittest.ms.com",
                   "--ttl", 2147483648,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        out = self.badrequesttest(command)
        self.matchoutput(out, "TTL must be between 0 and 2147483647.",
                         command)

    def test_800_grn(self):
        self.event_add_arecord(
            fqdn='arecord50.aqd-unittest.ms.com',
            ip=str(self.net['unknown0'].usable[50]),
            dns_environment='internal',
        )
        self.dsdb_expect_add("arecord50.aqd-unittest.ms.com",
                             self.net["unknown0"].usable[50])
        command = ["add_address", "--ip=%s" % self.net["unknown0"].usable[50],
                   "--fqdn=arecord50.aqd-unittest.ms.com",
                   "--grn", "grn:/ms/ei/aquilon/aqd"] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify()
        self.events_verify()

    def test_820_verifygrn(self):
        net = self.net["unknown0"]
        command = ["show_address", "--fqdn=arecord50.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord50.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % net.usable[50], command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)
        self.matchclean(out, "Reverse", command)

    def test_830_eon_id(self):
        self.event_add_arecord(
            fqdn='arecord51.aqd-unittest.ms.com',
            ip=str(self.net['unknown0'].usable[51]),
            dns_environment='internal',
        )
        self.dsdb_expect_add("arecord51.aqd-unittest.ms.com",
                             self.net["unknown0"].usable[51])
        command = ["add_address", "--ip=%s" % self.net["unknown0"].usable[51],
                   "--fqdn=arecord51.aqd-unittest.ms.com",
                   "--eon_id", "3"] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify()
        self.events_verify()

    def test_840_verifygrn(self):
        net = self.net["unknown0"]
        command = ["show_address", "--fqdn=arecord51.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: arecord51.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "IP: %s" % net.usable[51], command)
        self.matchoutput(out, "Network: %s [%s]" % (net.name, net), command)
        self.matchoutput(out, "Network Environment: internal", command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/unittest", command)
        self.matchclean(out, "Reverse", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
