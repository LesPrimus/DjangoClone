# Django Clone Handler

Create clone of Django models with customizable behaviour.

---

Add a clone (class) to a model.

    class Artist(models.Model):
        name = models.CharField(max_length=100)

        class clone(CloneHandler):

            many_to_one = [
                ManyToOneParam(
                    name='album_set', 
                    reverse_name='artist', 
                    attrs={'title': 'cloned album title'}
                ),

                ManyToOneParam(
                    name='song_set', 
                    reverse_name='artist', 
                    attrs={'title': 'cloned song title'}
                ),
            ]

            one_to_one = [
                OneToOneParam(
                    name='passport', reverse_name='owner'
                ),
            ]


        def __str__(self):
            return self.name

---
Call the create_child method to clone the instance and related ManyToOne, ManyToMany, etc..
based on the CloneHandler subclass configurations.

    artist = Artist.objects.get()

    artist.clone.make_child()
---
or pass ManyToOneParam, OneToOneParam etc. as  arguments to instance.create_child

---
    m2o_param = ManyToOneParam(name='album_set', reverse_name='artist',attrs={'title': 'cloned album title'})

    artist.clone.make_child(many_to_one=[m2o_param])
---
