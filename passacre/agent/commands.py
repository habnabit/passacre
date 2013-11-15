from twisted.protocols import amp


class AgentLocked(Exception):
    pass


class AgentUnlocked(Exception):
    pass


class SiteListUnavailable(Exception):
    pass


class Unlock(amp.Command):
    arguments = [
        ('password', amp.Unicode()),
    ]
    response = []
    errors = {AgentUnlocked: 'AGENT_UNLOCKED'}


class Lock(amp.Command):
    arguments = []
    response = []
    errors = {AgentLocked: 'AGENT_LOCKED'}


class Generate(amp.Command):
    arguments = [
        ('site', amp.Unicode()),
        ('username', amp.Unicode(optional=True)),
        ('password', amp.Unicode(optional=True)),
    ]
    response = [
        ('password', amp.Unicode()),
    ]
    errors = {AgentLocked: 'AGENT_LOCKED'}


class FetchSiteList(amp.Command):
    arguments = [
        ('force_disk_load', amp.Boolean(optional=True)),
    ]
    response = [
        ('sites', amp.ListOf(amp.Unicode())),
    ]
    errors = {
        AgentLocked: 'AGENT_LOCKED',
        SiteListUnavailable: 'SITE_LIST_UNAVAILABLE',
    }


class WriteSiteList(amp.Command):
    arguments = [
        ('sites', amp.ListOf(amp.Unicode())),
    ]
    response = []
    errors = {
        AgentLocked: 'AGENT_LOCKED',
        SiteListUnavailable: 'SITE_LIST_UNAVAILABLE',
    }
