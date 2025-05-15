from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Parcelle

@admin.register(Parcelle)
class ParcelleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_bdn', 'theme', 'pays', 'sum_superf')
    search_fields = ('nom', 'code_bdn', 'theme', 'pays')
