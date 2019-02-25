# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2015,2018  Contributor
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

from aquilon.worker.templates.base import (
    add_location_info,
    ObjectPlenary,
    Plenary,
    PlenaryCollection,
    PlenaryParameterized,
    StructurePlenary,
)
from aquilon.worker.templates.city import PlenaryCity
from aquilon.worker.templates.personality import (PlenaryPersonality,
                                                  PlenaryPersonalityBase)
from aquilon.worker.templates.switchdata import PlenarySwitchData
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.templates.network import PlenaryNetwork
from aquilon.worker.templates.resource import PlenaryResource
from aquilon.worker.templates.service import (PlenaryService,
                                              PlenaryServiceToplevel,
                                              PlenaryServiceClientDefault,
                                              PlenaryServiceServerDefault,
                                              PlenaryServiceInstance,
                                              PlenaryServiceInstanceToplevel,
                                              PlenaryServiceInstanceClientDefault,
                                              PlenaryServiceInstanceServer,
                                              PlenaryServiceInstanceServerDefault)
from aquilon.worker.templates.grn import PlenaryParameterizedGrn
from aquilon.worker.templates.metacluster import (PlenaryMetaCluster,
                                                  PlenaryMetaClusterData,
                                                  PlenaryMetaClusterObject)
from aquilon.worker.templates.cluster import (PlenaryCluster,
                                              PlenaryClusterData,
                                              PlenaryClusterObject,
                                              PlenaryClusterClient)
from aquilon.worker.templates.host import (
    PlenaryHost,
    PlenaryHostData,
    PlenaryHostGrn,
    PlenaryHostObject,
)
from aquilon.worker.templates.network_device import PlenaryNetworkDeviceInfo
from aquilon.worker.templates.virtual_switch import PlenaryVirtualSwitchData
from aquilon.worker.templates.domain import TemplateDomain
