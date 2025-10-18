import datetime

from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField

from .base_model import BaseModel
from .budget_entry import BudgetEntry
from .transaction import Transaction


class Receipt(BaseModel):
    """Stores uploaded receipt images linked to transactions or budgets."""

    transaction = ForeignKeyField(
        Transaction,
        backref="receipts",
        null=True,
        column_name="transaction_id",
    )
    budget_entry = ForeignKeyField(
        BudgetEntry,
        backref="receipts",
        null=True,
        column_name="budget_entry_id",
    )
    file_path = CharField(unique=True)
    original_filename = CharField()
    content_type = CharField(null=True)
    file_size = IntegerField(null=True)
    uploaded_at = DateTimeField(default=datetime.datetime.utcnow)
