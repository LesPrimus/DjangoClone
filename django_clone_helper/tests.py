import pytest

from .helpers import CloneHandler, ManyToOneParam
from .models import Artist, Album, Song, Compilation, Instrument


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


@pytest.fixture
def instrument():
    instrument = Instrument.objects.create(name='bass')
    return instrument


def check_model_count(model, expected):
    assert model.objects.count() == expected


@pytest.mark.django_db
class TestSuite:

    def test_clone_model(self, artist):
        attrs = {'name': 'John'}
        cloned_artist = artist.clone.create_child(attrs=attrs)
        check_model_count(Artist, 2)
        assert cloned_artist.name == attrs.get('name')
        assert cloned_artist.album_set.count() == 0

    def test_clone_model_with_many_to_one_overriding_fields_on_model(self, album):
        artist = album.artist
        cloned_artist = artist.clone.create_child()
        assert cloned_artist.album_set.count() == 1
        assert cloned_artist.album_set.get().title == 'cloned album title'

    def test_clone_model_with_many_to_one_overriding_fields_params(self, album):
        artist = album.artist
        attrs = {'title': 'test title'}
        cloned_album = album.clone.create_child(attrs=attrs)
        check_model_count(Album, 2)
        assert cloned_album.title == attrs.get('title')
        assert artist.album_set.count() == 2

    def test_clone_model_with_more_fks(self, song):
        album, artist = song.album, song.artist
        attrs = {'title': 'test title'}
        cloned_song = song.clone.create_child(attrs=attrs)
        check_model_count(Song, 2)
        assert cloned_song.title == attrs.get('title')
        assert album.song_set.count() == 2
        assert artist.song_set.count() == 2

    def test_cloning_model_with_custom_id(self, instrument):
        cloned_instrument = instrument.clone.create_child()
        assert instrument.id != cloned_instrument.id

    def test_cloning_with_auto_now_field(self, instrument):
        cloned_instrument = instrument.clone.create_child()
        assert cloned_instrument.created_at != instrument.created_at


@pytest.mark.django_db
class TestHandler:
    def test_clone_handler_decoupled_from_model(self, artist):
        handler = CloneHandler(instance=artist, owner=artist.__class__)
        cloned_artist = handler.create_child(commit=True, attrs={'name': 'Test Name'})
        check_model_count(Artist, 2)
        assert cloned_artist.name != artist.name

    def test_clone_handler_many_to_one(self, album):
        artist = album.artist
        handler = CloneHandler(instance=artist, owner=artist.__class__)
        cloned_artist = handler.create_child(commit=True, attrs={'name': 'Test Name'})
        check_model_count(Artist, 2), check_model_count(Album, 1)
        m2o_param = ManyToOneParam(
            name='album_set',
            fk_name='artist',
        )
        cloned_m2o = handler._create_many_to_one(cloned_artist, commit=True, many_to_one=[m2o_param])
        check_model_count(Album, 2)
        assert artist.album_set.count() == 1
        assert cloned_artist.album_set.count() == 1
