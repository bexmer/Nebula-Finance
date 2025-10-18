from collections import defaultdict
import calendar
import calendar
import datetime
import json
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dateutil.relativedelta import relativedelta
from peewee import JOIN, fn, prefetch

# --- Importaciones de Modelos de Datos ---
from app.model.account import Account
from app.model.budget_entry import BudgetEntry
from app.model.portfolio_asset import PortfolioAsset
from app.model.budget_rule import BudgetRule
from app.model.debt import Debt
from app.model.goal import Goal
from app.model.recurring_transaction import RecurringTransaction
from app.model.tag import Tag
from app.model.parameter import Parameter
from app.model.trade import Trade
from app.model.transaction import Transaction
from app.model.transaction_split import TransactionSplit
from app.model.transaction_tag import TransactionTag
from app.model.receipt import Receipt
from app.model.base_model import db


MONTH_LABELS = [
    "",
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
]


DEFAULT_APP_SETTINGS = {
    "currency_symbol": "$",
    "decimal_places": 2,
    "theme": "dark",
}


RECEIPT_STORAGE_DIR = (
    Path(__file__).resolve().parents[1] / "storage" / "receipts"
)
RECEIPT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class AppController:
    """
    Controlador de la aplicación que maneja la lógica de negocio.
    Esta versión está adaptada para funcionar como un backend/API,
    eliminando todas las dependencias de la interfaz gráfica (app.view).
    """
    def __init__(self, view=None):
        self.view = view
        self.current_pages = {}

    # -----------------------------------------------------------------
    # --- Helpers for recurring budget calculations ---
    # -----------------------------------------------------------------
    _DEFAULT_FREQUENCY = "Mensual"

    def _normalize_frequency(self, raw_value: Optional[str]) -> str:
        """Return a normalized frequency label with title casing."""

        if not raw_value:
            return self._DEFAULT_FREQUENCY

        normalized = (
            unicodedata.normalize("NFD", str(raw_value))
            .encode("ascii", "ignore")
            .decode("ascii")
            .strip()
            .lower()
        )

        mapping = {
            "unica vez": "Única vez",
            "una vez": "Única vez",
            "semanal": "Semanal",
            "quincenal": "Quincenal",
            "mensual": "Mensual",
            "anual": "Anual",
        }

        return mapping.get(normalized, self._DEFAULT_FREQUENCY)

    def _frequency_delta(self, frequency: str):
        """Return a timedelta/relativedelta representing the frequency."""

        normalized = self._normalize_frequency(frequency)
        if normalized == "Única vez":
            return None
        if normalized == "Semanal":
            return datetime.timedelta(weeks=1)
        if normalized == "Quincenal":
            return datetime.timedelta(weeks=2)
        if normalized == "Anual":
            return relativedelta(years=1)
        return relativedelta(months=1)

    @staticmethod
    def _coerce_date(value: Optional[Any]) -> Optional[datetime.date]:
        """Try to convert a value into a date, returning None on failure."""

        if value in (None, "", 0):
            return None
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        try:
            return datetime.date.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_date(value: Optional[Any]) -> Optional[datetime.date]:
        """Parse user-provided dates and raise a ValueError when invalid."""

        if value in (None, "", 0):
            return None

        parsed = AppController._coerce_date(value)
        if parsed is None:
            raise ValueError(f"Fecha inválida: {value}")
        return parsed

    def _compute_period_bounds(
        self,
        start_date: Optional[datetime.date],
        frequency: str,
        due_date: Optional[datetime.date],
        end_date: Optional[datetime.date],
    ) -> Tuple[datetime.date, datetime.date]:
        """Given partial information, determine the active period for a budget."""

        normalized = self._normalize_frequency(frequency)
        start = start_date or due_date or end_date or datetime.date.today()

        if normalized == "Única vez":
            final_end = end_date or due_date or start
            return start, final_end

        delta = self._frequency_delta(normalized)
        if isinstance(delta, datetime.timedelta):
            tentative_end = start + delta - datetime.timedelta(days=1)
        else:
            tentative_end = (start + delta) - datetime.timedelta(days=1)

        final_end = end_date or due_date or tentative_end
        if final_end < start:
            final_end = start
        return start, final_end

    @staticmethod
    def _normalize_label(value: Optional[Any]) -> str:
        if value in (None, ""):
            return ""
        return (
            unicodedata.normalize("NFD", str(value))
            .encode("ascii", "ignore")
            .decode("ascii")
            .strip()
            .lower()
        )

    def _is_savings_account_type(self, account_type: Optional[str]) -> bool:
        normalized = self._normalize_label(account_type)
        return "ahorro" in normalized

    def _normalize_compounding_frequency(self, value: Optional[str]) -> str:
        normalized = self._normalize_label(value)
        mapping = {
            "mensual": "Mensual",
            "trimestral": "Trimestral",
            "semestral": "Semestral",
            "anual": "Anual",
            "bimestral": "Bimestral",
        }
        return mapping.get(normalized, "Mensual")

    def _months_per_compounding_period(self, frequency: Optional[str]) -> int:
        normalized = self._normalize_label(frequency)
        mapping = {
            "mensual": 1,
            "bimestral": 2,
            "trimestral": 3,
            "semestral": 6,
            "anual": 12,
        }
        return mapping.get(normalized, 1)

    def _apply_interest_for_account(
        self, account: Account, reference_date: Optional[datetime.date] = None
    ) -> None:
        """Post automatic interest transactions for savings accounts when due."""

        if not self._is_savings_account_type(getattr(account, "account_type", "")):
            return

        annual_rate = float(getattr(account, "annual_interest_rate", 0) or 0)
        if annual_rate <= 0:
            return

        today = reference_date or datetime.date.today()

        last_accrual = getattr(account, "last_interest_accrual", None)
        if last_accrual is None:
            account.last_interest_accrual = today
            account.save()
            return

        period_months = self._months_per_compounding_period(
            getattr(account, "compounding_frequency", "Mensual")
        )
        periods_per_year = max(1, int(round(12 / max(period_months, 1))))

        next_accrual = last_accrual + relativedelta(months=period_months)
        iterations = 0

        while next_accrual <= today and iterations < 36:
            interest_amount = round(
                float(getattr(account, "current_balance", 0) or 0)
                * (annual_rate / 100.0)
                / periods_per_year,
                2,
            )

            with db.atomic():
                if interest_amount > 0:
                    Transaction.create(
                        account=account,
                        date=next_accrual,
                        description=(
                            f"Intereses generados ({MONTH_LABELS[next_accrual.month]} {next_accrual.year})"
                        ),
                        amount=interest_amount,
                        type="Ingreso",
                        category="Ingresos por Intereses",
                        goal=None,
                        debt=None,
                        budget_entry=None,
                        is_transfer=False,
                        transfer_account=None,
                    )
                    account.current_balance = (
                        float(getattr(account, "current_balance", 0) or 0)
                        + interest_amount
                    )

                account.last_interest_accrual = next_accrual
                account.save()

            last_accrual = next_accrual
            next_accrual = last_accrual + relativedelta(months=period_months)
            iterations += 1

    def _resolve_entry_bounds(self, entry: Any) -> Tuple[datetime.date, datetime.date]:
        """Resolve the cached period for a budget entry or dict representation."""

        if isinstance(entry, dict):
            frequency = entry.get("frequency")
            start_raw = entry.get("start_date")
            due_raw = entry.get("due_date")
            end_raw = entry.get("end_date")
        else:
            frequency = getattr(entry, "frequency", None)
            start_raw = getattr(entry, "start_date", None)
            due_raw = getattr(entry, "due_date", None)
            end_raw = getattr(entry, "end_date", None)

        normalized = self._normalize_frequency(frequency)
        start_date = self._coerce_date(start_raw)
        due_date = self._coerce_date(due_raw)
        end_date = self._coerce_date(end_raw)

        start, final_end = self._compute_period_bounds(start_date, normalized, due_date, end_date)
        return start, final_end

    # =================================================================
    # --- SECCIÓN: LÓGICA GENERAL Y DE UTILIDAD ---
    # =================================================================

    def _prefetch_transactions(self, query):
        """Carga relaciones necesarias para trabajar con splits y etiquetas."""

        tag_links = TransactionTag.select().join(Tag)

        return list(
            prefetch(
                query,
                Account,
                BudgetEntry,
                TransactionSplit,
                tag_links,
                Receipt,
            )
        )

    @staticmethod
    def _sanitize_tags(tags: Optional[List[str]]) -> List[str]:
        """Normaliza una lista de etiquetas eliminando duplicados y espacios."""

        if not tags:
            return []

        cleaned: List[str] = []
        seen = set()
        for tag in tags:
            name = (tag or "").strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(name)
        return cleaned

    @staticmethod
    def _prepare_splits(splits: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Filtra y normaliza los detalles de una transacción dividida."""

        if not splits:
            return []

        prepared: List[Dict[str, Any]] = []
        for split in splits:
            category = (split or {}).get("category", "").strip()
            amount_value = (split or {}).get("amount", 0)
            try:
                amount = float(amount_value)
            except (TypeError, ValueError):
                amount = 0.0

            if not category or amount <= 0:
                continue

            prepared.append({"category": category, "amount": amount})

        return prepared

    @staticmethod
    def _iter_transaction_allocations(transactions: List[Transaction]):
        """Genera tuplas (transacción, monto, categoría) considerando splits."""

        for transaction in transactions:
            if getattr(transaction, "is_transfer", False):
                continue

            split_items = list(getattr(transaction, "splits", []))
            if split_items:
                for split in split_items:
                    amount = float(getattr(split, "amount", 0) or 0)
                    yield transaction, amount, getattr(split, "category", "")
            else:
                amount = float(getattr(transaction, "amount", 0) or 0)
                yield transaction, amount, getattr(transaction, "category", "")

    def _sync_transaction_splits(
        self, transaction: Transaction, splits: List[Dict[str, Any]]
    ) -> None:
        """Reemplaza los splits asociados a una transacción."""

        TransactionSplit.delete().where(
            TransactionSplit.transaction == transaction
        ).execute()

        if not splits:
            return

        TransactionSplit.insert_many(
            [
                {
                    "transaction": transaction.id,
                    "category": split["category"],
                    "amount": split["amount"],
                }
                for split in splits
            ]
        ).execute()

    def _sync_transaction_tags(
        self, transaction: Transaction, tags: List[str]
    ) -> None:
        """Actualiza las etiquetas vinculadas a una transacción."""

        TransactionTag.delete().where(
            TransactionTag.transaction == transaction
        ).execute()

        if not tags:
            return

        for tag_name in tags:
            tag, _ = Tag.get_or_create(name=tag_name)
            TransactionTag.get_or_create(transaction=transaction, tag=tag)

    def format_currency(self, value):
        """
        Formatea un valor numérico como moneda, con abreviaturas.
        Devuelve un diccionario para ser fácilmente convertido a JSON.
        """
        # Esta función puede ser llamada por cualquier endpoint que devuelva valores monetarios.
        abbreviate = False
        threshold = 1_000_000
        try:
            abbreviate_param = Parameter.get(Parameter.group == 'Display', Parameter.value == 'AbbreviateNumbers')
            if hasattr(abbreviate_param, 'extra_data') and abbreviate_param.extra_data is not None:
                abbreviate = bool(int(abbreviate_param.extra_data))
            
            threshold_param = Parameter.get(Parameter.group == 'Display', Parameter.value == 'AbbreviationThreshold')
            if hasattr(threshold_param, 'extra_data') and threshold_param.extra_data is not None:
                threshold = int(threshold_param.extra_data)
        except Parameter.DoesNotExist:
            pass

        full_text = f"${value:,.2f}"

        if abbreviate and abs(value) >= threshold:
            if abs(value) >= 1_000_000_000:
                display_text = f"${value / 1_000_000_000:.2f}B"
            elif abs(value) >= 1_000_000:
                display_text = f"${value / 1_000_000:.2f}M"
            elif abs(value) >= 1_000:
                display_text = f"${value / 1_000:.1f}k"
            else:
                display_text = full_text
            return {"display": display_text, "tooltip": full_text}
        else:
            return {"display": full_text, "tooltip": full_text}

    # =================================================================
    # --- SECCIÓN: DASHBOARD ---
    # =================================================================
    
    def get_dashboard_data(self, year: int, months: Optional[List[int]]):
        """Agrega y devuelve todos los datos necesarios para el Dashboard."""

        month_list = list(months) if months else []
        transactions = self._get_transactions_for_period(year, month_list)

        kpis = self._get_dashboard_kpis(year, month_list, transactions)
        net_worth_data = self._get_net_worth_data_for_chart()
        cash_flow_data = self._get_cash_flow_data_for_chart(year, month_list)

        goals_summary = self.get_goals_summary()
        debts_summary = self.get_debts_summary()
        upcoming_budget_payments = self.get_upcoming_budget_payments()

        accounts_summary = [
            {
                "id": account.id,
                "name": account.name,
                "account_type": account.account_type,
                "initial_balance": float(account.initial_balance or 0),
                "current_balance": float(account.current_balance or 0),
                "is_virtual": False,
            }
            for account in Account.select().order_by(Account.name)
        ]
        accounts_summary.append(self._build_virtual_budget_account())

        budget_vs_actual = self._get_budget_vs_actual_summary(year, month_list, transactions)
        budget_rule_control = self._get_budget_rule_control(transactions, kpis["income"]["amount"])
        expense_distribution = self._get_expense_distribution(transactions)
        expense_type_comparison = self._get_expense_type_comparison(transactions)

        dashboard_data = {
            "kpis": kpis,
            "net_worth_chart": net_worth_data,
            "cash_flow_chart": cash_flow_data,
            "goals": goals_summary,
            "debts": debts_summary,
            "accounts": accounts_summary,
            "budget_vs_actual": budget_vs_actual,
            "budget_rule_control": budget_rule_control,
            "expense_distribution": expense_distribution,
            "expense_type_comparison": expense_type_comparison,
            "upcoming_budget_payments": upcoming_budget_payments,
        }
        return dashboard_data

    def _get_dashboard_kpis(
        self,
        year: int,
        months: List[int],
        transactions: Optional[List[Transaction]] = None,
    ):
        """Calcula los KPIs de ingresos, gastos y ahorro para el período seleccionado."""

        start_date, end_date = self._get_date_range(year, months)

        if transactions is None:
            query = (
                Transaction.select()
                .where((Transaction.date >= start_date) & (Transaction.date <= end_date))
                .order_by(Transaction.date)
            )
            transactions = self._prefetch_transactions(query)

        relevant = [t for t in transactions if not getattr(t, "is_transfer", False)]
        income = sum(float(t.amount or 0) for t in relevant if t.type == "Ingreso")
        expense = sum(
            abs(float(t.amount or 0)) for t in relevant if t.type != "Ingreso"
        )
        net = income - expense

        num_months = len(months) if months else 12
        previous_start = start_date - relativedelta(months=num_months)
        previous_end = start_date - relativedelta(days=1)

        previous_query = (
            Transaction.select()
            .where(Transaction.date.between(previous_start, previous_end))
            .order_by(Transaction.date)
        )
        previous_trans = self._prefetch_transactions(previous_query)
        prev_relevant = [
            t for t in previous_trans if not getattr(t, "is_transfer", False)
        ]
        prev_income = sum(
            float(t.amount or 0) for t in prev_relevant if t.type == "Ingreso"
        )
        prev_expense = sum(
            abs(float(t.amount or 0)) for t in prev_relevant if t.type != "Ingreso"
        )
        prev_net = prev_income - prev_expense

        def _comparison(current_value, previous_value):
            if previous_value is None or previous_value == 0:
                return None
            return ((current_value - previous_value) / abs(previous_value)) * 100

        return {
            "income": {"amount": income, "comparison": _comparison(income, prev_income)},
            "expense": {"amount": expense, "comparison": _comparison(expense, prev_expense)},
            "net": {"amount": net, "comparison": _comparison(net, prev_net)},
        }

    def _get_net_worth_data_for_chart(self):
        """Prepara datos históricos del patrimonio neto usando el movimiento real."""
        today = datetime.date.today()

        accounts = list(Account.select())
        debts = list(Debt.select())
        transactions = self._prefetch_transactions(
            Transaction.select().order_by(Transaction.date.asc(), Transaction.id.asc())
        )

        account_running: Dict[int, float] = {
            account.id: float(account.initial_balance or 0.0)
            for account in accounts
        }

        # Calcula el saldo inicial de cada deuda sumando los pagos registrados
        total_debt_payments: Dict[int, float] = defaultdict(float)
        for transaction in transactions:
            if transaction.debt_id:
                total_debt_payments[transaction.debt_id] += float(
                    transaction.amount or 0.0
                )

        debt_running: Dict[int, float] = {}
        for debt in debts:
            base_balance = float(debt.current_balance or 0.0)
            paid_total = total_debt_payments.get(debt.id, 0.0)
            debt_running[debt.id] = max(0.0, base_balance + paid_total)

        month_points: List[datetime.date] = []
        current_month_start = today.replace(day=1)
        for offset in range(12, -1, -1):
            month_start = current_month_start - relativedelta(months=offset)
            month_end = (month_start + relativedelta(months=1)) - datetime.timedelta(days=1)
            if month_end > today:
                month_end = today
            month_points.append(month_end)

        cursor = 0
        dates: List[str] = []
        values: List[float] = []
        for month_end in month_points:
            while cursor < len(transactions) and transactions[cursor].date <= month_end:
                tx = transactions[cursor]
                amount = float(tx.amount or 0.0)
                amount_abs = abs(amount)
                tx_type = (tx.type or "").strip().lower()

                if getattr(tx, "is_transfer", False):
                    source_id = getattr(tx, "account_id", None)
                    target = getattr(tx, "transfer_account", None)
                    if source_id:
                        account_running[source_id] = account_running.get(source_id, 0.0) - amount_abs
                    if target is not None:
                        dest_id = getattr(target, "id", None)
                        if dest_id is not None:
                            account_running[dest_id] = account_running.get(dest_id, 0.0) + amount_abs
                    cursor += 1
                    continue

                if tx.account_id:
                    if tx_type == "ingreso":
                        account_running[tx.account_id] = account_running.get(tx.account_id, 0.0) + amount_abs
                    else:
                        account_running[tx.account_id] = account_running.get(tx.account_id, 0.0) - amount_abs

                if tx.debt_id and tx_type != "ingreso":
                    debt_running[tx.debt_id] = max(0.0, debt_running.get(tx.debt_id, 0.0) - amount_abs)

                cursor += 1

            total_assets = sum(account_running.values())
            total_liabilities = sum(debt_running.values())

            dates.append(month_end.strftime("%Y-%m-%d"))
            values.append(total_assets - total_liabilities)

        return {"dates": dates, "values": values}

    def _get_cash_flow_data_for_chart(self, year: int, months: List[int]):
        """Prepara los datos para el gráfico de flujo de efectivo mensual."""
        start_date, end_date = self._get_date_range(year, months)

        query = (
            Transaction
            .select(fn.strftime('%Y-%m', Transaction.date).alias('month'),
                    fn.SUM(Transaction.amount).alias('total'),
                    Transaction.type)
            .where(
                (Transaction.date >= start_date)
                & (Transaction.date <= end_date)
                & (Transaction.is_transfer == False)
            )
            .group_by(fn.strftime('%Y-%m', Transaction.date), Transaction.type)
            .order_by(fn.strftime('%Y-%m', Transaction.date))
        )

        monthly_data: Dict[str, Dict[str, float]] = defaultdict(lambda: {'income': 0.0, 'expense': 0.0})
        for row in query.dicts():
            month_key = row['month']
            amount = float(row['total'] or 0)
            if row['type'] == 'Ingreso':
                monthly_data[month_key]['income'] = amount
            else:
                monthly_data[month_key]['expense'] += abs(amount)

        sorted_items = sorted(monthly_data.items())
        labels = [month for month, _ in sorted_items]
        income_data = [values['income'] for _, values in sorted_items]
        expense_data = [values['expense'] for _, values in sorted_items]

        return {
            "months": labels,
            "income": income_data,
            "expense": expense_data,
        }

    def _get_transactions_for_period(self, year: int, months: List[int]) -> List[Transaction]:
        """Obtiene las transacciones dentro del periodo seleccionado."""

        start_date, end_date = self._get_date_range(year, months)
        query = (
            Transaction.select()
            .where(Transaction.date.between(start_date, end_date))
            .order_by(Transaction.date)
        )
        return self._prefetch_transactions(query)

    def _get_budget_vs_actual_summary(
        self,
        year: int,
        months: List[int],
        transactions: List[Transaction],
    ):
        """Construye el resumen de presupuesto vs. gasto real para ingresos y gastos."""

        start_date, end_date = self._get_date_range(year, months)
        budgeted_income = 0.0
        budgeted_expense = 0.0
        actual_income = 0.0
        actual_expense = 0.0

        for entry in BudgetEntry.select():
            period_start, period_end = self._resolve_entry_bounds(entry)
            if period_start > end_date or period_end < start_date:
                continue

            planned = float(getattr(entry, "budgeted_amount", 0) or 0)
            actual = float(getattr(entry, "actual_amount", 0) or 0)

            if (entry.type or "").strip().lower() == "ingreso":
                budgeted_income += planned
                actual_income += actual
            else:
                budgeted_expense += planned
                actual_expense += actual

        def _build_summary(budgeted: float, actual: float) -> Dict[str, Optional[float]]:
            execution = (actual / budgeted * 100) if budgeted else None
            return {
                "budgeted": budgeted,
                "actual": actual,
                "difference": actual - budgeted,
                "remaining": budgeted - actual,
                "execution": execution,
            }

        return {
            "income": _build_summary(budgeted_income, actual_income),
            "expense": _build_summary(budgeted_expense, actual_expense),
        }

    def _get_budget_rule_control(self, transactions: List[Transaction], total_income: float):
        """Calcula el cumplimiento de las reglas de presupuesto basadas en el ingreso."""

        parameters = Parameter.select().where(Parameter.group == "Tipo de Transacción")
        type_to_rule = {}
        for param in parameters:
            if param.budget_rule_id:
                type_to_rule[param.value] = param.budget_rule

        totals: Dict[str, float] = defaultdict(float)
        for transaction in transactions:
            if getattr(transaction, 'is_transfer', False):
                continue
            if transaction.type == "Ingreso":
                continue
            amount = abs(float(transaction.amount or 0))
            rule = type_to_rule.get(transaction.type)
            if rule:
                totals[rule.name] += amount
            else:
                totals['Sin Regla'] += amount

        results = []
        for rule in BudgetRule.select().order_by(BudgetRule.id):
            actual_amount = totals.pop(rule.name, 0.0)
            actual_percent = (actual_amount / total_income * 100) if total_income else 0.0
            if total_income == 0:
                state = 'neutral'
            elif actual_percent <= rule.percentage * 0.95:
                state = 'ok'
            elif actual_percent <= rule.percentage * 1.1:
                state = 'warning'
            else:
                state = 'critical'

            results.append({
                "name": rule.name,
                "ideal_percent": rule.percentage,
                "actual_amount": actual_amount,
                "actual_percent": actual_percent,
                "state": state,
            })

        other_amount = totals.pop('Sin Regla', 0.0)
        if other_amount:
            actual_percent = (other_amount / total_income * 100) if total_income else 0.0
            results.append({
                "name": 'Sin Regla',
                "ideal_percent": 0.0,
                "actual_amount": other_amount,
                "actual_percent": actual_percent,
                "state": 'warning' if actual_percent else 'neutral',
            })

        return results

    def _get_expense_distribution(self, transactions: List[Transaction]):
        """Distribución de gastos por categoría para gráficas de barras."""

        totals: Dict[str, float] = defaultdict(float)
        for transaction, amount, category in self._iter_transaction_allocations(transactions):
            if transaction.type == 'Ingreso':
                continue
            label = category or 'Sin categoría'
            totals[label] += abs(amount)

        sorted_items = sorted(totals.items(), key=lambda item: item[1], reverse=True)
        categories = [item[0] for item in sorted_items]
        amounts = [item[1] for item in sorted_items]

        return {"categories": categories, "amounts": amounts}

    def _get_expense_type_comparison(self, transactions: List[Transaction]):
        """Distribución de gastos por tipo (ej. fijo, variable)."""

        totals: Dict[str, float] = defaultdict(float)
        for transaction in transactions:
            if getattr(transaction, 'is_transfer', False):
                continue
            if transaction.type == 'Ingreso':
                continue
            label = transaction.type or 'Sin tipo'
            totals[label] += abs(float(transaction.amount or 0))

        sorted_items = sorted(totals.items(), key=lambda item: item[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        amounts = [item[1] for item in sorted_items]

        return {"labels": labels, "amounts": amounts}

    def get_cash_flow_analysis(self, year: Optional[int] = None, month: Optional[int] = None):
        """Obtiene el flujo de efectivo agrupado por categoría para un período."""
        today = datetime.date.today()
        if year is None:
            year = today.year

        month_list = [month] if month else list(range(1, 13))
        transactions = self._get_transactions_for_period(year, month_list)

        income_totals: Dict[str, float] = defaultdict(float)
        expense_totals: Dict[str, float] = defaultdict(float)

        for transaction, amount, category in self._iter_transaction_allocations(transactions):
            label = category or 'Sin categoría'
            if transaction.type == 'Ingreso':
                income_totals[label] += amount
            else:
                expense_totals[label] += abs(amount)

        income = [
            {"category": category, "amount": total}
            for category, total in income_totals.items()
        ]
        expenses = [
            {"category": category, "amount": total}
            for category, total in expense_totals.items()
        ]

        income.sort(key=lambda item: item["amount"], reverse=True)
        expenses.sort(key=lambda item: item["amount"], reverse=True)

        return {"income": income, "expenses": expenses}


    # =================================================================
    # --- SECCIÓN: ANÁLISIS FINANCIERO ---
    # =================================================================

    def get_analysis_overview(
        self,
        year: Optional[int] = None,
        months: Optional[List[int]] = None,
        projection_months: int = 12,
    ) -> Dict[str, Any]:
        """Compone los datos necesarios para la sección de análisis."""

        today = datetime.date.today()
        if year is None:
            year = today.year

        month_list = sorted(set(months)) if months else list(range(1, 13))
        transactions = self._get_transactions_for_period(year, month_list)

        annual_expense_report = self._build_annual_expense_report(year, month_list)
        budget_analysis = self._build_budget_analysis(year, month_list, transactions)
        cash_flow_projection = self._build_cash_flow_projection(
            year, month_list, projection_months, transactions
        )
        income_allocation = self._build_income_allocation_analysis(
            year, month_list, transactions
        )

        return {
            "year": year,
            "months": month_list,
            "annual_expense_report": annual_expense_report,
            "budget_analysis": budget_analysis,
            "cash_flow_projection": cash_flow_projection,
            "income_allocation": income_allocation,
        }

    def _build_annual_expense_report(self, year: int, months: List[int]) -> Dict[str, Any]:
        """Genera una tabla de gastos anuales agrupados por categoría y mes."""

        month_list = sorted(set(months)) if months else list(range(1, 13))
        transactions = self._get_transactions_for_period(year, month_list)

        rows: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        monthly_totals: Dict[int, float] = defaultdict(float)

        for transaction, amount, category in self._iter_transaction_allocations(transactions):
            if transaction.type == 'Ingreso':
                continue
            month_number = int(transaction.date.month)
            if month_number not in month_list:
                continue
            label = category or 'Sin categoría'
            value = abs(amount)
            rows[label][month_number] += value
            monthly_totals[month_number] += value

        ordered_months = month_list
        month_headers = [
            {"number": month, "label": MONTH_LABELS[month]}
            for month in ordered_months
        ]

        table_rows = []
        for category, values in rows.items():
            monthly_values = [values.get(month, 0.0) for month in ordered_months]
            total = sum(monthly_values)
            table_rows.append(
                {
                    "category": category,
                    "values": monthly_values,
                    "total": total,
                }
            )

        table_rows.sort(key=lambda row: row["total"], reverse=True)

        totals_by_month = [monthly_totals.get(month, 0.0) for month in ordered_months]
        grand_total = sum(totals_by_month)

        return {
            "months": month_headers,
            "rows": table_rows,
            "monthly_totals": totals_by_month,
            "grand_total": grand_total,
        }

    def _build_budget_analysis(
        self,
        year: int,
        months: List[int],
        transactions: List[Transaction],
    ) -> Dict[str, Any]:
        """Compara presupuesto anual vs gasto real agrupado por regla."""

        start_date, end_date = self._get_date_range(year, months)

        parameters = Parameter.select().where(Parameter.group == "Tipo de Transacción")
        type_to_rule: Dict[str, Optional[BudgetRule]] = {}
        for param in parameters:
            type_to_rule[param.value] = param.budget_rule if param.budget_rule_id else None

        budget_totals: Dict[str, float] = defaultdict(float)
        actual_totals: Dict[str, float] = defaultdict(float)

        for entry in BudgetEntry.select():
            period_start, period_end = self._resolve_entry_bounds(entry)
            if period_start > end_date or period_end < start_date:
                continue

            rule = type_to_rule.get(entry.type)
            rule_name = rule.name if rule else (entry.type or 'Sin Regla')

            planned = float(getattr(entry, 'budgeted_amount', 0) or 0)
            actual = float(getattr(entry, 'actual_amount', 0) or 0)

            budget_totals[rule_name] += planned
            actual_totals[rule_name] += actual

        rows = []
        total_budgeted = 0.0
        total_actual = 0.0

        for rule in BudgetRule.select().order_by(BudgetRule.id):
            budgeted = budget_totals.pop(rule.name, 0.0)
            actual = actual_totals.pop(rule.name, 0.0)
            difference = actual - budgeted
            compliance = (actual / budgeted * 100) if budgeted else None
            rows.append(
                {
                    "name": rule.name,
                    "budgeted": budgeted,
                    "actual": actual,
                    "difference": difference,
                    "compliance": compliance,
                    "ideal_percent": rule.percentage,
                }
            )
            total_budgeted += budgeted
            total_actual += actual

        # Add any remaining categories not tied to a configured rule
        for remaining_name, budgeted in budget_totals.items():
            actual = actual_totals.pop(remaining_name, 0.0)
            difference = actual - budgeted
            compliance = (actual / budgeted * 100) if budgeted else None
            rows.append(
                {
                    "name": remaining_name,
                    "budgeted": budgeted,
                    "actual": actual,
                    "difference": difference,
                    "compliance": compliance,
                    "ideal_percent": None,
                }
            )
            total_budgeted += budgeted
            total_actual += actual

        for remaining_name, actual in actual_totals.items():
            rows.append(
                {
                    "name": remaining_name,
                    "budgeted": 0.0,
                    "actual": actual,
                    "difference": actual,
                    "compliance": None,
                    "ideal_percent": None,
                }
            )
            total_actual += actual

        rows.sort(key=lambda row: row["actual"], reverse=True)

        total_difference = total_actual - total_budgeted
        total_compliance = (
            (total_actual / total_budgeted * 100) if total_budgeted else None
        )

        return {
            "rows": rows,
            "total_budgeted": total_budgeted,
            "total_actual": total_actual,
            "total_difference": total_difference,
            "total_compliance": total_compliance,
        }

    def _build_income_allocation_analysis(
        self,
        year: int,
        months: List[int],
        transactions: List[Transaction],
    ) -> Dict[str, Any]:
        """Resume ingresos mensuales y su asignación ideal vs real por reglas."""

        month_list = sorted(set(months)) if months else list(range(1, 13))
        month_headers = [
            {"number": month, "label": MONTH_LABELS[month]}
            for month in month_list
        ]
        month_set = set(month_list)

        income_by_month = {month: 0.0 for month in month_list}
        actual_spent_by_month = {month: 0.0 for month in month_list}

        parameters = Parameter.select().where(Parameter.group == "Tipo de Transacción")
        type_to_rule: Dict[str, Optional[BudgetRule]] = {}
        for param in parameters:
            type_to_rule[param.value] = param.budget_rule if param.budget_rule_id else None

        rules = list(BudgetRule.select().order_by(BudgetRule.id))
        rule_percentages: Dict[str, float] = {
            rule.name: float(getattr(rule, 'percentage', 0) or 0)
            for rule in rules
        }
        rule_order = [rule.name for rule in rules]

        def _fresh_month_totals() -> Dict[int, float]:
            return {month: 0.0 for month in month_list}

        actual_by_rule: Dict[str, Dict[int, float]] = {}

        for transaction, amount, _ in self._iter_transaction_allocations(transactions):
            month_number = int(transaction.date.month)
            if month_number not in month_set:
                continue

            amount_value = float(amount or 0)

            if transaction.type == "Ingreso":
                income_amount = amount_value if amount_value >= 0 else abs(amount_value)
                income_by_month[month_number] += income_amount
                continue

            spend_value = abs(amount_value)
            actual_spent_by_month[month_number] += spend_value

            mapped_rule = type_to_rule.get(transaction.type)
            rule_name = (
                mapped_rule.name
                if mapped_rule
                else (transaction.type or "Sin regla")
            )
            rule_totals = actual_by_rule.setdefault(rule_name, _fresh_month_totals())
            rule_totals[month_number] = rule_totals.get(month_number, 0.0) + spend_value

        additional_rules = [
            name for name in actual_by_rule.keys() if name not in rule_percentages
        ]
        additional_rules.sort()
        row_order = rule_order + additional_rules

        recommended_by_rule: Dict[str, Dict[int, float]] = {}
        for name in row_order:
            percentage = rule_percentages.get(name, 0.0)
            recommended_by_rule[name] = {
                month: income_by_month.get(month, 0.0) * (percentage / 100.0)
                for month in month_list
            }

        recommended_rows = []
        for name in row_order:
            monthly_values = [recommended_by_rule[name][month] for month in month_list]
            total_value = sum(monthly_values)
            recommended_rows.append(
                {
                    "rule": name,
                    "percentage": rule_percentages.get(name),
                    "share": None,
                    "values": monthly_values,
                    "total": total_value,
                }
            )

        total_actual_spent = sum(actual_spent_by_month.values())

        actual_rows = []
        for name in row_order:
            month_totals = actual_by_rule.get(name, _fresh_month_totals())
            monthly_values = [month_totals.get(month, 0.0) for month in month_list]
            total_value = sum(monthly_values)
            share = None
            if total_actual_spent > 0:
                share = (total_value / total_actual_spent) * 100
            actual_rows.append(
                {
                    "rule": name,
                    "percentage": rule_percentages.get(name),
                    "share": share,
                    "values": monthly_values,
                    "total": total_value,
                }
            )

        monthly_recommended_totals = [
            sum(recommended_by_rule[name][month] for name in row_order)
            for month in month_list
        ]
        monthly_actual_totals = [
            sum(actual_by_rule.get(name, {}).get(month, 0.0) for name in row_order)
            for month in month_list
        ]

        monthly_balances = []
        for index, month in enumerate(month_list):
            monthly_balances.append(
                {
                    "month": month,
                    "label": MONTH_LABELS[month],
                    "income": income_by_month.get(month, 0.0),
                    "recommended_spend": monthly_recommended_totals[index],
                    "actual_spend": monthly_actual_totals[index],
                    "net": income_by_month.get(month, 0.0)
                    - monthly_actual_totals[index],
                }
            )

        total_income = sum(income_by_month.values())
        total_recommended = sum(monthly_recommended_totals)

        return {
            "months": month_headers,
            "monthly_income": [income_by_month[month] for month in month_list],
            "total_income": total_income,
            "recommended_rows": recommended_rows,
            "actual_rows": actual_rows,
            "recommended_totals": {
                "monthly": monthly_recommended_totals,
                "total": total_recommended,
            },
            "actual_totals": {
                "monthly": monthly_actual_totals,
                "total": total_actual_spent,
            },
            "monthly_balances": monthly_balances,
            "period_balance": {
                "income": total_income,
                "recommended_spend": total_recommended,
                "actual_spend": total_actual_spent,
                "net": total_income - total_actual_spent,
            },
        }

    def _build_cash_flow_projection(
        self,
        year: int,
        months: List[int],
        projection_months: int,
        transactions: List[Transaction],
    ) -> Dict[str, Any]:
        """Calcula una proyección lineal del saldo total de cuentas."""

        month_list = sorted(set(months)) if months else list(range(1, 13))

        monthly_net: Dict[int, float] = defaultdict(float)
        for transaction in transactions:
            if getattr(transaction, 'is_transfer', False):
                continue
            month = int(transaction.date.month)
            amount = float(transaction.amount or 0)
            if transaction.type == 'Ingreso':
                monthly_net[month] += amount
            else:
                monthly_net[month] -= abs(amount)

        if month_list:
            total_net = sum(monthly_net.get(month, 0.0) for month in month_list)
            average_flow = total_net / len(month_list)
        else:
            average_flow = 0.0

        starting_balance = sum(float(acc.current_balance or 0) for acc in Account.select())

        start_date, end_date = self._get_date_range(year, months)
        next_month = end_date + relativedelta(months=1)

        projection_points = []
        balance = starting_balance
        for _ in range(max(projection_months, 0)):
            balance += average_flow
            label = f"{MONTH_LABELS[next_month.month]} {next_month.year}"
            projection_points.append({"label": label, "balance": balance})
            next_month = next_month + relativedelta(months=1)

        return {
            "starting_balance": starting_balance,
            "average_monthly_flow": average_flow,
            "projection_months": projection_months,
            "points": projection_points,
        }


    # =================================================================
    # --- SECCIÓN: CUENTAS (Accounts) ---
    # =================================================================

    def get_accounts_data_for_view(self):
        """Devuelve una lista de todas las cuentas."""
        today = datetime.date.today()
        real_accounts: List[Dict[str, Any]] = []

        for account in Account.select().order_by(Account.name):
            self._apply_interest_for_account(account, today)
            real_accounts.append(
                {
                    "id": account.id,
                    "name": account.name,
                    "account_type": account.account_type,
                    "initial_balance": float(account.initial_balance or 0),
                    "current_balance": float(account.current_balance or 0),
                    "annual_interest_rate": float(
                        getattr(account, "annual_interest_rate", 0) or 0
                    ),
                    "compounding_frequency": getattr(
                        account, "compounding_frequency", "Mensual"
                    ),
                    "last_interest_accrual": getattr(
                        account, "last_interest_accrual", None
                    ).isoformat()
                    if getattr(account, "last_interest_accrual", None)
                    else None,
                    "is_virtual": False,
                }
            )

        virtual = self._build_virtual_budget_account(today)
        return [virtual, *real_accounts]

    def add_account(self, data):
        """Crea una nueva cuenta."""
        try:
            name = data.get("name", "").strip()
            account_type = data.get("account_type", "").strip()
            if not name:
                return {"error": "El nombre de la cuenta es obligatorio."}
            if not account_type:
                return {"error": "El tipo de cuenta es obligatorio."}

            balance = float(data.get("initial_balance", 0) or 0)
            normalized_target = self._normalize_label(name)
            duplicate = any(
                self._normalize_label(existing.name) == normalized_target
                for existing in Account.select(Account.name)
            )
            if duplicate:
                return {"error": "Ya existe una cuenta con ese nombre."}

            rate_value = float(data.get("annual_interest_rate", 0) or 0)
            if rate_value < 0:
                return {"error": "La tasa anual no puede ser negativa."}

            comp_frequency = self._normalize_compounding_frequency(
                data.get("compounding_frequency")
            )

            is_savings = self._is_savings_account_type(account_type)
            if not is_savings:
                rate_value = 0.0
                comp_frequency = "Mensual"
                last_interest = None
            else:
                last_interest = datetime.date.today() if rate_value > 0 else None

            account = Account.create(
                name=name,
                account_type=account_type,
                initial_balance=balance,
                current_balance=balance,
                annual_interest_rate=rate_value,
                compounding_frequency=comp_frequency,
                last_interest_accrual=last_interest,
            )
            return account.__data__
        except (ValueError, KeyError) as e:
            return {"error": f"Datos inválidos: {e}"}

    def update_account(self, account_id: int, data):
        """Actualiza los datos básicos de una cuenta."""
        try:
            account = Account.get_by_id(account_id)
        except Account.DoesNotExist:
            return {"error": "La cuenta no existe."}

        updates = {}
        try:
            if "name" in data:
                name = data["name"].strip()
                if not name:
                    return {"error": "El nombre de la cuenta es obligatorio."}
                normalized_target = self._normalize_label(name)
                duplicate = any(
                    self._normalize_label(existing.name) == normalized_target
                    and existing.id != account_id
                    for existing in Account.select(Account.id, Account.name)
                )
                if duplicate:
                    return {"error": "Ya existe una cuenta con ese nombre."}
                updates["name"] = name

            if "account_type" in data:
                account_type = data["account_type"].strip()
                if not account_type:
                    return {"error": "El tipo de cuenta es obligatorio."}
                updates["account_type"] = account_type

            if "initial_balance" in data:
                return {"error": "El saldo inicial no se puede modificar."}

            if "current_balance" in data:
                updates["current_balance"] = float(data["current_balance"] or 0)

            target_type = updates.get("account_type", account.account_type)
            is_savings = self._is_savings_account_type(target_type)

            rate_payload = data.get("annual_interest_rate", None)
            if rate_payload is not None:
                rate_value = float(rate_payload or 0)
                if rate_value < 0:
                    return {"error": "La tasa anual no puede ser negativa."}
            else:
                rate_value = float(getattr(account, "annual_interest_rate", 0) or 0)

            frequency_payload = data.get("compounding_frequency", None)
            if frequency_payload is not None:
                frequency_value = self._normalize_compounding_frequency(frequency_payload)
            else:
                frequency_value = getattr(account, "compounding_frequency", "Mensual") or "Mensual"

            if not is_savings:
                rate_value = 0.0
                frequency_value = "Mensual"
                last_interest_value = None
            else:
                if rate_value > 0:
                    last_interest_value = getattr(account, "last_interest_accrual", None)
                    if last_interest_value is None:
                        last_interest_value = datetime.date.today()
                else:
                    last_interest_value = datetime.date.today()

            if (
                rate_payload is not None
                or not is_savings
                or rate_value != float(getattr(account, "annual_interest_rate", 0) or 0)
            ):
                updates["annual_interest_rate"] = rate_value

            if (
                frequency_payload is not None
                or not is_savings
                or frequency_value
                != (getattr(account, "compounding_frequency", "Mensual") or "Mensual")
            ):
                updates["compounding_frequency"] = frequency_value

            if (
                not is_savings
                or last_interest_value
                != getattr(account, "last_interest_accrual", None)
            ):
                updates["last_interest_accrual"] = last_interest_value

            if updates:
                Account.update(updates).where(Account.id == account_id).execute()

            return Account.get_by_id(account_id).__data__
        except (TypeError, ValueError) as e:
            return {"error": f"Datos inválidos: {e}"}

    def delete_account(self, account_id):
        """Elimina una cuenta si no tiene transacciones y su saldo es cero."""
        try:
            account = Account.get_by_id(account_id)
            if Transaction.select().where(Transaction.account == account).count() > 0:
                return {"error": "No se puede eliminar una cuenta con transacciones."}
            if account.current_balance != 0:
                return {"error": "No se puede eliminar una cuenta con saldo diferente de cero."}
            
            account.delete_instance()
            return {"success": True}
        except Account.DoesNotExist:
            return {"error": "La cuenta no existe."}

    def get_account_types(self):
        """Obtiene la lista de tipos de cuenta configurados."""
        return [
            param["value"]
            for param in Parameter.select()
            .where(Parameter.group == "Tipo de Cuenta")
            .order_by(Parameter.id)
            .dicts()
        ]
        
    # =================================================================
    # --- SECCIÓN: LÓGICA DE TRANSACCIONES RECURRENTES ---
    # =================================================================
    def process_recurring_transactions(self):
        """
        Procesa las reglas de transacciones recurrentes para crear
        transacciones nuevas si su fecha ha llegado.
        """
        print("Procesando transacciones recurrentes al inicio...")
        today = datetime.date.today()
        first_account = Account.select().first()
        if not first_account:
            print("No hay cuentas, se omite el procesamiento de transacciones recurrentes.")
            return False

        for rule in RecurringTransaction.select():
            start_from = rule.last_processed_date or rule.start_date
            if start_from > today:
                continue

            next_due_date = None
            if rule.frequency == "Mensual":
                next_due_date = start_from + relativedelta(months=1)
            elif rule.frequency == "Anual":
                next_due_date = start_from + relativedelta(years=1)

            if next_due_date and next_due_date <= today:
                Transaction.create(
                    date=next_due_date, description=rule.description, amount=rule.amount,
                    type=rule.type, category=rule.category, account=first_account,
                )
                
                if rule.type == "Ingreso":
                    first_account.current_balance += rule.amount
                else:
                    first_account.current_balance -= rule.amount
                first_account.save()
                
                rule.last_processed_date = next_due_date
                rule.save()
                print(f"Transacción recurrente '{rule.description}' procesada para la fecha {next_due_date}.")
        return True

    # =================================================================
    # --- SECCIÓN: TRANSACCIONES (Transactions) ---
    # =================================================================

    def get_transactions_data(self, filters=None):
        query = Transaction.select()

        if filters:
            if filters.get('search'):
                query = query.where(Transaction.description.contains(filters['search']))
            if filters.get('start_date'):
                query = query.where(Transaction.date >= filters['start_date'])
            if filters.get('end_date'):
                query = query.where(Transaction.date <= filters['end_date'])
            if filters.get('type'):
                query = query.where(Transaction.type == filters['type'])
            if filters.get('category'):
                category_value = filters['category']
                split_match = (
                    TransactionSplit.select(TransactionSplit.transaction_id)
                    .where(TransactionSplit.category == category_value)
                )
                query = query.where(
                    (Transaction.category == category_value)
                    | (Transaction.id.in_(split_match))
                )
            if filters.get('tags'):
                tags = [tag for tag in filters['tags'] if tag]
                if tags:
                    tag_match = (
                        TransactionTag.select(TransactionTag.transaction_id)
                        .join(Tag)
                        .where(Tag.name.in_(tags))
                    )
                    query = query.where(Transaction.id.in_(tag_match))

            sort_by = filters.get('sort_by', 'date_desc')
            if sort_by == 'date_asc':
                query = query.order_by(Transaction.date.asc(), Transaction.id.asc())
            elif sort_by == 'amount_desc':
                query = query.order_by(Transaction.amount.desc(), Transaction.id.desc())
            elif sort_by == 'amount_asc':
                query = query.order_by(Transaction.amount.asc(), Transaction.id.asc())
            else:
                query = query.order_by(Transaction.date.desc(), Transaction.id.desc())
        else:
            query = query.order_by(Transaction.date.desc(), Transaction.id.desc())

        transactions = self._prefetch_transactions(query)

        results = []
        for transaction in transactions:
            account = transaction.account
            splits = [
                {
                    "category": split.category,
                    "amount": float(split.amount or 0),
                }
                for split in getattr(transaction, 'splits', [])
            ]
            tags = [
                link.tag.name
                for link in getattr(transaction, 'tag_links', [])
                if link.tag is not None
            ]
            transfer_account = getattr(transaction, 'transfer_account', None)
            receipts = [
                self._serialize_receipt(receipt)
                for receipt in getattr(transaction, "receipts", [])
            ]

            transaction_data = {
                "id": transaction.id,
                "date": transaction.date.isoformat(),
                "description": transaction.description,
                "amount": float(transaction.amount or 0),
                "type": transaction.type,
                "portfolio_direction": getattr(transaction, 'portfolio_direction', None),
                "category": transaction.category,
                "account_id": transaction.account_id,
                "account": account.__data__ if account else None,
                "goal_id": transaction.goal.id if transaction.goal else None,
                "goal_name": transaction.goal.name if transaction.goal else None,
                "debt_id": transaction.debt.id if transaction.debt else None,
                "debt_name": transaction.debt.name if transaction.debt else None,
                "budget_entry_id": transaction.budget_entry.id
                if getattr(transaction, "budget_entry", None)
                else None,
                "budget_entry_name": transaction.budget_entry.description
                if getattr(transaction, "budget_entry", None)
                else None,
                "is_transfer": bool(transaction.is_transfer),
                "transfer_account_id": getattr(transfer_account, 'id', None),
                "transfer_account_name": getattr(transfer_account, 'name', None),
                "splits": splits,
                "tags": tags,
                "receipts": receipts,
            }
            results.append(transaction_data)
        return results

    @staticmethod
    def _serialize_receipt(receipt: Receipt) -> Dict[str, Any]:
        """Return a serializable representation of a receipt object."""

        uploaded_at = receipt.uploaded_at.isoformat() if receipt.uploaded_at else None
        return {
            "id": receipt.id,
            "transaction_id": receipt.transaction_id,
            "budget_entry_id": receipt.budget_entry_id,
            "original_filename": receipt.original_filename,
            "content_type": receipt.content_type,
            "file_size": receipt.file_size,
            "uploaded_at": uploaded_at,
            "download_url": f"/api/receipts/{receipt.id}",
        }

    def get_transaction_receipts(self, transaction_id: int):
        """Return every receipt associated with a transaction."""

        try:
            Transaction.get_by_id(transaction_id)
        except Transaction.DoesNotExist:
            return {"error": "La transacción no existe."}

        query = (
            Receipt.select()
            .where(Receipt.transaction_id == transaction_id)
            .order_by(Receipt.uploaded_at.desc())
        )
        return [self._serialize_receipt(receipt) for receipt in query]

    def register_receipt(
        self,
        *,
        file_path: str,
        original_filename: str,
        content_type: Optional[str] = None,
        file_size: Optional[int] = None,
        transaction_id: Optional[int] = None,
        budget_entry_id: Optional[int] = None,
    ):
        """Create a receipt row linked to a transaction or budget entry."""

        if not transaction_id and not budget_entry_id:
            return {"error": "Debes asociar el recibo a una transacción o presupuesto."}

        if transaction_id:
            try:
                Transaction.get_by_id(transaction_id)
            except Transaction.DoesNotExist:
                return {"error": "La transacción especificada no existe."}

        if budget_entry_id:
            try:
                BudgetEntry.get_by_id(budget_entry_id)
            except BudgetEntry.DoesNotExist:
                return {"error": "El presupuesto especificado no existe."}

        receipt = Receipt.create(
            transaction=transaction_id,
            budget_entry=budget_entry_id,
            file_path=file_path,
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
        )
        return self._serialize_receipt(receipt)

    def get_receipt_record(self, receipt_id: int):
        """Return the underlying receipt instance or None."""

        try:
            return Receipt.get_by_id(receipt_id)
        except Receipt.DoesNotExist:
            return None

    def delete_receipt(self, receipt_id: int):
        """Delete a receipt and return its serialized data and storage key."""

        try:
            receipt = Receipt.get_by_id(receipt_id)
        except Receipt.DoesNotExist:
            return None, None, "El recibo solicitado no existe."

        file_path = receipt.file_path
        payload = self._serialize_receipt(receipt)
        receipt.delete_instance()
        return payload, file_path, None


    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Devuelve todas las etiquetas disponibles ordenadas alfabéticamente."""

        return [
            {"id": tag.id, "name": tag.name}
            for tag in Tag.select().order_by(Tag.name.asc())
        ]


    def get_recurring_transactions(self):
        today = datetime.date.today()
        rules = []
        for rule in RecurringTransaction.select().order_by(RecurringTransaction.description):
            next_run = self._calculate_next_occurrence(rule, today)
            rules.append(
                {
                    "id": rule.id,
                    "description": rule.description,
                    "amount": float(rule.amount or 0.0),
                    "type": rule.type,
                    "category": rule.category,
                    "frequency": rule.frequency,
                    "day_of_month": rule.day_of_month,
                    "day_of_month_2": rule.day_of_month_2,
                    "start_date": rule.start_date.isoformat() if rule.start_date else None,
                    "last_processed_date": rule.last_processed_date.isoformat()
                    if rule.last_processed_date
                    else None,
                    "next_run": next_run.isoformat() if next_run else None,
                }
            )
        return rules

    def _calculate_next_occurrence(
        self, rule: RecurringTransaction, reference: datetime.date
    ) -> Optional[datetime.date]:
        if not reference:
            reference = datetime.date.today()

        start = rule.start_date or reference
        frequency = (rule.frequency or "").strip().lower()

        if frequency in ("mensual", "quincenal"):
            candidate_days: List[int] = []
            if rule.day_of_month:
                candidate_days.append(rule.day_of_month)
            if frequency == "quincenal" and rule.day_of_month_2:
                candidate_days.append(rule.day_of_month_2)
            if not candidate_days:
                candidate_days.append(start.day)

            base_month = reference.replace(day=1)
            for offset in range(0, 14):
                month_candidate = base_month + relativedelta(months=offset)
                for day in sorted(candidate_days):
                    last_day = calendar.monthrange(
                        month_candidate.year, month_candidate.month
                    )[1]
                    safe_day = min(day, last_day)
                    candidate = month_candidate.replace(day=safe_day)
                    if candidate < start:
                        continue
                    if candidate >= reference:
                        return candidate
            return None

        if frequency == "semanal":
            anchor = rule.last_processed_date or start
            if anchor >= reference:
                return anchor
            delta_days = (reference - anchor).days
            weeks_ahead = (delta_days + 6) // 7
            return anchor + datetime.timedelta(days=7 * weeks_ahead)

        if frequency == "anual":
            month = rule.month_of_year or start.month
            day = rule.day_of_month or start.day
            year = max(reference.year, start.year)

            def resolve(year_value: int) -> datetime.date:
                month_last_day = calendar.monthrange(year_value, month)[1]
                target_day = min(day, month_last_day)
                return datetime.date(year_value, month, target_day)

            candidate = resolve(year)
            if candidate < start:
                candidate = resolve(year + 1)
            if candidate < reference:
                candidate = resolve(candidate.year + 1)
            return candidate

        return rule.last_processed_date or start


    def _adjust_goal_progress(self, goal_id: Optional[int], amount_delta: float) -> None:
        if not goal_id or amount_delta == 0:
            return

        goal = Goal.get_or_none(Goal.id == goal_id)
        if not goal:
            return

        current = float(goal.current_amount or 0)
        goal.current_amount = max(0.0, current + amount_delta)
        goal.save()


    def _adjust_debt_balance(self, debt_id: Optional[int], payment_delta: float) -> None:
        if not debt_id or payment_delta == 0:
            return

        debt = Debt.get_or_none(Debt.id == debt_id)
        if not debt:
            return

        current = float(debt.current_balance or 0)
        debt.current_balance = max(0.0, current - payment_delta)
        debt.save()

    def _adjust_budget_allocation(self, budget_entry_id: Optional[int], amount_delta: float) -> None:
        """Actualiza el monto ejecutado de una entrada de presupuesto."""

        if not budget_entry_id or amount_delta == 0:
            return

        entry = BudgetEntry.get_or_none(BudgetEntry.id == budget_entry_id)
        if not entry:
            return

        current = float(entry.actual_amount or 0)
        new_value = current + amount_delta
        if new_value < 0:
            new_value = 0.0
        entry.actual_amount = new_value
        entry.save()

    def _resolve_transaction_cash_flow(
        self,
        transaction_type: Optional[str],
        portfolio_direction: Optional[str] = None,
    ) -> str:
        """Return 'Ingreso' or 'Gasto' describing the cash impact."""

        normalized_type = (transaction_type or "").strip().lower()
        if normalized_type == "movimiento portafolio":
            normalized_direction = (portfolio_direction or "").strip().lower()
            return "Ingreso" if normalized_direction == "venta" else "Gasto"
        return "Ingreso" if normalized_type == "ingreso" else "Gasto"

    def add_transaction(self, data):
        try:
            is_recurring = data.pop('is_recurring', False)
            frequency = data.pop('frequency', None)
            day_of_month = data.pop('day_of_month', None)

            splits_payload = self._prepare_splits(data.pop('splits', None))
            tags_payload = self._sanitize_tags(data.pop('tags', None))

            amount = float(data['amount'])
            if amount <= 0:
                return {"error": "El monto debe ser mayor a cero."}

            type_value = data.get('type')
            is_portfolio_movement = str(type_value or "").strip().lower() == "movimiento portafolio"
            if is_portfolio_movement:
                direction_value = (data.get('portfolio_direction') or "").strip().lower()
                if direction_value not in {"compra", "venta"}:
                    return {"error": "Selecciona si el movimiento de portafolio es una compra o una venta."}
                data['portfolio_direction'] = "Venta" if direction_value == "venta" else "Compra"
                if splits_payload:
                    return {"error": "Los movimientos de portafolio no admiten divisiones."}
            else:
                data['portfolio_direction'] = None

            if splits_payload:
                total_splits = sum(split['amount'] for split in splits_payload)
                if abs(total_splits - amount) > 0.01:
                    return {"error": "La suma de las divisiones debe coincidir con el monto total."}
                data['category'] = data.get('category') or 'Múltiples categorías'

            is_transfer = bool(data.get('is_transfer'))
            transfer_account_value = data.get('transfer_account_id')

            if is_transfer:
                if is_portfolio_movement:
                    return {"error": "Los movimientos de portafolio no pueden registrarse como transferencias."}
                if not transfer_account_value:
                    return {"error": "Selecciona la cuenta de destino de la transferencia."}
                if int(transfer_account_value) == int(data['account_id']):
                    return {"error": "La cuenta de origen y destino deben ser diferentes."}
                data['type'] = 'Transferencia'
                data['category'] = data.get('category') or 'Transferencia interna'
                data['goal_id'] = None
                data['debt_id'] = None
                data['budget_entry_id'] = None
            else:
                data['is_transfer'] = False
                data['transfer_account_id'] = None

            goal_value = data.get('goal_id')
            debt_value = data.get('debt_id')
            goal_id = int(goal_value) if goal_value not in (None, "", 0) else None
            debt_id = int(debt_value) if debt_value not in (None, "", 0) else None
            data['goal_id'] = goal_id
            data['debt_id'] = debt_id

            budget_value = data.get('budget_entry_id')
            budget_entry_id = int(budget_value) if budget_value not in (None, "", 0) else None
            data['budget_entry_id'] = None if is_transfer else budget_entry_id

            with db.atomic():
                account = Account.get_by_id(data['account_id'])
                cash_flow = self._resolve_transaction_cash_flow(
                    data.get('type'), data.get('portfolio_direction')
                )

                if is_transfer:
                    if float(account.current_balance or 0) + 1e-9 < amount:
                        return {
                            "error": "La cuenta de origen no tiene fondos suficientes para transferir ese monto."
                        }
                    destination = Account.get_by_id(int(transfer_account_value))
                    account.current_balance -= amount
                    destination.current_balance += amount
                    account.save()
                    if destination.id != account.id:
                        destination.save()
                    data['is_transfer'] = True
                    data['transfer_account_id'] = destination.id
                else:
                    if cash_flow == 'Ingreso':
                        account.current_balance += amount
                    else:
                        account.current_balance -= amount
                    account.save()

                transaction = Transaction.create(**data)

                if not is_transfer:
                    if goal_id:
                        self._adjust_goal_progress(goal_id, amount)
                    if debt_id:
                        self._adjust_debt_balance(debt_id, amount)
                    if budget_entry_id:
                        self._adjust_budget_allocation(budget_entry_id, amount)

                self._sync_transaction_splits(transaction, splits_payload)
                self._sync_transaction_tags(transaction, tags_payload)

                if is_recurring:
                    RecurringTransaction.create(
                        description=data['description'],
                        amount=amount,
                        type=data['type'],
                        category=data['category'],
                        frequency=frequency,
                        day_of_month=day_of_month,
                        start_date=data['date'],
                        last_processed_date=data['date'],
                    )

            return transaction.__data__
        except Exception as e:  # pylint: disable=broad-except
            return {"error": f"Datos inválidos: {e}"}

    def update_transaction(self, transaction_id, data):
        try:
            splits_payload = self._prepare_splits(data.pop('splits', None))
            tags_payload = self._sanitize_tags(data.pop('tags', None))

            amount = float(data['amount'])
            if amount <= 0:
                return {"error": "El monto debe ser mayor a cero."}

            type_value = data.get('type')
            is_portfolio_movement = str(type_value or "").strip().lower() == "movimiento portafolio"
            if is_portfolio_movement:
                direction_value = (data.get('portfolio_direction') or "").strip().lower()
                if direction_value not in {"compra", "venta"}:
                    return {"error": "Selecciona si el movimiento de portafolio es una compra o una venta."}
                data['portfolio_direction'] = "Venta" if direction_value == "venta" else "Compra"
                if splits_payload:
                    return {"error": "Los movimientos de portafolio no admiten divisiones."}
            else:
                data['portfolio_direction'] = None

            if splits_payload:
                total_splits = sum(split['amount'] for split in splits_payload)
                if abs(total_splits - amount) > 0.01:
                    return {"error": "La suma de las divisiones debe coincidir con el monto total."}
                data['category'] = data.get('category') or 'Múltiples categorías'

            is_transfer = bool(data.get('is_transfer'))
            transfer_account_value = data.get('transfer_account_id')
            if is_transfer:
                if is_portfolio_movement:
                    return {"error": "Los movimientos de portafolio no pueden registrarse como transferencias."}
                if not transfer_account_value:
                    return {"error": "Selecciona la cuenta de destino de la transferencia."}
                if int(transfer_account_value) == int(data['account_id']):
                    return {"error": "La cuenta de origen y destino deben ser diferentes."}
                data['type'] = 'Transferencia'
                data['category'] = data.get('category') or 'Transferencia interna'
                data['goal_id'] = None
                data['debt_id'] = None
                data['budget_entry_id'] = None
            else:
                data['is_transfer'] = False
                data['transfer_account_id'] = None

            goal_value = data.get('goal_id')
            debt_value = data.get('debt_id')
            goal_id = int(goal_value) if goal_value not in (None, "", 0) else None
            debt_id = int(debt_value) if debt_value not in (None, "", 0) else None
            data['goal_id'] = goal_id
            data['debt_id'] = debt_id

            budget_value = data.get('budget_entry_id')
            budget_entry_id = int(budget_value) if budget_value not in (None, "", 0) else None
            data['budget_entry_id'] = None if is_transfer else budget_entry_id

            with db.atomic():
                original_transaction = Transaction.get_by_id(transaction_id)
                original_amount = float(original_transaction.amount or 0)
                original_budget_entry_id = getattr(original_transaction, 'budget_entry_id', None)

                original_cash_flow = self._resolve_transaction_cash_flow(
                    original_transaction.type,
                    getattr(original_transaction, 'portfolio_direction', None),
                )

                if original_transaction.is_transfer:
                    source_account = original_transaction.account
                    target_account = original_transaction.transfer_account
                    if source_account:
                        source_account.current_balance += original_amount
                        source_account.save()
                    if target_account:
                        target_account.current_balance -= original_amount
                        target_account.save()
                else:
                    original_account = Account.get_by_id(original_transaction.account_id)
                    if original_cash_flow == 'Ingreso':
                        original_account.current_balance -= original_amount
                    else:
                        original_account.current_balance += original_amount
                    original_account.save()

                    self._adjust_goal_progress(
                        original_transaction.goal_id,
                        -original_amount,
                    )
                    self._adjust_debt_balance(
                        original_transaction.debt_id,
                        -original_amount,
                    )

                new_account = Account.get_by_id(data['account_id'])
                new_cash_flow = self._resolve_transaction_cash_flow(
                    data.get('type'), data.get('portfolio_direction')
                )

                if is_transfer:
                    if float(new_account.current_balance or 0) + 1e-9 < amount:
                        return {
                            "error": "La cuenta de origen no tiene fondos suficientes para transferir ese monto."
                        }
                    destination = Account.get_by_id(int(transfer_account_value))
                    new_account.current_balance -= amount
                    destination.current_balance += amount
                    new_account.save()
                    if destination.id != new_account.id:
                        destination.save()
                    data['is_transfer'] = True
                    data['transfer_account_id'] = destination.id
                else:
                    if new_cash_flow == 'Ingreso':
                        new_account.current_balance += amount
                    else:
                        new_account.current_balance -= amount
                    new_account.save()

                Transaction.update(**data).where(Transaction.id == transaction_id).execute()
                updated = Transaction.get_by_id(transaction_id)

                self._sync_transaction_splits(updated, splits_payload)
                self._sync_transaction_tags(updated, tags_payload)

                if not is_transfer:
                    if goal_id:
                        self._adjust_goal_progress(goal_id, amount)
                    if debt_id:
                        self._adjust_debt_balance(debt_id, amount)
                    if budget_entry_id:
                        self._adjust_budget_allocation(budget_entry_id, amount)

                if not original_transaction.is_transfer and original_budget_entry_id:
                    self._adjust_budget_allocation(original_budget_entry_id, -original_amount)

            return updated.__data__
        except Exception as e:  # pylint: disable=broad-except
            return {"error": f"Error al actualizar: {e}"}

    def delete_transaction(self, transaction_id, adjust_balance: bool = False):
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if adjust_balance:
                amount = float(transaction.amount or 0)
                if transaction.is_transfer:
                    source_account = transaction.account
                    target_account = transaction.transfer_account
                    if source_account:
                        source_account.current_balance += amount
                        source_account.save()
                    if target_account:
                        target_account.current_balance -= amount
                        target_account.save()
                else:
                    account = transaction.account
                    cash_flow = self._resolve_transaction_cash_flow(
                        transaction.type,
                        getattr(transaction, 'portfolio_direction', None),
                    )
                    if cash_flow == 'Ingreso':
                        account.current_balance -= amount
                    else:
                        account.current_balance += amount
                    account.save()

            if not transaction.is_transfer:
                self._adjust_goal_progress(transaction.goal_id, -float(transaction.amount or 0))
                self._adjust_debt_balance(transaction.debt_id, -float(transaction.amount or 0))
                self._adjust_budget_allocation(
                    getattr(transaction, 'budget_entry_id', None),
                    -float(transaction.amount or 0),
                )
            transaction.delete_instance()
            return {"success": True}
        except Transaction.DoesNotExist:
            return {"error": "La transacción no existe."}
        
    def get_transaction_by_id(self, transaction_id):
        """Obtiene una única transacción por su ID con datos de la cuenta."""
        try:
            # Hacemos un JOIN para obtener también el nombre de la cuenta
            transaction = (Transaction
                           .select(Transaction, Account)
                           .join(Account)
                           .where(Transaction.id == transaction_id)
                           .get())
            return transaction.to_dict() # Suponiendo que tienes un método to_dict en tu modelo
        except Transaction.DoesNotExist:
            return None

    # =================================================================
    # --- SECCIÓN: PARÁMETROS (Tipos y Categorías) ---
    # =================================================================
    def get_parameters_by_group(self, group_name):
        """
        Obtiene todos los parámetros que pertenecen a un grupo específico.
        Ej: 'Tipo de Transacción', 'Tipo de Cuenta'.
        """
        return list(Parameter.select().where(Parameter.group == group_name).dicts())

    def get_child_parameters(self, parent_id):
        """
        Obtiene los parámetros (categorías) que son hijos de otro parámetro (tipo).
        También incluye las categorías heredadas de otros tipos cuando aplique.
        """
        base_query = Parameter.select().where(Parameter.parent == parent_id)
        categories = []
        seen_ids = set()

        for row in base_query.dicts():
            categories.append(row)
            seen_ids.add(row["id"])

        try:
            parent_parameter = Parameter.get_by_id(parent_id)
        except Parameter.DoesNotExist:
            return categories

        inherited_type_ids = self._parse_inherited_category_ids(parent_parameter.extra_data)
        if not inherited_type_ids:
            return categories

        inherited_categories = (
            Parameter.select()
            .where(Parameter.parent.in_(inherited_type_ids))
            .order_by(Parameter.parent, Parameter.value)
        )

        for row in inherited_categories.dicts():
            if row["id"] in seen_ids:
                continue
            categories.append(row)
            seen_ids.add(row["id"])

        return categories

    # -----------------------------------------------------------------
    # --- Tipos de transacción y reglas de presupuesto ---
    # -----------------------------------------------------------------

    def _parse_inherited_category_ids(self, raw_extra: Optional[str]) -> List[int]:
        if not raw_extra:
            return []

        candidates: List[int] = []
        try:
            parsed = json.loads(raw_extra)
            if isinstance(parsed, dict):
                raw_list = parsed.get("inherits") or parsed.get("inherit_category_ids") or parsed.get("inherits_from")
            elif isinstance(parsed, list):
                raw_list = parsed
            elif isinstance(parsed, str):
                raw_list = [value.strip() for value in parsed.split(",") if value.strip()]
            else:
                raw_list = []
        except (TypeError, json.JSONDecodeError):
            raw_list = [value.strip() for value in str(raw_extra).split(",") if value.strip()]

        for value in raw_list:
            try:
                normalized = int(value)
            except (TypeError, ValueError):
                continue
            if normalized not in candidates:
                candidates.append(normalized)
        return candidates

    def _encode_inherited_category_ids(self, type_ids: List[int]) -> Optional[str]:
        if not type_ids:
            return None
        return json.dumps({"inherits": type_ids})

    def _normalize_inherited_type_ids(
        self, raw_ids: Optional[Any], *, exclude_id: Optional[int] = None
    ) -> Tuple[List[int], Optional[str]]:
        if raw_ids is None:
            return [], None

        if not isinstance(raw_ids, (list, tuple, set)):
            return [], "Los tipos seleccionados para heredar no son válidos."

        normalized: List[int] = []
        for value in raw_ids:
            try:
                candidate = int(value)
            except (TypeError, ValueError):
                return [], "Los tipos seleccionados para heredar no son válidos."

            if exclude_id is not None and candidate == exclude_id:
                continue

            parameter = Parameter.get_or_none(Parameter.id == candidate)
            if not parameter or parameter.group != "Tipo de Transacción":
                return [], "Uno de los tipos seleccionados para heredar no existe."

            if candidate not in normalized:
                normalized.append(candidate)

        return normalized, None

    def _serialize_transaction_type(self, parameter: Parameter) -> Dict[str, Any]:
        inherit_ids = self._parse_inherited_category_ids(parameter.extra_data)
        inherit_names: List[str] = []

        if inherit_ids:
            name_map = {
                item.id: item.value
                for item in Parameter.select()
                .where((Parameter.group == "Tipo de Transacción") & (Parameter.id.in_(inherit_ids)))
            }
            inherit_names = [name_map[type_id] for type_id in inherit_ids if type_id in name_map]

        return {
            "id": parameter.id,
            "name": parameter.value,
            "budget_rule_id": parameter.budget_rule_id,
            "budget_rule_name": parameter.budget_rule.name if parameter.budget_rule else None,
            "is_deletable": bool(parameter.is_deletable),
            "inherit_category_ids": inherit_ids,
            "inherit_category_names": inherit_names,
        }

    def _serialize_budget_rule(self, rule: BudgetRule) -> Dict[str, Any]:
        in_use = Parameter.select().where(Parameter.budget_rule == rule).exists()
        return {
            "id": rule.id,
            "name": rule.name,
            "percentage": float(rule.percentage or 0),
            "is_deletable": not in_use,
        }

    def _sum_budget_rule_percentage(self, exclude_id: Optional[int] = None) -> float:
        query = BudgetRule.select(fn.SUM(BudgetRule.percentage))
        if exclude_id is not None:
            query = query.where(BudgetRule.id != exclude_id)
        total = query.scalar() or 0.0
        return float(total)

    def get_transaction_types_overview(self) -> List[Dict[str, Any]]:
        query = (
            Parameter
            .select(Parameter, BudgetRule)
            .join(BudgetRule, JOIN.LEFT_OUTER)
            .where(Parameter.group == "Tipo de Transacción")
            .order_by(Parameter.id)
        )
        return [self._serialize_transaction_type(param) for param in query]

    def get_budget_rules(self) -> List[Dict[str, Any]]:
        return [self._serialize_budget_rule(rule) for rule in BudgetRule.select().order_by(BudgetRule.id)]

    def add_transaction_type(
        self,
        name: str,
        budget_rule_id: Optional[int],
        inherit_category_ids: Optional[List[int]],
    ) -> Dict[str, Any]:
        name = (name or "").strip()
        if not name:
            return {"error": "El nombre del tipo de transacción es obligatorio."}

        existing = Parameter.get_or_none(
            (Parameter.group == "Tipo de Transacción") & (Parameter.value == name)
        )
        if existing:
            return {"error": "Ya existe un tipo de transacción con ese nombre."}

        budget_rule = None
        if budget_rule_id is not None:
            budget_rule = BudgetRule.get_or_none(BudgetRule.id == budget_rule_id)
            if not budget_rule:
                return {"error": "La regla de presupuesto seleccionada no existe."}

        normalized_inherit_ids, inherit_error = self._normalize_inherited_type_ids(
            inherit_category_ids
        )
        if inherit_error:
            return {"error": inherit_error}

        parameter = Parameter.create(
            group="Tipo de Transacción",
            value=name,
            budget_rule=budget_rule,
            extra_data=self._encode_inherited_category_ids(normalized_inherit_ids),
        )
        return self._serialize_transaction_type(parameter)

    def update_transaction_type(self, parameter_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            parameter = Parameter.get_by_id(parameter_id)
        except Parameter.DoesNotExist:
            return {"error": "El tipo de transacción no existe."}

        if parameter.group != "Tipo de Transacción":
            return {"error": "El parámetro seleccionado no es un tipo de transacción."}

        updates: Dict[str, Any] = {}
        original_name = parameter.value

        if "name" in data:
            new_name = (data["name"] or "").strip()
            if not new_name:
                return {"error": "El nombre del tipo de transacción es obligatorio."}

            if not parameter.is_deletable and new_name != original_name:
                return {"error": "Este tipo es protegido, solo puedes actualizar su regla de presupuesto."}

            duplicate = Parameter.select().where(
                (Parameter.group == "Tipo de Transacción")
                & (Parameter.value == new_name)
                & (Parameter.id != parameter.id)
            ).exists()
            if duplicate:
                return {"error": "Ya existe un tipo de transacción con ese nombre."}

            updates["value"] = new_name

        if "budget_rule_id" in data:
            budget_rule_id = data["budget_rule_id"]
            if budget_rule_id is None:
                updates["budget_rule"] = None
            else:
                budget_rule = BudgetRule.get_or_none(BudgetRule.id == budget_rule_id)
                if not budget_rule:
                    return {"error": "La regla de presupuesto seleccionada no existe."}
                updates["budget_rule"] = budget_rule

        if "inherit_category_ids" in data:
            normalized_inherit_ids, inherit_error = self._normalize_inherited_type_ids(
                data.get("inherit_category_ids"), exclude_id=parameter.id
            )
            if inherit_error:
                return {"error": inherit_error}
            updates["extra_data"] = self._encode_inherited_category_ids(
                normalized_inherit_ids
            )

        if updates:
            Parameter.update(updates).where(Parameter.id == parameter.id).execute()

            if "value" in updates and updates["value"] != original_name:
                new_name = updates["value"]
                Transaction.update(type=new_name).where(Transaction.type == original_name).execute()
                BudgetEntry.update(type=new_name).where(BudgetEntry.type == original_name).execute()

        parameter = Parameter.get_by_id(parameter.id)
        return self._serialize_transaction_type(parameter)

    def delete_transaction_type(self, parameter_id: int) -> Dict[str, Any]:
        try:
            parameter = Parameter.get_by_id(parameter_id)
        except Parameter.DoesNotExist:
            return {"error": "El tipo de transacción no existe."}

        if parameter.group != "Tipo de Transacción":
            return {"error": "El parámetro seleccionado no es un tipo de transacción."}

        if not parameter.is_deletable:
            return {"error": "Este tipo de transacción no puede eliminarse."}

        if Parameter.select().where(Parameter.parent == parameter).exists():
            return {"error": "No se puede eliminar un tipo que todavía tiene categorías asociadas."}

        if Transaction.select().where(Transaction.type == parameter.value).exists():
            return {"error": "No se puede eliminar un tipo que está siendo utilizado por transacciones."}

        if BudgetEntry.select().where(BudgetEntry.type == parameter.value).exists():
            return {"error": "No se puede eliminar un tipo que está siendo utilizado por presupuestos."}

        parameter.delete_instance()
        return {"success": True}

    def add_budget_rule(self, name: str, percentage: float) -> Dict[str, Any]:
        name = (name or "").strip()
        if not name:
            return {"error": "El nombre de la regla es obligatorio."}

        if BudgetRule.select().where(fn.LOWER(BudgetRule.name) == name.lower()).exists():
            return {"error": "Ya existe una regla de presupuesto con ese nombre."}

        try:
            percentage_value = float(percentage)
        except (TypeError, ValueError):
            return {"error": "El porcentaje debe ser un número."}

        if percentage_value < 0 or percentage_value > 100:
            return {"error": "El porcentaje debe estar entre 0 y 100."}

        current_total = self._sum_budget_rule_percentage()
        if current_total + percentage_value > 100.0001:
            return {"error": "La suma de las reglas de presupuesto no puede exceder el 100%."}

        rule = BudgetRule.create(name=name, percentage=percentage_value)
        return self._serialize_budget_rule(rule)

    def update_budget_rule(self, rule_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rule = BudgetRule.get_by_id(rule_id)
        except BudgetRule.DoesNotExist:
            return {"error": "La regla de presupuesto no existe."}

        updates: Dict[str, Any] = {}

        if "name" in data:
            new_name = (data["name"] or "").strip()
            if not new_name:
                return {"error": "El nombre de la regla es obligatorio."}

            duplicate = BudgetRule.select().where(
                (fn.LOWER(BudgetRule.name) == new_name.lower()) & (BudgetRule.id != rule.id)
            ).exists()
            if duplicate:
                return {"error": "Ya existe una regla de presupuesto con ese nombre."}

            updates["name"] = new_name

        if "percentage" in data:
            try:
                updates["percentage"] = float(data["percentage"])
            except (TypeError, ValueError):
                return {"error": "El porcentaje debe ser un número."}

            if updates["percentage"] < 0 or updates["percentage"] > 100:
                return {"error": "El porcentaje debe estar entre 0 y 100."}

            other_total = self._sum_budget_rule_percentage(exclude_id=rule.id)
            if other_total + updates["percentage"] > 100.0001:
                return {"error": "La suma de las reglas de presupuesto no puede exceder el 100%."}

        if updates:
            BudgetRule.update(updates).where(BudgetRule.id == rule.id).execute()

        rule = BudgetRule.get_by_id(rule.id)
        return self._serialize_budget_rule(rule)

    def delete_budget_rule(self, rule_id: int) -> Dict[str, Any]:
        try:
            rule = BudgetRule.get_by_id(rule_id)
        except BudgetRule.DoesNotExist:
            return {"error": "La regla de presupuesto no existe."}

        if Parameter.select().where(Parameter.budget_rule == rule).exists():
            return {"error": "No se puede eliminar una regla asociada a tipos de transacción."}

        rule.delete_instance()
        return {"success": True}

    # -----------------------------------------------------------------
    # --- Tipos de cuenta ---
    # -----------------------------------------------------------------

    def _serialize_account_type(self, parameter: Parameter) -> Dict[str, Any]:
        has_accounts = Account.select().where(Account.account_type == parameter.value).exists()
        return {
            "id": parameter.id,
            "name": parameter.value,
            "is_deletable": bool(parameter.is_deletable) and not has_accounts,
        }

    def get_account_type_parameters(self) -> List[Dict[str, Any]]:
        query = Parameter.select().where(Parameter.group == "Tipo de Cuenta").order_by(Parameter.id)
        return [self._serialize_account_type(param) for param in query]

    def add_account_type(self, name: str) -> Dict[str, Any]:
        name = (name or "").strip()
        if not name:
            return {"error": "El nombre del tipo de cuenta es obligatorio."}

        if Parameter.select().where(
            (Parameter.group == "Tipo de Cuenta") & (fn.LOWER(Parameter.value) == name.lower())
        ).exists():
            return {"error": "Ya existe un tipo de cuenta con ese nombre."}

        parameter = Parameter.create(group="Tipo de Cuenta", value=name)
        return self._serialize_account_type(parameter)

    def update_account_type_parameter(self, parameter_id: int, name: str) -> Dict[str, Any]:
        try:
            parameter = Parameter.get_by_id(parameter_id)
        except Parameter.DoesNotExist:
            return {"error": "El tipo de cuenta no existe."}

        if parameter.group != "Tipo de Cuenta":
            return {"error": "El parámetro seleccionado no es un tipo de cuenta."}

        name = (name or "").strip()
        if not name:
            return {"error": "El nombre del tipo de cuenta es obligatorio."}

        duplicate = Parameter.select().where(
            (Parameter.group == "Tipo de Cuenta")
            & (fn.LOWER(Parameter.value) == name.lower())
            & (Parameter.id != parameter.id)
        ).exists()
        if duplicate:
            return {"error": "Ya existe un tipo de cuenta con ese nombre."}

        old_name = parameter.value
        Parameter.update(value=name).where(Parameter.id == parameter.id).execute()
        Account.update(account_type=name).where(Account.account_type == old_name).execute()

        parameter = Parameter.get_by_id(parameter.id)
        return self._serialize_account_type(parameter)

    def delete_account_type_parameter(self, parameter_id: int) -> Dict[str, Any]:
        try:
            parameter = Parameter.get_by_id(parameter_id)
        except Parameter.DoesNotExist:
            return {"error": "El tipo de cuenta no existe."}

        if parameter.group != "Tipo de Cuenta":
            return {"error": "El parámetro seleccionado no es un tipo de cuenta."}

        if not parameter.is_deletable:
            return {"error": "Este tipo de cuenta no puede eliminarse."}

        if Account.select().where(Account.account_type == parameter.value).exists():
            return {"error": "No se puede eliminar un tipo que está siendo utilizado por cuentas."}

        parameter.delete_instance()
        return {"success": True}

    # -----------------------------------------------------------------
    # --- Tipos de activo ---
    # -----------------------------------------------------------------

    def _serialize_asset_type(self, parameter: Parameter) -> Dict[str, Any]:
        has_assets = (
            PortfolioAsset.select()
            .where(fn.LOWER(PortfolioAsset.asset_type) == parameter.value.lower())
            .exists()
        )
        return {
            "id": parameter.id,
            "name": parameter.value,
            "is_deletable": bool(parameter.is_deletable) and not has_assets,
        }

    def get_asset_types(self) -> List[str]:
        return [
            item["value"]
            for item in Parameter.select()
            .where(Parameter.group == "Tipo de Activo")
            .order_by(Parameter.id)
            .dicts()
        ]

    def get_asset_type_parameters(self) -> List[Dict[str, Any]]:
        query = (
            Parameter.select()
            .where(Parameter.group == "Tipo de Activo")
            .order_by(Parameter.id)
        )
        return [self._serialize_asset_type(param) for param in query]

    def add_asset_type(self, name: str) -> Dict[str, Any]:
        name = (name or "").strip()
        if not name:
            return {"error": "El nombre del tipo de activo es obligatorio."}

        duplicate = Parameter.select().where(
            (Parameter.group == "Tipo de Activo")
            & (fn.LOWER(Parameter.value) == name.lower())
        ).exists()
        if duplicate:
            return {"error": "Ya existe un tipo de activo con ese nombre."}

        parameter = Parameter.create(group="Tipo de Activo", value=name)
        return self._serialize_asset_type(parameter)

    def update_asset_type_parameter(self, parameter_id: int, name: str) -> Dict[str, Any]:
        try:
            parameter = Parameter.get_by_id(parameter_id)
        except Parameter.DoesNotExist:
            return {"error": "El tipo de activo no existe."}

        if parameter.group != "Tipo de Activo":
            return {"error": "El parámetro seleccionado no es un tipo de activo."}

        name = (name or "").strip()
        if not name:
            return {"error": "El nombre del tipo de activo es obligatorio."}

        duplicate = Parameter.select().where(
            (Parameter.group == "Tipo de Activo")
            & (fn.LOWER(Parameter.value) == name.lower())
            & (Parameter.id != parameter.id)
        ).exists()
        if duplicate:
            return {"error": "Ya existe un tipo de activo con ese nombre."}

        old_name = parameter.value
        Parameter.update(value=name).where(Parameter.id == parameter.id).execute()
        PortfolioAsset.update(asset_type=name).where(
            fn.LOWER(PortfolioAsset.asset_type) == old_name.lower()
        ).execute()

        parameter = Parameter.get_by_id(parameter.id)
        return self._serialize_asset_type(parameter)

    def delete_asset_type_parameter(self, parameter_id: int) -> Dict[str, Any]:
        try:
            parameter = Parameter.get_by_id(parameter_id)
        except Parameter.DoesNotExist:
            return {"error": "El tipo de activo no existe."}

        if parameter.group != "Tipo de Activo":
            return {"error": "El parámetro seleccionado no es un tipo de activo."}

        if not parameter.is_deletable:
            return {"error": "Este tipo de activo no puede eliminarse."}

        if PortfolioAsset.select().where(
            fn.LOWER(PortfolioAsset.asset_type) == parameter.value.lower()
        ).exists():
            return {"error": "No se puede eliminar un tipo con activos registrados."}

        parameter.delete_instance()
        return {"success": True}

    # -----------------------------------------------------------------
    # --- Categorías ---
    # -----------------------------------------------------------------

    def _serialize_category(self, category: Parameter, parent: Parameter) -> Dict[str, Any]:
        in_use = Transaction.select().where(Transaction.category == category.value).exists() or \
            BudgetEntry.select().where(BudgetEntry.category == category.value).exists()
        return {
            "id": category.id,
            "name": category.value,
            "parent_id": parent.id,
            "parent_name": parent.value,
            "is_deletable": bool(category.is_deletable) and not in_use,
        }

    def get_category_overview(self) -> List[Dict[str, Any]]:
        parent_alias = Parameter.alias()
        query = (
            Parameter
            .select(Parameter, parent_alias)
            .join(parent_alias, on=(Parameter.parent == parent_alias.id))
            .where(Parameter.group == "Categoría")
            .order_by(parent_alias.value, Parameter.value)
        )

        results: List[Dict[str, Any]] = []
        for category in query:
            results.append(self._serialize_category(category, category.parent))
        return results

    def add_category(self, name: str, parent_id: int) -> Dict[str, Any]:
        name = (name or "").strip()
        if not name:
            return {"error": "El nombre de la categoría es obligatorio."}

        try:
            parent = Parameter.get_by_id(parent_id)
        except Parameter.DoesNotExist:
            return {"error": "El tipo de transacción seleccionado no existe."}

        if parent.group != "Tipo de Transacción":
            return {"error": "La categoría debe pertenecer a un tipo de transacción válido."}

        if Parameter.select().where(
            (Parameter.group == "Categoría")
            & (Parameter.parent == parent)
            & (fn.LOWER(Parameter.value) == name.lower())
        ).exists():
            return {"error": "Ya existe una categoría con ese nombre para el tipo seleccionado."}

        category = Parameter.create(group="Categoría", value=name, parent=parent)
        return self._serialize_category(category, parent)

    def update_category(self, category_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            category = Parameter.get_by_id(category_id)
        except Parameter.DoesNotExist:
            return {"error": "La categoría no existe."}

        if category.group != "Categoría":
            return {"error": "El parámetro seleccionado no es una categoría."}

        updates: Dict[str, Any] = {}
        original_name = category.value

        if "name" in data:
            new_name = (data["name"] or "").strip()
            if not new_name:
                return {"error": "El nombre de la categoría es obligatorio."}

            duplicate = Parameter.select().where(
                (Parameter.group == "Categoría")
                & (Parameter.parent == category.parent)
                & (fn.LOWER(Parameter.value) == new_name.lower())
                & (Parameter.id != category.id)
            ).exists()
            if duplicate:
                return {"error": "Ya existe una categoría con ese nombre para el tipo seleccionado."}

            updates["value"] = new_name

        if "parent_id" in data:
            new_parent_id = data["parent_id"]
            try:
                new_parent = Parameter.get_by_id(new_parent_id)
            except Parameter.DoesNotExist:
                return {"error": "El tipo de transacción seleccionado no existe."}

            if new_parent.group != "Tipo de Transacción":
                return {"error": "La categoría debe pertenecer a un tipo de transacción válido."}

            updates["parent"] = new_parent

        if updates:
            Parameter.update(updates).where(Parameter.id == category.id).execute()

            if "value" in updates and updates["value"] != original_name:
                new_value = updates["value"]
                Transaction.update(category=new_value).where(Transaction.category == original_name).execute()
                BudgetEntry.update(category=new_value).where(BudgetEntry.category == original_name).execute()

        category = Parameter.get_by_id(category.id)
        parent = category.parent
        return self._serialize_category(category, parent)

    def delete_category(self, category_id: int) -> Dict[str, Any]:
        try:
            category = Parameter.get_by_id(category_id)
        except Parameter.DoesNotExist:
            return {"error": "La categoría no existe."}

        if category.group != "Categoría":
            return {"error": "El parámetro seleccionado no es una categoría."}

        if not category.is_deletable:
            return {"error": "Esta categoría no puede eliminarse."}

        if Transaction.select().where(Transaction.category == category.value).exists():
            return {"error": "No se puede eliminar una categoría utilizada por transacciones."}

        if BudgetEntry.select().where(BudgetEntry.category == category.value).exists():
            return {"error": "No se puede eliminar una categoría utilizada por presupuestos."}

        category.delete_instance()
        return {"success": True}

    # -----------------------------------------------------------------
    # --- Preferencias de visualización ---
    # -----------------------------------------------------------------

    def _parse_bool_flag(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return value != 0
        value_str = str(value).strip().lower()
        return value_str in {"1", "true", "sí", "si", "yes"}

    def get_display_preferences(self) -> Dict[str, Any]:
        abbreviate_param = Parameter.get_or_none(
            (Parameter.group == "Display") & (Parameter.value == "AbbreviateNumbers")
        )
        threshold_param = Parameter.get_or_none(
            (Parameter.group == "Display") & (Parameter.value == "AbbreviationThreshold")
        )

        abbreviate = False
        threshold = 1_000_000

        if abbreviate_param and abbreviate_param.extra_data is not None:
            abbreviate = self._parse_bool_flag(abbreviate_param.extra_data)

        if threshold_param and threshold_param.extra_data is not None:
            try:
                threshold = int(threshold_param.extra_data)
            except (TypeError, ValueError):
                threshold = 1_000_000

        return {"abbreviate_numbers": abbreviate, "threshold": threshold}

    def update_display_preferences(self, abbreviate_numbers: bool, threshold: int) -> Dict[str, Any]:
        threshold_value = max(1_000, int(threshold or 1_000))

        abbrev_param, _ = Parameter.get_or_create(
            group="Display",
            value="AbbreviateNumbers",
            defaults={"extra_data": "1" if abbreviate_numbers else "0", "is_deletable": False},
        )
        abbrev_param.extra_data = "1" if abbreviate_numbers else "0"
        abbrev_param.is_deletable = False
        abbrev_param.save()

        threshold_param, _ = Parameter.get_or_create(
            group="Display",
            value="AbbreviationThreshold",
            defaults={"extra_data": str(threshold_value), "is_deletable": False},
        )
        threshold_param.extra_data = str(threshold_value)
        threshold_param.is_deletable = False
        threshold_param.save()

        return self.get_display_preferences()


    # =================================================================
    # --- SECCIÓN: CONFIGURACIÓN DE LA APLICACIÓN ---
    # =================================================================

    def get_app_settings(self):
        """Obtiene la configuración general de la aplicación."""
        settings = DEFAULT_APP_SETTINGS.copy()

        for param in Parameter.select().where(Parameter.group == 'Settings'):
            key = param.value
            if key not in settings:
                continue

            stored_value = param.extra_data if param.extra_data is not None else param.value

            if key == 'decimal_places':
                try:
                    settings[key] = int(stored_value)
                except (TypeError, ValueError):
                    continue
            else:
                settings[key] = stored_value

        return settings

    def update_app_settings(self, data):
        """Actualiza la configuración general de la aplicación."""
        validated_settings = self.get_app_settings()

        if 'currency_symbol' in data and isinstance(data['currency_symbol'], str):
            symbol = data['currency_symbol'].strip()
            if symbol:
                validated_settings['currency_symbol'] = symbol

        if 'theme' in data and isinstance(data['theme'], str):
            theme = data['theme'].strip().lower()
            if theme in {'dark', 'light'}:
                validated_settings['theme'] = theme

        if 'decimal_places' in data:
            try:
                validated_settings['decimal_places'] = max(0, int(data['decimal_places']))
            except (TypeError, ValueError):
                pass

        for key, value in validated_settings.items():
            param, _ = Parameter.get_or_create(
                group='Settings',
                value=key,
                defaults={'extra_data': str(value), 'is_deletable': False}
            )

            # Garantiza que no se eliminen accidentalmente desde la interfaz
            if param.is_deletable:
                param.is_deletable = False

            param.extra_data = str(value)
            param.save()

        return validated_settings


    # =================================================================
    # --- SECCIÓN: METAS Y DEUDAS (Goals & Debts) ---
    # =================================================================

    def get_goals_summary(self, limit=3):
        """Devuelve un resumen de las metas para el dashboard con progreso normalizado."""
        goals_data = []
        query = Goal.select()
        if limit:
            query = query.limit(limit)

        for goal in query:
            goals_data.append(self._serialize_goal(goal))
        return goals_data

    def get_debts_summary(self, limit=3):
        """Devuelve un resumen de las deudas activas para el dashboard."""
        debts_data: List[Dict[str, Any]] = []
        query = Debt.select()
        if limit:
            query = query.limit(limit)

        for debt in query:
            debts_data.append(self._serialize_debt(debt))
        return debts_data

    def get_upcoming_budget_payments(self, limit=6):
        """Obtiene las próximas entradas de presupuesto con saldo pendiente."""
        today = datetime.date.today()
        upcoming: List[Tuple[datetime.date, Dict[str, Any]]] = []

        for entry in BudgetEntry.select():
            serialized = self._serialize_budget_entry(entry)
            remaining = float(serialized.get("remaining_amount") or 0.0)
            if remaining <= 0:
                continue

            due_reference = (
                serialized.get("due_date")
                or serialized.get("end_date")
                or serialized.get("start_date")
            )
            due_date = self._coerce_date(due_reference)
            if due_date is None:
                continue
            if due_date < today:
                continue

            serialized["due_date"] = due_date.isoformat()
            upcoming.append((due_date, serialized))

        upcoming.sort(key=lambda item: item[0])

        if limit:
            upcoming = upcoming[:limit]

        return [data for _, data in upcoming]

    def get_all_goals(self):
        """Devuelve todas las metas con su progreso."""
        return [self._serialize_goal(goal) for goal in Goal.select()]

    def get_all_debts(self):
        """Devuelve todas las deudas con su progreso."""
        return [self._serialize_debt(debt) for debt in Debt.select()]

    def _serialize_goal(self, goal: Goal) -> Dict[str, Any]:
        """Prepara una meta con valores numéricos nativos y porcentaje calculado."""
        target_amount = float(goal.target_amount or 0)
        current_amount = float(goal.current_amount or 0)
        percentage = self._calculate_completion_percentage(current_amount, target_amount)
        return {
            "id": goal.id,
            "name": goal.name,
            "target_amount": target_amount,
            "current_amount": current_amount,
            "percentage": percentage,
            "completion_percentage": percentage,
        }

    def _serialize_debt(self, debt: Debt) -> Dict[str, Any]:
        """Devuelve una deuda serializada con sus métricas derivadas."""
        total_amount = float(debt.total_amount or 0)
        current_balance = float(debt.current_balance or 0)
        minimum_payment = float(debt.minimum_payment or 0)
        interest_rate = float(getattr(debt, "interest_rate", 0) or 0)
        paid_amount = max(total_amount - current_balance, 0.0)
        percentage = self._calculate_completion_percentage(paid_amount, total_amount)
        return {
            "id": debt.id,
            "name": debt.name,
            "total_amount": total_amount,
            "current_balance": current_balance,
            "minimum_payment": minimum_payment,
            "interest_rate": interest_rate,
            "percentage": percentage,
            "completion_percentage": percentage,
        }

    def _calculate_completion_percentage(self, achieved, total):
        """Calcula el porcentaje de finalización, evitando divisiones por cero."""
        try:
            total_value = float(total)
            achieved_value = float(achieved)
        except (TypeError, ValueError):
            return 0.0

        if total_value == 0:
            return 0.0

        percentage = (achieved_value / total_value) * 100
        if percentage < 0:
            return 0.0
        if percentage > 100:
            return 100.0
        return percentage

    def add_goal(self, data):
        try:
            target = float(data['target_amount'])
            goal = Goal.create(name=data['name'], target_amount=target, current_amount=0)
            return self._serialize_goal(goal)
        except (ValueError, KeyError) as e:
            return {"error": f"Datos de meta inválidos: {e}"}

    def update_goal(self, goal_id, data):
        try:
            goal = Goal.get_by_id(goal_id)
            if 'name' in data:
                goal.name = data['name']
            if 'target_amount' in data:
                goal.target_amount = float(data['target_amount'])
            if 'current_amount' in data:
                goal.current_amount = float(data['current_amount'])
            goal.save()
            return self._serialize_goal(goal)
        except Goal.DoesNotExist:
            return {"error": "La meta no existe."}
        except (ValueError, KeyError) as e:
            return {"error": f"Datos de meta inválidos: {e}"}

    def add_debt(self, data):
        try:
            total = float(data['total_amount'])
            min_payment = float(data.get('minimum_payment', 0) or 0)
            interest = float(data.get('interest_rate', 0) or 0)

            if total <= 0:
                return {"error": "El monto total debe ser mayor que cero."}
            if min_payment < 0:
                return {"error": "El pago mínimo no puede ser negativo."}
            if min_payment > total:
                return {"error": "El pago mínimo no puede ser mayor que el monto total."}

            debt = Debt.create(
                name=data['name'],
                total_amount=total,
                current_balance=total,
                minimum_payment=min_payment,
                interest_rate=interest
            )
            return self._serialize_debt(debt)
        except (ValueError, KeyError) as e:
            return {"error": f"Datos de deuda inválidos: {e}"}

    def update_debt(self, debt_id, data):
        try:
            debt = Debt.get_by_id(debt_id)
            new_total = float(data.get('total_amount', debt.total_amount))
            new_minimum = float(data.get('minimum_payment', debt.minimum_payment or 0))

            if new_total <= 0:
                return {"error": "El monto total debe ser mayor que cero."}
            if new_minimum < 0:
                return {"error": "El pago mínimo no puede ser negativo."}
            if new_minimum > new_total:
                return {"error": "El pago mínimo no puede ser mayor que el monto total."}

            if 'name' in data:
                debt.name = data['name']
            if 'total_amount' in data:
                debt.total_amount = float(data['total_amount'])
            if 'current_balance' in data:
                debt.current_balance = float(data['current_balance'])
            if 'minimum_payment' in data:
                debt.minimum_payment = float(data['minimum_payment'])
            if 'interest_rate' in data:
                debt.interest_rate = float(data['interest_rate'])
            debt.save()
            return self._serialize_debt(debt)
        except Debt.DoesNotExist:
            return {"error": "La deuda no existe."}
        except (ValueError, KeyError) as e:
            return {"error": f"Datos de deuda inválidos: {e}"}

    def delete_goal(self, goal_id):
        try:
            Transaction.update(goal=None).where(Transaction.goal == goal_id).execute()
            BudgetEntry.update(goal=None).where(BudgetEntry.goal == goal_id).execute()
            PortfolioAsset.update(linked_goal=None).where(
                PortfolioAsset.linked_goal == goal_id
            ).execute()
            Goal.get_by_id(goal_id).delete_instance()
            return {"success": True}
        except Goal.DoesNotExist:
            return {"error": "La meta no existe."}

    def delete_debt(self, debt_id):
        try:
            Transaction.update(debt=None).where(Transaction.debt == debt_id).execute()
            BudgetEntry.update(debt=None).where(BudgetEntry.debt == debt_id).execute()
            Debt.get_by_id(debt_id).delete_instance()
            return {"success": True}
        except Debt.DoesNotExist:
            return {"error": "La deuda no existe."}


    # =================================================================
    # --- SECCIÓN: PRESUPUESTO (Budget) ---
    # =================================================================

    def _serialize_budget_entry(self, entry):
        """Convierte una entrada de presupuesto en un diccionario apto para la API."""
        is_dict = isinstance(entry, dict)

        raw_frequency = entry.get("frequency") if is_dict else getattr(entry, "frequency", None)
        frequency = self._normalize_frequency(raw_frequency)

        raw_start = entry.get("start_date") if is_dict else getattr(entry, "start_date", None)
        raw_due = entry.get("due_date") if is_dict else getattr(entry, "due_date", None)
        raw_end = entry.get("end_date") if is_dict else getattr(entry, "end_date", None)

        start_date, period_end = self._compute_period_bounds(
            self._coerce_date(raw_start),
            frequency,
            self._coerce_date(raw_due),
            self._coerce_date(raw_end),
        )

        due_date = period_end
        month = due_date.month if due_date else None
        year = due_date.year if due_date else None

        goal = None
        debt = None
        if is_dict:
            goal = entry.get("goal") or entry.get("goal_id")
            debt = entry.get("debt") or entry.get("debt_id")
        else:
            goal = getattr(entry, "goal", None)
            debt = getattr(entry, "debt", None)

        goal_obj = None
        debt_obj = None
        if isinstance(goal, Goal):
            goal_obj = goal
        elif goal:
            goal_obj = Goal.get_or_none(Goal.id == goal)

        if isinstance(debt, Debt):
            debt_obj = debt
        elif debt:
            debt_obj = Debt.get_or_none(Debt.id == debt)

        planned_amount = float(
            (entry.get("budgeted_amount") if is_dict else getattr(entry, "budgeted_amount", 0))
            or 0
        )
        actual_amount = float(
            (entry.get("actual_amount") if is_dict else getattr(entry, "actual_amount", 0))
            or 0
        )
        remaining_amount = planned_amount - actual_amount
        over_budget_amount = actual_amount - planned_amount if actual_amount > planned_amount else 0.0
        execution = (actual_amount / planned_amount * 100) if planned_amount else None

        is_recurring = bool(
            entry.get("is_recurring") if is_dict else getattr(entry, "is_recurring", False)
        )
        if frequency == "Única vez":
            is_recurring = False

        use_custom_schedule = bool(
            entry.get("use_custom_schedule")
            if is_dict
            else getattr(entry, "use_custom_schedule", False)
        )

        return {
            "id": entry["id"] if is_dict else entry.id,
            "description": entry.get("description") if is_dict else entry.description,
            "category": entry.get("category") if is_dict else entry.category,
            "type": entry.get("type") if is_dict else entry.type,
            "frequency": frequency,
            "budgeted_amount": planned_amount,
            "actual_amount": actual_amount,
            "remaining_amount": remaining_amount,
            "over_budget_amount": over_budget_amount if over_budget_amount > 0 else 0.0,
            "execution": execution,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": due_date.isoformat() if due_date else None,
            "due_date": due_date.isoformat() if due_date else None,
            "month": month,
            "year": year,
            "goal_id": goal_obj.id if goal_obj else None,
            "goal_name": goal_obj.name if goal_obj else None,
            "debt_id": debt_obj.id if debt_obj else None,
            "debt_name": debt_obj.name if debt_obj else None,
            "is_recurring": is_recurring,
            "use_custom_schedule": use_custom_schedule,
        }

    def _prepare_budget_payload(self, data, existing_entry=None):
        """Normaliza los datos recibidos desde la API para la base de datos."""
        MISSING = object()
        try:
            category = data["category"]
            entry_type = data.get("type", "Gasto")
            if data.get("description"):
                description = data["description"]
            elif existing_entry is not None:
                description = existing_entry.description
            else:
                description = category

            raw_amount = data.get("budgeted_amount")
            if raw_amount is None:
                raw_amount = data.get("amount")
            if raw_amount is None:
                raise KeyError("budgeted_amount")
            amount = float(raw_amount)

            frequency = self._normalize_frequency(
                data.get("frequency")
                or (existing_entry.frequency if existing_entry else None)
            )

            if "month" in data or "year" in data:
                base_date = (
                    existing_entry.due_date
                    if existing_entry and existing_entry.due_date
                    else datetime.date.today()
                )
                month_value = int(data.get("month") or base_date.month)
                year_value = int(data.get("year") or base_date.year)
                month_based_date = datetime.date(year_value, month_value, 1)
            else:
                month_based_date = None

            custom_schedule_flag = data.get("use_custom_schedule")
            if custom_schedule_flag is None and existing_entry is not None:
                use_custom_schedule = bool(existing_entry.use_custom_schedule)
            else:
                use_custom_schedule = bool(custom_schedule_flag)

            if use_custom_schedule:
                start_date = self._parse_date(data.get("start_date"))
                due_date = self._parse_date(data.get("due_date")) or month_based_date
                end_date = self._parse_date(data.get("end_date"))

                if existing_entry is not None:
                    if start_date is None:
                        start_date = self._coerce_date(existing_entry.start_date)
                    if due_date is None:
                        due_date = self._coerce_date(existing_entry.due_date)
                    if end_date is None:
                        end_date = self._coerce_date(existing_entry.end_date)

                start_date, computed_end = self._compute_period_bounds(
                    start_date, frequency, due_date, end_date
                )
                due_date = computed_end
                end_date = computed_end
            else:
                reference_seed = month_based_date or datetime.date.today()
                start_seed = datetime.date(reference_seed.year, reference_seed.month, 1)
                start_date, computed_end = self._compute_period_bounds(
                    start_seed, frequency, None, None
                )
                due_date = computed_end
                end_date = computed_end

            is_recurring_flag = data.get("is_recurring")
            if is_recurring_flag is None:
                if existing_entry is not None:
                    is_recurring = bool(existing_entry.is_recurring)
                else:
                    is_recurring = frequency != "Única vez"
            else:
                is_recurring = bool(is_recurring_flag)
            if frequency == "Única vez":
                is_recurring = False

            goal_marker = data.get("goal_id", MISSING)
            debt_marker = data.get("debt_id", MISSING)

            goal = existing_entry.goal if existing_entry else None
            debt = existing_entry.debt if existing_entry else None

            if goal_marker is not MISSING:
                if goal_marker in (None, "", 0):
                    goal = None
                else:
                    goal = Goal.get_or_none(Goal.id == int(goal_marker))
                    if goal is None:
                        raise ValueError("La meta seleccionada no existe.")

            if debt_marker is not MISSING:
                if debt_marker in (None, "", 0):
                    debt = None
                else:
                    debt = Debt.get_or_none(Debt.id == int(debt_marker))
                    if debt is None:
                        raise ValueError("La deuda seleccionada no existe.")

            if goal is not None and debt is not None:
                raise ValueError("Una entrada de presupuesto no puede estar ligada a una meta y una deuda a la vez.")

            return {
                "description": description,
                "category": category,
                "type": entry_type,
                "budgeted_amount": amount,
                "frequency": frequency,
                "start_date": start_date,
                "end_date": end_date,
                "due_date": due_date,
                "use_custom_schedule": use_custom_schedule,
                "is_recurring": is_recurring,
                "goal": goal,
                "debt": debt,
            }
        except (ValueError, KeyError) as e:
            raise ValueError(f"Datos de presupuesto inválidos: {e}")

    def _build_virtual_budget_account(
        self, reference_date: Optional[datetime.date] = None
    ) -> Dict[str, Any]:
        """Calculate the remaining planned funds as a virtual account."""

        reference = reference_date or datetime.date.today()
        planned_income_total = 0.0
        planned_expense_total = 0.0
        actual_income_total = 0.0
        actual_expense_total = 0.0

        for entry in BudgetEntry.select():
            start, end = self._resolve_entry_bounds(entry)
            if start > reference or end < reference:
                continue

            entry_type = (getattr(entry, "type", "") or "").strip().lower()
            planned = float(getattr(entry, "budgeted_amount", 0) or 0)
            actual = float(getattr(entry, "actual_amount", 0) or 0)

            if entry_type == "ingreso":
                planned_income_total += planned
                actual_income_total += actual
            else:
                planned_expense_total += planned
                actual_expense_total += actual

        planned_net_total = planned_income_total - planned_expense_total
        balance = planned_net_total - actual_expense_total

        return {
            "id": -1,
            "name": "Saldo de Presupuesto",
            "account_type": "Virtual",
            "initial_balance": 0.0,
            "current_balance": balance,
            "is_virtual": True,
            "annual_interest_rate": 0.0,
            "compounding_frequency": "Mensual",
            "last_interest_accrual": None,
        }

    def get_budget_entries(self, filters=None):
        """Obtiene las entradas del presupuesto."""

        query = (
            BudgetEntry
            .select(BudgetEntry, Goal, Debt)
            .join(Goal, JOIN.LEFT_OUTER)
            .switch(BudgetEntry)
            .join(Debt, JOIN.LEFT_OUTER)
        )

        reference = datetime.date.today()

        if filters:
            status = (filters.get("status") or "").strip().lower()
            reference_value = filters.get("reference_date")

            if reference_value:
                if isinstance(reference_value, datetime.date):
                    reference = reference_value
                else:
                    try:
                        reference = datetime.date.fromisoformat(str(reference_value))
                    except (TypeError, ValueError):
                        reference = datetime.date.today()

            start_active = (
                (BudgetEntry.start_date <= reference)
                | BudgetEntry.start_date.is_null(True)
            )
            end_active = (
                (BudgetEntry.due_date >= reference)
                | BudgetEntry.due_date.is_null(True)
            )

            if status == "active":
                query = query.where(start_active & end_active)
            elif status == "upcoming":
                upcoming_condition = (
                    (BudgetEntry.start_date > reference)
                    | (
                        BudgetEntry.start_date.is_null(True)
                        & (BudgetEntry.due_date > reference)
                    )
                )
                query = query.where(upcoming_condition)
            elif status == "archived":
                query = query.where(BudgetEntry.due_date < reference)

        entries = [self._serialize_budget_entry(entry) for entry in query]

        def _sort_key(item: Dict[str, Any]):
            raw_due = item.get("due_date") or item.get("end_date")
            raw_start = item.get("start_date")
            try:
                return (
                    datetime.date.fromisoformat(raw_due)
                    if raw_due
                    else datetime.date.fromisoformat(raw_start)
                    if raw_start
                    else datetime.date.max
                )
            except (TypeError, ValueError):
                return datetime.date.max

        entries.sort(key=_sort_key)
        return entries

    def add_budget_entry(self, data):
        try:
            payload = self._prepare_budget_payload(data)
            entry = BudgetEntry.create(**payload)
            return self._serialize_budget_entry(entry)
        except ValueError as e:
            return {"error": str(e)}

    def update_budget_entry(self, entry_id, data):
        try:
            entry = BudgetEntry.get_by_id(entry_id)
            payload = self._prepare_budget_payload(data, existing_entry=entry)
            BudgetEntry.update(**payload).where(BudgetEntry.id == entry_id).execute()
            updated_entry = BudgetEntry.get_by_id(entry_id)
            return self._serialize_budget_entry(updated_entry)
        except BudgetEntry.DoesNotExist:
            return {"error": "La entrada de presupuesto no existe."}
        except ValueError as e:
            return {"error": str(e)}

    def delete_budget_entry(self, entry_id):
        try:
            Transaction.update(budget_entry=None).where(
                Transaction.budget_entry == entry_id
            ).execute()
            BudgetEntry.get_by_id(entry_id).delete_instance()
            return {"success": True}
        except BudgetEntry.DoesNotExist:
            return {"error": "La entrada de presupuesto no existe."}

    # =================================================================
    # --- SECCIÓN: PORTAFOLIO (Portfolio) ---
    # =================================================================
    
    def _trade_total_amount(self, payload: Dict[str, Any]) -> float:
        quantity = float(payload.get("quantity") or 0.0)
        price = float(payload.get("price") or 0.0)
        return quantity * price

    def _ensure_portfolio_category(self, category: str) -> None:
        """Guarantee that the portfolio transaction category exists."""

        normalized = (category or "").strip()
        if not normalized:
            return

        movimiento = Parameter.get_or_none(
            (Parameter.group == "Tipo de Transacción")
            & (Parameter.value == "Movimiento Portafolio")
        )

        if not movimiento:
            return

        exists = Parameter.get_or_none(
            (Parameter.group == "Categoría")
            & (Parameter.parent == movimiento)
            & (Parameter.value == normalized)
        )

        if exists:
            return

        Parameter.create(
            group="Categoría",
            value=normalized,
            parent=movimiento,
        )

    def _resolve_trade_account_name(self, trade: Trade) -> Optional[str]:
        """Return the most relevant account name linked to a trade."""

        transaction = getattr(trade, "linked_transaction", None)
        account = getattr(transaction, "account", None)
        if account and getattr(account, "name", None):
            return account.name

        linked_account = getattr(trade.asset, "linked_account", None)
        if linked_account and getattr(linked_account, "name", None):
            return linked_account.name

        return None

    def _build_trade_transaction_data(
        self,
        payload: Dict[str, Any],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        account = payload.get("linked_account")
        if account is None:
            return None, "Selecciona una cuenta para registrar la operación."

        normalized_type = self._normalize_trade_type(payload["trade_type"])
        amount = self._trade_total_amount(payload)
        description_prefix = "Venta" if normalized_type == "Venta" else "Compra"
        goal = payload.get("linked_goal")
        category = payload.get("asset_type") or f"Inversión {payload['symbol']}"
        self._ensure_portfolio_category(category)

        data = {
            "account_id": account.id,
            "date": payload["date"].isoformat(),
            "description": f"[Portafolio] {description_prefix} de {payload['symbol']}",
            "amount": amount,
            "type": "Movimiento Portafolio",
            "portfolio_direction": normalized_type,
            "category": category,
            "goal_id": getattr(goal, "id", None),
            "debt_id": None,
            "budget_entry_id": None,
            "is_transfer": False,
        }
        return data, None

    def _build_trade_budget_data(
        self,
        payload: Dict[str, Any],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        normalized_type = self._normalize_trade_type(payload["trade_type"])
        if normalized_type == "Venta":
            return None, "Las ventas deben registrarse como transacciones."

        amount = self._trade_total_amount(payload)
        description = f"[Portafolio] Compra planificada de {payload['symbol']}"
        goal = payload.get("linked_goal")
        date_value = payload["date"].isoformat()

        data = {
            "description": description,
            "category": payload.get("asset_type") or f"Inversión {payload['symbol']}",
            "type": "Gasto",
            "budgeted_amount": amount,
            "frequency": "Única vez",
            "use_custom_schedule": True,
            "start_date": date_value,
            "due_date": date_value,
            "end_date": date_value,
            "goal_id": getattr(goal, "id", None),
            "debt_id": None,
            "is_recurring": False,
        }
        return data, None

    def _create_trade_transaction(self, trade: Trade, payload: Dict[str, Any]):
        data, error = self._build_trade_transaction_data(payload)
        if error:
            return {"error": error}

        result = self.add_transaction(data)
        if "error" in result:
            return result

        trade.linked_transaction = result["id"]
        trade.save()
        return {"success": True}

    def _update_trade_transaction(self, trade: Trade, payload: Dict[str, Any]):
        data, error = self._build_trade_transaction_data(payload)
        if error:
            return {"error": error}

        if not getattr(trade, "linked_transaction_id", None):
            return self._create_trade_transaction(trade, payload)

        result = self.update_transaction(trade.linked_transaction_id, data)
        if "error" in result:
            return result
        return {"success": True}

    def _delete_trade_transaction(self, trade: Trade):
        transaction_id = getattr(trade, "linked_transaction_id", None)
        if not transaction_id:
            return {"success": True}

        result = self.delete_transaction(transaction_id, adjust_balance=True)
        if "error" in result:
            return result

        trade.linked_transaction = None
        trade.save()
        return {"success": True}

    def _create_trade_budget(self, trade: Trade, payload: Dict[str, Any]):
        data, error = self._build_trade_budget_data(payload)
        if error:
            return {"error": error}

        result = self.add_budget_entry(data)
        if "error" in result:
            return result

        trade.linked_budget_entry = result["id"]
        trade.save()
        return {"success": True}

    def _update_trade_budget(self, trade: Trade, payload: Dict[str, Any]):
        data, error = self._build_trade_budget_data(payload)
        if error:
            return {"error": error}

        entry_id = getattr(trade, "linked_budget_entry_id", None)
        if not entry_id:
            return self._create_trade_budget(trade, payload)

        result = self.update_budget_entry(entry_id, data)
        if "error" in result:
            return result
        return {"success": True}

    def _delete_trade_budget(self, trade: Trade):
        entry_id = getattr(trade, "linked_budget_entry_id", None)
        if not entry_id:
            return {"success": True}

        result = self.delete_budget_entry(entry_id)
        if "error" in result:
            return result

        trade.linked_budget_entry = None
        trade.save()
        return {"success": True}

    def get_portfolio_assets(self):
        """Obtiene los activos ejecutados y las operaciones planificadas."""

        assets = (
            PortfolioAsset
            .select(PortfolioAsset, Account, Goal)
            .join(Account, JOIN.LEFT_OUTER)
            .switch(PortfolioAsset)
            .join(Goal, JOIN.LEFT_OUTER)
            .where(PortfolioAsset.total_quantity > 0)
            .order_by(PortfolioAsset.symbol)
        )

        paid = []
        for asset in assets:
            quantity = float(asset.total_quantity or 0)
            avg_cost = float(asset.avg_cost_price or 0)
            current_price = float(asset.current_price or 0)
            market_value = quantity * current_price
            cost_basis = quantity * avg_cost
            unrealized_pnl = market_value - cost_basis

            annual_rate = float(asset.annual_yield_rate or 0)
            monthly_yield = market_value * (annual_rate / 1200) if annual_rate else 0.0
            linked_account = getattr(asset, "linked_account", None)
            linked_goal = getattr(asset, "linked_goal", None)

            paid.append(
                {
                    "symbol": asset.symbol,
                    "name": asset.asset_type,
                    "asset_type": asset.asset_type,
                    "quantity": quantity,
                    "avg_cost": avg_cost,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized_pnl,
                    "annual_yield_rate": annual_rate,
                    "monthly_yield": monthly_yield,
                    "linked_account_id": getattr(linked_account, "id", None),
                    "linked_account_name": getattr(linked_account, "name", None),
                    "linked_goal_id": getattr(linked_goal, "id", None),
                    "linked_goal_name": getattr(linked_goal, "name", None),
                }
            )

        planned_trades = (
            Trade
            .select(Trade, PortfolioAsset, BudgetEntry, Goal)
            .join(PortfolioAsset)
            .switch(Trade)
            .join(BudgetEntry, JOIN.LEFT_OUTER)
            .switch(PortfolioAsset)
            .join(Goal, JOIN.LEFT_OUTER)
            .switch(Trade)
            .where(Trade.is_planned == True)  # pylint: disable=singleton-comparison
            .order_by(Trade.date.desc(), Trade.id.desc())
        )

        planned = []
        for trade in planned_trades:
            normalized = self._normalize_trade_type(trade.trade_type)
            direction = "buy" if normalized == "Compra" else "sell"
            quantity = float(trade.quantity or 0)
            price = float(trade.price_per_unit or 0)
            budget_entry = getattr(trade, "linked_budget_entry", None)
            linked_goal = getattr(trade.asset, "linked_goal", None)

            planned.append(
                {
                    "id": trade.id,
                    "date": trade.date,
                    "symbol": trade.asset.symbol,
                    "asset_type": trade.asset.asset_type,
                    "type": direction,
                    "quantity": quantity,
                    "price": price,
                    "total_amount": quantity * price,
                    "linked_budget_entry_id": getattr(trade, "linked_budget_entry_id", None),
                    "budget_due_date": getattr(budget_entry, "due_date", None),
                    "budget_description": getattr(budget_entry, "description", None),
                    "linked_goal_id": getattr(linked_goal, "id", None),
                }
            )

        return {"paid": paid, "planned": planned}

    def get_trade_history(self):
        """Obtiene el historial de operaciones listo para la vista del frontend."""
        asset_query = (
            PortfolioAsset
            .select(PortfolioAsset, Account, Goal)
            .join(Account, JOIN.LEFT_OUTER)
            .switch(PortfolioAsset)
            .join(Goal, JOIN.LEFT_OUTER)
        )

        transaction_query = (
            Transaction
            .select(Transaction, Account)
            .join(Account, JOIN.LEFT_OUTER)
        )

        trades = prefetch(
            Trade.select().order_by(Trade.date.desc(), Trade.id.desc()),
            asset_query,
            transaction_query,
        )

        history = []
        for trade in trades:
            history.append(self._serialize_trade(trade))

        return history

    def add_trade(self, data):
        try:
            payload = self._parse_trade_payload(data)
        except ValueError as exc:
            return {"error": str(exc)}

        destination = str(data.get("sync_destination") or "none").strip().lower()
        if destination not in {"transaction", "budget", "none"}:
            return {"error": "Destino de registro no válido."}

        asset, created = PortfolioAsset.get_or_create(
            symbol=payload["symbol"], defaults={"asset_type": payload["asset_type"]}
        )
        metadata_dirty = False
        if payload["asset_type"] and asset.asset_type != payload["asset_type"]:
            asset.asset_type = payload["asset_type"]
            metadata_dirty = True

        if abs(float(asset.annual_yield_rate or 0) - payload["annual_yield_rate"]) > 1e-6:
            asset.annual_yield_rate = payload["annual_yield_rate"]
            metadata_dirty = True

        if asset.linked_account != payload["linked_account"]:
            asset.linked_account = payload["linked_account"]
            metadata_dirty = True

        if asset.linked_goal != payload["linked_goal"]:
            asset.linked_goal = payload["linked_goal"]
            metadata_dirty = True

        if metadata_dirty:
            asset.save()

        normalized_type = self._normalize_trade_type(payload["trade_type"])
        is_planned = destination == "budget"

        if destination == "transaction" and payload.get("linked_account") is None:
            return {"error": "Selecciona una cuenta para registrar la operación."}

        executed_entries = self._build_trade_entries(asset)
        available_quantity = float(getattr(asset, "total_quantity", 0) or 0.0)

        if not is_planned:
            if normalized_type == "Venta" and payload["quantity"] - available_quantity > 1e-4:
                return {"error": "No puedes vender más activos de los que posees."}

            projected_entries = executed_entries + [
                {
                    "id": None,
                    "date": payload["date"],
                    "trade_type": payload["trade_type"],
                    "quantity": payload["quantity"],
                    "price": payload["price"],
                }
            ]
            try:
                self._project_portfolio_asset(projected_entries, strict=True)
            except ValueError as exc:
                return {"error": str(exc)}
        else:
            if normalized_type == "Venta" and payload["quantity"] - available_quantity > 1e-4:
                return {
                    "error": "No puedes vender más activos ejecutados de los que posees."
                }

        try:
            with db.atomic():
                trade = Trade.create(
                    asset=asset,
                    trade_type=payload["trade_type"],
                    quantity=payload["quantity"],
                    price_per_unit=payload["price"],
                    date=payload["date"],
                    is_planned=is_planned,
                )

                if destination == "transaction":
                    sync_result = self._create_trade_transaction(trade, payload)
                    if "error" in sync_result:
                        raise ValueError(sync_result["error"])
                    trade.is_planned = False
                    trade.save()
                elif destination == "budget":
                    sync_result = self._create_trade_budget(trade, payload)
                    if "error" in sync_result:
                        raise ValueError(sync_result["error"])
                    trade.is_planned = True
                    trade.save()

                self._recalculate_portfolio_asset(asset, strict=True)
        except ValueError as exc:
            return {"error": str(exc)}

        return self._serialize_trade(trade)

    def update_trade(self, trade_id, data):
        try:
            trade = Trade.get_by_id(trade_id)
        except Trade.DoesNotExist:
            return {"error": "La operación no existe."}

        try:
            payload = self._parse_trade_payload(data)
        except ValueError as exc:
            return {"error": str(exc)}

        raw_destination = data.get("sync_destination")
        if raw_destination in (None, ""):
            if getattr(trade, "is_planned", False):
                destination = "budget"
            elif getattr(trade, "linked_transaction_id", None):
                destination = "transaction"
            else:
                destination = "none"
        else:
            destination = str(raw_destination).strip().lower()

        if destination not in {"transaction", "budget", "none"}:
            return {"error": "Destino de registro no válido."}

        normalized_type = self._normalize_trade_type(payload["trade_type"])
        is_planned = destination == "budget"

        if destination == "transaction" and payload.get("linked_account") is None:
            return {"error": "Selecciona una cuenta para registrar la operación."}

        original_asset = trade.asset
        target_asset, created = PortfolioAsset.get_or_create(
            symbol=payload["symbol"], defaults={"asset_type": payload["asset_type"]}
        )

        metadata_dirty = False
        if payload["asset_type"] and target_asset.asset_type != payload["asset_type"]:
            target_asset.asset_type = payload["asset_type"]
            metadata_dirty = True

        if abs(float(target_asset.annual_yield_rate or 0) - payload["annual_yield_rate"]) > 1e-6:
            target_asset.annual_yield_rate = payload["annual_yield_rate"]
            metadata_dirty = True

        if target_asset.linked_account != payload["linked_account"]:
            target_asset.linked_account = payload["linked_account"]
            metadata_dirty = True

        if target_asset.linked_goal != payload["linked_goal"]:
            target_asset.linked_goal = payload["linked_goal"]
            metadata_dirty = True

        if metadata_dirty:
            target_asset.save()

        exclude_id = trade.id if target_asset.id == original_asset.id else None
        target_entries = self._build_trade_entries(target_asset, exclude_id=exclude_id)
        new_entry = {
            "id": trade.id,
            "date": payload["date"],
            "trade_type": payload["trade_type"],
            "quantity": payload["quantity"],
            "price": payload["price"],
        }

        if not is_planned:
            projected_entries = target_entries + [new_entry]
            try:
                self._project_portfolio_asset(projected_entries, strict=True)
            except ValueError as exc:
                return {"error": str(exc)}
        else:
            if normalized_type == "Venta":
                current_qty, _, _ = self._project_portfolio_asset(target_entries, strict=True)
                if payload["quantity"] - current_qty > 1e-4:
                    return {
                        "error": "No puedes vender más activos ejecutados de los que posees."
                    }

        try:
            with db.atomic():
                trade.asset = target_asset
                trade.trade_type = payload["trade_type"]
                trade.quantity = payload["quantity"]
                trade.price_per_unit = payload["price"]
                trade.date = payload["date"]
                trade.is_planned = is_planned
                trade.save()

                if destination == "transaction":
                    if getattr(trade, "linked_budget_entry_id", None):
                        removal = self._delete_trade_budget(trade)
                        if "error" in removal:
                            raise ValueError(removal["error"])
                    sync_result = self._update_trade_transaction(trade, payload)
                    if "error" in sync_result:
                        raise ValueError(sync_result["error"])
                    trade.is_planned = False
                    trade.save()
                elif destination == "budget":
                    if getattr(trade, "linked_transaction_id", None):
                        removal = self._delete_trade_transaction(trade)
                        if "error" in removal:
                            raise ValueError(removal["error"])
                    sync_result = self._update_trade_budget(trade, payload)
                    if "error" in sync_result:
                        raise ValueError(sync_result["error"])
                    trade.is_planned = True
                    trade.save()
                else:
                    if getattr(trade, "linked_transaction_id", None):
                        removal = self._delete_trade_transaction(trade)
                        if "error" in removal:
                            raise ValueError(removal["error"])
                    if getattr(trade, "linked_budget_entry_id", None):
                        removal = self._delete_trade_budget(trade)
                        if "error" in removal:
                            raise ValueError(removal["error"])
                    trade.is_planned = False
                    trade.save()

                self._recalculate_portfolio_asset(target_asset, strict=True)
                if original_asset.id != target_asset.id:
                    self._recalculate_portfolio_asset(original_asset, strict=True)
        except ValueError as exc:
            return {"error": str(exc)}

        return self._serialize_trade(trade)

    def delete_trade(self, trade_id):
        try:
            trade = Trade.get_by_id(trade_id)
        except Trade.DoesNotExist:
            return {"error": "La operación no existe."}

        asset = trade.asset
        try:
            with db.atomic():
                removal_tx = self._delete_trade_transaction(trade)
                if "error" in removal_tx:
                    raise ValueError(removal_tx["error"])
                removal_budget = self._delete_trade_budget(trade)
                if "error" in removal_budget:
                    raise ValueError(removal_budget["error"])
                trade.delete_instance()
                self._recalculate_portfolio_asset(asset, strict=True)
        except ValueError as exc:
            return {"error": str(exc)}

        return {"success": True}

    # --- Métodos de utilidad internos ---

    def _parse_trade_payload(self, data):
        required_fields = ["symbol", "quantity", "price", "date"]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            raise ValueError(f"Faltan campos obligatorios: {', '.join(missing)}")

        try:
            quantity = float(data["quantity"])
            price = float(data["price"])
        except (TypeError, ValueError):
            raise ValueError("Cantidad y precio deben ser números válidos.")

        if quantity <= 0 or price <= 0:
            raise ValueError("Cantidad y precio deben ser mayores que cero.")

        raw_date = data.get("date")
        if isinstance(raw_date, datetime.date):
            trade_date = raw_date
        else:
            try:
                trade_date = datetime.datetime.strptime(str(raw_date), "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValueError(f"Fecha inválida: {exc}")

        trade_type = data.get("trade_type") or data.get("operation")
        normalized_type = self._normalize_trade_type(trade_type)

        symbol = str(data["symbol"]).strip().upper()
        asset_type = str(data.get("asset_type", "")).strip()

        if not symbol:
            raise ValueError("El símbolo del activo es obligatorio.")

        raw_yield = data.get("annual_yield_rate", 0)
        try:
            annual_yield_rate = float(raw_yield or 0)
        except (TypeError, ValueError):
            raise ValueError("La tasa anual debe ser un número válido.")

        if annual_yield_rate < 0:
            raise ValueError("La tasa anual no puede ser negativa.")

        account_marker = data.get("linked_account_id")
        goal_marker = data.get("linked_goal_id")

        linked_account = None
        linked_goal = None

        if account_marker not in (None, "", 0, "0"):
            try:
                account_id = int(account_marker)
            except (TypeError, ValueError):
                raise ValueError("La cuenta vinculada no es válida.")
            linked_account = Account.get_or_none(Account.id == account_id)
            if linked_account is None:
                raise ValueError("La cuenta vinculada no existe.")

        if goal_marker not in (None, "", 0, "0"):
            try:
                goal_id = int(goal_marker)
            except (TypeError, ValueError):
                raise ValueError("La meta vinculada no es válida.")
            linked_goal = Goal.get_or_none(Goal.id == goal_id)
            if linked_goal is None:
                raise ValueError("La meta vinculada no existe.")

        return {
            "symbol": symbol,
            "asset_type": asset_type or "Activo",
            "trade_type": normalized_type,
            "quantity": quantity,
            "price": price,
            "date": trade_date,
            "annual_yield_rate": annual_yield_rate,
            "linked_account": linked_account,
            "linked_goal": linked_goal,
        }

    def _normalize_trade_type(self, raw_type):
        if not raw_type:
            raise ValueError("El tipo de operación es obligatorio.")

        value = str(raw_type).strip().lower()
        if value in {"compra", "buy", "purchase"}:
            return "Compra"
        if value in {"venta", "sell"}:
            return "Venta"
        raise ValueError("Tipo de operación no reconocido. Usa Compra o Venta.")

    def _serialize_trade(self, trade):
        normalized = self._normalize_trade_type(trade.trade_type)
        response_type = "buy" if normalized == "Compra" else "sell"
        return {
            "id": trade.id,
            "date": trade.date,
            "symbol": trade.asset.symbol,
            "asset_type": trade.asset.asset_type,
            "type": response_type,
            "quantity": float(trade.quantity or 0),
            "price": float(trade.price_per_unit or 0),
            "annual_yield_rate": float(getattr(trade.asset, "annual_yield_rate", 0) or 0),
            "linked_account_id": getattr(getattr(trade.asset, "linked_account", None), "id", None),
            "linked_account_name": self._resolve_trade_account_name(trade),
            "linked_goal_id": getattr(getattr(trade.asset, "linked_goal", None), "id", None),
            "linked_transaction_id": getattr(trade, "linked_transaction_id", None),
            "linked_budget_entry_id": getattr(trade, "linked_budget_entry_id", None),
            "is_planned": bool(getattr(trade, "is_planned", False)),
        }

    def _build_trade_entries(self, asset, exclude_id=None, include_planned=False):
        entries = []
        for trade in asset.trades:
            if exclude_id and trade.id == exclude_id:
                continue
            if not include_planned and getattr(trade, "is_planned", False):
                continue
            entries.append({
                "id": trade.id,
                "date": trade.date,
                "trade_type": trade.trade_type,
                "quantity": float(trade.quantity or 0),
                "price": float(trade.price_per_unit or 0),
            })
        return entries

    def _project_portfolio_asset(self, entries, strict=True):
        if not entries:
            return 0.0, 0.0, 0.0

        ordered = sorted(
            entries,
            key=lambda item: (
                item.get("date") or datetime.date.today(),
                item.get("id") or 0,
            ),
        )

        total_quantity = 0.0
        avg_cost = 0.0
        last_price = 0.0

        for entry in ordered:
            normalized = self._normalize_trade_type(entry["trade_type"])
            quantity = float(entry.get("quantity") or 0)
            price = float(entry.get("price") or 0)
            last_price = price or last_price

            if normalized == "Compra":
                total_cost = (total_quantity * avg_cost) + (quantity * price)
                total_quantity += quantity
                avg_cost = total_cost / total_quantity if total_quantity > 0 else 0.0
            else:
                if strict and quantity - total_quantity > 1e-4:
                    raise ValueError("No puedes vender más activos de los que posees.")
                total_quantity = max(total_quantity - quantity, 0.0)

        if total_quantity <= 0:
            return 0.0, 0.0, last_price
        return total_quantity, avg_cost, last_price

    def _recalculate_portfolio_asset(self, asset, strict=False):
        entries = self._build_trade_entries(asset)
        if not entries:
            asset.total_quantity = 0.0
            asset.avg_cost_price = 0.0
            asset.current_price = 0.0
            asset.save()
            return asset

        try:
            total_qty, avg_cost, last_price = self._project_portfolio_asset(entries, strict=strict)
        except ValueError as exc:
            if strict:
                raise
            # En modo no estricto, mantenemos los valores actuales y registramos el problema.
            total_qty = asset.total_quantity
            avg_cost = asset.avg_cost_price
            last_price = asset.current_price

        asset.total_quantity = total_qty
        asset.avg_cost_price = avg_cost
        asset.current_price = last_price
        asset.save()
        return asset


    def _get_date_range(self, year, months):
        """Calcula las fechas de inicio y fin para un período."""
        if not months:
            start_date = datetime.date(year, 1, 1)
            end_date = datetime.date(year, 12, 31)
        else:
            min_month, max_month = min(months), max(months)
            start_date = datetime.date(year, min_month, 1)
            last_day = calendar.monthrange(year, max_month)[1]
            end_date = datetime.date(year, max_month, last_day)

        return start_date, end_date

