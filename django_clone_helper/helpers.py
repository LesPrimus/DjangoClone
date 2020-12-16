from copy import copy


class CloneMeta(type):

    def __get__(self, instance, owner):
        return self(instance, owner)


class CloneHandler(metaclass=CloneMeta):
    exclude = []
    many_to_one = []
    many_to_many = []

    def __init__(self, instance, owner):
        self.instance = instance
        self.owner = owner

    @classmethod
    def _create_clone(cls, instance, attrs=None, exclude=None):
        attrs = attrs or {}
        exclude = exclude or []
        cloned = copy(instance)
        cloned.pk = None
        assert not any([k in exclude for k in attrs.keys()])
        for k, v in attrs.items():
            if hasattr(instance, k):
                setattr(cloned, k, v() if callable(v) else v)
        # set a default if instance field in exclude
        for item in exclude:
            field = instance._meta.get_field(item)
            setattr(cloned, field.attname, field.get_default())
        return cloned

    def _pre_create_child(self, instance, attrs=None, exclude=None):
        return self._create_clone(instance, attrs=attrs, exclude=exclude)

    def _create_many_to_one(self, cloned, commit=True, in_bulk=False):
        cloned_fks = []
        for dict_param in self.many_to_one:
            for k, v in dict_param.items():
                attrs = v.get('attrs', {})
                exclude = v.get('exclude', [])
                fk_name = v.get('fk_name')
                assert fk_name, 'Fk name must be explicit'
                if hasattr(self.instance, k):
                    related_manager = getattr(self.instance, k)
                    queryset = related_manager.all()
                    for inst in queryset:
                        cloned_fk = self._create_clone(inst, attrs=attrs, exclude=exclude)
                        setattr(cloned_fk, fk_name, cloned)
                        if commit is True:
                            cloned_fk.save()
                        cloned_fks.append(cloned_fk)
        return cloned_fks

    def _create_many_to_many(self, cloned):
        pass

    def create_child(self, commit=True, attrs=None):
        _pre_create_child = getattr(self.instance, '_pre_create_child', self._pre_create_child)
        cloned = _pre_create_child(self.instance, attrs, exclude=self.exclude)
        if commit is True:
            cloned.save()
            if self.many_to_one:
                self._create_many_to_one(cloned)
            if self.many_to_many:
                self._create_many_to_many(cloned)
        return cloned
