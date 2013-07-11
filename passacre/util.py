# Parts of this file (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import json


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


def dotify(d, prefix=''):
    ret = []
    for k, v in d.items():
        if isinstance(v, dict):
            ret.extend(dotify(v, prefix=prefix + k + '.'))
        else:
            ret.append((prefix + k, v))
    return ret

def nested_get(d, keys):
    intermediate = d
    for key in keys:
        intermediate = intermediate.setdefault(key, {})
    return intermediate

def nested_set(d, keys, value):
    intermediate = nested_get(d, keys[:-1])
    intermediate[keys[-1]] = value

def jdumps(val):
    return json.dumps(val, sort_keys=True)
