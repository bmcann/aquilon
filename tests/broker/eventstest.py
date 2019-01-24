# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015-2017,2019  Contributor
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
"""Mixin for testing the events system"""

import os
from time import sleep
import json


def partial_match(want, got):
    '''
    Function to partially match what we want (first parameter) to what we
    actually got (second parameter). It recursively calls itself to check
    partial matches for sub dictionnaries and lists (lists must be identical
    in size)
    '''
    if isinstance(want, dict):
        if not isinstance(got, dict):
            return False
        for field, value in want.items():
            if field not in got:
                return False
            if not partial_match(value, got[field]):
                return False
    elif isinstance(want, list):
        if not isinstance(got, list):
            return False
        if len(want) != len(got):
            return False
        for i in range(len(want)):
            if not partial_match(want[i], got[i]):
                return False
    elif want != got:
        return False
    return True


class EventsTestMixin(object):

    @classmethod
    def setUpClass(cls):
        super(EventsTestMixin, cls).setUpClass()
        # Setup the list of expected events (._expected_events) and the path
        # where the events will be queued for checking (_event_dir)
        cls._expected_events = []
        if cls.config.has_section('unittest'):
            cls._event_dir = os.path.join(cls.config.get('unittest', 'scratchdir'), 'events')
        else:
            cls._event_dir = os.path.join(cls.config.get('quattordir'), 'scratch', 'events')
        if not cls._event_dir:
            raise ValueError('Cannot determin events store')
        if not os.path.exists(cls._event_dir):
            os.makedirs(cls._event_dir)

    def setUp(self):
        super(EventsTestMixin, self).setUp()
        self.events_reset()

    def events_reset(self):
        """Reset the events checking sub-system"""
        self._expected_events = []
        jsonfiles = [p for p in [os.path.join(self._event_dir, f)
                                 for f in os.listdir(self._event_dir)]
                     if os.path.isfile(p)]
        for jsonfile in jsonfiles:
            os.unlink(jsonfile)

    def _event_append_dns(self, fqdn, action, dns_environment='internal', dns_records=None):
        dns_record_list = []

        # Prepare the elements to be read as lists
        if not isinstance(fqdn, list):
            fqdn = [fqdn, ]
            if dns_records is not None:
                dns_records = [dns_records, ]
            dns_environment = [dns_environment, ]
        elif not isinstance(dns_environment, list):
            dns_environment = [dns_environment, ] * len(fqdn)

        # Create records for each element of the list
        for i in range(len(fqdn)):
            _fqdn = fqdn[i]
            _dns_records = (
                None
                if dns_records is None or i > len(dns_records)
                else dns_records[i]
            )
            _dns_environment = dns_environment[i]

            dns_record = {
                'fqdn': _fqdn,
                'environmentName': _dns_environment,
            }
            if _dns_records:
                dns_record['rdata'] = _dns_records

            dns_record_list.append(dns_record)

        self._expected_events.append({
            'action': action,
            'entityType': 'DNS_RECORD',
            'dnsRecordList': {
                'records': dns_record_list,
            },
        })

    def event_add_dns(self, fqdn, dns_records, dns_environment='internal'):
        self._event_append_dns(fqdn, 'CREATE', dns_environment, dns_records)

    def event_upd_dns(self, fqdn, dns_records, dns_environment='internal'):
        self._event_append_dns(fqdn, 'UPDATE', dns_environment, dns_records)

    def event_del_dns(self, fqdn, dns_environment='internal'):
        self._event_append_dns(fqdn, 'DELETE', dns_environment)

    def events_verify(self, strict=False):
        """Check for all expected events"""
        # As the event files are written by another process there is the
        # small chance that it will not have comeplted when we run this
        # check.  To accomodate this we will have two passes at processing
        # the events, after which we will consider it a failure.
        remaining = self._expected_events[:]
        unneeded = []
        for _ in range(1, 30):
            # Find all of the JSON event files in the event directory and
            # process them one by one looking for matches
            jsonfiles = [p for p in [os.path.join(self._event_dir, f)
                                     for f in os.listdir(self._event_dir)]
                         if os.path.isfile(p)]
            for jsonfile in jsonfiles:
                try:
                    with open(jsonfile) as fh:
                        data = json.load(fh)
                        cursize = len(remaining)
                        remaining[:] = [e for e in remaining
                                        if not partial_match(e, data)]
                        if len(remaining) == cursize:
                            unneeded.append(data)
                    os.unlink(jsonfile)
                except ValueError as e:
                    continue
                except IOError as e:
                    continue
            # Check if we have matched all of the remaining events, if so then
            # we have nothiing more to do...
            if not remaining:
                break
            # There are events remaining so we will insert a small delay and
            # after which we will try again.
            sleep(0.1)

        # If there are any events remaining then we have failed to match
        if remaining:
            self.fail('Unmatched events:\n{}\n\nUnused events:\n{}'.format(
                '\n'.join(str(e) for e in remaining),
                '\n'.join(str(e) for e in unneeded)))

        # Some tests call verify multiple times.  To avoid any false
        # results we reset again here just to make sure
        self.events_reset()

