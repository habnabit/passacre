# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import uuid

from passacre._version import __version__, __sha__


signing_uuid = uuid.UUID('dd34b62f-9ed5-597e-85a2-c15d48ed6832')

__all__ = ['__version__', '__sha__', 'signing_uuid']
