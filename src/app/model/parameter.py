from peewee import CharField, BooleanField
from .base_model import BaseModel

class Parameter(BaseModel):
    """
    Representa un parámetro personalizable del sistema.
    """
    group = CharField()
    value = CharField()
    is_deletable = BooleanField(default=True)
    budget_rule = CharField(null=True) # Nuevo campo para la regla de presupuesto