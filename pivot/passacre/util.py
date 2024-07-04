# Parts of this file (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import json

from passacre.compat import crochet_setup, wait_for_reactor
from passacre import jsonmini


class reify(object):
    """ Use as a class method decorator.  It operates almost exactly like the
    Python ``@property`` decorator, but it puts the result of the method it
    decorates into the instance dict after the first call, effectively
    replacing the function it decorates with an instance variable.  It is, in
    Python parlance, a non-data descriptor.  An example:

    .. code-block:: python

       class Foo(object):
           @reify
           def jammy(self):
               print 'jammy called'
               return 1

    And usage of Foo:

    >>> f = Foo()
    >>> v = f.jammy
    'jammy called'
    >>> print v
    1
    >>> f.jammy
    1
    >>> # jammy func not called the second time; it replaced itself with 1
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except: # pragma: no cover
            pass

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


def errormark(description, exitcode=3):
    def deco(f):
        def wrap(*a, **kw):
            try:
                return f(*a, **kw)
            except Exception as e:
                e._errormark = description, exitcode, a, kw
                raise
        return wrap
    return deco


def dotify(d, prefix=''):
    ret = []
    for k, v in d.items():
        if isinstance(v, dict):
            ret.extend(dotify(v, prefix=prefix + k + '.'))
        else:
            ret.append((prefix + k, v))
    return ret

def nested_get(d, keys, default_fac=lambda: None):
    intermediate = d
    for key in keys:
        if intermediate is None:
            intermediate = {}
        intermediate = intermediate.setdefault(key, default_fac())
    return intermediate

def nested_set(d, keys, value):
    intermediate = nested_get(d, keys[:-1], dict)
    intermediate[keys[-1]] = value

@errormark('loading the json-mini value: {0!r}')
def jloads(s):
    return jsonmini.parse(s)

def jdumps(val):
    return json.dumps(val, sort_keys=True)


def lazily_wait_for_reactor(f):
    f = wait_for_reactor(f)
    def wrap(*a, **kw):
        crochet_setup()
        return f(*a, **kw)
    return wrap
