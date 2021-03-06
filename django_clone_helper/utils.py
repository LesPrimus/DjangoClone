from collections import namedtuple
from collections.abc import MutableMapping

from django.db.models import Model


class Param(MutableMapping):
    def __init__(self, name, attrs=None, exclude=None):
        self.name = name
        self.attrs = attrs or {}
        self.exclude = exclude

    def __getitem__(self, item):
        return self.attrs[item]

    def __setitem__(self, key, value):
        self.attrs[key] = value

    def __iter__(self):
        return iter(self.attrs)

    def __delitem__(self, key):
        del self.attrs[key]

    def __len__(self):
        return len(self.attrs)


LookUp = namedtuple('LookUp', ['name'])
Cloned = namedtuple('Cloned', ['name'])


def is_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    return True


def generate_unique(instance: Model, field):
    Klass = instance.__class__
    qs = Klass._default_manager
    value = getattr(instance, field.name)
    lookup = {field.name: value}
    prefix = 1
    while qs.filter(**lookup).exists():
        lookup[field.name] = value + str(prefix)
        prefix += 1
    return lookup[field.name]


class ConditionalContextManager:

    def __init__(self, condition, contextmanager):
        self.condition = condition
        self.contextmanager = contextmanager

    def __enter__(self):
        if self.condition:
            return self.contextmanager.__enter__()

    def __exit__(self, *args):
        if self.condition:
            return self.contextmanager.__exit__(*args)
