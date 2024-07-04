# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

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

    def _check(self):
        if not self.usable:
            raise FeatureUnusable(self)

    def check(self, func=None):
        if func is None:
            return self._check()
        def wrap(*a, **kw):
            self._check()
            return func(*a, **kw)
        return wrap

    def usability_strings(self):
        for module, package in self.module_packages.items():
            usable = 'usable' if self.module_usable[module] else 'NOT USABLE'
            yield '"%s" module (%s on pypi): %s' % (module, package, usable)


yaml = Feature('YAML configuration', ('yaml', 'pyyaml'))
copying = Feature('password copying', ('xerox', 'xerox'))
yubikey = Feature('yubikey support', ('ykpers', 'ykpers-cffi'))

features = Feature.features
