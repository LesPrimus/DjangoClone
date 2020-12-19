from copy import copy

from django_clone_helper.utils import generate_unique, is_iterable


class CloneMeta(type):

    def __get__(self, instance, owner):
        return self(instance, owner)


class CloneHandler(metaclass=CloneMeta):
    exclude = []
    many_to_one = []
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
                setattr(cloned, k, v() if callable(v) else v)
        # set a default if instance field in exclude
        for item in exclude:
            field = instance._meta.get_field(item)
            setattr(cloned, field.attname, field.get_default())
        cls._set_unique_constrain(cloned, prefix=cls.unique_field_prefix)
        return cloned

    def _pre_create_child(self, instance, attrs=None, exclude=None):
        return self._create_clone(instance, attrs=attrs, exclude=exclude)

    def _clone_relations(self, cloned, instance, param):
        instance = instance if is_iterable(instance) else [instance]
        cloned_relations = []
        for inst in instance:
            cloned_inst = self._create_clone(inst, attrs=param.attrs, exclude=param.exclude)
            setattr(cloned_inst, param.reverse_name, cloned)
            for field_name, value in param.items():
                if hasattr(cloned_inst, field_name):
                    setattr(cloned_inst, field_name, value)
            cloned_relations.append(cloned_inst)
        return cloned_relations

    def _pre_create_relation(self, cloned, commit=True, param_inst=None):
        result = []
        for param in param_inst:
            assert param.reverse_name
            if hasattr(self.instance, param.name):
                related_relation = getattr(self.instance, param.name)
                if hasattr(related_relation, 'all'):
                    queryset = related_relation.all()
                    cloned_relations = self._clone_relations(cloned, queryset, param=param)
                    result.extend(cloned_relations)
                else:
                    cloned_relation = self._clone_relations(cloned, related_relation, param)
                    result.extend(cloned_relation)
        if commit is True:
            for inst in result:
                self._pre_save_validation(inst)
                inst.save()
        return result

    def _create_many_to_one(self, cloned, commit=True, many_to_one=None):
        cloned_fks = self._pre_create_relation(cloned, commit=commit, param_inst=many_to_one)
        return cloned_fks

    def _create_many_to_many(self, cloned, commit=True, many_to_many=None):
        pass

    def _create_one_to_one(self, cloned, commit=True, one_to_one=None):
        one_to_one = self._pre_create_relation(cloned, commit=commit, param_inst=one_to_one)
        return one_to_one

    def create_child(
            self,
            commit=True,
            attrs=None,
            exclude=None,
            many_to_one=None,
            many_to_many=None,
            one_to_one=None
    ):
        many_to_one = many_to_one or self.many_to_one
        many_to_many = many_to_many or self.many_to_many
        one_to_one = one_to_one or self.one_to_one
        _pre_create_child = getattr(self.instance, '_pre_create_child', self._pre_create_child)
        cloned = _pre_create_child(self.instance, attrs, exclude=exclude or self.exclude)
        if commit is True:
            self._pre_save_validation(cloned)
            cloned.save()
            if many_to_one:
                self._create_many_to_one(cloned, many_to_one=many_to_one)
            if many_to_many:
                self._create_many_to_many(cloned, many_to_many=many_to_many)
            if one_to_one:
                self._create_one_to_one(cloned, one_to_one=one_to_one)
        return cloned
