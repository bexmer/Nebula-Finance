import os
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, field_validator, constr
import datetime
from typing import Optional, List, Dict, Any, Literal

MAX_DIGITS = 10


def enforce_digit_limit(value: Optional[float], field_name: str) -> Optional[float]:
    if value is None:
        return value
    try:
        integer_digits = len(str(int(abs(value))))
    except (ValueError, TypeError):
        raise ValueError(f"El valor proporcionado para {field_name} no es numérico.")
    if integer_digits > MAX_DIGITS:
        raise ValueError(
            f"El campo '{field_name}' no puede tener más de {MAX_DIGITS} dígitos en la parte entera."
        )
    return value

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
    initial_balance: float
    current_balance: float


class AccountCreateModel(BaseModel):
    name: str
    account_type: str
    initial_balance: float = 0.0


class AccountUpdateModel(BaseModel):
    name: Optional[str] = None
    account_type: Optional[str] = None
    initial_balance: Optional[float] = None
    current_balance: Optional[float] = None

class TransactionModel(BaseModel):
    description: constr(max_length=100)
    amount: float
    date: datetime.date
    type: str
    category: str
    account_id: int
    goal_id: Optional[int] = None
    debt_id: Optional[int] = None

    @field_validator("amount")
    @classmethod
    def validate_amount_digits(cls, value: float):
        return enforce_digit_limit(value, "amount")


class BudgetEntryModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    description: Optional[str] = None
    category: str
    type: str
    budgeted_amount: float
    due_date: Optional[datetime.date] = None
    month: Optional[int] = None
    year: Optional[int] = None
    amount: Optional[float] = None
    goal_id: Optional[int] = None
    goal_name: Optional[str] = None
    debt_id: Optional[int] = None
    debt_name: Optional[str] = None


class BudgetEntryCreateModel(BaseModel):
    category: str
    budgeted_amount: Optional[float] = None
    amount: Optional[float] = None
    type: Optional[str] = "Gasto"
    description: Optional[constr(max_length=100)] = None
    due_date: Optional[datetime.date] = None
    month: Optional[int] = None
    year: Optional[int] = None
    goal_id: Optional[int] = None
    debt_id: Optional[int] = None

    @field_validator("budgeted_amount", "amount")
    @classmethod
    def validate_budget_amounts(cls, value: Optional[float], info):
        return enforce_digit_limit(value, info.field_name)


class BudgetEntryUpdateModel(BaseModel):
    category: Optional[str] = None
    budgeted_amount: Optional[float] = None
    amount: Optional[float] = None
    type: Optional[str] = None
    description: Optional[constr(max_length=100)] = None
    due_date: Optional[datetime.date] = None
    month: Optional[int] = None
    year: Optional[int] = None
    goal_id: Optional[int] = None
    debt_id: Optional[int] = None

    @field_validator("budgeted_amount", "amount")
    @classmethod
    def validate_budget_update_amounts(cls, value: Optional[float], info):
        return enforce_digit_limit(value, info.field_name)

class GoalModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    target_amount: float
    current_amount: float

class GoalCreateModel(BaseModel):
    name: str
    target_amount: float

    @field_validator("target_amount")
    @classmethod
    def validate_goal_amount(cls, value: float):
        return enforce_digit_limit(value, "target_amount")

class GoalUpdateModel(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    current_amount: Optional[float] = None

    @field_validator("target_amount", "current_amount")
    @classmethod
    def validate_goal_update_amounts(cls, value: Optional[float], info):
        return enforce_digit_limit(value, info.field_name)

class DebtModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    total_amount: float
    current_balance: float


class SettingsModel(BaseModel):
    currency_symbol: str
    decimal_places: int
    theme: str


class BudgetRuleItem(BaseModel):
    id: int
    name: str
    percentage: float
    is_deletable: bool


class BudgetRuleCreateModel(BaseModel):
    name: str
    percentage: float


class BudgetRuleUpdateModel(BaseModel):
    name: Optional[str] = None
    percentage: Optional[float] = None


class TransactionTypeItem(BaseModel):
    id: int
    name: str
    budget_rule_id: Optional[int] = None
    budget_rule_name: Optional[str] = None
    is_deletable: bool


class TransactionTypeCreateModel(BaseModel):
    name: str
    budget_rule_id: Optional[int] = None


class TransactionTypeUpdateModel(BaseModel):
    name: Optional[str] = None
    budget_rule_id: Optional[int] = None


class AccountTypeItem(BaseModel):
    id: int
    name: str
    is_deletable: bool


class AccountTypeCreateModel(BaseModel):
    name: str


class AccountTypeUpdateModel(BaseModel):
    name: str


class CategoryItem(BaseModel):
    id: int
    name: str
    parent_id: int
    parent_name: str
    is_deletable: bool


class CategoryCreateModel(BaseModel):
    name: str
    parent_id: int


class CategoryUpdateModel(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None


class RecurringTransactionModel(BaseModel):
    id: int
    description: str
    amount: float
    type: str
    category: str
    frequency: str
    day_of_month: Optional[int] = None
    day_of_month_2: Optional[int] = None
    start_date: Optional[datetime.date] = None
    last_processed_date: Optional[datetime.date] = None
    next_run: Optional[str] = None


class DisplayPreferencesModel(BaseModel):
    abbreviate_numbers: bool
    threshold: int


class PortfolioSummaryModel(BaseModel):
    symbol: str
    name: str
    asset_type: str
    quantity: float
    avg_cost: float
    market_value: float
    unrealized_pnl: float


class TradeResponseModel(BaseModel):
    id: int
    date: datetime.date
    symbol: str
    asset_type: str
    type: Literal["buy", "sell"]
    quantity: float
    price: float


class TradeCreateModel(BaseModel):
    symbol: str
    asset_type: str
    trade_type: Literal["buy", "sell", "compra", "venta"]
    quantity: float
    price: float
    date: datetime.date

    @field_validator("quantity", "price")
    @classmethod
    def validate_trade_numbers(cls, value: float, info):
        return enforce_digit_limit(value, info.field_name)


class TradeUpdateModel(TradeCreateModel):
    pass

class DebtCreateModel(BaseModel):
    name: str
    total_amount: float
    minimum_payment: Optional[float] = 0.0
    interest_rate: Optional[float] = 0.0

    @field_validator("total_amount", "minimum_payment")
    @classmethod
    def validate_debt_amounts(cls, value: Optional[float], info):
        return enforce_digit_limit(value, info.field_name)


class DebtUpdateModel(BaseModel):
    name: Optional[str] = None
    total_amount: Optional[float] = None
    current_balance: Optional[float] = None
    minimum_payment: Optional[float] = None
    interest_rate: Optional[float] = None

    @field_validator("total_amount", "current_balance", "minimum_payment")
    @classmethod
    def validate_debt_update_amounts(cls, value: Optional[float], info):
        return enforce_digit_limit(value, info.field_name)

# ===============================================
# --- ENDPOINTS DE LA API ---
# ===============================================

@app.get("/api/status")
def get_status():
    return {"status": "Backend funcionando correctamente!"}

@app.get("/api/accounts", response_model=List[AccountModel])
def get_accounts():
    return controller.get_accounts_data_for_view()


@app.post("/api/accounts", response_model=AccountModel, status_code=201)
def create_account(account: AccountCreateModel):
    result = controller.add_account(account.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/api/accounts/{account_id}", response_model=AccountModel)
def update_account(account_id: int, account: AccountUpdateModel):
    result = controller.update_account(account_id, account.model_dump(exclude_none=True))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/api/accounts/{account_id}")
def delete_account(account_id: int):
    result = controller.delete_account(account_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/api/transactions")
def get_transactions(
    search: Optional[str] = Query(default=None, description="Texto para buscar en la descripción"),
    start_date: Optional[datetime.date] = Query(default=None, description="Fecha inicial del rango"),
    end_date: Optional[datetime.date] = Query(default=None, description="Fecha final del rango"),
    transaction_type: Optional[str] = Query(
        default=None, alias="type", description="Tipo de transacción"
    ),
    category: Optional[str] = Query(default=None, description="Categoría de la transacción"),
    sort_by: Optional[str] = Query(default="date_desc", description="Ordenamiento deseado"),
):
    filters: Dict[str, Any] = {}

    if search:
        filters["search"] = search
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if transaction_type:
        filters["type"] = transaction_type
    if category:
        filters["category"] = category
    if sort_by:
        filters["sort_by"] = sort_by

    return controller.get_transactions_data(filters if filters else None)


@app.get("/api/recurring-transactions", response_model=List[RecurringTransactionModel])
def list_recurring_transactions():
    return controller.get_recurring_transactions()


@app.get("/api/dashboard")
def get_dashboard(year: int, months: Optional[List[int]] = Query(None)):
    month_values = list(months) if months else []
    return controller.get_dashboard_data(year, month_values)


@app.get("/api/analysis")
def get_analysis(
    year: Optional[int] = Query(default=None),
    months: Optional[List[int]] = Query(default=None),
    projection_months: int = Query(default=12, alias="projectionMonths"),
):
    month_values = list(months) if months else []
    return controller.get_analysis_overview(year, month_values, projection_months)


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
def delete_transaction(transaction_id: int, adjust_balance: bool = Query(False)):
    result = controller.delete_transaction(transaction_id, adjust_balance)
    if "error" in result: raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/goals")
def get_goals():
    """Devuelve todas las metas para el select del formulario."""
    return controller.get_all_goals()

@app.get("/api/dashboard-goals")
def get_dashboard_goals():
    return controller.get_goals_summary()

@app.get("/api/debts")
def get_debts():
    """Devuelve todas las deudas para el select del formulario."""
    return controller.get_all_debts()

@app.post("/api/goals", status_code=201)
def create_goal(goal: GoalCreateModel):
    result = controller.add_goal(goal.dict())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.put("/api/goals/{goal_id}")
def update_goal(goal_id: int, goal: GoalUpdateModel):
    result = controller.update_goal(goal_id, goal.dict(exclude_none=True))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: int):
    result = controller.delete_goal(goal_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/api/debts", status_code=201)
def create_debt(debt: DebtCreateModel):
    result = controller.add_debt(debt.dict())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.put("/api/debts/{debt_id}")
def update_debt(debt_id: int, debt: DebtUpdateModel):
    result = controller.update_debt(debt_id, debt.dict(exclude_none=True))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.delete("/api/debts/{debt_id}")
def delete_debt(debt_id: int):
    result = controller.delete_debt(debt_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/budget", response_model=List[BudgetEntryModel])
def list_budget_entries():
    return controller.get_budget_entries()


@app.post("/api/budget", response_model=BudgetEntryModel, status_code=201)
def create_budget_entry(entry: BudgetEntryCreateModel):
    result = controller.add_budget_entry(entry.model_dump(exclude_none=True))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/api/budget/{entry_id}", response_model=BudgetEntryModel)
def update_budget_entry(entry_id: int, entry: BudgetEntryUpdateModel):
    result = controller.update_budget_entry(entry_id, entry.model_dump(exclude_none=True))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.delete("/api/budget/{entry_id}")
def delete_budget_entry(entry_id: int):
    result = controller.delete_budget_entry(entry_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/portfolio/summary", response_model=List[PortfolioSummaryModel])
def get_portfolio_summary():
    return controller.get_portfolio_assets()


@app.get("/api/portfolio/history", response_model=List[TradeResponseModel])
def get_portfolio_history():
    return controller.get_trade_history()


@app.post("/api/portfolio/trades", response_model=TradeResponseModel, status_code=201)
def create_trade(trade: TradeCreateModel):
    result = controller.add_trade(trade.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/api/portfolio/trades/{trade_id}", response_model=TradeResponseModel)
def update_trade(trade_id: int, trade: TradeUpdateModel):
    result = controller.update_trade(trade_id, trade.model_dump())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.delete("/api/portfolio/trades/{trade_id}")
def delete_trade(trade_id: int):
    result = controller.delete_trade(trade_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/parameters/transaction-types")
def get_transaction_types():
    return controller.get_parameters_by_group('Tipo de Transacción')


@app.get("/api/parameters/account-types", response_model=List[str])
def get_account_types():
    return controller.get_account_types()

@app.get("/api/parameters/categories/{parent_id}")
def get_categories_by_type(parent_id: int):
    return controller.get_child_parameters(parent_id)


@app.get("/api/config/budget-rules", response_model=List[BudgetRuleItem])
def list_budget_rules():
    return controller.get_budget_rules()


@app.post("/api/config/budget-rules", response_model=BudgetRuleItem, status_code=201)
def create_budget_rule(rule: BudgetRuleCreateModel):
    result = controller.add_budget_rule(rule.name, rule.percentage)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/api/config/budget-rules/{rule_id}", response_model=BudgetRuleItem)
def update_budget_rule(rule_id: int, rule: BudgetRuleUpdateModel):
    result = controller.update_budget_rule(rule_id, rule.model_dump(exclude_unset=True))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/api/config/budget-rules/{rule_id}")
def delete_budget_rule(rule_id: int):
    result = controller.delete_budget_rule(rule_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/config/transaction-types", response_model=List[TransactionTypeItem])
def list_transaction_types():
    return controller.get_transaction_types_overview()


@app.post("/api/config/transaction-types", response_model=TransactionTypeItem, status_code=201)
def create_transaction_type(transaction_type: TransactionTypeCreateModel):
    result = controller.add_transaction_type(
        transaction_type.name,
        transaction_type.budget_rule_id,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/api/config/transaction-types/{type_id}", response_model=TransactionTypeItem)
def update_transaction_type(type_id: int, transaction_type: TransactionTypeUpdateModel):
    result = controller.update_transaction_type(type_id, transaction_type.model_dump(exclude_unset=True))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/api/config/transaction-types/{type_id}")
def delete_transaction_type(type_id: int):
    result = controller.delete_transaction_type(type_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/config/account-types", response_model=List[AccountTypeItem])
def list_account_types_config():
    return controller.get_account_type_parameters()


@app.post("/api/config/account-types", response_model=AccountTypeItem, status_code=201)
def create_account_type_parameter(account_type: AccountTypeCreateModel):
    result = controller.add_account_type(account_type.name)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/api/config/account-types/{type_id}", response_model=AccountTypeItem)
def update_account_type_parameter(type_id: int, account_type: AccountTypeUpdateModel):
    result = controller.update_account_type_parameter(type_id, account_type.name)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/api/config/account-types/{type_id}")
def delete_account_type_parameter(type_id: int):
    result = controller.delete_account_type_parameter(type_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/config/categories", response_model=List[CategoryItem])
def list_categories():
    return controller.get_category_overview()


@app.post("/api/config/categories", response_model=CategoryItem, status_code=201)
def create_category(category: CategoryCreateModel):
    result = controller.add_category(category.name, category.parent_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/api/config/categories/{category_id}", response_model=CategoryItem)
def update_category(category_id: int, category: CategoryUpdateModel):
    result = controller.update_category(category_id, category.model_dump(exclude_unset=True))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/api/config/categories/{category_id}")
def delete_category(category_id: int):
    result = controller.delete_category(category_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/config/display", response_model=DisplayPreferencesModel)
def get_display_preferences():
    return controller.get_display_preferences()


@app.put("/api/config/display", response_model=DisplayPreferencesModel)
def update_display_preferences(preferences: DisplayPreferencesModel):
    updated = controller.update_display_preferences(
        preferences.abbreviate_numbers,
        preferences.threshold,
    )
    return updated

@app.get("/api/transactions/{transaction_id}")
def get_transaction(transaction_id: int):
    """Obtiene los detalles de una única transacción para editarla."""
    transaction = controller.get_transaction_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@app.get("/api/settings", response_model=SettingsModel)
def get_settings():
    """Obtiene la configuración de la aplicación."""
    return controller.get_app_settings()


@app.post("/api/settings")
def update_settings(settings: SettingsModel):
    """Actualiza y persiste la configuración de la aplicación."""
    updated_settings = controller.update_app_settings(settings.model_dump())
    return {"message": "Configuración actualizada correctamente.", "settings": updated_settings}

# ===============================================
# --- INICIADOR DEL SERVIDOR ---
# ===============================================
# 2. Añadimos este bloque al final del archivo
if __name__ == "__main__":
    # Esto le dice a Uvicorn que corra la 'app' de este archivo
    # y que se reinicie automáticamente si detecta cambios en el código.
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
