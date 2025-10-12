from peewee import CharField, FloatField
from .base_model import BaseModel

class BudgetRule(BaseModel):
    """
    Representa una regla de presupuesto con su nombre y porcentaje.
    Ej: 'Esenciales', 50.0
    """
    name = CharField(unique=True)
    percentage = FloatField(default=0.0)