# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-16 20:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Airport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iata', models.CharField(blank=True, max_length=3)),
                ('icao', models.CharField(blank=True, max_length=4)),
                ('name', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('elevation', models.FloatField()),
                ('opened', models.DateField(blank=True, help_text='YYYY-MM-DD', null=True)),
                ('closed', models.DateField(blank=True, help_text='YYYY-MM-DD', null=True)),
            ],
        ),
    ]
