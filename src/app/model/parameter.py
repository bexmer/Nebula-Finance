from peewee import CharField, BooleanField, ForeignKeyField
from .base_model import BaseModel
from .budget_rule import BudgetRule

class Parameter(BaseModel):
    """
    Representa un parámetro personalizable del sistema.
    """
    group = CharField()
    value = CharField()
    is_deletable = BooleanField(default=True)
    budget_rule = ForeignKeyField(BudgetRule, backref='parameters', null=True, on_delete='SET NULL')
    
    # --- INICIO DE LA SOLUCIÓN ---
    # Añadimos una relación de padre para vincular categorías a tipos.
    # on_delete='CASCADE' significa que si se borra un Tipo, se borrarán sus categorías hijas.
    parent = ForeignKeyField('self', backref='children', null=True, on_delete='CASCADE')
    # --- FIN DE LA SOLUCIÓN ---