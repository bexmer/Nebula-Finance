from peewee import CharField, FloatField
from .base_model import BaseModel

class Debt(BaseModel):
    name = CharField()
    total_amount = FloatField()
    current_balance = FloatField()
    minimum_payment = FloatField(default=0.0)
    
    # --- INICIO DE LA SOLUCIÓN ---
    # Añadimos la tasa de interés anual (ej. 15.5 para 15.5%)
    interest_rate = FloatField(default=0.0)
    # --- FIN DE LA SOLUCIÓN ---