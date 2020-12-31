from uuid import uuid4

import pytest
from django.db.models.options import Options

from .helpers import CloneHandler

from django_clone_helper.models import (
    Artist,
    Album,
    Song,
    SongPart,
    Compilation,
    Instrument,
    Passport,
    Group,
    Membership,
    BassGuitar, A, B, C, D
)
from .utils import Param


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


@pytest.fixture
def bass_guitar():
    bass = BassGuitar.objects.create(
        id=uuid4(), name='Warwick', serial_number='4321ABC', type=BassGuitar.Type.ELECTRIC
    )
    return bass


def check_model_count(model, expected):
    assert model.objects.count() == expected


@pytest.fixture
def patch_clone(monkeypatch):
    def _patch_factory(model, **kwargs):
        class clone_patch(CloneHandler):
            exclude = kwargs.get('exclude', [])
            attrs = kwargs.get('attrs', {})
            one_to_one = kwargs.get('one_to_one', [])
            many_to_one = kwargs.get('many_to_one', [])
            many_to_many = kwargs.get('many_to_many', [])
        monkeypatch.setattr(model, 'clone', clone_patch)
    return _patch_factory


@pytest.mark.django_db
class TestModel:

    def test_clone_model(self, artist):
        cloned_artist = artist.clone.make_clone()
        check_model_count(Artist, 2)
        assert cloned_artist.name == artist.name

    def test_clone_model_override_attrs(self, artist):
        attrs = {'name': 'Clone Artist name'}
        cloned_artist = artist.clone.make_clone(attrs=attrs)
        check_model_count(Artist, 2)
        assert cloned_artist.name == attrs.get('name')

    def test_clone_model_with_unique_fields(self, instrument):
        cloned_instrument = instrument.clone.make_clone(attrs={'id': uuid4()})
        check_model_count(Instrument, 2)
        assert cloned_instrument.serial_number == f'{instrument.serial_number}{1}'

    def test_clone_model__with_inheritance(self, bass_guitar: BassGuitar):
        cloned_bass = bass_guitar.clone.make_clone(
            attrs={'id': uuid4(), 'name': 'Fender', 'type': BassGuitar.Type.ACOUSTIC}
        )
        check_model_count(BassGuitar, 2)
        check_model_count(Instrument, 2)
        assert cloned_bass.instrument_ptr != bass_guitar.instrument_ptr
        assert cloned_bass.type != bass_guitar.type


@pytest.mark.django_db
class TestOneToOne:
    def test_clone_model_with_o2o_attr(self, patch_clone, passport):
        one_to_one = [Param(name='passport')]
        patch_clone(Artist, one_to_one=one_to_one)
        artist = passport.owner
        check_model_count(Artist, 1)
        check_model_count(Passport, 1)

        cloned_artist = artist.clone.make_clone()
        check_model_count(Artist, 2)
        check_model_count(Passport, 2)
        assert cloned_artist.passport != artist.passport


@pytest.mark.django_db
class TestManyToOne:
    def test_clone_model_with_m2o_attr(self, patch_clone, album):
        many_to_one = [Param(name='album_set')]
        patch_clone(Artist, many_to_one=many_to_one)

        artist = album.artist
        check_model_count(Artist, 1)
        check_model_count(Album, 1)

        cloned_artist = artist.clone.make_clone()
        check_model_count(Artist, 2)
        check_model_count(Album, 2)
        assert artist.album_set.get() != cloned_artist.album_set.get()
        assert artist.album_set.get().title == cloned_artist.album_set.get().title

    def test_clone_model_with_m2o_attr_override(self, patch_clone, album):
        many_to_one = [
            Param(
                name='album_set',
                attrs={'title': 'Override Title'}
            )
        ]

        patch_clone(Artist, many_to_one=many_to_one)

        artist = album.artist
        check_model_count(Artist, 1)
        check_model_count(Album, 1)

        cloned_artist = artist.clone.make_clone()
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

        cloned_song = song.clone.make_clone()
        check_model_count(Artist, 1)
        check_model_count(Album, 1)
        check_model_count(Song, 2)

        assert cloned_song.artist == artist
        assert cloned_song.album == album
        assert artist.song_set.count() == 2
        assert album.song_set.count() == 2

    def test_cloning_with_multiple_m2o(self, patch_clone, song):
        many_to_one = [
            Param(name='song_set'),
        ]
        patch_clone(Artist, many_to_one=many_to_one)

        artist = song.artist
        check_model_count(Artist, 1)
        check_model_count(Song, 1)

        cloned_artist = artist.clone.make_clone()
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

    def test_cloning_with_multiple_m2o__update_relations(self, patch_clone, album, song):
        many_to_one = [
            Param(name='album_set'),
            Param(name='song_set'),
        ]
        patch_clone(Artist, many_to_one=many_to_one)
        artist = album.artist
        assert artist == song.artist
        check_model_count(Artist, 1)
        check_model_count(Album, 1)
        check_model_count(Song, 1)

        cloned_artist = artist.clone.make_clone()
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

    def test_cloning_with_many_to_one__related(self, song, patch_clone):
        many_to_one = [
            Param(name='songpart_set')
        ]
        patch_clone(Song, many_to_one=many_to_one)

        intro = SongPart.objects.create(name='Intro', song=song)
        verse = SongPart.objects.create(name='Verse', song=song)
        outro = SongPart.objects.create(name='Outro', song=song)
        check_model_count(Song, 1)
        check_model_count(SongPart, 3)

        cloned_song = song.clone.make_clone()
        assert cloned_song.songpart_set.count() == 3
        check_model_count(SongPart, 6)
        assert cloned_song.songpart_set.values('pk') != song.songpart_set.values('pk')
        assert sorted(list(song.songpart_set.values_list('name', flat=True))) \
               == \
               sorted(list(cloned_song.songpart_set.values_list('name', flat=True)))


@pytest.mark.django_db
class TestManyToMany:

    def test_cloning_model_with_m2m(self, compilation, patch_clone):
        many_to_many = [
            Param(name='songs')
        ]
        patch_clone(Compilation, many_to_many=many_to_many)
        check_model_count(Compilation, 1)
        check_model_count(Song, 2)
        check_model_count(Artist, 1)
        check_model_count(Album, 1)

        cloned_compilation = compilation.clone.make_clone()

        assert cloned_compilation.songs.count() == 2
        assert compilation.songs.count() == 2

        check_model_count(Compilation, 2)
        check_model_count(Song, 2)
        check_model_count(Artist, 1)
        check_model_count(Album, 1)

#     def test_cloning_m2m_with_through_explicit(self, artist, group, patch_clone):
#         many_to_one = [
#             ManyToOneParam(
#                 name='membership_set',
#                 reverse_name='person',
#                 attrs={
#                     'invite_reason': 'Need a great bassist',
#                 },
#             )
#         ]
#         patch_clone(Artist, many_to_one=many_to_one)
#         group.members.add(artist)
#         check_model_count(Artist, 1)
#         check_model_count(Group, 1)
#         check_model_count(Membership, 1)
#         cloned_artist = artist.clone.create_child()
#         assert cloned_artist.membership_set.count() == 1
#         assert artist.membership_set.count() == 1
#         assert group.members.count() == 2
#         cloned_membership = cloned_artist.membership_set.get()
#         assert cloned_membership.invite_reason == 'Need a great bassist'
#         assert cloned_membership.group == group
#         assert cloned_membership.date_joined == artist.membership_set.get().date_joined
#         check_model_count(Artist, 2)
#         check_model_count(Group, 1)
#         check_model_count(Membership, 2)
#
#     def test_cloning_m2m_through_implicit(self, artist, group, patch_clone):
#         many_to_many = [
#             ManyToManyParam(name='group_set', reverse_name='members')
#         ]
#         patch_clone(Artist, many_to_many=many_to_many)
#         artist.group_set.add(group)
#         check_model_count(Artist, 1)
#         check_model_count(Group, 1)
#         check_model_count(Membership, 1)
#
#         cloned_artist = artist.clone.create_child()
#
#         check_model_count(Artist, 2)
#         check_model_count(Group, 1)
#         check_model_count(Membership, 2)
#         cloned_membership = cloned_artist.membership_set.get()
#         assert cloned_membership.person == cloned_artist
#         assert cloned_membership.group == artist.membership_set.get().group

