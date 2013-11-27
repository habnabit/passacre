# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from twisted.protocols import amp


class AgentLocked(Exception):
    errorCode = 'AGENT_LOCKED'


class AgentUnlocked(Exception):
    errorCode = 'AGENT_UNLOCKED'


class AgentUnauthorized(Exception):
    errorCode = 'AGENT_UNAUTHORIZED'


class SiteListFailedDecryption(Exception):
    errorCode = 'SITE_LIST_FAILED_DECRYPTION'


class Unlock(amp.Command):
    arguments = [
        ('password', amp.Unicode()),
    ]
    response = []
    errors = {
        AgentUnlocked: 'AGENT_UNLOCKED',
        AgentUnauthorized: 'AGENT_UNAUTHORIZED',
    }


class Lock(amp.Command):
    arguments = []
    response = []
    errors = {
        AgentLocked: 'AGENT_LOCKED',
    }


class Generate(amp.Command):
    arguments = [
        ('site', amp.Unicode()),
        ('username', amp.Unicode(optional=True)),
        ('password', amp.Unicode(optional=True)),
        ('save_site', amp.Boolean(optional=True)),
    ]
    response = [
        ('password', amp.Unicode()),
    ]
    errors = {
        AgentLocked: 'AGENT_LOCKED',
        SiteListFailedDecryption: 'SITE_LIST_FAILED_DECRYPTION',
    }


class FetchSiteList(amp.Command):
    arguments = []
    response = [
        ('sites', amp.ListOf(amp.Unicode())),
    ]
    errors = {
        AgentLocked: 'AGENT_LOCKED',
    }


class Version(amp.Command):
    arguments = []
    response = [
        ('version', amp.Unicode()),
        ('sha', amp.Unicode()),
    ]


class Initialize(amp.Command):
    arguments = [
        ('password', amp.Unicode()),
    ]
    response = []
    errors = {
        AgentUnauthorized: 'AGENT_UNAUTHORIZED',
        SiteListFailedDecryption: 'SITE_LIST_FAILED_DECRYPTION',
    }
