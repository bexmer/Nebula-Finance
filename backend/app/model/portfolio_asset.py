from peewee import CharField, FloatField
from .base_model import BaseModel

class PortfolioAsset(BaseModel):
    """
    Representa el resumen de un activo en el portafolio.
    """
    symbol = CharField(unique=True) # ej: BTC, AAPL
    asset_type = CharField() # ej: Criptomoneda, Acción
    total_quantity = FloatField(default=0.0)
    avg_cost_price = FloatField(default=0.0)
    current_price = FloatField(default=0.0)

