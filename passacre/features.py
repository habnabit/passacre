class FeatureUnusable(Exception):
    def __init__(self, feature):
        self.feature = feature

    def __str__(self):
        message = ['the "%s" feature requires the following:' % (self.feature.name,)]
        message.extend(self.feature.usability_strings())
        return '\n'.join(message)


class Feature(object):
    features = []
    _import = staticmethod(__import__)

    def __init__(self, name, *module_packages):
        self.name = name
        self.module_packages = dict(module_packages)
        self.usable = True
        self.module_usable = {}
        for module in self.module_packages:
            try:
                self._import(module, fromlist=[module])
            except ImportError:
                self.usable = False
                self.module_usable[module] = False
            else:
                self.module_usable[module] = True
        self.features.append(self)

    def check(self, func):
        def wrap(*a, **kw):
            if not self.usable:
                raise FeatureUnusable(self)
            return func(*a, **kw)
        return wrap

    def usability_strings(self):
        for module, package in self.module_packages.items():
            usable = 'usable' if self.module_usable[module] else 'NOT USABLE'
            yield '"%s" module (%s on pypi): %s' % (module, package, usable)


yaml_config = Feature('YAML configuration', ('yaml', 'pyyaml'))
keccak_generation = Feature('keccak password generation', ('keccak', 'cykeccak'))
skein_generation = Feature('skein password generation', ('skein', 'pyskein'))
copying = Feature('password copying', ('xerox', 'xerox'))
yubikey = Feature('yubikey support', ('ykpers', 'ykpers-cffi'))
agent = Feature(
    'passacre agent support',
    ('twisted.protocols.amp', 'Twisted'),
    ('crochet', 'crochet'))

features = Feature.features
