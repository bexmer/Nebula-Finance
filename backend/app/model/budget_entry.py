from peewee import CharField, FloatField, DateField
from .base_model import BaseModel
import datetime

class BudgetEntry(BaseModel):
    """
    Representa una entrada de presupuesto mensual planeada.
    """
    description = CharField()
    category = CharField()
    type = CharField()
    budgeted_amount = FloatField()
    due_date = DateField(default=datetime.date.today)