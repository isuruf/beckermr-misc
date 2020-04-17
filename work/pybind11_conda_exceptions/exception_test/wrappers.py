

import warnings
import builtins

from . import exceptions

__all__ = [
    "register",
    "ExceptionMeta",
    "LSSTException", "CustomError",
    "translate"
]

registry = {}


def register(cls):
    """A Python decorator that adds a Python exception wrapper to the
    registry that maps C++ Exceptions to their Python wrapper classes.
    """
    registry[cls.WrappedClass] = cls
    return cls


class ExceptionMeta(type):
    """A metaclass for custom exception wrappers, which adds lookup of class attributes
    by delegating to the Swig-generated wrapper.
    """

    def __getattr__(cls, name):
        return getattr(cls.WrappedClass, name)


@register
class LSSTException(builtins.Exception, metaclass=ExceptionMeta):
    """The base class for Python-wrapped LSST C++ exceptions.
    """

    # wrappers.py is an implementation detail, not a public namespace,
    # so we pretend this is defined
    # in the package for pretty-printing purposes
    __module__ = "exceptions"

    WrappedClass = exceptions.LSSTException

    def __init__(self, arg, *args, **kwds):
        if isinstance(arg, exceptions.LSSTException):
            cpp = arg
            message = cpp.what()
        else:
            message = arg
            cpp = self.WrappedClass(message, *args, **kwds)
        super(Exception, self).__init__(message)
        self.cpp = cpp

    def __getattr__(self, name):
        return getattr(self.cpp, name)

    def __repr__(self):
        return "%s('%s')" % (type(self).__name__, self.cpp.what())

    def __str__(self):
        return self.cpp.what()


@register
class CustomError(LSSTException):
    WrappedClass = exceptions.CustomError


def translate(cpp):
    """Translate a C++ Exception instance to Python and return it."""
    PyType = registry.get(type(cpp), None)
    if PyType is None:
        warnings.warn("Could not find appropriate Python type for C++ Exception")
        PyType = Exception
    return PyType(cpp)
