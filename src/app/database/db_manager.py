from app.model.base_model import db
from app.model.transaction import Transaction
from app.model.goal import Goal
from app.model.debt import Debt
from app.model.budget_entry import BudgetEntry
from app.model.portfolio_asset import PortfolioAsset
from app.model.trade import Trade
from app.model.recurring_transaction import RecurringTransaction
from app.model.account import Account
from app.model.parameter import Parameter

def seed_initial_parameters():
    """
    Crea los parámetros iniciales y esenciales si no existen.
    """
    if Parameter.select().count() == 0:
        core_parameters = [
            # Tipos de Transacción con su regla de presupuesto asignada
            {'group': 'Tipo de Transacción', 'value': 'Ingreso', 'is_deletable': False, 'budget_rule': None},
            {'group': 'Tipo de Transacción', 'value': 'Gasto Fijo', 'is_deletable': False, 'budget_rule': 'Esenciales'},
            {'group': 'Tipo de Transacción', 'value': 'Gasto Variable', 'is_deletable': False, 'budget_rule': 'Recompensas'},
            {'group': 'Tipo de Transacción', 'value': 'Ahorro Meta', 'is_deletable': False, 'budget_rule': 'Crecimiento'},
            {'group': 'Tipo de Transacción', 'value': 'Pago Deuda', 'is_deletable': False, 'budget_rule': 'Estabilidad'},

            # Categorías
            {'group': 'Categoría', 'value': 'Nómina', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Comida', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Transporte', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Vivienda', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Ocio', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Salud', 'is_deletable': True},

            # Tipos de Cuenta
            {'group': 'Tipo de Cuenta', 'value': 'Cuenta de Ahorros', 'is_deletable': True},
            {'group': 'Tipo de Cuenta', 'value': 'Cuenta Corriente', 'is_deletable': True},
            {'group': 'Tipo de Cuenta', 'value': 'Tarjeta de Crédito', 'is_deletable': True},
            {'group': 'Tipo de Cuenta', 'value': 'Efectivo', 'is_deletable': True},

            # Reglas de Presupuesto
            {'group': 'Regla de Presupuesto', 'value': 'Esenciales', 'is_deletable': True, 'numeric_value': 0.50},
            {'group': 'Regla de Presupuesto', 'value': 'Crecimiento', 'is_deletable': True, 'numeric_value': 0.20},
            {'group': 'Regla de Presupuesto', 'value': 'Estabilidad', 'is_deletable': True, 'numeric_value': 0.15},
            {'group': 'Regla de Presupuesto', 'value': 'Recompensas', 'is_deletable': True, 'numeric_value': 0.15},
        ]
        Parameter.insert_many(core_parameters).execute()
        print("Initial parameters seeded.")

def initialize_database():
    db.connect()
    db.create_tables([
        Transaction, Goal, Debt, BudgetEntry,
        PortfolioAsset, Trade, RecurringTransaction, Account,
        Parameter
    ], safe=True)
    seed_initial_parameters()
    print("Database initialized and tables created if they didn't exist.")
