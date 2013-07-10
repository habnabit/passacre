from __future__ import unicode_literals

import os
import pytest

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
