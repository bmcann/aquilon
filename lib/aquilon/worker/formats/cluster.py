# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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

from operator import attrgetter

from aquilon.aqdb.model import (Cluster, EsxCluster, ComputeCluster,
                                StorageCluster)
from aquilon.worker.formats.formatters import ObjectFormatter


class ClusterFormatter(ObjectFormatter):
    def fill_proto(self, cluster, skeleton):
        skeleton.name = str(cluster.name)
        skeleton.status = str(cluster.status)
        self.add_personality_data(skeleton.personality, cluster.personality)
        self.add_branch_data(skeleton.domain, cluster.branch)

        skeleton.threshold = cluster.down_hosts_threshold
        skeleton.threshold_is_percent = cluster.down_hosts_percent
        if cluster.down_maint_threshold is not None:
            skeleton.maint_threshold = cluster.down_maint_threshold
            skeleton.maint_threshold_is_percent = \
                cluster.down_maint_percent

        for host in sorted(cluster.hosts, key=attrgetter("fqdn")):
            self.add_host_data(skeleton.hosts.add(), host)

        if cluster.resholder and len(cluster.resholder.resources) > 0:
            self.redirect_proto(cluster.resholder.resources, skeleton.resources)

        for dbsi in cluster.services_used:
            # Should be just 'services', but that would change the protocol.
            si = skeleton.aligned_services.add()
            si.service = dbsi.service.name
            si.instance = dbsi.name

        for personality in cluster.allowed_personalities:
            p = skeleton.allowed_personalities.add()
            p.name = str(personality.name)
            p.archetype.name = str(personality.archetype.name)

        if isinstance(cluster, EsxCluster):
            caps = cluster.get_total_capacity()
            if caps:
                overrides = cluster.get_capacity_overrides()
                for name, value in caps.items():
                    v = skeleton.limits.add()
                    v.name = name
                    v.value = value
                    if overrides.get(name) is not None:
                        v.override = True

            usage = cluster.get_total_usage()
            if usage:
                for name, value in usage.items():
                    u = skeleton.usage.add()
                    u.name = name
                    u.value = value

        if cluster.max_hosts is not None:
            skeleton.max_members = cluster.max_hosts

    def format_raw(self, cluster, indent=""):
        details = [indent + "{0:c}: {0.name}".format(cluster)]
        if cluster.metacluster:
            details.append(indent +
                           "  {0:c}: {0.name}".format(cluster.metacluster))
        details.append(self.redirect_raw(cluster.location_constraint,
                                         indent + "  "))
        if cluster.max_hosts is None:
            details.append(indent + "  Max members: unlimited")
        else:
            details.append(indent + "  Max members: %s" % cluster.max_hosts)

        if cluster.down_hosts_percent:
            dht = int((cluster.down_hosts_threshold * len(cluster.hosts)) / 100)
            details.append(indent + "  Down Hosts Threshold: %s (%s%%)" %
                           (dht, cluster.down_hosts_threshold))
        else:
            details.append(indent + "  Down Hosts Threshold: %s" %
                           cluster.down_hosts_threshold)

        if cluster.down_maint_threshold is not None:
            if cluster.down_maint_percent:
                dht = int((cluster.down_maint_threshold *
                           len(cluster.hosts)) / 100)
                details.append(indent + "  Maintenance Threshold: %s (%s%%)" %
                               (dht, cluster.down_maint_threshold))
            else:
                details.append(indent + "  Maintenance Threshold: %s" %
                               cluster.down_maint_threshold)

        if cluster.resholder and cluster.resholder.resources:
            details.append(indent + "  Resources:")
            for resource in sorted(cluster.resholder.resources,
                                   key=attrgetter('resource_type', 'name')):
                details.append(self.redirect_raw(resource, indent + "    "))

        if cluster.virtual_switch:
            details.append(indent + "  {0:c}: {0!s}"
                           .format(cluster.virtual_switch))

        if isinstance(cluster, EsxCluster):
            details.append(indent + "  Virtual Machine count: %s" %
                           len(cluster.virtual_machines))
            details.append(indent + "  ESX VMHost count: %s" %
                           len(cluster.hosts))
            if cluster.network_device:
                details.append(indent + "  {0:c}: {0!s}".format(cluster.network_device))
            caps = cluster.get_total_capacity()
            if caps:
                overrides = cluster.get_capacity_overrides()
                values = []
                for name, value in caps.items():
                    flags = ""
                    if overrides.get(name) is not None:
                        flags = " [override]"
                    values.append("%s: %s%s" % (name, value, flags))
                capstr = ", ".join(values)
            else:
                capstr = None
            details.append(indent + "  Capacity limits: %s" % capstr)
            usage = cluster.get_total_usage()
            if usage:
                usagestr = ", ".join(["%s: %s" % (name, value) for name, value
                                      in usage.items()])
            else:
                usagestr = None
            details.append(indent + "  Resources used by VMs: %s" % usagestr)
        details.append(self.redirect_raw(cluster.status, indent + "  "))
        details.append(self.redirect_raw(cluster.personality, indent + "  "))
        details.append(indent + "  {0:c}: {1}"
                       .format(cluster.branch, cluster.authored_branch))
        for dbsi in cluster.services_used:
            details.append(indent +
                           "  Member Alignment: Service %s Instance %s" %
                           (dbsi.service.name, dbsi.name))
        for srv in sorted(cluster.services_provided,
                          key=attrgetter("service_instance.service.name",
                                         "service_instance.name")):
            details.append(indent + "  Provides Service: %s Instance: %s"
                           % (srv.service_instance.service.name,
                              srv.service_instance.name))
            details.append(self.redirect_raw(srv, indent + "    "))
        for personality in cluster.allowed_personalities:
            details.append(indent + "  Allowed Personality: {0}".format(personality))
        for member in sorted(cluster._hosts, key=attrgetter("host.fqdn")):
            details.append(indent + "  Member: %s [node_index: %d]" %
                           (member.host.fqdn, member.node_index))
        if cluster.comments:
            details.append(indent + "  Comments: %s" % cluster.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Cluster] = ClusterFormatter()
ObjectFormatter.handlers[EsxCluster] = ClusterFormatter()
ObjectFormatter.handlers[ComputeCluster] = ClusterFormatter()
ObjectFormatter.handlers[StorageCluster] = ClusterFormatter()
