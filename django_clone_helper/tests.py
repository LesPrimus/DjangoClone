import pytest

from .models import Artist, Album, Song, Compilation


@pytest.fixture
def artist(db):
    artist = Artist.objects.create(name='Les')
    return artist


@pytest.fixture
def album(artist, db):
    album = Album.objects.create(title='Frizzle Fry', artist=artist)
    return album


@pytest.fixture
def song(artist, album, db):
    song = Song.objects.create(
        title='My name is mud', album=album, artist=artist
    )
    return song


@pytest.mark.django_db
class TestSuite:
    @classmethod
    def check_model_count(cls, model, expected):
        assert model.objects.count() == expected

    def test_clone_artist_model(self, artist):
        attrs = {'name': 'John'}
        cloned_artist = artist.clone.create_child(attrs=attrs)
        self.check_model_count(Artist, 2)
        assert cloned_artist.name == attrs.get('name')
        assert cloned_artist.album_set.count() == 0

    def test_clone_artist_many_to_one(self, album):
        artist = album.artist
        cloned_artist = artist.clone.create_child()
        assert cloned_artist.album_set.count() == 1
        assert cloned_artist.album_set.get().title == 'cloned album title'

    def test_clone_album_model(self, album):
        artist = album.artist
        attrs = {'title': 'test title'}
        cloned_album = album.clone.create_child(attrs=attrs)
        self.check_model_count(Album, 2)
        assert cloned_album.title == attrs.get('title')
        assert artist.album_set.count() == 2

    def test_clone_song_model(self, song):
        album, artist = song.album, song.artist
        attrs = {'title': 'test title'}
        cloned_song = song.clone.create_child(attrs=attrs)
        self.check_model_count(Song, 2)
        assert cloned_song.title == attrs.get('title')
        assert album.song_set.count() == 2
        assert artist.song_set.count() == 2
