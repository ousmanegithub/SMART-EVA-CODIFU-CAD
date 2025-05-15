from rest_framework import serializers
from .models import Parcelle

class ParcelleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parcelle
        fields = '__all__'
