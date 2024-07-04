# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import uuid

from passacre._version import get_versions


signing_uuid = uuid.UUID('dd34b62f-9ed5-597e-85a2-c15d48ed6832')
__version__ = get_versions()['version']
del get_versions


__all__ = ('__version__', 'signing_uuid')

from . import _version
__version__ = _version.get_versions()['version']
