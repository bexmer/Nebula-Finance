from peewee import BooleanField, CharField, DateField, FloatField, ForeignKeyField

from .base_model import BaseModel
from .budget_entry import BudgetEntry
from .portfolio_asset import PortfolioAsset
from .transaction import Transaction

class Trade(BaseModel):
    """
    Representa una operación individual de compra o venta de un activo.
    """
    asset = ForeignKeyField(PortfolioAsset, backref='trades')
    trade_type = CharField()  # 'Compra' o 'Venta'
    quantity = FloatField()
    price_per_unit = FloatField()
    date = DateField()
    linked_transaction = ForeignKeyField(
        Transaction,
        null=True,
        backref="portfolio_trades",
        column_name="linked_transaction_id",
        on_delete="SET NULL",
    )
    linked_budget_entry = ForeignKeyField(
        BudgetEntry,
        null=True,
        backref="portfolio_trades",
        column_name="linked_budget_entry_id",
        on_delete="SET NULL",
    )
    is_planned = BooleanField(default=False)
