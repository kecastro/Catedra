# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-08 17:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qr', '0003_estudiante_monitor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='estudiante',
            name='cursos',
            field=models.ManyToManyField(null=True, to='qr.Curso'),
        ),
    ]
