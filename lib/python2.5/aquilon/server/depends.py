#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Suggested versions of external libraries, and the defaults for the 
    binaries shipped.
    
"""

import sys
sys.path.append("//ms/dist/python/PROJ/ms.version/prod-2.5/common/lib/")
import ms.version
ms.version.addpkg('setuptools', '0.6c8-py25')
ms.version.addpkg('protoc', 'prod', meta='aquilon')
ms.version.addpkg('zope.interface', '3.3.0', 'dist')
ms.version.addpkg('twisted', '8.1.0', 'dist')
