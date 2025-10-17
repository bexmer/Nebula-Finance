"""Helpers for initializing and seeding the application database."""

import json
from importlib import import_module, util

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

# Detect whether the optional peewee-db-evolve package is installed.
_EVOLVE_SPEC = util.find_spec("peeweedbevolve")
HAVE_DB_EVOLVE = _EVOLVE_SPEC is not None

if HAVE_DB_EVOLVE:
    # Import for side effects so the Database.evolve helper registers itself.
    import_module("peeweedbevolve")  # noqa: F401


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

    if "portfolio_direction" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN portfolio_direction TEXT'
        )


def ensure_account_interest_columns() -> None:
    """Ensure savings account interest metadata columns exist."""

    table_name = Account._meta.table_name
    existing_columns = _existing_columns(table_name)

    if "annual_interest_rate" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN annual_interest_rate REAL DEFAULT 0'
        )

    if "compounding_frequency" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN compounding_frequency TEXT DEFAULT "Mensual"'
        )

    if "last_interest_accrual" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN last_interest_accrual DATE'
        )


def ensure_budget_entry_links() -> None:
    """Ensure budget entries can optionally reference a goal or debt."""

    table_name = BudgetEntry._meta.table_name
    existing_columns = _existing_columns(table_name)

    if "goal_id" not in existing_columns:
        db.execute_sql(f'ALTER TABLE "{table_name}" ADD COLUMN goal_id INTEGER')

    if "debt_id" not in existing_columns:
        db.execute_sql(f'ALTER TABLE "{table_name}" ADD COLUMN debt_id INTEGER')


def ensure_budget_entry_enhancements() -> None:
    """Add extended budgeting fields when missing on existing databases."""

    table_name = BudgetEntry._meta.table_name
    existing_columns = _existing_columns(table_name)

    if "frequency" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN frequency TEXT DEFAULT "Mensual"'
        )

    if "start_date" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN start_date DATE DEFAULT CURRENT_DATE'
        )

    if "end_date" not in existing_columns:
        db.execute_sql(f'ALTER TABLE "{table_name}" ADD COLUMN end_date DATE')

    if "is_recurring" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN is_recurring INTEGER DEFAULT 0'
        )

    if "actual_amount" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN actual_amount REAL DEFAULT 0'
        )

    if "use_custom_schedule" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN use_custom_schedule INTEGER DEFAULT 0'
        )


def ensure_portfolio_asset_enhancements() -> None:
    """Add optional savings tracking fields to portfolio assets."""

    table_name = PortfolioAsset._meta.table_name
    existing_columns = _existing_columns(table_name)

    if "annual_yield_rate" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN annual_yield_rate REAL DEFAULT 0'
        )

    if "linked_account_id" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN linked_account_id INTEGER'
        )

    if "linked_goal_id" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN linked_goal_id INTEGER'
        )


def ensure_trade_enhancements() -> None:
    """Ensure portfolio trades can link to cash movements and budgets."""

    table_name = Trade._meta.table_name
    existing_columns = _existing_columns(table_name)

    if "linked_transaction_id" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN linked_transaction_id INTEGER'
        )

    if "linked_budget_entry_id" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN linked_budget_entry_id INTEGER'
        )

    if "is_planned" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN is_planned INTEGER DEFAULT 0'
        )


def ensure_savings_category_inheritance() -> None:
    """Guarantee savings and debt types inherit variable expense categories."""

    variable = Parameter.get_or_none(
        (Parameter.group == "Tipo de Transacción")
        & (Parameter.value == "Gasto Variable")
    )

    if not variable:
        return

    payload = json.dumps({"inherits": [variable.id]})

    for value in ("Ahorro Meta", "Pago Deuda"):
        parameter = Parameter.get_or_none(
            (Parameter.group == "Tipo de Transacción") & (Parameter.value == value)
        )
        if parameter and not parameter.extra_data:
            parameter.extra_data = payload
            parameter.save()


def ensure_transaction_budget_link() -> None:
    """Guarantee transactions can reference a budget entry when required."""

    table_name = Transaction._meta.table_name
    existing_columns = _existing_columns(table_name)

    if "budget_entry_id" not in existing_columns:
        db.execute_sql(
            f'ALTER TABLE "{table_name}" ADD COLUMN budget_entry_id INTEGER'
        )


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
        extra_data=json.dumps({"inherits": []}),
    )
    pago_deuda = Parameter.create(
        group="Tipo de Transacción",
        value="Pago Deuda",
        is_deletable=False,
        budget_rule=estabilidad,
        extra_data=json.dumps({"inherits": []}),
    )
    movimiento_portafolio = Parameter.create(
        group="Tipo de Transacción",
        value="Movimiento Portafolio",
        is_deletable=False,
        budget_rule=crecimiento,
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

    savings_inheritance = json.dumps({"inherits": [gasto_variable.id]})
    ahorro_meta.extra_data = savings_inheritance
    ahorro_meta.save()
    pago_deuda.extra_data = savings_inheritance
    pago_deuda.save()

    Parameter.create(group="Tipo de Cuenta", value="Cuenta de Ahorros")
    Parameter.create(group="Tipo de Cuenta", value="Cuenta Corriente")
    Parameter.create(group="Tipo de Cuenta", value="Tarjeta de Crédito")
    Parameter.create(group="Tipo de Cuenta", value="Efectivo")

    asset_type_values = [
        "Acción",
        "Fondo de Inversión",
        "Criptomoneda",
        "Cuenta de Ahorro",
    ]
    for asset_type_value in asset_type_values:
        Parameter.create(group="Tipo de Activo", value=asset_type_value)
        if "ahorro" in asset_type_value.lower():
            continue
        Parameter.create(
            group="Categoría",
            value=asset_type_value,
            parent=movimiento_portafolio,
        )

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


def ensure_portfolio_transaction_catalog() -> None:
    """Ensure the portfolio transaction type and categories exist."""

    movimiento = Parameter.get_or_none(
        (Parameter.group == "Tipo de Transacción")
        & (Parameter.value == "Movimiento Portafolio")
    )

    if not movimiento:
        crecimiento = BudgetRule.get_or_none(BudgetRule.name == "Crecimiento")
        movimiento = Parameter.create(
            group="Tipo de Transacción",
            value="Movimiento Portafolio",
            is_deletable=False,
            budget_rule=crecimiento,
        )

    asset_types = Parameter.select().where(Parameter.group == "Tipo de Activo")
    existing_categories = {
        parameter.value
        for parameter in Parameter.select().where(
            (Parameter.group == "Categoría") & (Parameter.parent == movimiento)
        )
    }

    for asset_type in asset_types:
        if not asset_type.value or "ahorro" in asset_type.value.lower():
            continue
        if asset_type.value in existing_categories:
            continue
        Parameter.create(
            group="Categoría",
            value=asset_type.value,
            parent=movimiento,
        )

def initialize_database() -> None:
    """Connect to the database, evolve tables, and seed initial data."""

    try:
        if db.is_closed():
            db.connect()
            print("Database connection opened.")

        if HAVE_DB_EVOLVE:
            print("Evolving database schema...")
            db.evolve(MODELS)
            print("Database schema is up to date.")
        else:
            print(
                "peewee-db-evolve not installed; using create_tables fallback."
            )
            db.create_tables(MODELS, safe=True)

        ensure_transaction_enhancements()
        ensure_budget_entry_links()
        ensure_budget_entry_enhancements()
        ensure_account_interest_columns()
        ensure_portfolio_asset_enhancements()
        ensure_trade_enhancements()
        ensure_transaction_budget_link()
        ensure_savings_category_inheritance()
        seed_initial_budget_rules()
        seed_initial_parameters()
        ensure_transfer_transaction_type()
        ensure_portfolio_transaction_catalog()

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
