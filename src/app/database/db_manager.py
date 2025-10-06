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
from app.model.budget_rule import BudgetRule # <-- AÑADIR ESTA LÍNEA

def seed_initial_budget_rules():
    """Crea las reglas de presupuesto iniciales si no existen."""
    if BudgetRule.select().count() == 0:
        rules = [
            {'name': 'Esenciales', 'percentage': 50.0},
            {'name': 'Crecimiento', 'percentage': 20.0},
            {'name': 'Estabilidad', 'percentage': 15.0},
            {'name': 'Recompensas', 'percentage': 15.0},
        ]
        BudgetRule.insert_many(rules).execute()
        print("Initial budget rules seeded.")

def seed_initial_parameters():
    """
    Crea los parámetros iniciales y esenciales si no existen.
    """
    if Parameter.select().count() == 0:
        # Asigna las reglas por su nombre
        esenciales = BudgetRule.get_or_none(BudgetRule.name == 'Esenciales')
        recompensas = BudgetRule.get_or_none(BudgetRule.name == 'Recompensas')
        crecimiento = BudgetRule.get_or_none(BudgetRule.name == 'Crecimiento')
        estabilidad = BudgetRule.get_or_none(BudgetRule.name == 'Estabilidad')

        core_parameters = [
            {'group': 'Tipo de Transacción', 'value': 'Ingreso', 'is_deletable': False, 'budget_rule': None},
            {'group': 'Tipo de Transacción', 'value': 'Gasto Fijo', 'is_deletable': False, 'budget_rule': esenciales},
            {'group': 'Tipo de Transacción', 'value': 'Gasto Variable', 'is_deletable': False, 'budget_rule': recompensas},
            {'group': 'Tipo de Transacción', 'value': 'Ahorro Meta', 'is_deletable': False, 'budget_rule': crecimiento},
            {'group': 'Tipo de Transacción', 'value': 'Pago Deuda', 'is_deletable': False, 'budget_rule': estabilidad},
            {'group': 'Categoría', 'value': 'Nómina', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Comida', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Transporte', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Vivienda', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Ocio', 'is_deletable': True},
            {'group': 'Categoría', 'value': 'Salud', 'is_deletable': True},
            {'group': 'Tipo de Cuenta', 'value': 'Cuenta de Ahorros', 'is_deletable': True},
            {'group': 'Tipo de Cuenta', 'value': 'Cuenta Corriente', 'is_deletable': True},
            {'group': 'Tipo de Cuenta', 'value': 'Tarjeta de Crédito', 'is_deletable': True},
            {'group': 'Tipo de Cuenta', 'value': 'Efectivo', 'is_deletable': True},
        ]
        Parameter.insert_many(core_parameters).execute()
        print("Initial parameters seeded.")

def initialize_database():
    db.connect()
    db.create_tables([
        Transaction, Goal, Debt, BudgetEntry,
        PortfolioAsset, Trade, RecurringTransaction, Account,
        Parameter, BudgetRule # <-- AÑADIR ESTA LÍNEA
    ], safe=True)
    # Se siembran primero las reglas para que los parámetros puedan usarlas
    seed_initial_budget_rules()
    seed_initial_parameters()
    print("Database initialized and tables created if they didn't exist.")