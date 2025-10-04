from peewee import Model, SqliteDatabase

db = SqliteDatabase('finanzas.db')

class BaseModel(Model):
    class Meta:
        database = db