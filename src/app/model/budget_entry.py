from peewee import CharField, FloatField
from .base_model import BaseModel

class BudgetEntry(BaseModel):
    """
    Representa una entrada de presupuesto mensual planeada,
    ya sea un ingreso o un gasto recurrente.
    """
    description = CharField()
    category = CharField()
    type = CharField()  # 'Ingreso Planeado' o 'Gasto Planeado'
    budgeted_amount = FloatField()
