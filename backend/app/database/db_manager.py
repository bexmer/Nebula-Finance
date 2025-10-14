"""Helpers for initializing and seeding the application database."""

from peewee import OperationalError

from app.model.account import Account
from app.model.base_model import db
from app.model.budget_entry import BudgetEntry
from app.model.budget_rule import BudgetRule
from app.model.debt import Debt
from app.model.goal import Goal
from app.model.parameter import Parameter
from app.model.portfolio_asset import PortfolioAsset
from app.model.recurring_transaction import RecurringTransaction
from app.model.tag import Tag
from app.model.trade import Trade
from app.model.transaction import Transaction
from app.model.transaction_split import TransactionSplit
from app.model.transaction_tag import TransactionTag

# Every model that requires a table created on startup.
MODELS = [
    Transaction,
    Tag,
    TransactionSplit,
    TransactionTag,
    Goal,
    Debt,
    BudgetEntry,
    PortfolioAsset,
    Trade,
    RecurringTransaction,
    Account,
    Parameter,
    BudgetRule,
]


def _existing_columns(table_name: str) -> set[str]:
    """Return the existing column names for a given table."""

    try:
        return {column.name for column in db.get_columns(table_name)}
    except OperationalError:
        return set()


def ensure_transaction_enhancements() -> None:
    """Add new transaction columns required for transfers if missing."""

    table_name = Transaction._meta.table_name
    existing_columns = _existing_columns(table_name)

    if "is_transfer" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN is_transfer INTEGER DEFAULT 0'
        )

    if "transfer_account_id" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN transfer_account_id INTEGER'
        )


def ensure_budget_entry_links() -> None:
    """Ensure budget entries can optionally reference a goal or debt."""

    table_name = BudgetEntry._meta.table_name
    existing_columns = _existing_columns(table_name)

    if "goal_id" not in existing_columns:
        db.execute_sql(f'ALTER TABLE "{table_name}" ADD COLUMN goal_id INTEGER')

    if "debt_id" not in existing_columns:
        db.execute_sql(f'ALTER TABLE "{table_name}" ADD COLUMN debt_id INTEGER')


def seed_initial_budget_rules() -> None:
    """Create the default budget rules if the table is empty."""

    if BudgetRule.select().count() != 0:
        return

    rules = [
        {"name": "Esenciales", "percentage": 50.0},
        {"name": "Crecimiento", "percentage": 20.0},
        {"name": "Estabilidad", "percentage": 15.0},
        {"name": "Recompensas", "percentage": 15.0},
    ]
    BudgetRule.insert_many(rules).execute()
    print("Initial budget rules seeded.")


def seed_initial_parameters() -> None:
    """Create the default transaction types, categories, and account types."""

    if Parameter.select().count() != 0:
        return

    esenciales = BudgetRule.get_or_none(BudgetRule.name == "Esenciales")
    recompensas = BudgetRule.get_or_none(BudgetRule.name == "Recompensas")
    crecimiento = BudgetRule.get_or_none(BudgetRule.name == "Crecimiento")
    estabilidad = BudgetRule.get_or_none(BudgetRule.name == "Estabilidad")

    ingreso = Parameter.create(
        group="Tipo de Transacción", value="Ingreso", is_deletable=False
    )
    gasto_fijo = Parameter.create(
        group="Tipo de Transacción",
        value="Gasto Fijo",
        is_deletable=False,
        budget_rule=esenciales,
    )
    gasto_variable = Parameter.create(
        group="Tipo de Transacción",
        value="Gasto Variable",
        is_deletable=False,
        budget_rule=recompensas,
    )
    ahorro_meta = Parameter.create(
        group="Tipo de Transacción",
        value="Ahorro Meta",
        is_deletable=False,
        budget_rule=crecimiento,
    )
    pago_deuda = Parameter.create(
        group="Tipo de Transacción",
        value="Pago Deuda",
        is_deletable=False,
        budget_rule=estabilidad,
    )

    Parameter.create(group="Categoría", value="Nómina", parent=ingreso)
    Parameter.create(group="Categoría", value="Freelance", parent=ingreso)
    Parameter.create(group="Categoría", value="Otros Ingresos", parent=ingreso)

    Parameter.create(group="Categoría", value="Vivienda", parent=gasto_fijo)
    Parameter.create(group="Categoría", value="Servicios", parent=gasto_fijo)

    Parameter.create(group="Categoría", value="Transporte", parent=gasto_variable)
    Parameter.create(group="Categoría", value="Comida", parent=gasto_variable)
    Parameter.create(group="Categoría", value="Ocio", parent=gasto_variable)
    Parameter.create(group="Categoría", value="Salud", parent=gasto_variable)
    Parameter.create(group="Categoría", value="Educación", parent=gasto_variable)
    Parameter.create(group="Categoría", value="Otros Gastos", parent=gasto_variable)

    Parameter.create(group="Tipo de Cuenta", value="Cuenta de Ahorros")
    Parameter.create(group="Tipo de Cuenta", value="Cuenta Corriente")
    Parameter.create(group="Tipo de Cuenta", value="Tarjeta de Crédito")
    Parameter.create(group="Tipo de Cuenta", value="Efectivo")

    print("Initial parameters seeded with parent-child relationships.")


def ensure_transfer_transaction_type() -> None:
    """Guarantee that the transfer type exists even on existing databases."""

    exists = Parameter.select().where(
        (Parameter.group == "Tipo de Transacción")
        & (Parameter.value == "Transferencia")
    ).exists()

    if not exists:
        Parameter.create(
            group="Tipo de Transacción",
            value="Transferencia",
            is_deletable=False,
        )


def initialize_database() -> None:
    """Connect to the database, create tables, and seed initial data."""

    try:
        if db.is_closed():
            db.connect()
            print("Database connection opened.")

        db.create_tables(MODELS, safe=True)
        print("Tables created successfully (if they didn't exist).")

        ensure_transaction_enhancements()
        ensure_budget_entry_links()
        seed_initial_budget_rules()
        seed_initial_parameters()
        ensure_transfer_transaction_type()

        print("Database initialization complete.")
    except OperationalError as exc:
        print(f"Database operational error during initialization: {exc}")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"An unexpected error occurred during database initialization: {exc}")


def close_db() -> None:
    """Close the database connection when the server stops."""

    if not db.is_closed():
        db.close()
        print("Database connection closed.")
