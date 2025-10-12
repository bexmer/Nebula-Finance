# --- IMPORTACIONES ---
# Importamos el objeto 'db' desde el base_model, como en tu estructura original.
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
from peewee import OperationalError

# Lista de todos los modelos que la base de datos debe conocer
MODELS = [
    Transaction, Goal, Debt, BudgetEntry, PortfolioAsset, Trade,
    RecurringTransaction, Account, Parameter, BudgetRule
]

# =================================================================
# --- SECCIÓN: SEMBRADO DE DATOS INICIALES (Tu Lógica) ---
# =================================================================

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
    """Crea los parámetros iniciales con la jerarquía de Tipo -> Categoría."""
    if Parameter.select().count() == 0:
        # Obtenemos las reglas de presupuesto para vincularlas
        esenciales = BudgetRule.get_or_none(BudgetRule.name == 'Esenciales')
        recompensas = BudgetRule.get_or_none(BudgetRule.name == 'Recompensas')
        crecimiento = BudgetRule.get_or_none(BudgetRule.name == 'Crecimiento')
        estabilidad = BudgetRule.get_or_none(BudgetRule.name == 'Estabilidad')

        # 1. Tipos de Transacción (Padres)
        ingreso = Parameter.create(group='Tipo de Transacción', value='Ingreso', is_deletable=False)
        gasto_fijo = Parameter.create(group='Tipo de Transacción', value='Gasto Fijo', is_deletable=False, budget_rule=esenciales)
        gasto_variable = Parameter.create(group='Tipo de Transacción', value='Gasto Variable', is_deletable=False, budget_rule=recompensas)
        ahorro_meta = Parameter.create(group='Tipo de Transacción', value='Ahorro Meta', is_deletable=False, budget_rule=crecimiento)
        pago_deuda = Parameter.create(group='Tipo de Transacción', value='Pago Deuda', is_deletable=False, budget_rule=estabilidad)

        # 2. Categorías (Hijos)
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

        # 3. Tipos de Cuenta
        Parameter.create(group='Tipo de Cuenta', value='Cuenta de Ahorros')
        Parameter.create(group='Tipo de Cuenta', value='Cuenta Corriente')
        Parameter.create(group='Tipo de Cuenta', value='Tarjeta de Crédito')
        Parameter.create(group='Tipo de Cuenta', value='Efectivo')
        
        print("Initial parameters seeded with parent-child relationships.")

# =================================================================
# --- SECCIÓN: MANEJO DE LA BASE DE DATOS ---
# =================================================================

def initialize_database():
    """
    Conecta a la BD, crea las tablas y siembra los datos iniciales.
    Se llama una sola vez al iniciar el servidor.
    """
    try:
        if db.is_closed():
            db.connect()
            print("Database connection opened.")
        
        db.create_tables(MODELS, safe=True)
        print("Tables created successfully (if they didn't exist).")

        # Llamamos a tus funciones de sembrado
        seed_initial_budget_rules()
        seed_initial_parameters()
        
        print("Database initialization complete.")

    except OperationalError as e:
        print(f"Database operational error during initialization: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during database initialization: {e}")

def close_db():
    """
    Cierra la conexión a la base de datos.
    Se llama una sola vez cuando el servidor se detiene.
    """
    if not db.is_closed():
        db.close()
        print("Database connection closed.")