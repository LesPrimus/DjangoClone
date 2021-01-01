from copy import copy
from itertools import chain

from django_clone_helper.utils import generate_unique


class CloneMeta(type):

    def __get__(self, instance, owner):
        return self(instance, owner)


class CloneHandler(metaclass=CloneMeta):
    exclude = []
    one_to_one = []
    many_to_one = []
    many_to_many = []
    unique_field_prefix = None

    def __init__(self, instance, owner=None, mapping=None):
        self.instance = instance
        self.owner = owner or self.instance.__class__
        self.mapping = mapping or {}

    @classmethod
    def _set_unique_constrain(cls, instance, prefix=None):
        fields = [
            field for field in instance._meta.get_fields()
            if field.concrete and field.unique and not field.primary_key
        ]
        for field in fields:
            if hasattr(instance, field.name):
                setattr(instance, field.name, generate_unique(instance, field))
        return instance

    @staticmethod
    def get_many_to_one_fields(instance):
        fields = [
            f for f in instance._meta.get_fields()
            if f.many_to_one
        ]
        return fields

    @staticmethod
    def get_one_to_one_fields(instance):
        fields = [
            f for f in instance._meta.get_fields()
            if f.one_to_one
        ]
        return fields

    @staticmethod
    def get_many_to_many(instance):
        fields = [
            f for f in instance._meta.get_fields()
            if f.many_to_many
        ]
        return fields

    def clone_instance(self, instance, exclude=None, attrs=None, commit=True):
        exclude = exclude or []
        attrs = attrs or {}
        cloned = copy(instance)
        cloned.pk = None
        for k, v in attrs.items():
            if k in exclude:
                continue
            setattr(cloned, k, v)
        if commit:
            self._set_unique_constrain(cloned)
            cloned.full_clean()
            cloned.save()
        return cloned

    def clone_many_to_many(self, many_to_many):
        for param in many_to_many:
            cloned = self.mapping[self.instance]
            m2m = getattr(self.instance, param.name)
            for relation in m2m.all():
                getattr(cloned, param.name).add(relation)

    def clone_one_to_one(self, one_to_one):
        result = {}
        for param in one_to_one:
            o2o = getattr(self.instance, param.name)
            for field in chain(self.get_one_to_one_fields(o2o), self.get_many_to_one_fields(o2o)):
                original_rel = getattr(o2o, field.name)
                cloned_rel = self.mapping.get(original_rel, None)
                if cloned_rel is not None:
                    param.attrs.update({field.name: cloned_rel})
            cloned_o2o = o2o.clone.make_clone(attrs=param.attrs, exclude=param.exclude)
            result.update({o2o: cloned_o2o})
        return result

    def clone_many_to_one(self, many_to_one):
        result = {}
        for param in many_to_one:
            related_manager = getattr(self.instance, param.name)
            for m2o in related_manager.all():
                for field in chain(self.get_many_to_one_fields(m2o), self.get_one_to_one_fields(m2o)):
                    original_rel = getattr(m2o, field.name)
                    cloned_rel = self.mapping.get(original_rel, None)
                    if cloned_rel is not None:
                        param.attrs.update({field.name: cloned_rel})
                cloned_m2o = m2o.clone.make_clone(attrs=param.attrs, exclude=param.exclude)
                result.update({m2o: cloned_m2o})
                self.mapping.update(result)
        return result

    def make_clone(self, many_to_one=None, one_to_one=None, many_to_many=None, exclude=None, attrs=None, commit=True):
        many_to_one = many_to_one or self.many_to_one
        many_to_many = many_to_many or self.many_to_many
        one_to_one = one_to_one or self.one_to_one
        cloned_instance = self.clone_instance(self.instance, attrs=attrs, exclude=exclude, commit=commit)
        self.mapping.update({self.instance: cloned_instance})
        if many_to_one:
            self.clone_many_to_one(many_to_one)
        if one_to_one:
            self.clone_one_to_one(one_to_one)
        if many_to_many:
            self.clone_many_to_many(many_to_many)
        return cloned_instance
