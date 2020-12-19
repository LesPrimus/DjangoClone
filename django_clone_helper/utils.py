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


class ManyToOneParam(Param):
    def __init__(self, name, fk_name, attrs=None, exclude=None):
        super(ManyToOneParam, self).__init__(name, attrs=attrs, exclude=exclude)
        self.fk_name = fk_name


class OneToOneParam(Param):
    def __init__(self, name, o2o_name, attrs=None, exclude=None):
        super(OneToOneParam, self).__init__(name, attrs=attrs, exclude=exclude)
        self.o2o_name = o2o_name


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
