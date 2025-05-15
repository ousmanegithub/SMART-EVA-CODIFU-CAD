from django import forms

class GeoJSONUploadForm(forms.Form):
    file = forms.FileField(label="Téléverser un fichier GeoJSON")
class GenerateBDNForm(forms.Form):
    # Ce formulaire n'a pas de champs spécifiques, il est juste utilisé pour envoyer une requête POST
    pass

class GeospatialUploadForm(forms.Form):
    file = forms.FileField(label="Téléverser un fichier géospatial (GeoJSON, Shapefile, etc.)")