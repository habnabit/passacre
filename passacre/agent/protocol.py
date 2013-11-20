# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import json
import os

from twisted.internet import protocol
from twisted.protocols import amp
from twisted.python import log

from passacre.agent import commands, pencrypt


try:
    from nacl.exceptions import CryptoError
except ImportError:
    CryptoError = None


class PassacreAgentServerProtocol(amp.AMP):
    def __init__(self, factory, app):
        amp.AMP.__init__(self)
        self.factory = factory
        self.app = app
        self.sites_file = None

    @commands.Unlock.responder
    def unlock(self, password):
        if self.factory.password is not None:
            raise commands.AgentUnlocked()
        self.factory.password = password
        self.load_sites()
        return {}

    @commands.Lock.responder
    def lock(self):
        if self.factory.password is None:
            raise commands.AgentLocked()
        self.factory.password = None
        self.factory.sites = set()
        return {}

    @commands.Generate.responder
    def generate(self, site, username=None, password=None, save_site=False):
        if password is None:
            password = self.factory.password
        if password is None:
            raise commands.AgentLocked()
        generated = self.app.config.generate_for_site(
            username, password, site)
        if save_site and self.factory.password is not None:
            self.factory.sites.add(site)
            self.save_sites()
        return {'password': generated}

    @commands.FetchSiteList.responder
    def fetch_site_list(self):
        if self.factory.password is None:
            raise commands.AgentLocked()
        return {'sites': list(self.factory.sites)}


    box_of_config_and_password = staticmethod(pencrypt.box_of_config_and_password)

    def build_box(self):
        if self.factory.password is None:
            raise commands.AgentLocked()
        return self.box_of_config_and_password(self.app.config, self.factory.password)

    def make_sites_file(self):
        return pencrypt.EncryptedFile(
            self.build_box(),
            os.path.expanduser(self.factory.site_list_path))

    def load_sites(self):
        if not self.factory.site_list_usable:
            return
        sites_file = self.make_sites_file()
        try:
            data = sites_file.read()
            self.factory.sites.update(json.loads(data.decode()))
        except Exception:
            log.err(None, 'error loading sites file')

    def save_sites(self):
        sites_file = self.make_sites_file()
        try:
            sites_file.read()
        except IOError:
            pass
        except CryptoError:
            raise commands.SiteListFailedDecryption()
        sites_file.write(json.dumps(list(self.factory.sites)).encode())


class PassacreAgentServerFactory(protocol.Factory):
    protocol = PassacreAgentServerProtocol
    site_list_path = '~/.config/passacre/sites'
    site_list_usable = pencrypt.SecretBox is not None

    def __init__(self, app_factory):
        self.app_factory = app_factory
        self.password = None
        self.sites = set()

    def buildProtocol(self, addr):
        return self.protocol(self, self.app_factory())
