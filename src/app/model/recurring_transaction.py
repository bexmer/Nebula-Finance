from peewee import CharField, FloatField, IntegerField, DateField
from .base_model import BaseModel

class RecurringTransaction(BaseModel):
    """
    Representa una regla para una transacción recurrente (ej. sueldo, suscripciones).
    """
    description = CharField()
    amount = FloatField()
    type = CharField()
    category = CharField()
    frequency = CharField() # 'Mensual', 'Quincenal', 'Anual'
    day_of_month = IntegerField()
    day_of_month_2 = IntegerField(null=True) # Para el segundo día de la quincena
    month_of_year = IntegerField(null=True) # Para pagos anuales
    start_date = DateField()
    last_processed_date = DateField(null=True)