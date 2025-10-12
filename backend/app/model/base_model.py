import os
from peewee import Model, SqliteDatabase

# --- DEFINICIÓN CENTRAL DE LA BASE DE DATOS ---
# Construimos una ruta explícita al archivo de la base de datos
# para que siempre sepa dónde encontrarlo.

# Esto encuentra la ruta a la carpeta 'backend'
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# Y esto crea la ruta completa al archivo de la base de datos
DB_PATH = os.path.join(BACKEND_DIR, 'finanzas.db')

# Usamos la ruta explícita
db = SqliteDatabase(DB_PATH)

class BaseModel(Model):
    """
    Un modelo base que especifica la base de datos para todos los demás modelos.
    """
    class Meta:
        database = db