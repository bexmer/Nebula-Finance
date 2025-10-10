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
from app.model.budget_rule import BudgetRule

def seed_initial_budget_rules():
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
    Crea los parámetros iniciales con la nueva jerarquía de Tipo -> Categoría.
    """
    if Parameter.select().count() == 0:
        esenciales = BudgetRule.get_or_none(BudgetRule.name == 'Esenciales')
        recompensas = BudgetRule.get_or_none(BudgetRule.name == 'Recompensas')
        crecimiento = BudgetRule.get_or_none(BudgetRule.name == 'Crecimiento')
        estabilidad = BudgetRule.get_or_none(BudgetRule.name == 'Estabilidad')

        # 1. Creamos los Tipos de Transacción (los 'padres')
        ingreso = Parameter.create(group='Tipo de Transacción', value='Ingreso', is_deletable=False)
        gasto_fijo = Parameter.create(group='Tipo de Transacción', value='Gasto Fijo', is_deletable=False, budget_rule=esenciales)
        gasto_variable = Parameter.create(group='Tipo de Transacción', value='Gasto Variable', is_deletable=False, budget_rule=recompensas)
        ahorro_meta = Parameter.create(group='Tipo de Transacción', value='Ahorro Meta', is_deletable=False, budget_rule=crecimiento)
        pago_deuda = Parameter.create(group='Tipo de Transacción', value='Pago Deuda', is_deletable=False, budget_rule=estabilidad)

        # 2. Creamos las Categorías (los 'hijos') y las vinculamos a su padre
        Parameter.create(group='Categoría', value='Nómina', parent=ingreso)
        Parameter.create(group='Categoría', value='Freelance', parent=ingreso)
        Parameter.create(group='Categoría', value='Otros Ingresos', parent=ingreso)
        
        Parameter.create(group='Categoría', value='Vivienda', parent=gasto_fijo)
        Parameter.create(group='Categoría', value='Servicios', parent=gasto_fijo)
        
        Parameter.create(group='Categoría', value='Transporte', parent=gasto_variable)
        Parameter.create(group='Categoría', value='Comida', parent=gasto_variable)
        Parameter.create(group='Categoría', value='Ocio', parent=gasto_variable)
        Parameter.create(group='Categoría', value='Salud', parent=gasto_variable)
        Parameter.create(group='Categoría', value='Educación', parent=gasto_variable)
        Parameter.create(group='Categoría', value='Otros Gastos', parent=gasto_variable)

        # 3. Tipos de cuenta no tienen padre
        Parameter.create(group='Tipo de Cuenta', value='Cuenta de Ahorros')
        Parameter.create(group='Tipo de Cuenta', value='Cuenta Corriente')
        Parameter.create(group='Tipo de Cuenta', value='Tarjeta de Crédito')
        Parameter.create(group='Tipo de Cuenta', value='Efectivo')
        
        print("Initial parameters seeded with parent-child relationships.")

def initialize_database():
    db.connect()
    db.create_tables([
        Transaction, Goal, Debt, BudgetEntry,
        PortfolioAsset, Trade, RecurringTransaction, Account,
        Parameter, BudgetRule
    ], safe=True)
    seed_initial_budget_rules()
    seed_initial_parameters()
    print("Database initialized and tables created if they didn't exist.")