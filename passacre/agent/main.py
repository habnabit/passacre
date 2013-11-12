import sys

from twisted.internet import endpoints, task, defer
from twisted.protocols.amp import AMP
from twisted.python import log

from passacre.agent.protocol import PassacreAgentServerFactory


def _twisted_server_main(reactor, app, description):
    endpoint = endpoints.serverFromString(reactor, description)
    d = endpoint.listen(PassacreAgentServerFactory(app))
    d.addCallback(lambda ign: defer.Deferred())
    return d


def server_main(*args):
    log.startLogging(sys.stdout)
    task.react(_twisted_server_main, args)


def _twisted_client_main(reactor, deferred, description, command, args):
    endpoint = endpoints.clientFromString(reactor, description)
    amp = AMP()
    d = endpoints.connectProtocol(endpoint, amp)
    d.addCallback(lambda ign: amp.callRemote(command, **args))
    d.addBoth(deferred.callback)
    d.addCallback(lambda ign: deferred)
    return d


def client_main(*args):
    task.react(_twisted_client_main, args)
