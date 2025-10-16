from peewee import (
    BooleanField,
    CharField,
    DateField,
    FloatField,
    ForeignKeyField,
    TextField,
)

from .account import Account
from .base_model import BaseModel
from .budget_entry import BudgetEntry
from .debt import Debt
from .goal import Goal


class Transaction(BaseModel):
    """Modelo principal de transacciones financieras."""

    account = ForeignKeyField(Account, backref="transactions")
    date = DateField()
    description = TextField()
    amount = FloatField()
    type = CharField()
    category = CharField()

    goal = ForeignKeyField(Goal, backref="transactions", null=True)
    debt = ForeignKeyField(Debt, backref="transactions", null=True)
    budget_entry = ForeignKeyField(
        BudgetEntry,
        backref="transactions",
        null=True,
        column_name="budget_entry_id",
    )
    is_transfer = BooleanField(default=False)
    transfer_account = ForeignKeyField(
        Account,
        backref="incoming_transfers",
        null=True,
        column_name="transfer_account_id",
    )
