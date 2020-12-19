from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError

from .helpers import CloneHandler
from .utils import ManyToOneParam, is_iterable
from .models import Artist, Album, Song, Compilation, Instrument, Passport


@pytest.fixture
def artist(db):
    artist = Artist.objects.create(name='Les')
    return artist


@pytest.fixture
def passport(db, artist):
    passport = Passport.objects.create(owner=artist)
    return passport


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
    instrument = Instrument.objects.create(name='bass', serial_number='1234ABC')
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

    def test_clone_with_multi_m2o_params(self, album, song):
        artist = album.artist
        assert artist == song.artist
        check_model_count(Artist, 1)
        check_model_count(Album, 1)
        check_model_count(Song, 1)

        cloned_artist = artist.clone.create_child()
        check_model_count(Artist, 2)
        check_model_count(Album, 2)
        check_model_count(Song, 2)

        cloned_album = cloned_artist.album_set.get()
        assert cloned_album.artist == cloned_artist
        assert cloned_album.title == 'cloned album title'
        cloned_song = cloned_artist.song_set.get()
        assert cloned_song.artist == cloned_artist
        assert cloned_song.title == 'cloned song title'

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
        assert cloned_song.artist == artist
        assert cloned_song.album == album
        assert album.song_set.count() == 2
        assert artist.song_set.count() == 2

    def test_cloning_model_with_custom_id(self, instrument):
        cloned_instrument = instrument.clone.create_child(attrs={'id': uuid4()})
        assert instrument.id != cloned_instrument.id

    def test_cloning_with_auto_now_field(self, instrument):
        cloned_instrument = instrument.clone.create_child(attrs={'id': uuid4()})
        assert cloned_instrument.created_at != instrument.created_at

    def test_cloning_with_unique_field(self, instrument):
        cloned_instr = instrument.clone.create_child(attrs={'id': uuid4()})
        cloned_instr_1 = instrument.clone.create_child(attrs={'id': uuid4()})
        assert cloned_instr.serial_number == f'{instrument.serial_number}{1}'
        assert cloned_instr_1.serial_number == f'{instrument.serial_number}{2}'

    def test_cloning_with_constrains(self):
        pass

    def test_cloning_with_full_clean(self, artist):
        with pytest.raises(ValidationError):
            cloned_artist = artist.clone.create_child(exclude=['name'])

    def test_cloning_with_one_to_one(self, passport):
        artist = passport.owner
        cloned_artist = artist.clone.create_child()
        check_model_count(Artist, 2)
        check_model_count(Passport, 2)


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
            reverse_name='artist',
        )
        cloned_m2o = handler._create_many_to_one(cloned_artist, commit=True, many_to_one=[m2o_param])
        check_model_count(Album, 2)
        assert artist.album_set.count() == 1
        assert cloned_artist.album_set.count() == 1

    def test_clone_handler_with_unique_fields(self, instrument):
        handler = CloneHandler(instance=instrument, owner=instrument.__class__)
        cloned_instrument = handler.create_child(commit=True, attrs={'id': uuid4()})
        check_model_count(Instrument, 2)
        assert cloned_instrument.serial_number == f'{instrument.serial_number}{1}'
