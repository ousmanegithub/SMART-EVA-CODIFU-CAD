# Generated by Django 5.1.3 on 2024-12-04 13:14

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Parcelle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('geometry', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                ('region', models.CharField(max_length=100)),
                ('code_bdn', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('area', models.FloatField()),
                ('historique', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
