from django.db import models
from django.contrib.gis.db import models

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from django.contrib.gis.db import models

class Parcelle(models.Model):
    code_bdn = models.CharField(max_length=100, null=True, blank=True)
    geometry = models.GeometryField()
    nom = models.CharField(max_length=255, null=True, blank=True)
    theme = models.CharField(max_length=100, null=True, blank=True)
    pays = models.CharField(max_length=100, null=True, blank=True)
    iduu = models.CharField(max_length=100, null=True, blank=True)
    sum_superf = models.FloatField(null=True, blank=True)
    shape_leng = models.FloatField(null=True, blank=True)
    shape_area = models.FloatField(null=True, blank=True)
    properties = models.JSONField(null=True, blank=True)  # Utilisez la version moderne de JSONField

    def __str__(self):
        return f"Parcelle {self.nom} ({self.code_bdn})"

from django.db import models

class TaskStatus(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default='en cours')
    progress = models.IntegerField(default=0)
    message = models.TextField(blank=True)

# Create your models here.
