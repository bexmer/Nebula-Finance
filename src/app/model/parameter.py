from peewee import CharField, BooleanField, ForeignKeyField
from .base_model import BaseModel
from .budget_rule import BudgetRule # <-- AÑADIR ESTA LÍNEA

class Parameter(BaseModel):
    """
    Representa un parámetro personalizable del sistema.
    """
    group = CharField()
    value = CharField()
    is_deletable = BooleanField(default=True)
    # --- CAMBIO: De CharField a ForeignKeyField ---
    budget_rule = ForeignKeyField(BudgetRule, backref='parameters', null=True, on_delete='SET NULL')