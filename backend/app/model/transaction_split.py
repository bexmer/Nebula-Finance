from peewee import CharField, FloatField, ForeignKeyField

from .base_model import BaseModel
from .transaction import Transaction


class TransactionSplit(BaseModel):
    """Detalle de categorías para transacciones divididas."""

    transaction = ForeignKeyField(
        Transaction,
        backref="splits",
        on_delete="CASCADE",
    )
    category = CharField()
    amount = FloatField()
