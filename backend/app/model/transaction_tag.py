from peewee import ForeignKeyField, UniqueConstraint

from .base_model import BaseModel
from .tag import Tag
from .transaction import Transaction


class TransactionTag(BaseModel):
    """Relación muchos a muchos entre transacciones y etiquetas."""

    transaction = ForeignKeyField(
        Transaction,
        backref="tag_links",
        on_delete="CASCADE",
    )
    tag = ForeignKeyField(
        Tag,
        backref="transaction_links",
        on_delete="CASCADE",
    )

    class Meta:
        constraints = [UniqueConstraint("transaction", "tag")]
