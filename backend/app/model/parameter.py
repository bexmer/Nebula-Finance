from peewee import CharField, BooleanField, ForeignKeyField, TextField
from .base_model import BaseModel
from .budget_rule import BudgetRule

class Parameter(BaseModel):
    group = CharField()
    value = CharField()
    is_deletable = BooleanField(default=True)
    budget_rule = ForeignKeyField(BudgetRule, backref='parameters', null=True, on_delete='SET NULL')
    parent = ForeignKeyField('self', backref='children', null=True, on_delete='CASCADE')
    extra_data = TextField(null=True) 