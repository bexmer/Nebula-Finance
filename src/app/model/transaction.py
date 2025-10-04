from peewee import CharField, DateField, FloatField, TextField, ForeignKeyField
from .base_model import BaseModel
from .goal import Goal
from .debt import Debt
# --- INICIO DE LA MODIFICACIÓN ---
from .account import Account
# --- FIN DE LA MODIFICACIÓN ---

class Transaction(BaseModel):
    """
    Representa una única transacción financiera en la base de datos.
    Está vinculada a las tablas de metas y deudas.
    """
    # --- INICIO DE LA MODIFICACIÓN ---
    account = ForeignKeyField(Account, backref='transactions')
    # --- FIN DE LA MODIFICACIÓN ---
    date = DateField()
    description = TextField()
    amount = FloatField()
    type = CharField()
    category = CharField()
    
    goal = ForeignKeyField(Goal, backref='transactions', null=True)
    debt = ForeignKeyField(Debt, backref='transactions', null=True)