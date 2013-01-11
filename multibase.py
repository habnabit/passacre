class MultiBase(object):
    def __init__(self, bases):
        self.bases = bases

    def encode(self, n):
        ret = []
        for base in reversed(self.bases):
            n, d = divmod(n, len(base))
            ret.append(base[d])
        ret.reverse()
        return ''.join(ret), n

    def decode(self, x):
        if len(x) != len(self.bases):
            raise ValueError(
                "the length of %r (%d) doesn't match the number of bases (%d)" % (
                    x, len(x), len(self.bases)))
        ret = 0
        for base, d in zip(self.bases, x):
            ret = (ret * len(base)) + base.index(d)
        return ret

    @property
    def max_encodable_value(self):
        ret = 1
        for base in self.bases:
            ret *= len(base)
        return ret - 1
