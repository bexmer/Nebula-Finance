from peewee import CharField, BooleanField, FloatField
from .base_model import BaseModel

class Parameter(BaseModel):
    """
    Representa un parámetro personalizable del sistema.
    """
    group = CharField()
    value = CharField()
    is_deletable = BooleanField(default=True)
    budget_rule = CharField(null=True) 
    numeric_value = FloatField(null=True)
