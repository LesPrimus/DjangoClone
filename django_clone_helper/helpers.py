from copy import copy

from django_clone_helper.utils import generate_unique


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
                setattr(instance, field.name, new_value := generate_unique(instance, field))
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

    def _pre_create_relation(self, cloned, commit=True, param_inst=None):
        pass

    def _create_many_to_one(self, cloned, commit=True, many_to_one=None):
        many_to_one = many_to_one or self.many_to_one
        cloned_fks = []  # todo switch to set-default dict
        for param in many_to_one:
            assert param.fk_name, 'Fk name must be explicit'
            if hasattr(self.instance, param.name):
                related_manager = getattr(self.instance, param.name)
                queryset = related_manager.all()
                for inst in queryset:
                    cloned_fk = self._create_clone(inst, attrs=param.attrs, exclude=param.exclude)
                    setattr(cloned_fk, param.fk_name, cloned)
                    for field_name, value in param.items():
                        if hasattr(cloned_fk, field_name):
                            setattr(cloned_fk, field_name, value)
                    if commit is True:
                        self._pre_save_validation(cloned_fk)
                        cloned_fk.save()
                    cloned_fks.append(cloned_fk)
        return cloned_fks

    def _create_many_to_many(self, cloned, commit=True, many_to_many=None):
        pass

    def _create_one_to_one(self, cloned, commit=True, one_to_one=None):
        one_to_one = one_to_one or self.one_to_one
        result = []
        for param in one_to_one:
            assert param.o2o_name, 'One-to-one name must be explicit'
            if hasattr(self.instance, param.name):
                original_o2o = getattr(self.instance, param.name)
                cloned_o2o = self._create_clone(original_o2o, attrs=param.attrs, exclude=param.exclude)
                setattr(cloned_o2o, param.o2o_name, cloned)
                for field_name, value in param.items():
                    if hasattr(cloned_o2o, field_name):
                        setattr(cloned_o2o, field_name, value)
                if commit is True:
                    self._pre_save_validation(cloned_o2o)
                    cloned_o2o.save()
                result.append(cloned_o2o)
        return result

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
