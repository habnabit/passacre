# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

import pytest
import py.path
import sqlite3
import unittest

from passacre import application
from passacre.test.util import excinfo_arg_0


datadir = py.path.local(__file__).dirpath('data')


def fake_open(path, mode):
    if 'fail' in path:
        raise IOError()
    return path, mode

def fake_expanduser(path):
    return path.replace('~', '.')

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
    def init_capsys(self, capsys):
        self.capsys = capsys

    def setUp(self):
        datadir.join(self.config_dir).chdir()
        self.app = application.Passacre()
        _load_config = self.app.load_config
        self.app.load_config = lambda f=None: _load_config(f, expanduser=fake_expanduser)
        self.confirmed_password = False
        self.app.prompt_password = self.prompt_password
        self.password = 'passacre'

    def prompt_password(self, confirm):
        self.confirmed_password = confirm
        return self.password


    def test_generate_with_newline(self):
        self.app.main(['generate', 'example.com'])
        assert not self.confirmed_password
        out, err = self.capsys.readouterr()
        assert not err
        assert out == self.hashed_password + '\n'

    def test_generate_no_newline(self):
        self.app.main(['generate', '-n', 'example.com'])
        out, err = self.capsys.readouterr()
        assert not err
        assert out == self.hashed_password

    def test_generate_prompt_site(self):
        self.app.prompt = lambda _: 'example.com'
        self.app.main(['generate'])
        out, err = self.capsys.readouterr()
        assert not err
        assert out == self.hashed_password + '\n'

    def test_generate_confirm_password(self):
        self.app.main(['generate', 'example.com', '-c'])
        assert self.confirmed_password
        out, err = self.capsys.readouterr()
        assert not err
        assert out == self.hashed_password + '\n'

    def test_generate_copying(self):
        self.app.xerox = FakeXerox()
        self.app.main(['generate', 'example.com', '-C'])
        out, err = self.capsys.readouterr()
        assert not out
        assert err == 'password copied.\n'
        assert self.app.xerox.copied == [self.hashed_password]

    def test_generate_copy_timeout(self):
        self.app.xerox = FakeXerox()
        self.app.sleep = FakeSleep()
        self.app.atexit = FakeAtexit()
        self.app.main(['generate', 'example.com', '-C', '-w', '10'])
        out, err = self.capsys.readouterr()
        assert not out
        assert err == 'password copied.\n'
        assert self.app.xerox.copied == [self.hashed_password]
        assert self.app.sleep.duration == 10
        self.app.atexit.call_all()
        assert self.app.xerox.copied == [self.hashed_password, '']

    def test_generate_copy_timeout_interrupted(self):
        self.app.xerox = FakeXerox()
        self.app.sleep = FakeSleep(interrupt=True)
        self.app.atexit = FakeAtexit()
        self.app.main(['generate', 'example.com', '-C', '-w', '10'])
        out, err = self.capsys.readouterr()
        assert not out
        assert err == 'password copied.\n'
        assert self.app.xerox.copied == [self.hashed_password]
        assert self.app.sleep.duration == 10
        self.app.atexit.call_all()
        assert self.app.xerox.copied == [self.hashed_password, '']


    def test_entropy(self):
        self.app.main(['entropy'])
        out, err = self.capsys.readouterr()
        assert not err
        # stripping trailing whitespace is a bitch
        out = '\n'.join(line.rstrip() for line in out.splitlines())
        assert out == """
                      site                         entropy (bits)

default                                                209.75
becu.org                                               190.53
fidelity.com                                           101.72
schwab.com                                              47.63
still.further.example.com                               39.68
further.example.com                                     26.58
example.com                                             26.58
%s        13.29""" % (self.hashed_site,)


    def test_site_hash_with_newline(self):
        self.app.main(['site', 'hash', 'hashed.example.com'])
        assert not self.confirmed_password
        out, err = self.capsys.readouterr()
        assert not err
        assert out == self.hashed_site + '\n'

    def test_site_hash_no_newline(self):
        self.app.main(['site', 'hash', '-n', 'hashed.example.com'])
        out, err = self.capsys.readouterr()
        assert not err
        assert out == self.hashed_site

    def test_site_hash_prompt_site(self):
        self.app.prompt = lambda _: 'hashed.example.com'
        self.app.main(['site', 'hash'])
        out, err = self.capsys.readouterr()
        assert not err
        assert out == self.hashed_site + '\n'

    def test_site_hash_confirm_password(self):
        self.app.main(['site', 'hash', 'hashed.example.com', '-c'])
        assert self.confirmed_password
        out, err = self.capsys.readouterr()
        assert not err
        assert out == self.hashed_site + '\n'

    def test_site_hash_overridden_method_keccak(self):
        self.app.main(['site', 'hash', 'hashed.example.com', '-m', 'keccak'])
        out, err = self.capsys.readouterr()
        assert not err
        assert out == 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4\n'

    @pytest.mark.skipif("sys.version_info < (3,)")
    def test_site_hash_overridden_method_skein(self):
        self.app.main(['site', 'hash', 'hashed.example.com', '-m', 'skein'])
        out, err = self.capsys.readouterr()
        assert not err
        assert out == 'UYfDoAN9nYMdxCYtgKenzjhbc9eonu3w92ec3SAA5UbT1J3L\n'


    def test_no_args(self):
        with pytest.raises(SystemExit) as excinfo:
            self.app.main([])
        assert excinfo_arg_0(excinfo) == 2


class SqliteTestCaseMixin(object):
    def test_schema_entropy(self):
        self.app.main(['entropy', '--schema'])
        out, err = self.capsys.readouterr()
        assert not err
        out = '\n'.join(line.rstrip() for line in out.splitlines())
        assert out == """
 schema    entropy (bits)

schema_5       209.75
schema_3       190.53
schema_6       101.72
schema_1        47.63
schema_4        39.68
schema_2        26.58
schema_0        26.58
schema_7        13.29"""


class KeccakTestCaseMixin(ApplicationTestCaseMixin):
    hashed_site = 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4'
    hashed_password = 'Abaris abaisance abashedness abarticulation'

class KeccakYAMLTestCase(KeccakTestCaseMixin, unittest.TestCase):
    config_dir = 'keccak-yaml'

class KeccakSqliteTestCase(KeccakTestCaseMixin, SqliteTestCaseMixin, unittest.TestCase):
    config_dir = 'keccak-sqlite'


@pytest.mark.skipif("sys.version_info < (3,)")
class SkeinTestCaseMixin(ApplicationTestCaseMixin):
    hashed_site = 'UYfDoAN9nYMdxCYtgKenzjhbc9eonu3w92ec3SAA5UbT1J3L'
    hashed_password = 'abactor abattoir abashedly abaca'

class SkeinYAMLTestCase(SkeinTestCaseMixin, unittest.TestCase):
    config_dir = 'skein-yaml'

class SkeinSqliteTestCase(SkeinTestCaseMixin, SqliteTestCaseMixin, unittest.TestCase):
    config_dir = 'skein-sqlite'


@pytest.fixture
def app():
    app = application.Passacre()
    app.load_config(datadir.join('keccak.sqlite').open('rb'))
    return app

@pytest.fixture
def mutable_app(app, tmpdir):
    datadir.join('keccak.sqlite').copy(tmpdir)
    db_copy = tmpdir.join('keccak.sqlite')
    app._db = sqlite3.connect(db_copy.strpath)
    app.load_config(db_copy.open('rb'))
    app.prompt_password = lambda confirm: 'passacre'
    return app

def test_init(app, tmpdir):
    dbpath = tmpdir.join('test.db').strpath
    app.main(['init', dbpath])
    db = sqlite3.connect(dbpath)
    curs = db.cursor()

    curs.execute('SELECT * FROM config_values')
    assert curs.fetchall() == []

    curs.execute('SELECT schema_id, name, value FROM schemata')
    (schema_id, name, value), = curs
    assert (name, value) == ('32-printable', '[[32, "printable"]]')

    curs.execute('SELECT site_name, schema_id FROM sites')
    assert curs.fetchall() == [('default', schema_id)]

def test_site_yaml(app, capsys):
    app.load_config(datadir.join('keccak.yaml').open('rb'))
    app.main(['site'])
    out, err = capsys.readouterr()
    assert not err
    assert out == """gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4
becu.org
default
example.com
fhcrc.org
fidelity.com
further.example.com
schwab.com
still.further.example.com
"""

def test_site_sqlite(app, capsys):
    app.main(['site'])
    out, err = capsys.readouterr()
    assert not err
    assert out == """gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4: schema_7
becu.org: schema_3
default: schema_5
example.com: schema_0
fhcrc.org: schema_5
fidelity.com: schema_6
further.example.com: schema_2
schwab.com: schema_1
still.further.example.com: schema_4
"""

    app.main(['site', '--by-schema'])
    out, err = capsys.readouterr()
    assert not err
    assert out == """schema_0: example.com
schema_1: schwab.com
schema_2: further.example.com
schema_3: becu.org
schema_4: still.further.example.com
schema_5: default, fhcrc.org
schema_6: fidelity.com
schema_7: gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4
"""

def get_site_schema(curs, site):
    curs.execute(
        'SELECT value FROM sites JOIN schemata USING (schema_id) WHERE site_name = ?',
        (site,))
    return curs.fetchall()

def test_site_add(mutable_app):
    app = mutable_app
    curs = app._db.cursor()

    app.main(['site', 'add', 'example.org', 'schema_0'])
    assert get_site_schema(curs, 'example.org') == [('[[" ", 4, "word"]]',)]

    app.main(['site', '-a', 'add', 'hashed.example.org', 'schema_0'])
    assert get_site_schema(
        curs, 'ovzItJro7gu7DYNiwa5ve23okNCe-yWv9v1a0PNiBKIbHKBp') == [('[[" ", 4, "word"]]',)]

def test_site_set_schema(mutable_app):
    app = mutable_app
    curs = app._db.cursor()

    app.main(['site', 'set-schema', 'example.com', 'schema_7'])
    assert get_site_schema(curs, 'example.com') == [('[[" ", 2, "word"]]',)]

    app.main(['site', '-a', 'set-schema', 'hashed.example.com', 'schema_7'])
    assert get_site_schema(
        curs, 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4') == [('[[" ", 2, "word"]]',)]

def test_site_remove(mutable_app):
    app = mutable_app
    curs = app._db.cursor()

    app.main(['site', 'remove', 'example.com'])
    curs.execute('SELECT * FROM sites WHERE site_name = "example.com"')
    assert curs.fetchall() == []

    app.main(['site', '-a', 'remove', 'hashed.example.com'])
    curs.execute('SELECT * FROM sites WHERE site_name = "hashed.example.com"')
    assert curs.fetchall() == []

def test_site_remove_default_fails(app):
    with pytest.raises(SystemExit) as excinfo:
        app.main(['site', 'remove', 'default'])
    assert excinfo_arg_0(excinfo)

def test_config(app, capsys):
    app.main(['config'])
    out, err = capsys.readouterr()
    assert not err
    assert out == """site-hashing.enabled: true
site-hashing.iterations: 10
words-file: "words"
"""

    app.main(['config', 'site-hashing.enabled'])
    out, err = capsys.readouterr()
    assert not err
    assert out == 'true\n'

    app.main(['config', 'site-hashing'])
    out, err = capsys.readouterr()
    assert not err
    assert out == '{"enabled": true, "iterations": 10}\n'

    app.main(['config', '-s', 'fhcrc.org'])
    out, err = capsys.readouterr()
    assert not err
    assert out == 'increment: 5\n'

    app.main(['config', '-s', 'fhcrc.org', 'increment'])
    out, err = capsys.readouterr()
    assert not err
    assert out == '5\n'

def get_config_name(curs, site, name):
    curs.execute(
        'SELECT value FROM config_values WHERE site_name IS ? AND name = ?',
        (site, name))
    return curs.fetchall()

def test_config_set(mutable_app):
    app = mutable_app
    curs = app._db.cursor()

    app.main(['config', 'words-file', 'foo'])
    assert get_config_name(curs, None, 'words-file') == [('"foo"',)]

    app.main(['config', 'words-file', 'null'])
    assert get_config_name(curs, None, 'words-file') == []

    app.main(['config', 'spam.spam.spam.eggs', 'spam'])
    assert get_config_name(curs, None, 'spam') == [('{"spam": {"spam": {"eggs": "spam"}}}',)]

    app.main(['config', 'spam.spam.spam.spam', 'spam'])
    assert get_config_name(curs, None, 'spam') == [
        ('{"spam": {"spam": {"eggs": "spam", "spam": "spam"}}}',)]

    app.main(['config', '-s', 'fhcrc.org', 'increment', '6'])
    assert get_config_name(curs, 'fhcrc.org', 'increment') == [('6',)]

    app.main(['config', '-s', 'example.com', 'increment', '7'])
    assert get_config_name(curs, 'example.com', 'increment') == [('7',)]

    app.main(['config', '-as', 'hashed.example.com', 'increment', '8'])
    assert get_config_name(
        curs, 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4', 'increment') == [('8',)]

    app.main(['config', '-cas', 'hashed.example.com', 'increment', '9'])
    assert get_config_name(
        curs, 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4', 'increment') == [('9',)]

def test_schema(app, capsys):
    app.main(['schema'])
    out, err = capsys.readouterr()
    assert not err
    assert out == r"""schema_0: [[" ", 4, "word"]]
schema_1: [[8, "alphanumeric"]]
schema_2: [[", ", 4, "word"]]
schema_3: [[32, "alphanumeric"]]
schema_4: ["printable", [", ", 4, "word"], "printable"]
schema_5: [[32, "printable"]]
schema_6: [[16, ["alphanumeric", "\"%'()+,-/:;<=>?\\ ^_|"]]]
schema_7: [[" ", 2, "word"]]
"""

def get_schema_value(curs, name):
    curs.execute('SELECT value FROM schemata WHERE name = ?', (name,))
    return curs.fetchall()

def test_schema_add(mutable_app):
    app = mutable_app
    curs = app._db.cursor()

    app.main(['schema', 'add', 'schema_10', '["alphanumeric", [10, "digit"]]'])
    assert get_schema_value(curs, 'schema_10') == [('["alphanumeric", [10, "digit"]]',)]

def test_schema_set_value(mutable_app):
    app = mutable_app
    curs = app._db.cursor()

    app.main(['schema', 'set-value', 'schema_0', '[[10, "digit"]]'])
    assert get_schema_value(curs, 'schema_0') == [('[[10, "digit"]]',)]
    assert get_site_schema(curs, 'example.com') == [('[[10, "digit"]]',)]

def test_schema_set_name(mutable_app):
    app = mutable_app
    curs = app._db.cursor()

    app.main(['schema', 'set-name', 'schema_0', 'schema_10'])
    assert get_schema_value(curs, 'schema_10') == [('[[" ", 4, "word"]]',)]
    curs.execute(
        'SELECT name FROM schemata JOIN sites USING (schema_id) WHERE site_name = "example.com"')
    assert curs.fetchall() == [('schema_10',)]

def test_schema_remove(mutable_app):
    app = mutable_app
    curs = app._db.cursor()
    curs.execute('INSERT INTO schemata (name, value) VALUES ("schema_10", "[""digit""]")')
    app._db.commit()

    assert get_schema_value(curs, 'schema_10') != []
    app.main(['schema', 'remove', 'schema_10'])
    assert get_schema_value(curs, 'schema_10') == []
