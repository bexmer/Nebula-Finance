from peewee import CharField, FloatField, DateField, ForeignKeyField
from .base_model import BaseModel
from .portfolio_asset import PortfolioAsset

class Trade(BaseModel):
    """
    Representa una operación individual de compra o venta de un activo.
    """
    asset = ForeignKeyField(PortfolioAsset, backref='trades')
    trade_type = CharField() # 'Compra' o 'Venta'
    quantity = FloatField()
    price_per_unit = FloatField()
    date = DateField()
