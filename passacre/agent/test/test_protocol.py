import pytest

from passacre.test.test_application import create_application, app, mutable_app, datadir


_shush_pyflakes = [app, mutable_app]


protocol = pytest.importorskip('passacre.agent.protocol')
commands = pytest.importorskip('passacre.agent.commands')
unittest = pytest.importorskip('twisted.trial.unittest')


@pytest.fixture
def proto(mutable_app, tmpdir):
    def make_app():
        app = create_application()
        app.load_config(tmpdir.join('keccak.sqlite').open('rb'))
        return app
    fac = protocol.PassacreAgentServerFactory(make_app)
    fac.site_list_path = datadir.join('site-list').strpath
    return fac.buildProtocol(None)


def test_generate_while_locked(proto):
    pytest.raises(commands.AgentLocked, proto.generate, 'example.com')

def test_lock_while_locked(proto):
    pytest.raises(commands.AgentLocked, proto.lock)

def test_fetch_site_list_while_locked(proto):
    pytest.raises(commands.AgentLocked, proto.fetch_site_list)

def test_unlock_while_unlocked(proto):
    proto.unlock('passacre')
    pytest.raises(commands.AgentUnlocked, proto.unlock, 'passacre')

def test_generate(proto):
    proto.unlock('passacre')
    assert proto.generate('example.com') == {
        'password': 'Abaris abaisance abashedness abarticulation'}

def test_generate_with_password(proto):
    assert proto.generate('example.com', password='passacre') == {
        'password': 'Abaris abaisance abashedness abarticulation'}

def test_generate_with_username(proto):
    assert proto.generate('schwab.com', 'passacre', 'passacre') == {
        'password': 'JkbefmM3'}

def test_generate_after_site_config_update(mutable_app, tmpdir):
    proto1 = proto(mutable_app, tmpdir)
    assert proto1.generate('example.com', password='passacre') == {
        'password': 'Abaris abaisance abashedness abarticulation'}
    app2 = create_application()
    app2.load_config(tmpdir.join('keccak.sqlite').open('rb'))
    app2.main(['site', 'config', 'example.com', 'increment', '2'])
    proto2 = proto(mutable_app, tmpdir)
    assert proto2.generate('example.com', password='passacre') == {
        'password': 'Ababdeh abasement aa abashedness'}

def test_generate_after_global_config_update(mutable_app, tmpdir):
    proto1 = proto(mutable_app, tmpdir)
    assert proto1.generate('example.com', password='passacre') == {
        'password': 'Abaris abaisance abashedness abarticulation'}
    app2 = create_application()
    app2.load_config(tmpdir.join('keccak.sqlite').open('rb'))
    app2.main(['config', 'words-file', 'words2'])
    proto2 = proto(mutable_app, tmpdir)
    assert proto2.generate('example.com', password='passacre') == {
        'password': 'abey abeltree abhorring abeyant'}


class LoggingTests(unittest.TestCase):
    pass
