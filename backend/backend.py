import os
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
import datetime
from typing import Optional, List

# --- CONFIGURACIÓN DE PATH ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORTACIONES ---
from app.controller.app_controller import AppController
from app.database.db_manager import initialize_database, close_db

# --- MANEJO DE LA VIDA DEL SERVIDOR (LIFESPAN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Server startup: Initializing database...")
    initialize_database()
    controller.process_recurring_transactions()
    yield
    print("INFO:     Server shutdown: Closing database connection...")
    close_db()

# --- Inicialización de la Aplicación ---
app = FastAPI(lifespan=lifespan)
controller = AppController()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- MODELOS DE DATOS PARA LA API (PYDANTIC V2) ---
class AccountModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    account_type: str
    current_balance: float

class TransactionModel(BaseModel):
    description: str
    amount: float
    date: datetime.date
    type: str
    category: str
    account_id: int
    goal_id: Optional[int] = None
    debt_id: Optional[int] = None

class GoalModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    target_amount: float
    current_amount: float

class DebtModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    total_amount: float
    current_balance: float

# ===============================================
# --- ENDPOINTS DE LA API ---
# ===============================================

@app.get("/api/status")
def get_status():
    return {"status": "Backend funcionando correctamente!"}

@app.get("/api/accounts", response_model=List[AccountModel])
def get_accounts():
    return controller.get_accounts_data_for_view()

@app.get("/api/transactions")
def get_transactions(): return controller.get_transactions_data()

@app.post("/api/transactions", status_code=201)
def create_transaction(transaction: TransactionModel):
    result = controller.add_transaction(transaction.dict())
    if "error" in result: raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.put("/api/transactions/{transaction_id}")
def update_transaction(transaction_id: int, transaction: TransactionModel):
    result = controller.update_transaction(transaction_id, transaction.dict())
    if "error" in result: raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(transaction_id: int):
    result = controller.delete_transaction(transaction_id)
    if "error" in result: raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/goals")
def get_goals():
    """Devuelve todas las metas para el select del formulario."""
    return controller.get_all_goals()

@app.get("/api/debts")
def get_debts():
    """Devuelve todas las deudas para el select del formulario."""
    return controller.get_all_debts()

@app.get("/api/parameters/transaction-types")
def get_transaction_types():
    return controller.get_parameters_by_group('Tipo de Transacción')

@app.get("/api/parameters/categories/{parent_id}")
def get_categories_by_type(parent_id: int):
    return controller.get_child_parameters(parent_id)

@app.get("/api/transactions/{transaction_id}")
def get_transaction(transaction_id: int):
    """Obtiene los detalles de una única transacción para editarla."""
    transaction = controller.get_transaction_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


def _resolve_year_and_months(year: Optional[int], months: Optional[List[int]]):
    """Helper to resolve dashboard query parameters with sensible defaults."""
    today = datetime.date.today()
    resolved_year = year or today.year
    resolved_months = months or list(range(1, today.month + 1))
    return resolved_year, resolved_months


@app.get("/api/dashboard-kpis")
def get_dashboard_kpis(year: Optional[int] = None, months: Optional[List[int]] = Query(None)):
    resolved_year, resolved_months = _resolve_year_and_months(year, months)
    dashboard_data = controller.get_dashboard_data(resolved_year, resolved_months)
    kpis = dashboard_data.get("kpis", {})
    accounts_summary = dashboard_data.get("accounts_summary", [])

    total_balance = sum(float(account.get("current_balance", 0) or 0) for account in accounts_summary)
    income = float(kpis.get("income", 0) or 0)
    raw_expense = float(kpis.get("expense", 0) or 0)
    expenses = abs(raw_expense)
    net_income = float(kpis.get("net", income - expenses) or 0)

    return {
        "total_balance": total_balance,
        "income": income,
        "expenses": expenses,
        "net_income": net_income,
    }


@app.get("/api/charts/income-expense")
def get_income_expense_chart(year: Optional[int] = None, months: Optional[List[int]] = Query(None)):
    resolved_year, resolved_months = _resolve_year_and_months(year, months)
    cash_flow = controller._get_cash_flow_data_for_chart(resolved_year, resolved_months)

    labels, income_data, expense_data = [], [], []
    for month, values in cash_flow.items():
        labels.append(month)
        income_data.append(float(values.get("income", 0) or 0))
        expense_value = float(values.get("expense", 0) or 0)
        expense_data.append(abs(expense_value))

    return {
        "labels": labels,
        "income_data": income_data,
        "expense_data": expense_data,
    }


@app.get("/api/dashboard-goals")
def get_dashboard_goals():
    goals = controller.get_goals_summary()
    normalized_goals = []
    for goal in goals:
        target_amount = float(goal.get("target_amount", 0) or 0)
        current_amount = float(goal.get("current_amount", 0) or 0)
        percentage = (current_amount / target_amount * 100) if target_amount else 0.0
        normalized_goals.append({
            "id": goal.get("id"),
            "name": goal.get("name"),
            "target_amount": target_amount,
            "current_amount": current_amount,
            "percentage": percentage,
        })

    return normalized_goals

# ===============================================
# --- INICIADOR DEL SERVIDOR ---
# ===============================================
# 2. Añadimos este bloque al final del archivo
if __name__ == "__main__":
    # Esto le dice a Uvicorn que corra la 'app' de este archivo
    # y que se reinicie automáticamente si detecta cambios en el código.
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)