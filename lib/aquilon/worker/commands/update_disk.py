# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014,2015,2016,2017,2019  Contributor
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
"""Contains the logic for `aq update disk`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Machine, Disk, VirtualDisk, Filesystem, Share
from aquilon.utils import force_wwn
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import find_resource
from aquilon.worker.dbwrappers.hardware_entity import get_hardware
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateDisk(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["disk"]

    def render(self, session, plenaries, disk, controller, share,
               filesystem, resourcegroup, address, comments, size, boot,
               snapshot, rename_to, wwn, bus_address, iops_limit,
               disk_tech, diskgroup_key, model_key, usage, vsan_policy_key,
               user, justification, reason, logger, **kwargs):

        dbmachine = get_hardware(session, compel=True, **kwargs)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **kwargs)
        cm.consider(dbmachine)
        cm.validate()

        dbdisk = Disk.get_unique(session, device_name=disk, machine=dbmachine,
                                 compel=True)

        plenaries.add(dbmachine)

        if rename_to:
            Disk.get_unique(session, device_name=rename_to, machine=dbmachine,
                            preclude=True)
            dbdisk.device_name = rename_to

        if comments is not None:
            dbdisk.comments = comments

        if disk_tech is not None:
            if disk_tech:
                dbdisk.disk_tech = disk_tech
            else:
                dbdisk.disk_tech = None     # clear to NULL if empty-string

        if diskgroup_key is not None:
            if diskgroup_key:
                dbdisk.diskgroup_key = diskgroup_key
            else:
                dbdisk.diskgroup_key = None   # clear to NULL if empty-string

        if model_key is not None:
            if model_key:
                dbdisk.model_key = model_key
            else:
                dbdisk.model_key = None     # clear to NULL if empty-string

        if usage is not None:
            if usage:
                dbdisk.usage = usage
            else:
                dbdisk.usage = None         # clear to NULL if empty-string

        if vsan_policy_key is not None:
            if not isinstance(dbdisk, VirtualDisk):
                raise ArgumentError("VSAN policy can only be set for "
                                    "virtual disks.")
            if vsan_policy_key:
                dbdisk.vsan_policy_key = vsan_policy_key
            else:
                dbdisk.vsan_policy_key = None   # clear to NULL if ""

        if wwn is not None:
            wwn = force_wwn("--wwn", wwn)
            dbdisk.wwn = wwn

        if size is not None:
            dbdisk.capacity = size

        if controller:
            dbdisk.controller_type = controller

        if boot is not None:
            dbdisk.bootable = boot
            # There should be just one boot disk. We may need to re-think this
            # if we want to model software RAID in the database.
            for disk in dbmachine.disks:
                if disk == dbdisk:
                    continue
                if boot and disk.bootable:
                    disk.bootable = False

        if address is not None:
            dbdisk.address = address

        if bus_address is not None:
            dbdisk.bus_address = bus_address

        if snapshot is not None:
            if not isinstance(dbdisk, VirtualDisk):
                raise ArgumentError("Snapshot capability can only be set for "
                                    "virtual disks.")
            dbdisk.snapshotable = snapshot

        if iops_limit is not None:
            if not isinstance(dbdisk, VirtualDisk):
                raise ArgumentError("IOPS limit can only be set for virtual disks.")
            dbdisk.iops_limit = iops_limit

        if share or filesystem:
            if not isinstance(dbdisk, VirtualDisk):
                raise ArgumentError("Disk {0!s} of {1:l} is not a virtual "
                                    "disk, changing the backend store is not "
                                    "possible.".format(dbdisk, dbmachine))

            if share:
                dbres = find_resource(Share,
                                      dbmachine.vm_container.holder.holder_object,
                                      resourcegroup, share)
            elif filesystem:
                dbres = find_resource(Filesystem,
                                      dbmachine.vm_container.holder.holder_object,
                                      resourcegroup, filesystem)

            dbdisk.backing_store = dbres

        session.flush()

        plenaries.write()

        return
