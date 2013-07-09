import os
import pytest
import unittest

from passacre import config


datadir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

class ConfigTestCaseMixin(object):
    password = 'passacre'
    config_file = None
    expected_passwords = {}
    expected_username_passwords = {}

    def setUp(self):
        os.chdir(datadir)
        self.config = config.load(open(self.config_file, 'rb'))

    def test_expected_passwords(self):
        for site, expected in self.expected_passwords.items():
            self.assertEqual(
                expected, self.config.generate_for_site(None, self.password, site))

    def test_expected_username_passwords(self):
        for (username, site), expected in self.expected_username_passwords.items():
            self.assertEqual(
                expected, self.config.generate_for_site(username, self.password, site))


class KeccakTestCaseMixin(ConfigTestCaseMixin):
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


class KeccakYAMLTestCase(KeccakTestCaseMixin, unittest.TestCase):
    config_file = 'keccak.yaml'

class KeccakSqliteTestCase(KeccakTestCaseMixin, unittest.TestCase):
    config_file = 'keccak.sqlite'


@pytest.mark.skipif("sys.version_info < (3,)")
class SkeinTestCaseMixin(ConfigTestCaseMixin):
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


class SkeinYAMLTestCase(SkeinTestCaseMixin, unittest.TestCase):
    config_file = 'skein.yaml'

class SkeinSqliteTestCase(SkeinTestCaseMixin, unittest.TestCase):
    config_file = 'skein.sqlite'
