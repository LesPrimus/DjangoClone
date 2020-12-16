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


@pytest.mark.djangp_db
class TestSuite:
    @classmethod
    def check_model_count(cls, model, expected):
        assert model.objects.count() == expected

    def test_clone_artist_model(self, artist):
        attrs = {'name': 'John'}
        cloned_artist = artist.clone.create_child(attrs=attrs)
        self.check_model_count(Artist, 2)
        assert cloned_artist.name == attrs.get('name')
