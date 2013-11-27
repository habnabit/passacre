# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import pytest

from passacre.agent import pencrypt
from passacre.test.test_application import create_application, app, mutable_app


_shush_pyflakes = [app, mutable_app]


protocol = pytest.importorskip('passacre.agent.protocol')
commands = pytest.importorskip('passacre.agent.commands')
secret = pytest.importorskip('nacl.secret')
amp = pytest.importorskip('twisted.protocols.amp')
unittest = pytest.importorskip('twisted.trial.unittest')


@pytest.fixture
def proto(mutable_app, tmpdir):
    def make_app():
        app = create_application()
        app.load_config(tmpdir.join('keccak.sqlite').open('rb'))
        return app
    fac = protocol.PassacreAgentServerFactory(make_app)
    fac.nacl_usable = False
    return fac.buildProtocol(None)


def raises_amp_error(amp_error, f, *a, **kw):
    with pytest.raises(amp.RemoteAmpError) as excinfo:
        f(*a, **kw)
    assert excinfo.value.errorCode == amp_error.errorCode


def test_generate_while_locked(proto):
    raises_amp_error(commands.AgentLocked, proto.generate, 'example.com')

def test_lock_while_locked(proto):
    raises_amp_error(commands.AgentLocked, proto.lock)

def test_fetch_site_list_while_locked(proto):
    raises_amp_error(commands.AgentLocked, proto.fetch_site_list)

def test_build_box_locked(proto):
    raises_amp_error(commands.AgentLocked, proto.build_box, 'site-list')

def test_unlock_while_unlocked(proto):
    proto.unlock('passacre')
    raises_amp_error(commands.AgentUnlocked, proto.unlock, 'passacre')

def test_lock(proto):
    proto.unlock('passacre')
    proto.lock()
    raises_amp_error(commands.AgentLocked, proto.lock)

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


@pytest.fixture
def site_list(tmpdir, proto):
    site_list = tmpdir.join('sites')
    proto.factory.nacl_usable = True
    proto.factory.site_list_path = site_list.strpath
    return site_list

@pytest.fixture
def auth_file(tmpdir, proto):
    auth_file = tmpdir.join('auth')
    proto.factory.nacl_usable = True
    proto.factory.agent_authorization_path = auth_file.strpath
    return auth_file

@pytest.fixture
def box(proto):
    box = secret.SecretBox('\x00' * 32)
    proto.box_of_config_and_password = lambda *a: box
    return box

def test_loading_sites(box, site_list, proto):
    ef = pencrypt.EncryptedFile(box, site_list.strpath)
    ef.write('["list1.example.com", "list2.example.com"]')
    proto.unlock('passacre')
    assert proto.factory.sites == set(['list1.example.com', 'list2.example.com'])

def test_fetching_sites(box, site_list, proto):
    ef = pencrypt.EncryptedFile(box, site_list.strpath)
    ef.write('["list1.example.com"]')
    proto.unlock('passacre')
    assert proto.fetch_site_list() == {'sites': ['list1.example.com']}

def test_saving_sites(box, site_list, proto):
    ef = pencrypt.EncryptedFile(box, site_list.strpath)
    proto.unlock('passacre')
    proto.generate('list1.example.com', save_site=True)
    assert ef.read() == '["list1.example.com"]'

def test_saving_sites_does_not_clobber(box, site_list, proto):
    ef = pencrypt.EncryptedFile(box, site_list.strpath)
    proto.unlock('passacre')
    ef.write('["list1.example.com"]')
    proto.generate('list2.example.com', save_site=True)
    assert ef.read() == '["list1.example.com", "list2.example.com"]'

def test_saving_sites_fails_silently_with_locked_agent(box, site_list, proto):
    ef = pencrypt.EncryptedFile(box, site_list.strpath)
    ef.write('["list1.example.com"]')
    proto.generate('list2.example.com', password='passacre', save_site=True)
    assert ef.read() == '["list1.example.com"]'

def test_saving_sites_fails_on_decryption_failures(site_list, proto):
    with site_list.open('wb') as outfile:
        outfile.write('\x00' * 64)
    proto.unlock('passacre')
    raises_amp_error(commands.SiteListFailedDecryption,
                     proto.generate, 'list1.example.com', save_site=True)

def test_lock_clears_sites(box, site_list, proto):
    ef = pencrypt.EncryptedFile(box, site_list.strpath)
    ef.write('["list1.example.com"]')
    proto.unlock('passacre')
    proto.lock()
    assert proto.factory.sites == set()

def test_initialize_site_list(box, auth_file, site_list, proto):
    ef = pencrypt.EncryptedFile(box, site_list.strpath)
    proto.initialize('passacre')
    assert ef.read() == '[]'

def test_initialize_auth_file(box, auth_file, site_list, proto):
    ef = pencrypt.EncryptedFile(box, auth_file.strpath)
    proto.initialize('passacre')
    assert ef.read() == 'ok'

def test_initialize_does_not_clobber_site_list(box, auth_file, site_list, proto):
    ef = pencrypt.EncryptedFile(box, site_list.strpath)
    ef.write('["list1.example.com"]')
    proto.initialize('passacre')
    assert ef.read() == '["list1.example.com"]'

def test_initialize_does_not_clobber_auth_file(box, auth_file, site_list, proto):
    ef = pencrypt.EncryptedFile(box, auth_file.strpath)
    ef.write('ok')
    proto.initialize('passacre')
    assert ef.read() == 'ok'

def test_initialize_reraises_other_than_ENOENT(auth_file, site_list, proto):
    with auth_file.open('wb') as outfile:
        outfile.write('\x00' * 64)
    auth_file.chmod(0)
    pytest.raises(IOError, proto.initialize, 'passacre')

def test_initialize_checks_authorization_file_encryption(auth_file, site_list, proto):
    with auth_file.open('wb') as outfile:
        outfile.write('\x00' * 64)
    raises_amp_error(commands.AgentUnauthorized, proto.initialize, 'passacre')

def test_initialize_checks_authorization_file_contents(box, auth_file, site_list, proto):
    ef = pencrypt.EncryptedFile(box, auth_file.strpath)
    ef.write('no-kay')
    raises_amp_error(commands.AgentUnauthorized, proto.initialize, 'passacre')

def test_unlock_checks_authorization_file_encryption(auth_file, proto):
    with auth_file.open('wb') as outfile:
        outfile.write('\x00' * 64)
    proto.app.config.global_config.update({'agent': {'require-authorization': True}})
    raises_amp_error(commands.AgentUnauthorized, proto.unlock, 'passacre')

def test_unlock_checks_authorization_file_contents(box, auth_file, proto):
    ef = pencrypt.EncryptedFile(box, auth_file.strpath)
    ef.write('no-kay')
    proto.app.config.global_config.update({'agent': {'require-authorization': True}})
    raises_amp_error(commands.AgentUnauthorized, proto.unlock, 'passacre')

def test_unlock_only_optionally_checks_authorization_file(auth_file, proto):
    with auth_file.open('wb') as outfile:
        outfile.write('\x00' * 64)
    proto.app.config.global_config.update({'agent': {'require-authorization': False}})
    proto.unlock('passacre')
    assert proto.factory.password == 'passacre'


class LoggingTests(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def init_proto(self, proto):
        self.proto = proto

    def test_errors_get_logged(self):
        self.proto.factory.nacl_usable = True
        self.proto.factory.site_list_path = 'non/extant/path'
        self.proto.unlock('passacre')
        assert len(self.flushLoggedErrors(IOError)) == 1
