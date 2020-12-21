from uuid import uuid4

from django.db import models

from django_clone_helper.helpers import CloneHandler
from django_clone_helper.utils import (
    ManyToOneParam,
    OneToManyParam,
    OneToOneParam,
)


class Artist(models.Model):
    name = models.CharField(max_length=100)

    class clone(CloneHandler):
        many_to_one = [
            ManyToOneParam(name='album_set', reverse_name='artist', attrs={'title': 'cloned album title'}),
            ManyToOneParam(name='song_set', reverse_name='artist', attrs={'title': 'cloned song title'}),
        ]
        one_to_one = [
            OneToOneParam(name='passport', reverse_name='owner')
        ]

    def __str__(self):
        return self.name


class Passport(models.Model):
    owner = models.OneToOneField(Artist, primary_key=True, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.__class__.__name__}-{self.owner.name}'


class Album(models.Model):
    title = models.CharField(max_length=100)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)

    class clone(CloneHandler):
        one_to_many = [
            OneToManyParam(name='artist', reverse_name='album_set')
        ]

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
        unique_field_prefix = 'Clone'

    def __str__(self):
        return self.name
