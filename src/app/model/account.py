from peewee import CharField, FloatField
from .base_model import BaseModel

class Account(BaseModel):
    """
    Representa una cuenta financiera del usuario (ej. cuenta bancaria, tarjeta de crédito, efectivo).
    """
    name = CharField()
    account_type = CharField() # Ej: 'Cuenta de Ahorros', 'Tarjeta de Crédito', 'Efectivo'
    initial_balance = FloatField(default=0.0)
    current_balance = FloatField(default=0.0)