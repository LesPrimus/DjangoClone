# Generated by Django 3.1.4 on 2020-12-18 10:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_clone_helper', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Passport',
            fields=[
                ('owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='django_clone_helper.artist')),
            ],
        ),
    ]
