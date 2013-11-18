import sys

from twisted.internet import endpoints, task, defer
from twisted.protocols.amp import AMP
from twisted.python import log

from passacre.agent.protocol import PassacreAgentServerFactory
from passacre.util import lazily_wait_for_reactor


def _twisted_server_main(reactor, app, description):
    endpoint = endpoints.serverFromString(reactor, description)
    d = endpoint.listen(PassacreAgentServerFactory(app))
    d.addCallback(lambda ign: defer.Deferred())
    return d


def server_main(*args):
    log.startLogging(sys.stdout)
    task.react(_twisted_server_main, args)


def _run_amp_command(description, command, args, reactor=None):
    if reactor is None:
        from twisted.internet import reactor
    endpoint = endpoints.clientFromString(reactor, description)
    amp = AMP()
    d = endpoints.connectProtocol(endpoint, amp)
    d.addCallback(lambda ign: amp.callRemote(command, **args))
    return d

run_amp_command = lazily_wait_for_reactor(_run_amp_command)
