from django.db import models

from django_clone_helper.helpers import CloneHandler, ManyToOneParam


class Artist(models.Model):
    name = models.CharField(max_length=100)

    class clone(CloneHandler):
        many_to_one = [
            ManyToOneParam(name='album_set', fk_name='artist', attrs={'title': 'cloned album title'})
        ]

    def __str__(self):
        return self.name


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


class Compilation(models.Model):
    title = models.CharField(max_length=100)
    songs = models.ManyToManyField(Song)

    def __str__(self):
        return self.title
