# Django Clone Handler

Create clone of Django models with customizable behaviour.

---

Add a clone (class) to a model.

    class Artist(models.Model):
        name = models.CharField(max_length=100)

        class clone(CloneHandler):

            many_to_one = [
                Param(
                    name='album_set',
                    attrs={'title': 'cloned album title'}
                ),

                Param(
                    name='song_set',
                    attrs={'title': 'cloned song title'}
                ),
            ]

            one_to_one = [
                Param(
                    name='passport'
                ),
            ]


        def __str__(self):
            return self.name

---
Call the make_clone method to clone the instance and related ManyToOne, ManyToMany, etc..
based on the CloneHandler subclass configurations.

    artist = Artist.objects.get()

    artist.clone.make_clone()
---
or pass Param class instances as  arguments to instance.create_child

---
    m2o_param = Param(name='album_set', attrs={'title': 'cloned album title'})

    artist.clone.make_clone(many_to_one=[m2o_param])
---
