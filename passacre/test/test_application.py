from __future__ import unicode_literals

import os
import pytest
import unittest

from passacre import application


datadir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


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
        os.chdir(os.path.join(datadir, self.config_dir))
        self.app = application.Passacre()
        _load_config = self.app.load_config
        self.app.load_config = lambda: _load_config(expanduser=fake_expanduser)
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
        assert excinfo.value.args[0] == 2


class KeccakTestCaseMixin(ApplicationTestCaseMixin):
    hashed_site = 'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4'
    hashed_password = 'Abaris abaisance abashedness abarticulation'

class KeccakYAMLTestCase(KeccakTestCaseMixin, unittest.TestCase):
    config_dir = 'keccak-yaml'

class KeccakSqliteTestCase(KeccakTestCaseMixin, unittest.TestCase):
    config_dir = 'keccak-sqlite'


@pytest.mark.skipif("sys.version_info < (3,)")
class SkeinTestCaseMixin(ApplicationTestCaseMixin):
    hashed_site = 'UYfDoAN9nYMdxCYtgKenzjhbc9eonu3w92ec3SAA5UbT1J3L'
    hashed_password = 'abactor abattoir abashedly abaca'

class SkeinYAMLTestCase(SkeinTestCaseMixin, unittest.TestCase):
    config_dir = 'skein-yaml'

class SkeinSqliteTestCase(SkeinTestCaseMixin, unittest.TestCase):
    config_dir = 'skein-sqlite'
