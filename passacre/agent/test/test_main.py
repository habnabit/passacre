import pytest

commands = pytest.importorskip('passacre.agent.commands')
main = pytest.importorskip('passacre.agent.main')
proto_helpers = pytest.importorskip('twisted.test.proto_helpers')


def make_connection(reactor, host, port):
    idx = next(e for e, (h, p, _, _, _) in enumerate(reactor.tcpClients) if host == h and port == p)
    _, _, fac, _, _ = reactor.tcpClients.pop(idx)
    proto = fac.buildProtocol(None)
    transport = proto_helpers.StringTransport()
    proto.makeConnection(transport)
    return proto, transport


def test_run_amp_command():
    reactor = proto_helpers.MemoryReactor()
    d = main._run_amp_command('tcp:localhost:9000', commands.Lock, {}, reactor)
    result = []
    d.addCallback(result.append)
    proto, transport = make_connection(reactor, 'localhost', 9000)
    assert transport.value() == '\x00\x04_ask\x00\x011\x00\x08_command\x00\x04Lock\x00\x00'
    proto.dataReceived('\x00\x07_answer\x00\x011\x00\x00')
    assert result == [{}]
