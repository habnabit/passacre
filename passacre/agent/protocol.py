from twisted.internet import protocol
from twisted.protocols import amp

from passacre.agent import commands


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
        self.factory.password = None
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


class PassacreAgentServerFactory(protocol.Factory):
    protocol = PassacreAgentServerProtocol

    def __init__(self, app):
        self.app = app
        self.password = None

    def buildProtocol(self, addr):
        return self.protocol(self, self.app)
