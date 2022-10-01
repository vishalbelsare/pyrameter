"""Representation of a hyperparameter domain.

Classes
-------
Domain
    Base class for hyperparameter domains.
"""

import importlib
import inspect
import itertools
import os
import re

from pyrameter.reproducibility import RNG


class MetaDomain(type):
    """Metaclass for behind the scenes processes for domains."""

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        x._counter = itertools.count(0)
        return x


class Domain(object, metaclass=MetaDomain):
    """Base class for hyperparameter domains.

    Parameters
    ----------
    name : str
        The name of this hyperparameter domain.

    """

    def __init__(self, name=None):
        self.id = next(self.__class__._counter)
        self.name = name
        self.current = None
        self._complexity = None
        self._rng = None

    def __call__(self, *args, **kwargs):
        margs, mvargs, mkwargs, _ = inspect.getargspec(self.generate)
        if len(margs) > 1 or mvargs is not None or mkwargs is not None:
            self.current = self.generate(*args, **kwargs)
        else:
            self.current = self.generate()
        return self.current

    def __eq__(self, other):
        return self.name == other.name

    def __ge__(self, other):
        return self.name >= other.name

    def __gt__(self, other):
        return self.name > other.name

    def __hash__(self):
        return hash(self.name)

    def __le__(self, other):
        return self.name <= other.name

    def __lt__(self, other):
        return self.name < other.name

    def __ne__(self, other):
        return self.name != other.name

    def bound_index(self, idx):
        """Clamp an index into the domain to its viable values.

        Parameters
        ----------
        idx
            The index to clamp.

        Returns
        -------
        idx
            Returns the input unaltered.

        Notes
        -----
        This is in place for consistency across domain subclasses. Override
        to clamp in special cases, like DiscreteDomain, where it does not make
        sense to go out of bounds.
        """
        return idx

    @property
    def complexity(self):
        """Compute the search complexity (size) of this domain.

        Complexity is computed as defined by Kinnison *et al.*
        """
        if self._complexity is None:
            self._complexity = 1
        return self._complexity

    @staticmethod
    def from_json(obj):
        """Convert a JSON object to an instance of the serialized domain.

        Parameters
        ----------
        obj : dict
            A dictionary generated by the ``to_json`` method of any ``Domain``
            subclass.
        
        Returns
        -------
        domain : subclass of Domain
            A ``Domain`` subclass of type ``obj['type']`` instantiated with
            the values in ``obj``.
        
        See Also
        --------
        `pyrameter.domains.base.Domain.to_json`
            Convert the domain to a JSON-compatible format.
        """
        # Get the module containing the serialized domain's class and the
        # class name.
        mod, cls = os.path.splitext(obj['type'])

        # Import the module dynamically.
        mod = importlib.import_module(mod)

        # Get the class object from the module.
        cls = getattr(mod, cls.strip('.'))

        # Instantiate the domain with its own ``from_json`` method.
        return cls.from_json(obj)

    def generate(self):
        """Generate a hyperparameter value from this domain.
        
        This method must be implemented in a subclass of ``Domain`` to
        define the behavior for drawing hyperparameter values.
        """
        raise NotImplementedError

    def map_to_domain(self, index, bound=True):
        """Convert an index to its value within the domain.

        Discrete/categorical domains must be mapped to a numeric value for
        use with guided hyperparameter search methods. This method takes an
        index and returns the corresponding value in the domain. Must be
        overridden by any subclass of Domain.

        Parameters
        ----------
        index : int
            Index into a discrete/categorical domain (e.g., a list).
        bound : bool, optional
            If True and ``index`` is out of bounds, return the first or last
            entry in the domain (whichever is closer). Otherwise, raises an
            IndexError if ``index`` is out of bounds.

        Returns
        -------
        value
            The value at ``index`` in the domain.

        Raises
        ------
        IndexError
            Raised when ``index`` is out of bounds and ``bound`` is ``False``.
        """
        raise NotImplementedError
        
    def set_rng(self, rng):
        self._rng = rng

    def to_index(self, value):
        """Convert a value to its index in the domain."""
        return value

    def to_json(self):
        """Convert the domain to a JSON-compatible format.
        
        Returns
        -------
        obj : dict
            Dictionary containing the class name/module path of this domain
            and the user-provided name of the domain.

        See Also
        --------
        `pyrameter.domains.base.Domain.from_json`
            Convert a JSON object to an instance of the serialized domain.
        """
        # To reconstruct this domain later, record the full module path
        # and class name for dynamic imports.
        classname = re.match(r"^<class '(.+)'>$",
                             str(self.__class__)).groups()[0]
        return {
            'id': self.id,
            'name': self.name,
            'current': self.current,
            'type': classname
        }
