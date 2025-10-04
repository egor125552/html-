# -*- coding: utf-8 -*-

# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A module which provides backward compatibility to Python 2 and 3."""

import collections
import os
import sys

PY3 = sys.version_info[0] == 3

# ===================================================================
# --- Python 2 / 3 compatibility
# ===================================================================

if PY3:
    # strings
    basestring = str
    unicode = str

    # long
    long = int

    # range
    xrange = range

    # callable
    callable = callable

    # exceptions
    try:
        # In Python 3.3+, these are in the built-in namespace.
        # In Python 3.2, they are in the "os" module.
        FileNotFoundError = FileNotFoundError
        PermissionError = PermissionError
        ProcessLookupError = ProcessLookupError
        InterruptedError = InterruptedError
        ChildProcessError = ChildProcessError
    except NameError:
        # Fallback for Python 3.2.
        FileNotFoundError = getattr(__import__('os'), 'FileNotFoundError')
        PermissionError = getattr(__import__('os'), 'PermissionError')
        ProcessLookupError = getattr(__import__('os'), 'ProcessLookupError')
        InterruptedError = getattr(__import__('os'), 'InterruptedError')
        ChildProcessError = getattr(__import__('os'), 'ChildProcessError')

    # others
    import configparser
    from io import StringIO
    import functools
    reduce = functools.reduce

    def execfile(path, glob, loc):
        """A Python 3 implementation of execfile."""
        with open(path, 'r') as f:
            # According to the docs, the file must be parsed as a
            # sequence of statements, which means it can't be passed to
            # compile() with 'exec' as the second argument.
            # The only way to do that is to call compile() against each
            # single line of code.
            # See: http://tinyurl.com/69h6l7
            code = compile(f.read(), path, 'exec')
            exec(code, glob, loc)

    # In Python 3, the 'super' function can be called with no arguments.
    # This is a replacement that mimics this behavior.
    _super = super

    def super(cls, instance):
        # We need to look up the MRO for the class that is after 'cls'.
        # That's what 'super' does.
        mro = instance.__class__.mro()
        try:
            next_class = mro[mro.index(cls) + 1]
        except (AttributeError, IndexError):
            # We are at the end of the MRO.
            # This is a replacement for super(cls, instance)
            # which would otherwise raise an error.
            return _super(cls, instance)
        else:
            return _super(next_class, instance)

else:  # Python 2
    # strings
    basestring = basestring
    unicode = unicode

    # long
    long = long

    # range
    xrange = xrange

    # callable
    callable = callable

    # exceptions
    FileNotFoundError = IOError
    PermissionError = IOError
    ProcessLookupError = OSError
    InterruptedError = IOError
    ChildProcessError = OSError

    # others
    import ConfigParser as configparser  # noqa
    from StringIO import StringIO  # noqa
    reduce = reduce

    # execfile is a built-in in Python 2.
    execfile = execfile

    # super
    super = super


# ===================================================================
# --- collections.namedtuple
# ===================================================================

if sys.version_info < (2, 7):
    def namedtuple(typename, field_names, verbose=False, rename=False):
        """A replacement for collections.namedtuple for Python 2.6.
        It does not provide the same features but it's good enough.
        """
        # See: http://code.activestate.com/recipes/500261/
        from operator import itemgetter
        from sys import _getframe

        # ... then we're not in a lambda or list comprehension, so
        # it's safe to use the default of None
        if isinstance(field_names, basestring):
            field_names = field_names.replace(',', ' ').split()
        field_names = tuple(map(str, field_names))
        if rename:
            names = list(field_names)
            seen = set()
            for i, name in enumerate(names):
                if (not all(c.isalnum() or c == '_' for c in name) or
                        name.startswith('_') or name in seen):
                    names[i] = '_%d' % i
                seen.add(name)
            field_names = tuple(names)

        # Create and fill the class template
        # We're dynamically creating a new class here, so we need to
        # be careful about the namespace.
        # We're using a temporary namespace to avoid polluting the
        # global one.
        temp_namespace = dict(
            __name__='namedtuple_%s' % typename,
            _itemgetter=itemgetter,
            _new=classmethod(
                lambda cls, *args, **kwargs:
                cls.__new__(cls, *args, **kwargs)),
            _len=lambda self: len(self),
            _repr=lambda self:
            '%s(%s)' % (
                self.__class__.__name__,
                ', '.join(
                    '%s=%r' % (name, self[i])
                    for i, name in enumerate(self._fields))),
            _asdict=lambda self:
            dict(zip(self._fields, self)),
            _replace=lambda self, **kwds:
            self._make(map(kwds.get, self._fields, self)),
            _fields=field_names,
            __slots__=(),
            __getnewargs__=lambda self: tuple(self)
        )
        # We can't use a dict literal because we need to preserve order.
        for i, name in enumerate(field_names):
            temp_namespace[name] = property(itemgetter(i))

        # We're using exec to create the class.
        # This is not ideal but it's the only way to do it in Python 2.6.
        try:
            exec(
                "class %(typename)s(tuple):\n"
                "    __slots__ = ()\n"
                "    _fields = %(field_names)r\n"
                "    def __new__(_cls, %(arg_list)s):\n"
                "        return _tuple.__new__(_cls, (%(arg_list)s))\n"
                "    @classmethod\n"
                "    def _make(cls, iterable, new=tuple.__new__, len=len):\n"
                "        result = new(cls, iterable)\n"
                "        if len(result) != %(num_fields)d:\n"
                "            raise TypeError(\n"
                "                'Expected %(num_fields)d arguments, got %%d' %% len(result))\n"  # noqa
                "        return result\n"
                "    def __repr__(self):\n"
                "        return '%(typename)s(%(repr_fmt)s)' %% self\n"
                "    def _asdict(self):\n"
                "        return dict(zip(self._fields, self))\n"
                "    def __getnewargs__(self):\n"
                "        return tuple(self)\n"
                % dict(
                    typename=typename,
                    field_names=field_names,
                    num_fields=len(field_names),
                    arg_list=repr(field_names).replace(
                        "'", "")[1:-1],
                    repr_fmt=', '.join(
                        '%s=%%r' % name for name in field_names)
                ),
                temp_namespace)
        except SyntaxError as e:
            e.msg = "invalid field name: %r" % (e.text.strip(),)
            raise e

        result = temp_namespace[typename]

        # For pickling to work, the __module__ variable needs to be set
        # to the frame where the named tuple is created.  Bypass this
        # step in environments where frames are not available.
        if hasattr(_getframe, 'f_globals'):
            result.__module__ = _getframe(1).f_globals.get(
                '__name__', '__main__')

        return result
else:
    namedtuple = collections.namedtuple