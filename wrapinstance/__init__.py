"""Wrap Instance."""

__author__ = """Maxim Zaslavsky"""
__email__ = "maxim@maximz.com"
__version__ = "0.0.1"

# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())

class ClassInstanceWrapper:
    """
    Allows wrapping any class instance. This is like casting an instance of a base class to a derived class.
    The provided class instance will be set as self._inner but its attributes will be exposed directly.
    Any additional methods will override what's available from the original class instance.

    Based on https://stackoverflow.com/a/1383646/130164
    See also https://stackoverflow.com/a/1445289/130164 for potential alternatives.

    Usage example:
        class BaseClass:
            pass
        class DerivedClass(ClassInstanceWrapper):
            def __init__(self, inner, ...):
                # sets self._inner
                super().__init__(inner)
                ...
        obj = BaseClass()
        wrapped_obj = DerivedClass(obj)

    Limitations (see tests for examples):
    - Logic defined in the base class can't access the derived class's overloaded methods
    - Modifying attributes on the wrapped instance detaches those instance attributes, rather than modifying the inner instance
    - Modifying attributes on the base inner instance will be passed through unless those attributes have already been detached as above.
    """

    # Set _inner None here to prevent infinite recursion in this scenario:
    # A child class attempts to access a self.something that doesn't exist (triggering __getattr__),
    # but before calling super().__init__(), i.e. before _inner is set to something.
    # In this situation, when __getattr__ runs getattr(self._inner), this will trigger __getattr__ again  since _inner doesn't exist at all yet.
    # In other words, without setting _inner to be None originally, _inner won't exist at all, so getattr will just call itself.
    # See test_wrong_usage_does_not_cause_infinite_recursion()
    _inner = None

    def __init__(self, inner):
        # Set inner
        self._inner = inner
        # TODO: should we dynamically register as a subclass of inner's class?
        # See https://stackoverflow.com/questions/9269902/is-there-a-way-to-create-subclasses-on-the-fly
        # And https://stackoverflow.com/questions/56658569/how-to-create-a-python-class-that-is-a-subclass-of-another-class-but-fails-issu
        # For now we will fail isinstance checks for parent class.

    def __getattr__(self, attr):
        # Pass unknown attribute accesses through to inner.
        # See https://python-reference.readthedocs.io/en/latest/docs/dunderattr/getattr.html
        return getattr(self._inner, attr)

    # Override getstate and setstate because of our override of getattr
    # Otherwise we will fail to pickle these classes with this error on loading: "RecursionError: maximum recursion depth exceeded while calling a Python object"
    # See https://stackoverflow.com/a/50888571/130164 and https://stackoverflow.com/a/50888532/130164
    # We have a test for this now.

    # The stack trace with this error will look like:
    # File "site-packages/joblib/numpy_pickle.py", line 585, in load
    #     obj = _unpickle(fobj, filename, mmap_mode)
    # File "site-packages/joblib/numpy_pickle.py", line 504, in _unpickle
    #     obj = unpickler.load()
    # File "pickle.py", line 1088, in load
    #     dispatch[key[0]](self)
    # File "site-packages/joblib/numpy_pickle.py", line 329, in load_build
    #     Unpickler.load_build(self)
    # File "pickle.py", line 1550, in load_build
    #     setstate = getattr(inst, "__setstate__", None)
    # File "class_instance_wrapper.py", line 33, in __getattr__
    #     return getattr(self._inner, attr)
    # File "class_instance_wrapper.py", line 33, in __getattr__
    #     return getattr(self._inner, attr)
    # File "class_instance_wrapper.py", line 33, in __getattr__
    #     return getattr(self._inner, attr)
    # [Previous line repeated 1471 more times]
    # RecursionError: maximum recursion depth exceeded while calling a Python object

    def __getstate__(self):
        return vars(self)

    def __setstate__(self, state):
        vars(self).update(state)

    def __repr__(self):
        return f"{self.__class__.__name__}: {repr(self._inner)}"

    def _repr_mimebundle_(self, **kwargs):
        """Configure how Jupyter displays an object's repr."""
        return {"text/plain": repr(self), "text/html": f"<pre>{repr(self)}</pre>"}

    # TODO: make ClassInstanceWrapper subscriptable:
    # forward __getitem__() to parent if it exists
    # test case is sklearn Pipeline [:-1]
