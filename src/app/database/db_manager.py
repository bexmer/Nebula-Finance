from app.model.base_model import db
from app.model.transaction import Transaction
from app.model.goal import Goal
from app.model.debt import Debt
from app.model.budget_entry import BudgetEntry
from app.model.portfolio_asset import PortfolioAsset
from app.model.trade import Trade
from app.model.recurring_transaction import RecurringTransaction
# --- INICIO DE LA MODIFICACIÓN ---
from app.model.account import Account
# --- FIN DE LA MODIFICACIÓN ---


def initialize_database():
    """
    Se conecta a la base de datos y crea las tablas si no existen.
    """
    db.connect()
    # --- INICIO DE LA MODIFICACIÓN ---
    db.create_tables([
        Transaction, Goal, Debt, BudgetEntry,
        PortfolioAsset, Trade, RecurringTransaction, Account
    ], safe=True)
    # --- FIN DE LA MODIFICACIÓN ---
    print("Database initialized and tables created if they didn't exist.")