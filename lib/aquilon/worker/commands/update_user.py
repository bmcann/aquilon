#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2011,2013-2014,2016-2018  Contributor
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

from aquilon.aqdb.model import (
    User,
    UserType,
)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateUser(BrokerCommand):

    required_parameters = ["username"]

    def render(self, session, username, uid, gid, full_name, home_directory,
               user, type, justification, reason, logger, **arguments):
        dbuser = User.get_unique(session, username, compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(dbuser)
        cm.validate()

        # 0 is a valid value for uid
        if uid is not None:
            dbuser.uid = uid

        # 0 is a valid value for gid
        if gid is not None:
            dbuser.gid = gid

        if full_name:
            dbuser.full_name = full_name

        if home_directory:
            dbuser.home_dir = home_directory

        if type:
            dbtype = UserType.get_unique(session, name=type, compel=True)
            dbuser.type = dbtype

        session.flush()

        return
