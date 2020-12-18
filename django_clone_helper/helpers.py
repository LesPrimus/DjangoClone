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

    def _create_many_to_one(self, cloned, commit=True, many_to_one=None):
        many_to_one = many_to_one or self.many_to_one
        cloned_fks = []  # todo switch to set-default dict
        for param in many_to_one:
            attrs = param.attrs
            exclude = param.exclude
            fk_name = param.fk_name
            assert fk_name, 'Fk name must be explicit'
            if hasattr(self.instance, param.name):
                related_manager = getattr(self.instance, param.name)
                queryset = related_manager.all()
                for inst in queryset:
                    cloned_fk = self._create_clone(inst, attrs=attrs, exclude=exclude)
                    setattr(cloned_fk, fk_name, cloned)
                    for field_name, value in param.items():
                        if hasattr(cloned_fk, field_name):
                            setattr(cloned_fk, field_name, value)
                    if commit is True:
                        cloned_fk.save()
                    cloned_fks.append(cloned_fk)
        return cloned_fks

    def _create_many_to_many(self, cloned):
        pass

    def create_child(self, commit=True, attrs=None, exclude=None):
        _pre_create_child = getattr(self.instance, '_pre_create_child', self._pre_create_child)
        cloned = _pre_create_child(self.instance, attrs, exclude=exclude or self.exclude)
        if commit is True:
            try:
                cloned.full_clean()
            except Exception as e:
                raise e
            cloned.save()
            if self.many_to_one:
                self._create_many_to_one(cloned)
            if self.many_to_many:
                self._create_many_to_many(cloned)
        return cloned
