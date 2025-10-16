import os
from peewee import Model, SqliteDatabase

# --- DEFINICIÓN CENTRAL DE LA BASE DE DATOS ---
# Construimos una ruta explícita al archivo de la base de datos
# para que siempre sepa dónde encontrarlo.

# Esto encuentra la ruta a la carpeta 'backend'
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# Y esto crea la ruta completa al archivo de la base de datos
DB_PATH = os.path.join(BACKEND_DIR, 'finanzas.db')

# Usamos la ruta explícita y configuramos la base de datos con parámetros que
# reduzcan los bloqueos de escritura típicos de SQLite cuando se maneja desde
# múltiples hilos (como FastAPI ejecutándose con varios workers).  El modo WAL
# permite lecturas concurrentes mientras se realizan escrituras y el timeout
# extendido da margen a que una operación termine antes de disparar un error
# `database is locked`.
db = SqliteDatabase(
    DB_PATH,
    pragmas={
        "journal_mode": "wal",
        "foreign_keys": 1,
        "cache_size": -64_000,
        "synchronous": 0,
    },
    timeout=15,
    check_same_thread=False,
)

class BaseModel(Model):
    """
    Un modelo base que especifica la base de datos para todos los demás modelos.
    """
    class Meta:
        database = db