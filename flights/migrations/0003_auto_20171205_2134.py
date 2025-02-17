# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-05 21:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flights', '0002_auto_20171121_1908'),
    ]

    operations = [
        migrations.CreateModel(
            name='Flight',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(blank=True, help_text='YYYY-MM-DD', null=True)),
                ('number', models.CharField(blank=True, max_length=10)),
                ('airline', models.CharField(blank=True, max_length=100)),
                ('aircraft', models.CharField(blank=True, max_length=100)),
                ('aircraft_registration', models.CharField(blank=True, max_length=10)),
                ('distance', models.FloatField(default=-1)),
                ('travel_class', models.CharField(blank=True, max_length=100)),
                ('seat', models.CharField(blank=True, max_length=10)),
                ('operator', models.CharField(blank=True, max_length=100)),
                ('comments', models.TextField(blank=True, max_length=10000)),
                ('sortid', models.IntegerField()),
                ('picture', models.ImageField(blank=True, upload_to='flights/user_pics')),
            ],
        ),
        migrations.AlterField(
            model_name='airport',
            name='country_iso',
            field=models.CharField(help_text='ISO 3166-1 alpha-2', max_length=100, verbose_name='Country code'),
        ),
        migrations.AlterField(
            model_name='airport',
            name='iata',
            field=models.CharField(blank=True, max_length=3, verbose_name='IATA'),
        ),
        migrations.AlterField(
            model_name='airport',
            name='icao',
            field=models.CharField(blank=True, max_length=4, verbose_name='ICAO'),
        ),
        migrations.AlterField(
            model_name='airport',
            name='region_iso',
            field=models.CharField(blank=True, help_text='ISO 3166-2', max_length=10, verbose_name='Region code'),
        ),
        migrations.AddField(
            model_name='flight',
            name='destination',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='destinations', to='flights.Airport'),
        ),
        migrations.AddField(
            model_name='flight',
            name='origin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='origins', to='flights.Airport'),
        ),
        migrations.AddField(
            model_name='flight',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
