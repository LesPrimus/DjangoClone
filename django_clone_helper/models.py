from uuid import uuid4

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from django_clone_helper.helpers import CloneHandler


class Artist(models.Model):
    name = models.CharField(max_length=100)

    class clone(CloneHandler):
        pass

    def set_album_title(self):
        return f'{self.name}--album'

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(max_length=128)
    members = models.ManyToManyField(Artist, through='Membership')

    class clone(CloneHandler):
        pass

    def __str__(self):
        return self.name


class Membership(models.Model):
    person = models.ForeignKey(Artist, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date_joined = models.DateField(auto_now=True)
    invite_reason = models.CharField(max_length=64)

    class clone(CloneHandler):
        pass


class Passport(models.Model):
    owner = models.OneToOneField(Artist, primary_key=True, on_delete=models.CASCADE)

    class clone(CloneHandler):
        pass

    def __str__(self):
        return f'{self.__class__.__name__}-{self.owner.name}'


class Album(models.Model):
    title = models.CharField(max_length=100)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)

    class clone(CloneHandler):
        pass

    def __str__(self):
        return self.title


class Song(models.Model):
    title = models.CharField(max_length=100)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)

    class clone(CloneHandler):
        pass

    def __str__(self):
        return self.title


class SongPart(models.Model):
    name = models.CharField(max_length=50)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class clone(CloneHandler):
        pass

    def __str__(self):
        return f'{self.song}--{self.name}'


class Compilation(models.Model):
    title = models.CharField(max_length=100)
    songs = models.ManyToManyField(Song)

    class clone(CloneHandler):
        pass

    def __str__(self):
        return self.title


class Instrument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class clone(CloneHandler):
        pass

    def __str__(self):
        return self.name


class TaggedItem(models.Model):
    tag = models.SlugField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.tag


class BassGuitar(Instrument):
    class Type(models.TextChoices):
        ACOUSTIC = 'AC'
        ELECTRIC = 'EL'

    type = models.CharField(max_length=2, choices=Type.choices, default=Type.ELECTRIC)

    def __str__(self):
        return self.name


class A(models.Model):
    pass

    class clone(CloneHandler):
        pass


class B(models.Model):
    a = models.ForeignKey(A, on_delete=models.CASCADE)

    class clone(CloneHandler):
        pass


class C(models.Model):
    b = models.ForeignKey(B, on_delete=models.CASCADE)

    class clone(CloneHandler):
        pass


class D(models.Model):
    c = models.ForeignKey(C, on_delete=models.CASCADE)

    class clone(CloneHandler):
        pass
