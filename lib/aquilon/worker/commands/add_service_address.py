#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012-2019  Contributor
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
"""Contains the logic for `aq add service address`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import ServiceAddress, Host, Fqdn, DnsDomain, Bunker
from aquilon.utils import validate_nlist_key
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.interface import get_interfaces, generate_ip
from aquilon.worker.dbwrappers.location import get_default_dns_domain
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.dbwrappers.search import search_next
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandAddServiceAddress(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["name"]

    def render(self, session, logger, plenaries, service_address, shortname, prefix,
               dns_domain, ip, ipfromtype, name, interfaces, hostname, cluster, metacluster,
               resourcegroup, network_environment, map_to_primary, shared,
               comments, user, justification, reason, exporter, **kwargs):

        validate_nlist_key("name", name)
        audit_results = []

        # TODO: generalize the error message - Layer-3 failover may be
        # implemented by other software, not just Zebra.
        if name == "hostname":
            raise ArgumentError("The hostname service address is reserved for "
                                "Zebra.  Please specify the --zebra_interfaces "
                                "option when calling add_host if you want the "
                                "primary name of the host to be managed by "
                                "Zebra.")

        holder = get_resource_holder(session, logger, hostname, cluster,
                                     metacluster, resourcegroup, compel=False)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **kwargs)
        cm.consider(holder)
        cm.validate()

        toplevel_holder = holder.toplevel_holder_object

        ServiceAddress.get_unique(session, name=name, holder=holder,
                                  preclude=True)

        net_location_set = None

        if ipfromtype is not None:
            if not self.config.getboolean("site", "ipfromtype"):
                raise ArgumentError("--ipfromtype option is not allowed to be "
                                    "used in this Aquilon broker instance.")
            # We only care about Bunker locations to filter Networks assigned correct locations
            # ipfromtype only works for bunkerized networks
            if isinstance(toplevel_holder, Host):
                net_location_set = set([toplevel_holder.hardware_entity.location.bunker]) \
                    if toplevel_holder.hardware_entity.location.bunker else None
            elif hasattr(toplevel_holder, 'members'):
                # Metacluster
                net_location_set = toplevel_holder.member_hosts_locations(location_class=Bunker)
            elif hasattr(toplevel_holder, 'hosts'):
                # Cluster
                net_location_set = toplevel_holder.member_locations(location_class=Bunker)
            if not net_location_set:
                raise ArgumentError('Host(s) location is not inside a Bunker, --ipfromtype cannot be used.')
        if shared:
            if not isinstance(toplevel_holder, Host):
                raise ArgumentError("The --shared option works only "
                                    "for host-based service addresses.")

        if not service_address:
            if dns_domain:
                dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                    compel=True)
            elif isinstance(toplevel_holder, Host):
                dbdns_domain = toplevel_holder.hardware_entity.primary_name.fqdn.dns_domain
            else:
                dbdns_domain = get_default_dns_domain(toplevel_holder.location_constraint)

            if prefix:
                prefix = AqStr.normalize(prefix)
                dbdns_domain.lock_row()

                result = search_next(session=session, cls=Fqdn, attr=Fqdn.name,
                                     value=prefix, dns_domain=dbdns_domain,
                                     start=None, pack=None)
                shortname = "%s%d" % (prefix, result)

            service_address = "%s.%s" % (shortname, dbdns_domain)
            logger.info("Selected FQDN {0!s} for {1:l}."
                        .format(service_address, toplevel_holder))
            audit_results.append(('service_address', service_address))

        ip = generate_ip(session, logger, None, net_location_set, ip=ip, ipfromtype=ipfromtype)

        # TODO: add allow_multi=True
        dbdns_rec, newly_created = grab_address(session, service_address, ip,
                                                network_environment,
                                                allow_shared=shared,
                                                exporter=exporter,
                                                require_grn=False)
        ip = dbdns_rec.ip

        if map_to_primary:
            if not isinstance(toplevel_holder, Host):
                raise ArgumentError("The --map_to_primary option works only "
                                    "for host-based service addresses.")
            dbdns_rec.reverse_ptr = toplevel_holder.hardware_entity.primary_name.fqdn

        dbifaces = []
        if interfaces:
            if isinstance(toplevel_holder, Host):
                dbifaces = get_interfaces(toplevel_holder.hardware_entity,
                                          interfaces, dbdns_rec.network)
            else:
                logger.client_info("The --interfaces option is only valid for "
                                   "host-bound service addresses, and is "
                                   "ignored otherwise.")

        dsdb_runner = DSDBRunner(logger=logger)
        with session.no_autoflush:
            dbsrv = ServiceAddress(name=name, dns_record=dbdns_rec,
                                   comments=comments)
            holder.resources.append(dbsrv)
            if dbifaces:
                dbsrv.interfaces = dbifaces

        session.flush()

        plenaries.add(holder.holder_object)
        plenaries.add(dbsrv)

        with plenaries.transaction():
            if dbdns_rec.network.is_internal:

                # If the IP address was not just created, and if it is not
                # shared, we will delete it for it to be re-added just after
                deleted = False
                if not shared and not newly_created:
                    deleted = True
                    dsdb_runner.delete_host_details(dbsrv.dns_record, dbsrv.ip)

                # If the IP address has just been created, or if it was
                # deleted just before, we will re-add it to DSDB
                if newly_created or deleted:
                    dsdb_runner.add_host_details(dbsrv.dns_record, dbsrv.ip,
                                                 comments=comments)

            dsdb_runner.commit_or_rollback("Could not add host to DSDB")

        for name, value in audit_results:
            self.audit_result(session, name, value, **kwargs)
        return
