from peewee import CharField, FloatField
from .base_model import BaseModel

class Debt(BaseModel):
    name = CharField()
    total_amount = FloatField()
    current_balance = FloatField()
    minimum_payment = FloatField(default=0.0) # Añadimos un valor por defecto