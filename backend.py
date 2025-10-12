import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import datetime
from fastapi import Query

# --- SOLUCIÓN DEFINITIVA AL ModuleNotFoundError ---
# Añade la carpeta 'src' al path de Python de forma robusta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Ahora importa los módulos después de ajustar el path
from app.controller.app_controller import AppController
from app.database.db_manager import initialize_database

# --- Inicialización ---
initialize_database()
app = FastAPI()

# --- Configuración de CORS (añadiendo el origen de Tauri) ---
origins = [
    "http://localhost:1420",
    "tauri://localhost" 
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = AppController(view=None)

class BudgetEntryModel(BaseModel):
    id: int
    category: str
    amount: float
    type: str
    month: int
    year: int

    class Config:
        from_attributes = True
        
# --- Modelos Pydantic ---
class TransactionModel(BaseModel):
    id: int
    date: datetime.date
    description: str
    amount: float
    type: str
    category: str
    account_id: int
    class Config: from_attributes = True

class GoalProgressModel(BaseModel):
    name: str
    current_amount: float
    target_amount: float
    percentage: float

class KpiModel(BaseModel):
    total_balance: str
    income: str
    expenses: str
    net_income: str
    
class PortfolioSummaryModel(BaseModel):
    symbol: str
    name: str
    quantity: float
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    
class TradeHistoryModel(BaseModel):
    id: int
    date: datetime.date
    symbol: str
    type: str
    quantity: float
    price: float
    
class CashFlowCategoryModel(BaseModel):
    category: str
    amount: float

class CashFlowAnalysisModel(BaseModel):
    income: List[CashFlowCategoryModel]
    expenses: List[CashFlowCategoryModel]
    
class SettingsModel(BaseModel):
    currency_symbol: str
    decimal_places: int
    theme: str


# --- Endpoints de la API ---
@app.get("/api/transactions", response_model=List[TransactionModel])
def get_transactions():
    return controller.get_all_transactions_for_api()

@app.get("/api/dashboard-kpis", response_model=KpiModel)
def get_dashboard_kpis():
    return controller.get_dashboard_kpis_for_api()

@app.on_event("startup")
def startup_event():
    print("Procesando transacciones recurrentes al inicio...")
    controller.process_recurring_transactions()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
    
class ChartData(BaseModel):
    labels: List[str]
    income_data: List[float]
    expense_data: List[float]
    
@app.get("/api/charts/income-expense", response_model=ChartData)
def get_income_expense_chart():
    # Llama a un nuevo método en el controlador que debemos crear
    chart_data = controller.get_income_expense_chart_data()
    return chart_data

class GoalProgressModel(BaseModel):
    name: str
    current_amount: float
    target_amount: float
    percentage: float

@app.get("/api/dashboard-goals", response_model=List[GoalProgressModel])
def get_dashboard_goals():
    return controller.get_dashboard_goals_for_api()

class AccountModel(BaseModel):
    id: int
    name: str
    account_type: str
    current_balance: float

    class Config:
        from_attributes = True
        
@app.get("/api/accounts", response_model=List[AccountModel])
def get_accounts():
    return controller.get_all_accounts_for_api()

@app.get("/api/budget", response_model=List[BudgetEntryModel])
def get_budget_entries():
    return controller.get_all_budget_entries_for_api()

class DebtModel(BaseModel):
    name: str
    total_amount: float
    current_balance: float
    minimum_payment: float
    interest_rate: float
    percentage: float # Porcentaje pagado

    class Config:
        from_attributes = True
        
@app.get("/api/debts", response_model=List[DebtModel])
def get_debts():
    return controller.get_all_debts_for_api()

@app.get("/api/portfolio/summary", response_model=List[PortfolioSummaryModel])
def get_portfolio_summary():
    return controller.get_portfolio_summary_for_api()

@app.get("/api/portfolio/history", response_model=List[TradeHistoryModel])
def get_trade_history():
    return controller.get_trade_history_for_api()

@app.get("/api/analysis/cash-flow", response_model=CashFlowAnalysisModel)
def get_cash_flow_analysis(year: int, month: int):
    # Pasamos los parámetros al controlador
    return controller.get_cash_flow_analysis_for_api(year, month)

@app.get("/api/settings", response_model=SettingsModel)
def get_settings():
    return controller.get_settings_for_api()

@app.post("/api/settings")
def save_settings(settings: SettingsModel):
    controller.save_settings_from_api(settings.dict())
    return {"status": "success", "message": "Configuración guardada."}

class CreateTransactionModel(BaseModel):
    date: datetime.date
    description: str
    amount: float
    type: str
    category: str
    account_id: int
    # goal_id y debt_id son opcionales
    goal_id: int | None = None
    debt_id: int | None = None
    
@app.post("/api/transactions", response_model=TransactionModel)
def create_transaction(transaction_data: CreateTransactionModel):
    new_transaction = controller.add_transaction_from_api(transaction_data.dict())
    return new_transaction

class CreateAccountModel(BaseModel):
    name: str
    account_type: str
    current_balance: float
    
@app.post("/api/accounts", response_model=AccountModel)
def create_account(account_data: CreateAccountModel):
    new_account = controller.add_account_from_api(account_data.dict())
    return new_account

@app.put("/api/accounts/{account_id}", response_model=AccountModel)
def update_account(account_id: int, account_data: CreateAccountModel):
    updated_account = controller.update_account_from_api(account_id, account_data.dict())
    return updated_account

@app.delete("/api/accounts/{account_id}")
def delete_account(account_id: int):
    controller.delete_account_from_api(account_id)
    return {"status": "success", "message": "Cuenta eliminada."}

class CreateGoalModel(BaseModel):
    name: str
    target_amount: float

class CreateDebtModel(BaseModel):
    name: str
    total_amount: float
    minimum_payment: float
    interest_rate: float
    
@app.post("/api/goals", response_model=GoalProgressModel)
def create_goal(goal_data: CreateGoalModel):
    new_goal = controller.add_goal_from_api(goal_data.dict())
    return new_goal

@app.put("/api/goals/{goal_id}")
def update_goal(goal_id: int, goal_data: CreateGoalModel):
    controller.update_goal_from_api(goal_id, goal_data.dict())
    return {"status": "success"}

@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: int):
    controller.delete_goal_from_api(goal_id)
    return {"status": "success"}

# --- NUEVOS Endpoints para DEUDAS ---
@app.post("/api/debts", response_model=DebtModel)
def create_debt(debt_data: CreateDebtModel):
    new_debt = controller.add_debt_from_api(debt_data.dict())
    return new_debt

@app.put("/api/debts/{debt_id}")
def update_debt(debt_id: int, debt_data: CreateDebtModel):
    controller.update_debt_from_api(debt_id, debt_data.dict())
    return {"status": "success"}

@app.delete("/api/debts/{debt_id}")
def delete_debt(debt_id: int):
    controller.delete_debt_from_api(debt_id)
    return {"status": "success"}

class CreateBudgetEntryModel(BaseModel):
    category: str
    amount: float
    type: str
    month: int
    year: int
    
@app.post("/api/budget", response_model=BudgetEntryModel)
def create_budget_entry(entry_data: CreateBudgetEntryModel):
    new_entry = controller.add_budget_entry_from_api(entry_data.dict())
    return new_entry

@app.put("/api/budget/{entry_id}", response_model=BudgetEntryModel)
def update_budget_entry(entry_id: int, entry_data: CreateBudgetEntryModel):
    updated_entry = controller.update_budget_entry_from_api(entry_id, entry_data.dict())
    return updated_entry

@app.delete("/api/budget/{entry_id}")
def delete_budget_entry(entry_id: int):
    controller.delete_budget_entry_from_api(entry_id)
    return {"status": "success", "message": "Entrada de presupuesto eliminada."}

@app.put("/api/transactions/{transaction_id}", response_model=TransactionModel)
def update_transaction(transaction_id: int, transaction_data: CreateTransactionModel):
    updated_transaction = controller.update_transaction_from_api(transaction_id, transaction_data.dict())
    return updated_transaction

@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(transaction_id: int):
    controller.delete_transaction_from_api(transaction_id)
    return {"status": "success", "message": "Transacción eliminada."}