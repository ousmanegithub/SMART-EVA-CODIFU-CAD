import pandas as pd
import pyarrow.parquet as pq

# Créer un DataFrame de test
data = {'col1': [1, 2], 'col2': [3, 4]}
df = pd.DataFrame(data)

# Écrire en Parquet
df.to_parquet("test.parquet", engine="pyarrow")
print("Fichier Parquet créé avec succès.")

# Lire depuis le fichier Parquet
read_df = pd.read_parquet("test.parquet", engine="pyarrow")
print("Données lues depuis le fichier Parquet :", read_df)
from django.test import TestCase

# Create your tests here.
