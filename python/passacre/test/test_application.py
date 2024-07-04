# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import pytest
import py.path
import sys
import traceback

from passacre import application, features, _pyo3_backend


_shush_pyflakes = [features]


datadir = py.path.local(__file__).dirpath('data')


def create_application():
    app = application.Passacre()
    app.environ = {}
    return app


def fake_open(path, mode):
    if 'fail' in path:
        raise IOError()
    return path, mode

def fake_expanduser(path):
    return path.replace('~', '.')

def read_out(capsys, app, *args):
    app.main(args)
    out, err = capsys.readouterr()
    assert not err
    return out

def read_err(capsys, app, *args):
    app.main(args)
    out, err = capsys.readouterr()
    assert not out
    return err


def test_open_first():
    assert application.open_first([
        'fail-spam',
        'fail-spam',
        'eggs',
        'spam',
    ], open=fake_open) == ('eggs', 'r')
    assert application.open_first([
        '~/fail-spam',
        '~/fail-spam',
        '~/eggs',
        '~/spam',
    ], open=fake_open, expanduser=fake_expanduser) == ('./eggs', 'r')
    assert application.open_first([
        'fail-spam',
        'fail-spam',
        'eggs',
        'spam',
    ], 'w', open=fake_open) == ('eggs', 'w')
    with pytest.raises(ValueError):
        application.open_first(['fail-spam', 'fail-eggs'], open=fake_open)
    with pytest.raises(ValueError):
        application.open_first([
            '~/fail-spam',
            '~/fail-eggs'
        ], open=fake_open, expanduser=fake_expanduser)
    with pytest.raises(ValueError):
        application.open_first([], open=fake_open)


def test_prompt(capsys):
    assert application.prompt('foo: ', input=lambda: 'bar') == 'bar'
    out, err = capsys.readouterr()
    assert not out
    assert err == 'foo: '


def fake_getpass(outputs):
    def getpass(prompt=None):
        assert prompt in outputs
        return outputs[prompt]
    return getpass

def test_prompt_password():
    assert 'bar' == application.prompt_password(False, getpass=fake_getpass({None: 'bar'}))
    assert 'bar' == application.prompt_password(
        True, getpass=fake_getpass({None: 'bar', 'Confirm password: ': 'bar'}))
    with pytest.raises(ValueError):
        application.prompt_password(
            True, getpass=fake_getpass({None: 'foo', 'Confirm password: ': 'bar'}))


class FakeXerox(object):
    def __init__(self):
        self.copied = []

    def copy(self, arg):
        self.copied.append(arg)

class FakeSleep(object):
    def __init__(self, interrupt=False):
        self.duration = None
        self.interrupt = interrupt

    def __call__(self, duration):
        self.duration = duration
        if self.interrupt:
            raise KeyboardInterrupt()

class FakeAtexit(object):
    def __init__(self):
        self.calls = []

    def register(self, f, *a, **kw):
        self.calls.append((f, a, kw))

    def call_all(self):
        for f, a, kw in self.calls:
            f(*a, **kw)


class ApplicationTestCaseMixin(object):
    config_dir = None
    hashed_site = None
    hashed_password = None

    @pytest.fixture(autouse=True)
    def set_everything_up(self, capsys):
        self.capsys = capsys
        datadir.join(self.config_dir).chdir()
        self.app = create_application()
        _load_config = self.app.load_config
        self.app.load_config = lambda f=None: _load_config(f, expanduser=fake_expanduser)
        self.confirmed_password = False
        self.app._prompt_password = self.prompt_password
        self.password = 'passacre'

    def prompt_password(self, confirm):
        self.confirmed_password = confirm
        return self.password


    def test_generate_with_newline(self):
        out = read_out(self.capsys, self.app, 'generate', 'example.com')
        assert not self.confirmed_password
        assert out == self.hashed_password + '\n'

    def test_generate_no_newline(self):
        out = read_out(self.capsys, self.app, 'generate', '-n', 'example.com')
        assert out == self.hashed_password

    def test_generate_prompt_site(self):
        self.app.prompt = lambda _: 'example.com'
        out = read_out(self.capsys, self.app, 'generate')
        assert out == self.hashed_password + '\n'

    def test_generate_confirm_password(self):
        out = read_out(self.capsys, self.app, 'generate', 'example.com', '-c')
        assert self.confirmed_password
        assert out == self.hashed_password + '\n'

    def test_generate_copying(self):
        self.app.xerox = FakeXerox()
        err = read_err(self.capsys, self.app, 'generate', 'example.com', '-C')
        assert err == 'password copied.\n'
        assert self.app.xerox.copied == [self.hashed_password]

    def test_generate_copy_timeout(self):
        self.app.xerox = FakeXerox()
        self.app.sleep = FakeSleep()
        self.app.atexit = FakeAtexit()
        err = read_err(self.capsys, self.app, 'generate', 'example.com', '-C', '-w', '10')
        assert err == 'password copied.\n'
        assert self.app.xerox.copied == [self.hashed_password]
        assert self.app.sleep.duration == 10
        self.app.atexit.call_all()
        assert self.app.xerox.copied == [self.hashed_password, '']

    def test_generate_copy_timeout_interrupted(self):
        self.app.xerox = FakeXerox()
        self.app.sleep = FakeSleep(interrupt=True)
        self.app.atexit = FakeAtexit()
        err = read_err(self.capsys, self.app, 'generate', 'example.com', '-C', '-w', '10')
        assert err == 'password copied.\n'
        assert self.app.xerox.copied == [self.hashed_password]
        assert self.app.sleep.duration == 10
        self.app.atexit.call_all()
        assert self.app.xerox.copied == [self.hashed_password, '']


    def test_entropy(self):
        out = read_out(self.capsys, self.app, 'entropy')
        # stripping trailing whitespace is a bitch
        out = '\n'.join(line.rstrip() for line in out.splitlines())
        assert out == """
                      site                         entropy (bits)

default                                                       210
becu.org                                                      191
fidelity.com                                                  102
schwab.com                                                     48
still.further.example.com                                      40
further.example.com                                            27
example.com                                                    27
%s               14""" % (self.hashed_site,)


    def test_site_hash_with_newline(self):
        out = read_out(self.capsys, self.app, 'site', 'hash', 'hashed.example.com')
        assert not self.confirmed_password
        assert out == self.hashed_site + '\n'

    def test_site_hash_no_newline(self):
        out = read_out(self.capsys, self.app, 'site', 'hash', '-n', 'hashed.example.com')
        assert out == self.hashed_site

    def test_site_hash_prompt_site(self):
        self.app.prompt = lambda _: 'hashed.example.com'
        out = read_out(self.capsys, self.app, 'site', 'hash')
        assert out == self.hashed_site + '\n'

    def test_site_hash_confirm_password(self):
        out = read_out(self.capsys, self.app, 'site', 'hash', 'hashed.example.com', '-c')
        assert self.confirmed_password
        assert out == self.hashed_site + '\n'

    def test_site_hash_overridden_method_keccak(self):
        out = read_out(self.capsys, self.app, 'site', 'hash', 'hashed.example.com', '-m', 'keccak')
        assert out == 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4\n'

    def test_site_hash_overridden_method_skein(self):
        out = read_out(self.capsys, self.app, 'site', 'hash', 'hashed.example.com', '-m', 'skein')
        assert out == 'UYfDoAN9nYMdxCYtgKenzjhbc9eonu3w92ec3SAA5UbT1J3L\n'


    def test_no_args(self):
        with pytest.raises(SystemExit) as excinfo:
            self.app.main([])
        assert excinfo.value.code == 2


class SqliteTestCaseMixin(object):
    def test_schema_entropy(self):
        out = read_out(self.capsys, self.app, 'entropy', '--schema')
        out = '\n'.join(line.rstrip() for line in out.splitlines())
        assert out == """
 schema    entropy (bits)

schema_5              210
schema_3              191
schema_6              102
schema_1               48
schema_4               40
schema_2               27
schema_0               27
schema_7               14"""


class KeccakTestCaseMixin(ApplicationTestCaseMixin):
    hashed_site = 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4'
    hashed_password = 'Abaris abaisance abashedness abarticulation'


class TestKeccakYAML(KeccakTestCaseMixin):
    config_dir = 'keccak-yaml'


class TestKeccakSqlite(KeccakTestCaseMixin, SqliteTestCaseMixin):
    config_dir = 'keccak-sqlite'


class SkeinTestCaseMixin(ApplicationTestCaseMixin):
    hashed_site = 'UYfDoAN9nYMdxCYtgKenzjhbc9eonu3w92ec3SAA5UbT1J3L'
    hashed_password = 'abactor abattoir abashedly abaca'


class TestSkeinYAML(SkeinTestCaseMixin):
    config_dir = 'skein-yaml'


class TestSkeinSqlite(SkeinTestCaseMixin, SqliteTestCaseMixin):
    config_dir = 'skein-sqlite'


@pytest.fixture
def app():
    datadir.chdir()
    app = create_application()
    app.load_config(datadir.join('keccak.sqlite').open('rb'))
    return app

@pytest.fixture
def init_app(app, tmpdir):
    dbpath = tmpdir.join('test.db').strpath
    app.main(['init', dbpath])
    return dbpath, create_application()

def test_init_config(init_app, capsys):
    dbpath, app = init_app
    out = read_out(capsys, app, '-f', dbpath, 'config')
    assert out == ''

def test_init_schemata(init_app, capsys):
    dbpath, app = init_app
    out = read_out(capsys, app, '-f', dbpath, 'schema')
    assert out == '32-printable: [[32, printable]]\n'

def test_init_sites(init_app, capsys):
    dbpath, app = init_app
    out = read_out(capsys, app, '-f', dbpath, 'site')
    assert out == 'default: 32-printable\n'


@pytest.fixture
def yaml2sqlite_app(tmpdir):
    tmp_app = create_application()
    dbpath = tmpdir.join('test.db')
    tmp_app.main(
        ['init', '-y', datadir.join('keccak.yaml').strpath, dbpath.strpath])
    app = create_application()
    app.load_config(dbpath.open('rb'))
    return app

def test_init_from_yaml(yaml2sqlite_app, capsys):
    app = yaml2sqlite_app
    assert read_out(capsys, app, 'schema') == """12-alphanumeric: [[12, alphanumeric]]
32-alphanumeric: [[32, alphanumeric]]
32-printable: [[32, printable]]
8-alphanumeric: [[8, alphanumeric]]
schema_0: [printable, [", ", 4, word], printable]
schema_1: [[" ", 2, word]]
schema_2: [[" ", 4, word]]
schema_3: [[", ", 4, word]]
schema_4: [[16, [alphanumeric, "\\"%'()+,-/:;<=>?\\\\ ^_|"]]]
"""

def test_init_from_yaml_sites(yaml2sqlite_app, capsys):
    app = yaml2sqlite_app
    assert read_out(capsys, app, 'site') == """gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4: schema_1
becu.org: 32-alphanumeric
default: 32-printable
example.com: schema_2
fhcrc.org: 32-printable
fidelity.com: schema_4
further.example.com: schema_3
schwab.com: 8-alphanumeric
scrypt.example.com: 32-printable
scrypt2.example.com: 32-printable
still.further.example.com: schema_0
"""

def test_init_from_yaml_config(yaml2sqlite_app, capsys):
    app = yaml2sqlite_app
    assert read_out(capsys, app, 'config') == """site-hashing.enabled: true
site-hashing.iterations: 10
words-file: words
"""

def test_init_from_yaml_site_config(yaml2sqlite_app, capsys):
    app = yaml2sqlite_app
    assert read_out(capsys, app, 'config', '-s', 'default') == """iterations: 10
method: keccak
"""


def test_site_yaml(app, capsys):
    app.load_config(datadir.join('keccak.yaml').open('rb'))
    out = read_out(capsys, app, 'site')
    assert out == """gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4
becu.org
default
example.com
fhcrc.org
fidelity.com
further.example.com
schwab.com
scrypt.example.com
scrypt2.example.com
still.further.example.com
"""

def test_site_sqlite(app, capsys):
    out = read_out(capsys, app, 'site')
    assert out == """gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4: schema_7
becu.org: schema_3
default: schema_5
example.com: schema_0
fhcrc.org: schema_5
fidelity.com: schema_6
further.example.com: schema_2
schwab.com: schema_1
scrypt.example.com
scrypt2.example.com
still.further.example.com: schema_4
"""

def test_site_yaml_no_hashed(app, capsys):
    app.load_config(datadir.join('keccak.yaml').open('rb'))
    out = read_out(capsys, app, 'site', '--omit-hashed')
    assert out == """becu.org
default
example.com
fhcrc.org
fidelity.com
further.example.com
schwab.com
scrypt.example.com
scrypt2.example.com
still.further.example.com
"""

def test_site_sqlite_no_hashed(app, capsys):
    out = read_out(capsys, app, 'site', '--omit-hashed')
    assert out == """becu.org: schema_3
default: schema_5
example.com: schema_0
fhcrc.org: schema_5
fidelity.com: schema_6
further.example.com: schema_2
schwab.com: schema_1
scrypt.example.com
scrypt2.example.com
still.further.example.com: schema_4
"""

def test_site_sqlite_by_schema(app, capsys):
    out = read_out(capsys, app, 'site', '--by-schema')
    assert out == """schema_0: example.com
schema_1: schwab.com
schema_2: further.example.com
schema_3: becu.org
schema_4: still.further.example.com
schema_5: default, fhcrc.org
schema_6: fidelity.com
schema_7: gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4
"""


def copy_app(name, app, tmpdir):
    datadir.join(name).copy(tmpdir)
    db_copy = tmpdir.join(name)
    app.load_config(db_copy.open('rb'))
    app._prompt_password = lambda confirm: 'passacre'
    return app

@pytest.fixture
def mutable_app(app, tmpdir):
    return copy_app('keccak.sqlite', app, tmpdir)

def test_site_add(mutable_app, capsys):
    app = mutable_app
    assert '\nexample.org: schema_0\n' not in read_out(capsys, app, 'site')
    app.main(['site', 'add', 'example.org', 'schema_0'])
    assert '\nexample.org: schema_0\n' in read_out(capsys, app, 'site')

def test_site_add_hashed(mutable_app, capsys):
    app = mutable_app
    assert 'KE76ybZ-sO7o4iS944E_mo_jTQPCjzifFjyRELZS-RuDbcGu: schema_0\n' not in read_out(
        capsys, app, 'site')
    app.main(['site', '-a', 'add', 'example.org', 'schema_0'])
    assert 'KE76ybZ-sO7o4iS944E_mo_jTQPCjzifFjyRELZS-RuDbcGu: schema_0\n' in read_out(
        capsys, app, 'site')

def test_site_add_with_schema(mutable_app, capsys):
    app = mutable_app
    app.main(['site', 'add', '-N', '[[21, printable]]', 'example.org', '21-printable'])
    assert 'example.org: 21-printable' in read_out(capsys, app, 'site').splitlines()
    assert '21-printable: [[21, printable]]' in read_out(capsys, app, 'schema').splitlines()

def test_site_set_schema(mutable_app, capsys):
    app = mutable_app
    assert '\nexample.com: schema_0\n' in read_out(capsys, app, 'site')
    app.main(['site', 'set-schema', 'example.com', 'schema_7'])
    assert '\nexample.com: schema_7\n' in read_out(capsys, app, 'site')

def test_site_set_schema_hashed(mutable_app, capsys):
    app = mutable_app
    assert 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4: schema_7\n' in read_out(capsys, app, 'site')
    app.main(['site', '-a', 'set-schema', 'hashed.example.com', 'schema_0'])
    assert 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4: schema_0\n' in read_out(capsys, app, 'site')

def test_site_remove(mutable_app, capsys):
    app = mutable_app
    assert '\nexample.com:' in read_out(capsys, app, 'site')
    app.main(['site', 'remove', 'example.com'])
    assert '\nexample.com:' not in read_out(capsys, app, 'site')

def test_site_remove_hashed(mutable_app, capsys):
    app = mutable_app
    assert 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4:' in read_out(capsys, app, 'site')
    app.main(['site', '-a', 'remove', 'hashed.example.com'])
    assert 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4:' not in read_out(capsys, app, 'site')

def test_site_remove_default_fails(app):
    with pytest.raises(SystemExit) as excinfo:
        app.main(['site', 'remove', 'default'])
    assert excinfo.value.code

def test_config(app, capsys):
    out = read_out(capsys, app, 'config')
    assert out == """site-hashing.enabled: true
site-hashing.iterations: 10
words-file: words
"""

    out = read_out(capsys, app, 'config', 'site-hashing.enabled')
    assert out == 'true\n'

    out = read_out(capsys, app, 'config', 'site-hashing')
    assert out == 'enabled: true, iterations: 10\n'

    out = read_out(capsys, app, 'config', '-s', 'fhcrc.org')
    assert out == 'increment: 5\n'

    out = read_out(capsys, app, 'config', '-s', 'fhcrc.org', 'increment')
    assert out == '5\n'

def get_config_name(app, capsys, site, name):
    args = ['config']
    if site is not None:
        args.extend(['-s', site])
    args.append(name)
    app.main(args)
    out, err = capsys.readouterr()
    assert not err
    return out.rstrip('\n')

def test_config_set(mutable_app, capsys):
    app = mutable_app

    app.main(['config', 'words-file', 'foo'])
    assert get_config_name(app, capsys, None, 'words-file') == 'foo'

    app.main(['config', 'words-file', 'null'])
    assert get_config_name(app, capsys, None, 'words-file') == ''

    app.main(['config', 'spam.spam.spam.eggs', 'spam'])
    assert get_config_name(app, capsys, None, 'spam') == 'spam: {spam: {eggs: spam}}'

    app.main(['config', 'spam.spam.spam.spam', 'spam'])
    assert get_config_name(app, capsys, None, 'spam') == (
        'spam: {spam: {eggs: spam, spam: spam}}')

config_site_set_base_tests = [
    ([], ['increment', '6'], 'fhcrc.org', 'fhcrc.org', 'increment', '6'),
    ([], ['increment', '7'], 'example.com', 'example.com', 'increment', '7'),
    (['-a'], ['increment', '8'], 'hashed.example.com',
     'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4', 'increment', '8'),
    (['-ca'], ['increment', '9'], 'hashed.example.com',
     'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4', 'increment', '9'),
]

config_site_set_tests = []
for pre_args, args, real_site, site, name, value in config_site_set_base_tests:
    config_site_set_tests.append((
        ['config', '-s', real_site] + pre_args + args, site, name, value))
    config_site_set_tests.append((
        ['site', 'config'] + pre_args + [real_site] + args, site, name, value))

@pytest.mark.parametrize(('args', 'site', 'name', 'value'), config_site_set_tests)
def test_config_site_setting(mutable_app, capsys, args, site, name, value):
    mutable_app.main(args)
    assert get_config_name(mutable_app, capsys, site, name) == value

def test_config_set_for_site_without_schema(mutable_app, capsys):
    app = mutable_app
    app.main(['config', '-s', 'nonextant.example.com', 'spam', 'eggs'])
    assert get_config_name(app, capsys, 'nonextant.example.com', 'spam') == 'eggs'
    out = read_out(capsys, app, 'config', '-s', 'nonextant.example.com')
    assert out == 'spam: eggs\n'
    out = read_out(capsys, app, 'site')
    assert 'nonextant.example.com' in out.splitlines()

def test_schema(app, capsys):
    app.main(['schema'])
    out, err = capsys.readouterr()
    assert not err
    assert out == r"""schema_0: [[" ", 4, word]]
schema_1: [[8, alphanumeric]]
schema_2: [[", ", 4, word]]
schema_3: [[32, alphanumeric]]
schema_4: [printable, [", ", 4, word], printable]
schema_5: [[32, printable]]
schema_6: [[16, [alphanumeric, "\"%'()+,-/:;<=>?\\ ^_|"]]]
schema_7: [[" ", 2, word]]
"""

def test_schema_add(mutable_app, capsys):
    app = mutable_app
    app.main(['schema', 'add', 'schema_10', '[alphanumeric, [10, digit]]'])
    assert '\nschema_10: [alphanumeric, [10, digit]]\n' in read_out(capsys, app, 'schema')

def test_schema_set_value(mutable_app, capsys):
    app = mutable_app
    app.main(['schema', 'set-value', 'schema_0', '[[10, digit]]'])
    assert 'schema_0: [[10, digit]]\n' in read_out(capsys, app, 'schema')

def test_schema_set_name(mutable_app, capsys):
    app = mutable_app
    assert 'schema_10:' not in read_out(capsys, app, 'schema')
    app.main(['schema', 'set-name', 'schema_0', 'schema_10'])
    assert 'schema_10:' in read_out(capsys, app, 'schema')

def test_schema_remove(mutable_app, capsys):
    app = mutable_app
    app.main(['schema', 'add', 'schema_10', '[alphanumeric, [10, digit]]'])
    assert 'schema_10:' in read_out(capsys, app, 'schema')
    app.main(['schema', 'remove', 'schema_10'])
    assert 'schema_10:' not in read_out(capsys, app, 'schema')


@pytest.fixture
def always_hash_app(app, tmpdir):
    return copy_app('always-hash.sqlite', app, tmpdir)

def test_always_hash_site_add(always_hash_app, capsys):
    app = always_hash_app
    assert 'KE76ybZ-sO7o4iS944E_mo_jTQPCjzifFjyRELZS-RuDbcGu: schema_0\n' not in read_out(
        capsys, app, 'site')
    app.main(['site', 'add', 'example.org', 'schema_0'])
    assert 'KE76ybZ-sO7o4iS944E_mo_jTQPCjzifFjyRELZS-RuDbcGu: schema_0\n' in read_out(
        capsys, app, 'site')

def test_always_hash_site_remove(always_hash_app, capsys):
    app = always_hash_app
    assert 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4: schema_7\n' in read_out(
        capsys, app, 'site')
    app.main(['site', 'remove', 'hashed.example.com'])
    assert 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4' not in read_out(
        capsys, app, 'site')

def test_always_hash_site_config(always_hash_app, capsys):
    app = always_hash_app
    assert read_out(capsys, app, 'config', '-s', 'hashed.example.com') == 'foo: bar\n'
    app.main(['config', '-s', 'hashed.example.com', 'foo', 'spam'])
    assert read_out(capsys, app, 'config', '-s', 'hashed.example.com') == 'foo: spam\n'


@pytest.fixture
def always_confirm_app(app, tmpdir):
    app = copy_app('always-confirm.sqlite', app, tmpdir)
    def prompt_password(confirm):
        app._confirmed_password = confirm
        return 'passacre'
    app._prompt_password = prompt_password
    return app

def test_always_confirm_site_add(always_confirm_app):
    app = always_confirm_app
    app.main(['site', '-a', 'add', 'example.org', 'schema_0'])
    assert app._confirmed_password

def test_always_confirm_site_remove(always_confirm_app):
    app = always_confirm_app
    app.main(['site', '-a', 'remove', 'hashed.example.com'])
    assert app._confirmed_password

def test_always_confirm_site_config(always_confirm_app):
    app = always_confirm_app
    app.main(['config', '-a', '-s', 'hashed.example.com'])
    assert app._confirmed_password


@pytest.fixture
def nonextant_words_app(app, tmpdir):
    return copy_app('nonextant-words.sqlite', app, tmpdir)

def test_nonextant_words_warns(nonextant_words_app):
    app = nonextant_words_app
    with pytest.raises(_pyo3_backend.PassacreException):
        app.main(['generate', 'example.com'])


class FakeRunAmpCommand(object):
    def __init__(self):
        self.commands = []

    def __call__(self, description, command, args):
        self.commands.append((description, command, args))


@pytest.fixture
def amp_command_app(app):
    app._run_amp_command = FakeRunAmpCommand()
    return app


class FakeError(Exception):
    pass

def test_terse_excepthook(capsys, app):
    app.verbose = False
    try:
        raise FakeError('example')
    except:
        with pytest.raises(SystemExit) as excinfo:
            app.excepthook(*sys.exc_info())
    out, err = capsys.readouterr()
    assert not out
    assert err == '(pass -v for the full traceback)\nFakeError: example\n'
    assert excinfo.value.code == 1

def test_terse_errormark(capsys, app):
    app.verbose = False
    exc = FakeError('example')
    exc._errormark = 'testing this code {0} {spam}', 8, ('foo', 'bar'), {'spam': 'eggs'}
    try:
        raise exc
    except:
        with pytest.raises(SystemExit) as excinfo:
            app.excepthook(*sys.exc_info())
    out, err = capsys.readouterr()
    assert not out
    assert err == """an error occurred testing this code foo eggs
(pass -v for the full traceback)
FakeError: example
"""
    assert excinfo.value.code == 8

def test_verbose_errormark(capsys, app):
    app.verbose = True
    exc = FakeError('example')
    exc._errormark = 'testing this code {0} {spam}', 8, ('foo', 'bar'), {'spam': 'eggs'}
    try:
        raise exc
    except:
        exc_info = sys.exc_info()
    with pytest.raises(SystemExit) as excinfo:
        app.excepthook(*exc_info)
    tb_string = ''.join(traceback.format_exception(*exc_info))
    out, err = capsys.readouterr()
    assert not out
    assert err == 'an error occurred testing this code foo eggs\n' + tb_string
    assert excinfo.value.code == 8
