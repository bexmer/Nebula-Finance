from peewee import CharField, FloatField
from .base_model import BaseModel

class Goal(BaseModel):
    """
    Representa una meta financiera en la base de datos.
    """
    name = CharField()
    target_amount = FloatField()
    current_amount = FloatField(default=0.0)

