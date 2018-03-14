import numpy as np
from scipy.stats import randint


class Domain(object):
    """Base class for defining search domains.

    Parameters
    ----------
    domain
        The set or range of values to search.
    path : str
        Path to this domain in the search hierarchy.

    Notes
    -----
    ``path`` is automatically computed when models are created during the
    splitting process.
    """
    def __init__(self, domain, path=None):
        self.domain = domain
        self.path = path
        self.__complexity = None

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __iter__(self):
        return self

    def __next__(self):
        return self.generate()

    def next(self):
        return self.__next__()

    def generate(self, index=False):
        raise NotImplementedError

    def complexity(self):
        raise NotImplementedError

    def map_to_domain(self, value):
        return value

    def to_json(self):
        raise NotImplementedError


class ContinuousDomain(Domain):
    def __init__(self, domain, path=None, *args, **kws):
        super(ContinuousDomain, self).__init__(domain(*args, **kws), path=path)

    @property
    def complexity(self):
        if self.__complexity is None:
            a, b = self.domain.interval(.99)
            self.__complexity = 2.0 + np.linalg.norm(b - a)
        return self.__complexity

    def generate(self, index=False):
        return self.domain.rvs()

    def to_json(self):
        return {
            'path': self.path,
            'distribution': self.domain.dist.name,
            'args': self.domain.args,
            'kws': self.domain.kwds
        }


class DiscreteDomain(Domain):
    def __init__(self, domain, path=None):
        try:
            self.rng = randint(0, len(domain))
        except AttributeError:
            domain = [domain]
            self.rng = randint(0, len(domain))
        super(DiscreteDomain, self).__init__(domain, path=path)

    @property
    def complexity(self):
        if self.__complexity is None:
            self.__complexity = 2.0 - (1.0 / len(self.domain))
        return self.__complexity

    def generate(self, index=False):
        idx = self.rng.rvs()
        return self.domain[idx] if not index else idx

    def map_to_domain(self, val):
        try:
            idx = self.domain.index(val)
        except ValueError:
            idx = None
        return idx

    def to_json(self):
        return {
            'path': self.path,
            'domain': self.domain
        }


class ExhaustiveDomain(Domain):
    def __init__(self, domain, path=None):
        self.idx = 0
        if not isinstance(domain, list):
            domain = [domain]
        super(ExhaustiveDomain, self).__init__(domain, path=path)

    @property
    def complexity(self):
        if self.__complexity is None:
            self.__complexity = 2.0 - (1.0 / len(self.domain))
        return self.__complexity

    def generate(self, index=False):
        val = self.domain[self.idx]
        self.idx = (self.idx + 1) % len(self.domain)
        return val if not index else self.idx

    def map_to_domain(self, val):
        try:
            idx = self.domain.index(val)
        except ValueError:
            idx = None
        return idx

    def to_json(self):
        return {
            'path': self.path,
            'domain': self.domain,
            'idx': self.idx
        }
