# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import itertools
import os

import pytest

from passacre import config


datadir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def pytest_generate_tests(metafunc):
    if metafunc.cls is None:
        return
    uses = getattr(metafunc.function, '_uses', None)
    if uses is None:
        return
    attrname, key, value = uses
    attr = getattr(metafunc.cls, attrname)
    metafunc.parametrize((key, value), attr.items())


def uses(attrname, key, value):
    def deco(func):
        func._uses = attrname, key, value
        return func
    return deco


class ConfigTestCaseMixin(object):
    password = 'passacre'
    config_file = None
    method = None

    expected_passwords = {}
    expected_username_passwords = {}

    expected_sites = {
        'default': {
            'iterations': 10, 'schema': [[32, 'printable']],
        },
        'becu.org': {
            'iterations': 10, 'schema': [[32, 'alphanumeric']],
        },
        'example.com': {
            'iterations': 10, 'schema': [[' ', 4, 'word']],
        },
        'fhcrc.org': {
            'increment': 5, 'iterations': 15, 'schema': [[32, 'printable']],
        },
        'fidelity.com': {
            'iterations': 10,
            'schema': [[16, ['alphanumeric', '"%\'()+,-/:;<=>?\\ ^_|']]],
        },
        'further.example.com': {
            'iterations': 10, 'schema': [[', ', 4, 'word']],
        },
        'schwab.com': {
            'iterations': 10, 'schema': [[8, 'alphanumeric']],
        },
        'still.further.example.com': {
            'iterations': 10,
            'schema': ['printable', [', ', 4, 'word'], 'printable'],
        },
        'scrypt.example.com': {
            'iterations': 10, 'schema': [[32, 'printable']],
            'scrypt': {'n': 16, 'r': 1, 'p': 1},
        },
        'scrypt2.example.com': {
            'iterations': 10, 'schema': [[32, 'printable']],
            'scrypt': {'n': 1024, 'r': 8, 'p': 16},
        },
    }
    extra_expected_sites = {}

    @pytest.fixture
    def config_obj(self):
        os.chdir(datadir)
        return config.load(open(self.config_file, 'rb'))

    @uses('expected_passwords', 'site', 'expected')
    def test_expected_passwords(self, config_obj, site, expected):
        assert expected == config_obj.generate_for_site(
            None, self.password, site)

    @uses('expected_username_passwords', 'username_site', 'expected')
    def test_expected_username_passwords(self, config_obj, username_site, expected):
        username, site = username_site
        assert expected == config_obj.generate_for_site(
            username, self.password, site)

    def test_get_all_sites(self, config_obj):
        sites = config_obj.get_all_sites()
        for site_config in sites.values():
            site_config.pop('multibase', None)
            site_config.pop('schema-name', None)
        expected = {}
        all_expected = itertools.chain(
            self.expected_sites.items(), self.extra_expected_sites.items())
        for site, site_config in all_expected:
            site_config = site_config.copy()
            site_config['method'] = self.method
            expected[site] = site_config
        assert expected == sites


class KeccakTestCaseMixin(ConfigTestCaseMixin):
    method = 'keccak'
    expected_passwords = {
        'becu.org': 'qRnda94q1srpHWCjaQUTDobnxIgJkKlO',
        'fhcrc.org': 's"E;JE*?&md?19{2}<4Q.Rf):X?BUe^0',
        'schwab.com': 'jRWs2Wzl',
        'fidelity.com': 'B2M4=KQ2yzYLacW1',
        'example.com': 'Abaris abaisance abashedness abarticulation',
        'further.example.com': 'a, abaton, abatement, abask',
        'still.further.example.com': ')abased, abaculus, Abaris, abature=',
        'hashed.example.com': 'Abasgi abatement',
        'default.example.com': '-1`mCLq}HF?t#unm>dJC8k)FkLO-jcy8',
    }
    expected_username_passwords = {
        ('passacre', 'schwab.com'): 'JkbefmM3',
        ('passacre', 'fhcrc.org'): 'r(O.vF`Avz44Z;$ZvQ..4LqN/CEz/*#?',
        ('passacre', 'hashed.example.com'): 'Aaronic Abassin',
        ('passacre', 'default.example.com'): '''RN*6~h'Jc-A"Ro-OefetOVes~tR<~=[K''',
    }
    extra_expected_sites = {
        'gN7y2jQ72IbdvQZxrZLNmC4hrlDmB-KZnGJiGpoB4VEcOCn4': {
            'iterations': 10, 'schema': [[' ', 2, 'word']]
        },
    }


class TestKeccakYAML(KeccakTestCaseMixin):
    config_file = 'keccak.yaml'


class TestKeccakSqlite(KeccakTestCaseMixin):
    config_file = 'keccak.sqlite'


class SkeinTestCaseMixin(ConfigTestCaseMixin):
    method = 'skein'
    expected_passwords = {
        'becu.org': 'GEifpmhAzCtbTHBdj40B215CTXZATzzy',
        'fhcrc.org': 'C^#l04.LnhZ-m4}]6&RPMWYS#oW2_E)U',
        'schwab.com': '2CFNqPya',
        'fidelity.com': '9DT"bYHp4Gch\\"jL',
        'example.com': 'abactor abattoir abashedly abaca',
        'further.example.com': 'abandonable, aal, abalienate, abampere',
        'still.further.example.com': ';abate, abaciscus, abandonable, abalonea',
        'hashed.example.com': 'aardvark Abadite',
        'default.example.com': '~N8q0u$fYwnpD{VITu^F*,-NO1~PV>m&',
    }
    expected_username_passwords = {
        ('passacre', 'schwab.com'): 'sKvqo9Y0',
        ('not-passacre', 'schwab.com'): 'JlOdJ7KC',
        ('passacre', 'fhcrc.org'): '''~,HDW+W9@hg{'pU*P"qpckS8]gmaEe)D''',
        ('passacre', 'hashed.example.com'): 'abastardize abacist',
        ('passacre', 'default.example.com'): 'GEvloj!NLoJTP;$ymbp0lz<P#`3[/#4>',
    }
    extra_expected_sites = {
        'UYfDoAN9nYMdxCYtgKenzjhbc9eonu3w92ec3SAA5UbT1J3L': {
            'iterations': 10, 'schema': [[' ', 2, 'word']]
        },
    }


class TestSkeinYAML(SkeinTestCaseMixin):
    config_file = 'skein.yaml'


class TestSkeinSqlite(SkeinTestCaseMixin):
    config_file = 'skein.sqlite'


def test_no_words_file():
    # using sqlite for lazy-loading of site data, otherwise the `load` call
    # will fail too.
    c = config.load(open(os.path.join(datadir, 'no-words.sqlite'), 'rb'))
    assert c.word_list_path is None
    with pytest.raises(Exception):
        c.generate_for_site(None, 'passacre', 'example.com')
