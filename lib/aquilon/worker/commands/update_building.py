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
"""Contains the logic for `aq update building`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import HardwareEntity, ServiceMap
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location, update_location
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandUpdateBuilding(BrokerCommand):

    required_parameters = ["building"]

    def render(self, session, logger, building, city, address,
               fullname, default_dns_domain, comments, **_):
        dbbuilding = get_location(session, building=building)

        old_city = dbbuilding.city

        dsdb_runner = DSDBRunner(logger=logger)

        if address is not None:
            old_address = dbbuilding.address
            dbbuilding.address = address
            dsdb_runner.update_building(dbbuilding.name, dbbuilding.address,
                                        old_address)

        update_location(dbbuilding, fullname=fullname, comments=comments,
                        default_dns_domain=default_dns_domain)

        plenaries = PlenaryCollection(logger=logger)
        if city:
            dbcity = get_location(session, city=city)

            q = session.query(HardwareEntity)
            # HW types which have plenary templates
            q = q.filter(HardwareEntity.hardware_type.in_(['machine',
                                                           'network_device']))
            q = q.filter(HardwareEntity.location_id.in_(dbbuilding.offspring_ids()))

            # This one would change the template's locations hence forbidden
            if dbcity.hub != dbbuilding.hub and q.count():
                # Doing this both to reduce user error and to limit
                # testing required.
                raise ArgumentError("Cannot change hubs. {0} is in {1:l}, "
                                    "while {2:l} is in {3:l}."
                                    .format(dbcity, dbcity.hub, dbbuilding,
                                            dbbuilding.hub))

            # issue svcmap warnings
            maps = session.query(ServiceMap).filter_by(location=old_city).count()

            if maps:
                logger.client_info("There are {0} service(s) mapped to the "
                                   "old location of the ({1:l}), please "
                                   "review and manually update mappings for "
                                   "the new location as needed."
                                   .format(maps, dbbuilding.city))

            dbbuilding.update_parent(parent=dbcity)

            if old_city.campus and (old_city.campus != dbcity.campus):
                dsdb_runner.del_campus_building(old_city.campus, building)

            if dbcity.campus and (old_city.campus != dbcity.campus):
                dsdb_runner.add_campus_building(dbcity.campus, building)

            plenaries.extend(map(Plenary.get_plenary, q))

        session.flush()

        if plenaries.plenaries:
            with plenaries.transaction():
                dsdb_runner.commit_or_rollback()
        else:
            dsdb_runner.commit_or_rollback()

        return
