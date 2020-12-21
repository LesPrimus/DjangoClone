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
based on the clone(CloneHandler) configurations.

    artist = Artist.objects.get()
    artist.clone.make_child()
---
To-Do add more examples