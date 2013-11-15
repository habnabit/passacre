import errno
import json
import os

from twisted.internet import protocol
from twisted.protocols import amp

from passacre.agent import commands
from passacre.application import is_likely_hashed_site


try:
    from passacre.agent import pencrypt
except ImportError:
    pencrypt = None


class PassacreAgentServerProtocol(amp.AMP):
    def __init__(self, factory, app):
        amp.AMP.__init__(self)
        self.factory = factory
        self.app = app

    @commands.Unlock.responder
    def unlock(self, password):
        if self.factory.password is not None:
            raise commands.AgentUnlocked()
        self.factory.password = password
        return {}

    @commands.Lock.responder
    def lock(self):
        if self.factory.password is None:
            raise commands.AgentLocked()
        self.factory.password = self.factory.sites = None
        return {}

    @commands.Generate.responder
    def generate(self, site, username=None, password=None):
        if password is None:
            password = self.factory.password
        if password is None:
            raise commands.AgentLocked()
        generated = self.app.config.generate_for_site(
            username, password, site)
        return {'password': generated}

    @commands.FetchSiteList.responder
    def fetch_site_list(self, force_disk_load=False):
        if force_disk_load or self.factory.sites is None:
            fobj = self.factory.sites_file()
            try:
                data = fobj.read()
            except (OSError, IOError) as e:
                if e.errno != errno.EEXIST:
                    raise
                else:
                    self.factory.sites = []
            else:
                self.factory.sites = json.loads(data.decode())
        return {'sites': self.factory.sites}

    @commands.WriteSiteList.responder
    def write_site_list(self, sites):
        fobj = self.factory.sites_file()
        fobj.write(json.dumps(sites).encode())


class PassacreAgentServerFactory(protocol.Factory):
    protocol = PassacreAgentServerProtocol

    def __init__(self, app):
        self.app = app
        self.password = None
        self.sites = None

    def build_box(self):
        if pencrypt is None:
            raise commands.SiteListUnavailable()
        if self.password is None:
            raise commands.AgentLocked()
        return pencrypt.box_of_config_and_password(self.app.config, self.password)

    def sites_file(self):
        return pencrypt.EncryptedFile(
            self.build_box(),
            os.path.expanduser('~/.config/passacre/sites'))

    def buildProtocol(self, addr):
        return self.protocol(self, self.app)
