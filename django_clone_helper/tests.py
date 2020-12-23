from unittest.mock import patch, PropertyMock
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db.models import ForeignKey

from .helpers import CloneHandler
from .utils import ManyToOneParam, OneToManyParam, OneToOneParam, ParentLookUp, Cloned
from django_clone_helper.models import (
    Artist,
    Album,
    Song,
    Compilation,
    Instrument,
    Passport,
    Group,
    Membership,
)


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
def compilation(artist, album):
    song = Song.objects.create(
        title='Song1', album=album, artist=artist
    )
    song1 = Song.objects.create(
        title='Song2', album=album, artist=artist
    )
    compilation = Compilation.objects.create(
        title='New Compilation',
    )
    compilation.songs.add(song, song1)
    return compilation


@pytest.fixture
def group():
    group = Group.objects.create(name='Primus Band')
    return group


@pytest.fixture
def instrument():
    instrument = Instrument.objects.create(name='bass', serial_number='1234ABC')
    return instrument


def check_model_count(model, expected):
    assert model.objects.count() == expected


@pytest.mark.django_db
class TestModel:

    def test_clone_model(self, artist):
        cloned_artist = artist.clone.create_child()
        check_model_count(Artist, 2)
        assert cloned_artist.name == artist.name

    def test_clone_model_override_attrs(self, artist):
        attrs = {'name': 'Clone Artist name'}
        cloned_artist = artist.clone.create_child(attrs=attrs)
        check_model_count(Artist, 2)
        assert cloned_artist.name == attrs.get('name')

    @patch(
        'django_clone_helper.models.CloneHandler.exclude',
        new_callable=PropertyMock
    )
    def test_clone_model_exclude_required_attr_raise(self, mocked_exclude, artist):
        mocked_exclude.return_value = ['name']
        with pytest.raises(ValidationError):
            artist.clone.create_child()

    def test_clone_model_with_unique_fields(self, instrument):
        cloned_instrument = instrument.clone.create_child(attrs={'id': uuid4()})
        check_model_count(Instrument, 2)
        assert cloned_instrument.serial_number == f'{instrument.serial_number}{1}'


@pytest.mark.django_db
class TestOneToOne:
    @patch(
        'django_clone_helper.models.CloneHandler.one_to_one',
        new_callable=PropertyMock
    )
    def test_clone_model_with_o2o_attr(self, mocked_o2o, passport):
        mocked_o2o.return_value = [
            OneToOneParam(
                name='passport',
                reverse_name='owner'
            )
        ]
        artist = passport.owner
        check_model_count(Artist, 1)
        check_model_count(Passport, 1)

        cloned_artist = artist.clone.create_child()
        check_model_count(Artist, 2)
        check_model_count(Passport, 2)
        assert cloned_artist.passport != artist.passport


@pytest.mark.django_db
class TestManyToOne:
    @patch(
        'django_clone_helper.models.CloneHandler.many_to_one',
        new_callable=PropertyMock
    )
    def test_clone_model_with_m2o_attr(self, mocked_m2o, album):
        mocked_m2o.return_value = [
            ManyToOneParam(
                name='album_set',
                reverse_name='artist'
            )
        ]
        artist = album.artist
        check_model_count(Artist, 1)
        check_model_count(Album, 1)

        cloned_artist = artist.clone.create_child()
        check_model_count(Artist, 2)
        check_model_count(Album, 2)
        assert artist.album_set.get() != cloned_artist.album_set.get()
        assert artist.album_set.get().title == cloned_artist.album_set.get().title

    @patch(
        'django_clone_helper.models.CloneHandler.many_to_one',
        new_callable=PropertyMock
    )
    def test_clone_model_with_m2o_attr_override(self, mocked_m2o, album):
        mocked_m2o.return_value = [ # noqa
            ManyToOneParam(
                name='album_set',
                reverse_name='artist',
                attrs={'title': 'Override Title'}
            )
        ]
        artist = album.artist
        check_model_count(Artist, 1)
        check_model_count(Album, 1)

        cloned_artist = artist.clone.create_child()
        check_model_count(Artist, 2)
        check_model_count(Album, 2)
        assert artist.album_set.get() != cloned_artist.album_set.get()
        assert artist.album_set.get().title != cloned_artist.album_set.get().title
        assert cloned_artist.album_set.get().title == "Override Title"

    def test_clone_model_with_multiple_fks(self, song):
        artist = song.artist
        album = song.album
        check_model_count(Artist, 1)
        check_model_count(Album, 1)
        check_model_count(Song, 1)

        cloned_song = song.clone.create_child()
        check_model_count(Artist, 1)
        check_model_count(Album, 1)
        check_model_count(Song, 2)

        assert cloned_song.artist == artist
        assert cloned_song.album == album
        assert artist.song_set.count() == 2
        assert album.song_set.count() == 2

    @patch(
        'django_clone_helper.models.CloneHandler.many_to_one',
        new_callable=PropertyMock
    )
    def test_cloning_with_multiple_m2o(self, mocked_m2o, song):
        mocked_m2o.return_value = [
            ManyToOneParam(name='song_set', reverse_name='artist'),
        ]
        artist = song.artist
        check_model_count(Artist, 1)
        check_model_count(Song, 1)

        cloned_artist = artist.clone.create_child()
        check_model_count(Artist, 2)
        check_model_count(Song, 2)
        check_model_count(Album, 1)

        cloned_song = cloned_artist.song_set.get()

        check_model_count(Artist, 2)
        check_model_count(Album, 1)
        check_model_count(Song, 2)

        assert cloned_song.artist == cloned_artist
        assert cloned_song.album == song.album  # same as parent.
        assert cloned_song.title == song.title  # same as parent.

    @patch(
        'django_clone_helper.models.CloneHandler.many_to_one',
        new_callable=PropertyMock
    )
    def test_cloning_with_multiple_m2o_update_relations(self, mocked_m2o, album, song):
        mocked_m2o.return_value = [
            ManyToOneParam(name='album_set', reverse_name='artist'),
            ManyToOneParam(name='song_set', reverse_name='artist', attrs={'album': Cloned('album')}),
        ]
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
        cloned_song = cloned_artist.song_set.get()

        assert cloned_album.artist == cloned_artist
        assert cloned_album.title == album.title

        assert cloned_song.artist == cloned_artist
        assert cloned_song.album == cloned_album
        assert cloned_song.title == song.title


#     def test_clone_with_multi_m2o_params(self, album, song):
#         artist = album.artist
#         assert artist == song.artist
#         check_model_count(Artist, 1)
#         check_model_count(Album, 1)
#         check_model_count(Song, 1)
#
#         cloned_artist = artist.clone.create_child()
#         check_model_count(Artist, 2)
#         check_model_count(Album, 2)
#         check_model_count(Song, 2)
#
#         cloned_album = cloned_artist.album_set.get()
#         assert cloned_album.artist == cloned_artist
#         assert cloned_album.title == 'cloned album title'
#         cloned_song = cloned_artist.song_set.get()
#         assert cloned_song.artist == cloned_artist
#         assert cloned_song.title == 'cloned song title'
#
#     def test_clone_model_with_many_to_one_overriding_fields_on_model(self, album):
#         artist = album.artist
#         cloned_artist = artist.clone.create_child()
#         assert cloned_artist.album_set.count() == 1
#         assert cloned_artist.album_set.get().title == 'cloned album title'
#
#     def test_clone_model_with_many_to_one_overriding_fields_params(self, album):
#         pass
#
#     def test_clone_model_with_more_fks(self, song):
#         album, artist = song.album, song.artist
#         attrs = {'title': 'test title'}
#         cloned_song = song.clone.create_child(attrs=attrs)
#         check_model_count(Song, 2)
#         assert cloned_song.title == attrs.get('title')
#         assert cloned_song.artist == artist
#         assert cloned_song.album == album
#         assert album.song_set.count() == 2
#         assert artist.song_set.count() == 2
#
#     def test_cloning_model_with_custom_id(self, instrument):
#         cloned_instrument = instrument.clone.create_child(attrs={'id': uuid4()})
#         assert instrument.id != cloned_instrument.id
#
#     def test_cloning_model_with_parent_lookup_attrs_override(self, album):
#         artist = album.artist
#         m2o_param = ManyToOneParam(
#             name='album_set',
#             reverse_name='artist',
#             attrs={'title': ParentLookUp(name='artist.set_album_title')}
#         )
#         cloned_artist = artist.clone.create_child(many_to_one=[m2o_param])
#         cloned_album = cloned_artist.album_set.get()
#         assert cloned_album.title == f'{cloned_album.artist.set_album_title()}'
#
#     def test_cloning_with_auto_now_field(self, instrument):
#         cloned_instrument = instrument.clone.create_child(attrs={'id': uuid4()})
#         assert cloned_instrument.created_at != instrument.created_at
#
#     def test_cloning_with_unique_field(self, instrument):
#         cloned_instr = instrument.clone.create_child(attrs={'id': uuid4()})
#         cloned_instr_1 = instrument.clone.create_child(attrs={'id': uuid4()})
#         assert cloned_instr.serial_number == f'{instrument.serial_number}{1}'
#         assert cloned_instr_1.serial_number == f'{instrument.serial_number}{2}'
#
#     def test_cloning_with_constrains(self):
#         pass
#
#     def test_cloning_with_full_clean(self, artist):
#         with pytest.raises(ValidationError):
#             cloned_artist = artist.clone.create_child(exclude=['name'])
#
#     def test_cloning_with_one_to_one(self, passport):
#         artist = passport.owner
#         cloned_artist = artist.clone.create_child()
#         check_model_count(Artist, 2)
#         check_model_count(Passport, 2)
#
#     def test_cloning_with_one_to_many(self, album):
#         artist = album.artist
#         cloned_album = album.clone.create_child()
#         check_model_count(Album, 2)
#         check_model_count(Artist, 2)
#         cloned_album.refresh_from_db()
#         assert cloned_album.artist != artist
#
#     def test_cloning_with_m2m(self, compilation):
#         check_model_count(Compilation, 1)
#         check_model_count(Song, 2)
#         attrs = {'title': 'New Title'}
#         cloned_compilation = compilation.clone.create_child(attrs=attrs)
#         check_model_count(Compilation, 2)
#         check_model_count(Song, 2)
#         assert cloned_compilation.title == attrs.get('title')
#         assert cloned_compilation.songs.count() == 2
#
#     def test_cloning_through_fk(self, artist, group):
#         group.members.add(artist)
#         check_model_count(Membership, 1)
#         assert artist.membership_set.count() == 1
#         cloned_artist = artist.clone.create_child()
#         assert cloned_artist.membership_set.count() == 1
#         cloned_artist_membership = cloned_artist.membership_set.get()
#         assert cloned_artist_membership.invite_reason == 'Need a great bassist'
#         check_model_count(Membership, 2)
#
#     def test_cloning_m2m_through(self, artist, group):
#         group.members.add(artist)
#         assert artist.group_set.count() == 1
#         assert artist.membership_set.count() == 1
#         check_model_count(Group, 1)
#         check_model_count(Membership, 1)
#
#         cloned_artist = artist.clone.create_child()
#         check_model_count(Membership, 2)
#         assert cloned_artist.group_set.count() == 1
#         assert cloned_artist.membership_set.count() == 1
#
#
# @pytest.mark.django_db
# class TestHandler:
#     def test_clone_handler_decoupled_from_model(self, artist):
#         handler = CloneHandler(instance=artist, owner=artist.__class__)
#         cloned_artist = handler.create_child(commit=True, attrs={'name': 'Test Name'})
#         check_model_count(Artist, 2)
#         assert cloned_artist.name != artist.name
#
#     def test_clone_handler_many_to_one(self, album):
#         artist = album.artist
#         handler = CloneHandler(instance=artist, owner=artist.__class__)
#         cloned_artist = handler.create_child(commit=True, attrs={'name': 'Test Name'})
#         check_model_count(Artist, 2), check_model_count(Album, 1)
#         m2o_param = ManyToOneParam(
#             name='album_set',
#             reverse_name='artist',
#         )
#         cloned_m2o = handler._create_many_to_one(cloned_artist, commit=True, many_to_one=[m2o_param])
#         check_model_count(Album, 2)
#         assert artist.album_set.count() == 1
#         assert cloned_artist.album_set.count() == 1
##
#     def test_clone_handler_with_one_to_many(self, album):
#         artist = album.artist
#         check_model_count(Artist, 1)
#         check_model_count(Album, 1)
#         o2m_param = OneToManyParam(name='artist', reverse_name='album_set')
#         cloned_album = album.clone.create_child(one_to_many=o2m_param)
#         cloned_artist = cloned_album.artist
#         check_model_count(Artist, 2)
#         check_model_count(Album, 2)
#         assert artist.album_set.count() == 1
#         assert cloned_artist.album_set.count() == 1
#
#     def test_clone_handler_with_one_to_one(self, passport):
#         artist = passport.owner
#         check_model_count(Artist, 1)
#         check_model_count(Passport, 1)
#         cloned_artist = artist.clone.create_child(one_to_one=[
#             OneToOneParam(name='passport', reverse_name='owner')
#         ])
#         check_model_count(Artist, 2)
#         check_model_count(Passport, 2)
