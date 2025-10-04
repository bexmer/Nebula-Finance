from peewee import CharField, FloatField
from .base_model import BaseModel

class Debt(BaseModel):
    name = CharField()
    total_amount = FloatField()
    current_balance = FloatField()
    # CORRECCIÓN: El nombre del campo ahora es el correcto.
    minimum_payment = FloatField()

