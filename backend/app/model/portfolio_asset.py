from peewee import CharField, FloatField, ForeignKeyField
from .base_model import BaseModel
from .account import Account
from .goal import Goal

class PortfolioAsset(BaseModel):
    """
    Representa el resumen de un activo en el portafolio.
    """
    symbol = CharField(unique=True) # ej: BTC, AAPL
    asset_type = CharField() # ej: Criptomoneda, Acción
    total_quantity = FloatField(default=0.0)
    avg_cost_price = FloatField(default=0.0)
    current_price = FloatField(default=0.0)
    annual_yield_rate = FloatField(default=0.0)
    linked_account = ForeignKeyField(
        Account,
        null=True,
        backref="portfolio_assets",
        on_delete="SET NULL",
    )
    linked_goal = ForeignKeyField(
        Goal,
        null=True,
        backref="portfolio_assets",
        on_delete="SET NULL",
    )

