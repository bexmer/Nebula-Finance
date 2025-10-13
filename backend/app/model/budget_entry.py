import datetime

from peewee import CharField, DateField, FloatField, ForeignKeyField

from .base_model import BaseModel
from .debt import Debt
from .goal import Goal


class BudgetEntry(BaseModel):
    """Representa una entrada de presupuesto mensual planeada."""

    description = CharField()
    category = CharField()
    type = CharField()
    budgeted_amount = FloatField()
    due_date = DateField(default=datetime.date.today)
    goal = ForeignKeyField(Goal, backref="budget_entries", null=True)
    debt = ForeignKeyField(Debt, backref="budget_entries", null=True)