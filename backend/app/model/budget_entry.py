import datetime

import datetime

from peewee import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    ForeignKeyField,
)

from .base_model import BaseModel
from .debt import Debt
from .goal import Goal


class BudgetEntry(BaseModel):
    """Representa una entrada de presupuesto mensual planeada."""

    description = CharField()
    category = CharField()
    type = CharField()
    frequency = CharField(default="Mensual")
    budgeted_amount = FloatField()
    start_date = DateField(default=datetime.date.today)
    end_date = DateField(null=True)
    due_date = DateField(default=datetime.date.today)
    use_custom_schedule = BooleanField(default=False)
    is_recurring = BooleanField(default=False)
    actual_amount = FloatField(default=0.0)
    goal = ForeignKeyField(Goal, backref="budget_entries", null=True)
    debt = ForeignKeyField(Debt, backref="budget_entries", null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
