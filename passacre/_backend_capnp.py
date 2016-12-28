from contextlib import closing
import os
import socket
import sys

import capnp

from passacre import _passacre_capnp

try:
    import subprocess32 as subprocess
except ImportError:
    import subprocess


_32bit_overrides = {
    ('Darwin', 'x86_64'): 'i386',
    ('Darwin', 'ppc64'): 'ppc',
    ('Linux', 'x86_64'): 'i686',
}


def _determine_backend():
    """
    The backend used is chosen using pip's (non-public) logic for determining
    platform and architecture, which is based on the architecture that python
    is compiled for, not the architecture of the kernel (as returned by uname).
    """
    plat, _, _, _, arch = os.uname()
    if sys.maxsize == 0x7fffffff:  # 32-bit python
        arch = _32bit_overrides.get((plat, arch), arch)
    return 'passacre-backend-{0}-{1}'.format(plat, arch)


class SubprocessClient(object):
    _proc = _sock = None
    _backend = _determine_backend()

    def _reconnect(self):
        if self._sock is not None:
            self._sock.close()
        if self._proc is not None:
            self._proc.wait()
        self._sock, remote = socket.socketpair()
        with closing(remote):
            with open(os.devnull, 'r+') as devnull:
                self._proc = subprocess.Popen(
                    [self._backend, str(remote.fileno())],
                    stdin=devnull, pass_fds=[remote.fileno()])
        self._sock_client = capnp.TwoPartyClient(self._sock)
        self._client = self._sock_client.bootstrap().cast_as(_passacre_capnp.Toplevel)

    @property
    def _active_client(self):
        if self._proc is None or self._proc.poll() is not None:
            self._reconnect()
        return self._client

    def derive(self, site, user_input):
        return self._active_client.derive(site, user_input).wait().derived

    def entropy_bits(self, schema):
        return self._active_client.entropyBits(schema).wait().bits


default_client = SubprocessClient()
