import operator
from copy import copy

from django_clone_helper.utils import generate_unique, ParentLookUp, Cloned


class CloneMeta(type):

    def __get__(self, instance, owner):
        return self(instance, owner)


class CloneHandler(metaclass=CloneMeta):
    exclude = []
    many_to_one = []
    one_to_many = []
    many_to_many = []
    one_to_one = []
    unique_field_prefix = None

    def __init__(self, instance, owner):
        self.instance = instance
        self.owner = owner

    @classmethod
    def _pre_save_validation(cls, instance):
        try:
            instance.full_clean()
        except Exception as e:
            raise e
        return instance

    @classmethod
    def _get_value_from_parent(cls, parent, value: ParentLookUp):
        try:
            return operator.attrgetter(value.name)(parent)
        except AttributeError as e:
            raise e

    def _set_cloned_fk(self, cloned_inst, values: list, cloned_mapping: dict):
        for cloned_param in values:
            if hasattr(cloned_inst, cloned_param.name):
                original_fk = getattr(cloned_inst, cloned_param.name)
                cloned_fk = cloned_mapping.get(original_fk, None)
                if cloned_fk:
                    setattr(cloned_inst, cloned_param.name, cloned_fk)

    @classmethod
    def _set_unique_constrain(cls, instance, prefix):
        fields = [
            field for field in instance._meta.get_fields()
            if field.concrete and field.unique and not field.primary_key
        ]
        for field in fields:
            if hasattr(instance, field.name):
                # Todo add a callable to model.clone settings
                setattr(instance, field.name, generate_unique(instance, field))
        return instance

    @classmethod
    def _create_clone(cls, instance, attrs=None, exclude=None):
        attrs = attrs or {}
        exclude = exclude or []
        assert not any([k in exclude for k in attrs.keys()])
        cloned = copy(instance)
        cloned.pk = None
        for k, v in attrs.items():
            if hasattr(instance, k):
                value = v if not isinstance(v, ParentLookUp) else cls._get_value_from_parent(cloned, v)
                setattr(cloned, k, value() if callable(value) else value)
        # set a default if instance field in exclude
        for item in exclude:
            field = instance._meta.get_field(item)
            setattr(cloned, field.attname, field.get_default())
        cls._set_unique_constrain(cloned, prefix=cls.unique_field_prefix)
        return cloned

    def _pre_create_child(self, instance, attrs=None, exclude=None):
        return self._create_clone(instance, attrs=attrs, exclude=exclude)

    def _pre_create_many_to_one(self, cloned, many_to_one, commit=True):
        result = {}
        for param in many_to_one:
            assert param.reverse_name
            cloned_attrs = [param.attrs.pop(k) for k, v in dict(param.attrs).items() if isinstance(v, Cloned)]
            if hasattr(self.instance, param.name):
                m2o_manager = getattr(self.instance, param.name)
                queyset = m2o_manager.all()
                for inst in queyset:
                    cloned_inst = self._create_clone(inst, attrs=param.attrs, exclude=param.exclude)
                    setattr(cloned_inst, param.reverse_name, cloned)
                    result[inst] = cloned_inst
                    self._set_cloned_fk(cloned_inst, cloned_attrs, result)
                    if commit is True:
                        cloned_inst.save()
        return result

    def _pre_create_one_to_many(self, cloned, one_to_many, commit=True):
        result = []
        for param in one_to_many:
            assert param.reverse_name
            if hasattr(self.instance, param.name):
                o2m = getattr(self.instance, param.name)
                cloned_o2m = self._create_clone(o2m, attrs=param.attrs, exclude=param.exclude)
                if commit is True:
                    cloned_o2m.save()
                    getattr(cloned_o2m, param.reverse_name).add(cloned)
                result.append(cloned_o2m)
        return result

    def _pre_create_one_to_one(self, cloned, one_to_one, commit=True):
        result = []
        for param in one_to_one:
            assert param.reverse_name
            if hasattr(self.instance, param.name):
                o2o = getattr(self.instance, param.name)
                cloned_o2o = self._create_clone(o2o, attrs=param.attrs, exclude=param.exclude)
                setattr(cloned_o2o, param.reverse_name, cloned)
                if commit is True:
                    cloned_o2o.save()
                    result.append(cloned_o2o)
        return result

    def _pre_create_many_to_many(self, cloned, many_to_many, commit=True):
        result = []
        for param in many_to_many:
            source = getattr(self.instance, param.name)
            destination = getattr(cloned, param.name)
            for m2m_relation in source.all():
                destination.add(m2m_relation)
                result.append(m2m_relation)
        return result

    def _create_many_to_one(self, cloned, many_to_one, commit=True):
        cloned_fks = self._pre_create_many_to_one(cloned, commit=commit, many_to_one=many_to_one)
        return cloned_fks

    def _create_one_to_many(self, cloned, one_to_many, commit=True):
        cloned_fks = self._pre_create_one_to_many(cloned, one_to_many=one_to_many, commit=commit)
        return cloned_fks

    def _create_many_to_many(self, cloned, many_to_many, commit=True):
        m2m_added = self._pre_create_many_to_many(cloned, many_to_many=many_to_many, commit=commit)
        return m2m_added

    def _create_one_to_one(self, cloned, one_to_one, commit=True):
        one_to_one = self._pre_create_one_to_one(cloned, one_to_one=one_to_one, commit=commit)
        return one_to_one

    def create_child(
            self,
            commit=True,
            attrs=None,
            exclude=None,
            many_to_one=None,
            one_to_many=None,
            many_to_many=None,
            one_to_one=None
    ):
        many_to_one = many_to_one or self.many_to_one
        one_to_many = one_to_many or self.one_to_many
        many_to_many = many_to_many or self.many_to_many
        one_to_one = one_to_one or self.one_to_one
        _pre_create_child = getattr(self.instance, '_pre_create_child', self._pre_create_child)
        cloned = _pre_create_child(self.instance, attrs, exclude=exclude or self.exclude)
        if commit is True:
            self._pre_save_validation(cloned)
            cloned.save()
            if many_to_one:
                self._create_many_to_one(cloned, many_to_one=many_to_one)
            if one_to_many:
                self._create_one_to_many(cloned, one_to_many=one_to_many)
            if many_to_many:
                self._create_many_to_many(cloned, many_to_many=many_to_many)
            if one_to_one:
                self._create_one_to_one(cloned, one_to_one=one_to_one)
        return cloned
