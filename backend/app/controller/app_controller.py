from collections import defaultdict
import calendar
import datetime
from typing import Optional, List, Dict, Any
from dateutil.relativedelta import relativedelta
from peewee import fn, JOIN

# --- Importaciones de Modelos de Datos ---
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


class AppController:
    """
    Controlador de la aplicación que maneja la lógica de negocio.
    Esta versión está adaptada para funcionar como un backend/API,
    eliminando todas las dependencias de la interfaz gráfica (app.view).
    """
    def __init__(self, view=None):
        self.view = view
        self.current_pages = {}

    # =================================================================
    # --- SECCIÓN: LÓGICA GENERAL Y DE UTILIDAD ---
    # =================================================================

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
        transactions = list(self._get_transactions_for_period(year, month_list))

        kpis = self._get_dashboard_kpis(year, month_list, transactions)
        net_worth_data = self._get_net_worth_data_for_chart()
        cash_flow_data = self._get_cash_flow_data_for_chart(year, month_list)

        goals_summary = self.get_goals_summary()

        accounts_summary = [
            {
                "id": account.id,
                "name": account.name,
                "account_type": account.account_type,
                "initial_balance": float(account.initial_balance or 0),
                "current_balance": float(account.current_balance or 0),
            }
            for account in Account.select().order_by(Account.name)
        ]

        budget_vs_actual = self._get_budget_vs_actual_summary(year, month_list, transactions)
        budget_rule_control = self._get_budget_rule_control(transactions, kpis["income"]["amount"])
        expense_distribution = self._get_expense_distribution(transactions)
        expense_type_comparison = self._get_expense_type_comparison(transactions)

        dashboard_data = {
            "kpis": kpis,
            "net_worth_chart": net_worth_data,
            "cash_flow_chart": cash_flow_data,
            "goals": goals_summary,
            "accounts": accounts_summary,
            "budget_vs_actual": budget_vs_actual,
            "budget_rule_control": budget_rule_control,
            "expense_distribution": expense_distribution,
            "expense_type_comparison": expense_type_comparison,
        }
        return dashboard_data

    def _get_dashboard_kpis(self, year: int, months: List[int], transactions: Optional[List[Transaction]] = None):
        """Calcula los KPIs de ingresos, gastos y ahorro para el período seleccionado."""
        start_date, end_date = self._get_date_range(year, months)

        if transactions is None:
            transactions = list(
                Transaction.select().where(
                    (Transaction.date >= start_date) & (Transaction.date <= end_date)
                )
            )

        income = sum(float(t.amount or 0) for t in transactions if t.type == "Ingreso")
        expense = sum(abs(float(t.amount or 0)) for t in transactions if t.type != "Ingreso")
        net = income - expense

        num_months = len(months) if months else 12
        previous_start = start_date - relativedelta(months=num_months)
        previous_end = start_date - relativedelta(days=1)

        previous_trans = list(Transaction.select().where(Transaction.date.between(previous_start, previous_end)))
        prev_income = sum(float(t.amount or 0) for t in previous_trans if t.type == "Ingreso")
        prev_expense = sum(abs(float(t.amount or 0)) for t in previous_trans if t.type != "Ingreso")
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
        """Prepara los datos para el gráfico de evolución de patrimonio neto."""
        today = datetime.date.today()
        dates, values = [], []
        for i in range(12, -1, -1):
            month_end = (today - relativedelta(months=i)).replace(day=1)
            next_m = month_end.replace(day=28) + datetime.timedelta(days=4)
            month_end = next_m - datetime.timedelta(days=next_m.day)
            if month_end > today: month_end = today
            
            total_balance = Account.select(fn.SUM(Account.current_balance)).scalar() or 0.0
            liabilities = Debt.select(fn.SUM(Debt.current_balance)).scalar() or 0.0
            
            dates.append(month_end.strftime("%Y-%m-%d"))
            values.append(total_balance - liabilities)
        return {"dates": dates, "values": values}

    def _get_cash_flow_data_for_chart(self, year: int, months: List[int]):
        """Prepara los datos para el gráfico de flujo de efectivo mensual."""
        start_date, end_date = self._get_date_range(year, months)

        query = (
            Transaction
            .select(fn.strftime('%Y-%m', Transaction.date).alias('month'),
                    fn.SUM(Transaction.amount).alias('total'),
                    Transaction.type)
            .where((Transaction.date >= start_date) & (Transaction.date <= end_date))
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

    def _get_transactions_for_period(self, year: int, months: List[int]):
        """Obtiene las transacciones dentro del periodo seleccionado."""
        start_date, end_date = self._get_date_range(year, months)
        return Transaction.select().where(Transaction.date.between(start_date, end_date))

    def _get_budget_vs_actual_summary(
        self,
        year: int,
        months: List[int],
        transactions: List[Transaction],
    ):
        """Construye el resumen de presupuesto vs. gasto real para ingresos y gastos."""

        start_date, end_date = self._get_date_range(year, months)
        entries = list(BudgetEntry.select().where(BudgetEntry.due_date.between(start_date, end_date)))

        budgeted_income = 0.0
        budgeted_expense = 0.0
        for entry in entries:
            amount = float(getattr(entry, 'budgeted_amount', 0) or 0)
            if entry.type == 'Ingreso':
                budgeted_income += amount
            else:
                budgeted_expense += amount

        actual_income = sum(float(t.amount or 0) for t in transactions if t.type == 'Ingreso')
        actual_expense = sum(abs(float(t.amount or 0)) for t in transactions if t.type != 'Ingreso')

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

        parameters = Parameter.select().where(Parameter.group == 'Tipo de Transacción')
        type_to_rule = {}
        for param in parameters:
            if param.budget_rule_id:
                type_to_rule[param.value] = param.budget_rule

        totals: Dict[str, float] = defaultdict(float)
        for transaction in transactions:
            if transaction.type == 'Ingreso':
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
        for transaction in transactions:
            if transaction.type == 'Ingreso':
                continue
            category = transaction.category or 'Sin categoría'
            totals[category] += abs(float(transaction.amount or 0))

        sorted_items = sorted(totals.items(), key=lambda item: item[1], reverse=True)
        categories = [item[0] for item in sorted_items]
        amounts = [item[1] for item in sorted_items]

        return {"categories": categories, "amounts": amounts}

    def _get_expense_type_comparison(self, transactions: List[Transaction]):
        """Distribución de gastos por tipo (ej. fijo, variable)."""

        totals: Dict[str, float] = defaultdict(float)
        for transaction in transactions:
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

        if month:
            start_date = datetime.date(year, month, 1)
            end_date = (start_date + relativedelta(months=1)) - datetime.timedelta(days=1)
        else:
            start_date = datetime.date(year, 1, 1)
            end_date = datetime.date(year, 12, 31)

        query = (
            Transaction
            .select(
                Transaction.category,
                Transaction.type,
                fn.SUM(Transaction.amount).alias('total')
            )
            .where((Transaction.date >= start_date) & (Transaction.date <= end_date))
            .group_by(Transaction.category, Transaction.type)
        )

        income = []
        expenses = []
        for row in query.dicts():
            amount = float(row['total'] or 0)
            entry = {"category": row['category'], "amount": abs(amount) if amount is not None else 0}
            if row['type'] == 'Ingreso':
                entry["amount"] = amount
                income.append(entry)
            else:
                expenses.append(entry)

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
        transactions = list(self._get_transactions_for_period(year, month_list))

        annual_expense_report = self._build_annual_expense_report(year, month_list)
        budget_analysis = self._build_budget_analysis(year, month_list, transactions)
        cash_flow_projection = self._build_cash_flow_projection(
            year, month_list, projection_months, transactions
        )

        return {
            "year": year,
            "months": month_list,
            "annual_expense_report": annual_expense_report,
            "budget_analysis": budget_analysis,
            "cash_flow_projection": cash_flow_projection,
        }

    def _build_annual_expense_report(self, year: int, months: List[int]) -> Dict[str, Any]:
        """Genera una tabla de gastos anuales agrupados por categoría y mes."""

        start_date, end_date = self._get_date_range(year, months)
        month_list = sorted(set(months)) if months else list(range(1, 13))

        category_field = fn.COALESCE(Transaction.category, 'Sin categoría').alias('category_name')
        month_field = fn.strftime('%m', Transaction.date).alias('month')

        query = (
            Transaction.select(
                category_field,
                month_field,
                fn.SUM(Transaction.amount).alias('total'),
            )
            .where(
                (Transaction.date.between(start_date, end_date))
                & (Transaction.type != 'Ingreso')
            )
            .group_by(category_field, month_field)
        )

        rows: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        monthly_totals: Dict[int, float] = defaultdict(float)

        for item in query.dicts():
            category = item.get('category_name') or 'Sin categoría'
            month_number = int(item.get('month') or 0)
            if month_number not in month_list:
                continue
            amount = abs(float(item.get('total') or 0.0))
            rows[category][month_number] += amount
            monthly_totals[month_number] += amount

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

        parameters = Parameter.select().where(Parameter.group == 'Tipo de Transacción')
        type_to_rule: Dict[str, Optional[BudgetRule]] = {}
        for param in parameters:
            type_to_rule[param.value] = param.budget_rule if param.budget_rule_id else None

        budget_entries = BudgetEntry.select().where(
            BudgetEntry.due_date.between(start_date, end_date)
        )

        budget_totals: Dict[str, float] = defaultdict(float)
        for entry in budget_entries:
            key = type_to_rule.get(entry.type)
            rule_name = key.name if key else (entry.type or 'Sin Regla')
            budget_totals[rule_name] += float(getattr(entry, 'budgeted_amount', 0) or 0)

        actual_totals: Dict[str, float] = defaultdict(float)
        for transaction in transactions:
            if transaction.type == 'Ingreso':
                continue
            rule = type_to_rule.get(transaction.type)
            rule_name = rule.name if rule else (transaction.type or 'Sin Regla')
            actual_totals[rule_name] += abs(float(transaction.amount or 0))

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
        return list(Account.select().dicts())

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
            account = Account.create(
                name=name,
                account_type=account_type,
                initial_balance=balance,
                current_balance=balance,
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
        query = Transaction.select(Transaction, Account).join(Account)
        
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
                query = query.where(Transaction.category == filters['category'])

            sortBy = filters.get('sort_by', 'date_desc')
            if sortBy == 'date_asc': query = query.order_by(Transaction.date.asc())
            elif sortBy == 'amount_desc': query = query.order_by(Transaction.amount.desc())
            elif sortBy == 'amount_asc': query = query.order_by(Transaction.amount.asc())
            else: query = query.order_by(Transaction.date.desc())
        else:
            query = query.order_by(Transaction.date.desc())
            
        results = []
        for transaction in query:
            t_data = transaction.__data__
            t_data['account'] = transaction.account.__data__ # Anidar info de la cuenta
            results.append(t_data)
        return results
            
    
    def add_transaction(self, data):
        try:
            is_recurring = data.pop('is_recurring', False)
            frequency = data.pop('frequency', None)
            day_of_month = data.pop('day_of_month', None)

            amount = float(data['amount'])
            account = Account.get_by_id(data['account_id'])
            if data['type'] == 'Ingreso': account.current_balance += amount
            else: account.current_balance -= amount
            account.save()
            
            transaction = Transaction.create(**data)

            if is_recurring:
                RecurringTransaction.create(
                    description=data['description'], amount=amount, type=data['type'],
                    category=data['category'], frequency=frequency, day_of_month=day_of_month,
                    start_date=data['date'], last_processed_date=data['date']
                )
            return transaction.__data__
        except Exception as e:
            return {"error": f"Datos inválidos: {e}"}

    def update_transaction(self, transaction_id, data):
        try:
            original_transaction = Transaction.get_by_id(transaction_id)
            
            original_account = Account.get_by_id(original_transaction.account_id)
            if original_transaction.type == 'Ingreso': original_account.current_balance -= original_transaction.amount
            else: original_account.current_balance += original_transaction.amount
            
            new_account = Account.get_by_id(data['account_id'])
            new_amount = float(data['amount'])
            if data['type'] == 'Ingreso': new_account.current_balance += new_amount
            else: new_account.current_balance -= new_amount

            original_account.save()
            if original_account.id != new_account.id: new_account.save()
                
            query = Transaction.update(**data).where(Transaction.id == transaction_id)
            query.execute()
            
            return Transaction.get_by_id(transaction_id).__data__
        except Exception as e:
            return {"error": f"Error al actualizar: {e}"}

    def delete_transaction(self, transaction_id):
        try:
            transaction = Transaction.get_by_id(transaction_id)
            account = transaction.account
            if transaction.type == 'Ingreso': account.current_balance -= transaction.amount
            else: account.current_balance += transaction.amount
            account.save()
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
        """
        return list(Parameter.select().where(Parameter.parent == parent_id).dicts())

    # -----------------------------------------------------------------
    # --- Tipos de transacción y reglas de presupuesto ---
    # -----------------------------------------------------------------

    def _serialize_transaction_type(self, parameter: Parameter) -> Dict[str, Any]:
        return {
            "id": parameter.id,
            "name": parameter.value,
            "budget_rule_id": parameter.budget_rule_id,
            "budget_rule_name": parameter.budget_rule.name if parameter.budget_rule else None,
            "is_deletable": bool(parameter.is_deletable),
        }

    def _serialize_budget_rule(self, rule: BudgetRule) -> Dict[str, Any]:
        in_use = Parameter.select().where(Parameter.budget_rule == rule).exists()
        return {
            "id": rule.id,
            "name": rule.name,
            "percentage": float(rule.percentage or 0),
            "is_deletable": not in_use,
        }

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

    def add_transaction_type(self, name: str, budget_rule_id: Optional[int]) -> Dict[str, Any]:
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

        parameter = Parameter.create(
            group="Tipo de Transacción",
            value=name,
            budget_rule=budget_rule,
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
            target_amount = float(goal.target_amount or 0)
            current_amount = float(goal.current_amount or 0)
            percentage = (current_amount / target_amount * 100) if target_amount else 0.0
            goals_data.append({
                "id": goal.id,
                "name": goal.name,
                "target_amount": target_amount,
                "current_amount": current_amount,
                "percentage": percentage,
            })
        return goals_data

    def get_all_goals(self):
        """Devuelve todas las metas con su progreso."""
        goals = []
        for goal in Goal.select():
            goal_dict = goal._data.copy()
            goal_dict["completion_percentage"] = self._calculate_completion_percentage(
                goal_dict.get("current_amount", 0),
                goal_dict.get("target_amount", 0),
            )
            goals.append(goal_dict)
        return goals

    def get_all_debts(self):
        """Devuelve todas las deudas con su progreso."""
        debts = []
        for debt in Debt.select():
            debt_dict = debt._data.copy()
            paid_amount = debt_dict.get("total_amount", 0) - debt_dict.get("current_balance", 0)
            debt_dict["completion_percentage"] = self._calculate_completion_percentage(
                paid_amount,
                debt_dict.get("total_amount", 0),
            )
            debts.append(debt_dict)
        return debts

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
            return goal._data
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
            return goal._data
        except Goal.DoesNotExist:
            return {"error": "La meta no existe."}
        except (ValueError, KeyError) as e:
            return {"error": f"Datos de meta inválidos: {e}"}

    def add_debt(self, data):
        try:
            total = float(data['total_amount'])
            min_payment = float(data.get('minimum_payment', 0))
            interest = float(data.get('interest_rate', 0))
            
            debt = Debt.create(
                name=data['name'],
                total_amount=total,
                current_balance=total,
                minimum_payment=min_payment,
                interest_rate=interest
            )
            return debt._data
        except (ValueError, KeyError) as e:
            return {"error": f"Datos de deuda inválidos: {e}"}

    def update_debt(self, debt_id, data):
        try:
            debt = Debt.get_by_id(debt_id)
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
            return debt._data
        except Debt.DoesNotExist:
            return {"error": "La deuda no existe."}
        except (ValueError, KeyError) as e:
            return {"error": f"Datos de deuda inválidos: {e}"}

    def delete_goal(self, goal_id):
        try:
            Transaction.update(goal=None).where(Transaction.goal == goal_id).execute()
            Goal.get_by_id(goal_id).delete_instance()
            return {"success": True}
        except Goal.DoesNotExist:
            return {"error": "La meta no existe."}
            
    def delete_debt(self, debt_id):
        try:
            Transaction.update(debt=None).where(Transaction.debt == debt_id).execute()
            Debt.get_by_id(debt_id).delete_instance()
            return {"success": True}
        except Debt.DoesNotExist:
            return {"error": "La deuda no existe."}


    # =================================================================
    # --- SECCIÓN: PRESUPUESTO (Budget) ---
    # =================================================================

    def _serialize_budget_entry(self, entry):
        """Convierte una entrada de presupuesto en un diccionario apto para la API."""
        due_date = entry.due_date if hasattr(entry, "due_date") else None
        if due_date is not None and not isinstance(due_date, datetime.date):
            # Peewee puede devolver strings si se utilizan .dicts()
            if isinstance(due_date, str):
                due_date = datetime.date.fromisoformat(due_date)

        month = due_date.month if due_date else None
        year = due_date.year if due_date else None

        is_dict = isinstance(entry, dict)

        return {
            "id": entry["id"] if is_dict else entry.id,
            "description": entry.get("description") if is_dict else entry.description,
            "category": entry.get("category") if is_dict else entry.category,
            "type": entry.get("type") if is_dict else entry.type,
            "amount": entry.get("budgeted_amount") if is_dict else entry.budgeted_amount,
            "budgeted_amount": entry.get("budgeted_amount")
            if is_dict
            else entry.budgeted_amount,
            "due_date": due_date.isoformat() if due_date else None,
            "month": month,
            "year": year,
        }

    def _prepare_budget_payload(self, data, existing_entry=None):
        """Normaliza los datos recibidos desde la API para la base de datos."""
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

            raw_due_date = data.get("due_date")
            if raw_due_date:
                if isinstance(raw_due_date, datetime.datetime):
                    due_date = raw_due_date.date()
                elif isinstance(raw_due_date, datetime.date):
                    due_date = raw_due_date
                else:
                    due_date = datetime.date.fromisoformat(str(raw_due_date))
            else:
                if existing_entry and existing_entry.due_date:
                    default_month = existing_entry.due_date.month
                    default_year = existing_entry.due_date.year
                else:
                    today = datetime.date.today()
                    default_month = today.month
                    default_year = today.year
                month = int(data.get("month", default_month))
                year = int(data.get("year", default_year))
                due_date = datetime.date(year, month, 1)

            return {
                "description": description,
                "category": category,
                "type": entry_type,
                "budgeted_amount": amount,
                "due_date": due_date,
            }
        except (ValueError, KeyError) as e:
            raise ValueError(f"Datos de presupuesto inválidos: {e}")

    def get_budget_entries(self, filters=None):
        """Obtiene las entradas del presupuesto."""
        entries = BudgetEntry.select().order_by(BudgetEntry.due_date.desc())
        return [self._serialize_budget_entry(entry) for entry in entries]

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
            BudgetEntry.get_by_id(entry_id).delete_instance()
            return {"success": True}
        except BudgetEntry.DoesNotExist:
            return {"error": "La entrada de presupuesto no existe."}

    # =================================================================
    # --- SECCIÓN: PORTAFOLIO (Portfolio) ---
    # =================================================================
    
    def get_portfolio_assets(self):
        """Obtiene todos los activos del portafolio listos para la vista del frontend."""
        assets = (
            PortfolioAsset
            .select()
            .where(PortfolioAsset.total_quantity > 0)
            .order_by(PortfolioAsset.symbol)
        )

        summary = []
        for asset in assets:
            quantity = float(asset.total_quantity or 0)
            avg_cost = float(asset.avg_cost_price or 0)
            current_price = float(asset.current_price or 0)
            market_value = quantity * current_price
            cost_basis = quantity * avg_cost
            unrealized_pnl = market_value - cost_basis

            summary.append(
                {
                    "symbol": asset.symbol,
                    "name": asset.asset_type,
                    "asset_type": asset.asset_type,
                    "quantity": quantity,
                    "avg_cost": avg_cost,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized_pnl,
                }
            )

        return summary

    def get_trade_history(self):
        """Obtiene el historial de operaciones listo para la vista del frontend."""
        trades = (
            Trade
            .select(Trade, PortfolioAsset)
            .join(PortfolioAsset)
            .order_by(Trade.date.desc())
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

        asset, created = PortfolioAsset.get_or_create(
            symbol=payload["symbol"], defaults={"asset_type": payload["asset_type"]}
        )
        if payload["asset_type"] and asset.asset_type != payload["asset_type"]:
            asset.asset_type = payload["asset_type"]
            asset.save()

        projected_entries = self._build_trade_entries(asset)
        projected_entries.append({
            "id": None,
            "date": payload["date"],
            "trade_type": payload["trade_type"],
            "quantity": payload["quantity"],
            "price": payload["price"],
        })

        try:
            total_qty, avg_cost, last_price = self._project_portfolio_asset(projected_entries, strict=True)
        except ValueError as exc:
            return {"error": str(exc)}

        trade = Trade.create(
            asset=asset,
            trade_type=payload["trade_type"],
            quantity=payload["quantity"],
            price_per_unit=payload["price"],
            date=payload["date"],
        )

        asset.total_quantity = total_qty
        asset.avg_cost_price = avg_cost
        asset.current_price = last_price
        asset.save()

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

        original_asset = trade.asset
        target_asset, created = PortfolioAsset.get_or_create(
            symbol=payload["symbol"], defaults={"asset_type": payload["asset_type"]}
        )
        if payload["asset_type"] and target_asset.asset_type != payload["asset_type"]:
            target_asset.asset_type = payload["asset_type"]
            target_asset.save()

        # Construimos la proyección para el activo destino
        target_entries = self._build_trade_entries(target_asset, exclude_id=trade.id if target_asset.id == original_asset.id else None)
        target_entries.append({
            "id": trade.id,
            "date": payload["date"],
            "trade_type": payload["trade_type"],
            "quantity": payload["quantity"],
            "price": payload["price"],
        })

        try:
            target_qty, target_avg, target_price = self._project_portfolio_asset(target_entries, strict=True)
        except ValueError as exc:
            return {"error": str(exc)}

        # Si el activo cambia, recalculamos también el original excluyendo la operación
        if original_asset.id != target_asset.id:
            original_entries = self._build_trade_entries(original_asset, exclude_id=trade.id)
            try:
                orig_qty, orig_avg, orig_price = self._project_portfolio_asset(original_entries, strict=True)
            except ValueError as exc:
                return {"error": str(exc)}
        else:
            orig_qty, orig_avg, orig_price = target_qty, target_avg, target_price

        trade.asset = target_asset
        trade.trade_type = payload["trade_type"]
        trade.quantity = payload["quantity"]
        trade.price_per_unit = payload["price"]
        trade.date = payload["date"]
        trade.save()

        target_asset.total_quantity = target_qty
        target_asset.avg_cost_price = target_avg
        target_asset.current_price = target_price
        target_asset.save()

        if original_asset.id != target_asset.id:
            original_asset.total_quantity = orig_qty
            original_asset.avg_cost_price = orig_avg
            original_asset.current_price = orig_price
            original_asset.save()

        return self._serialize_trade(trade)

    def delete_trade(self, trade_id):
        try:
            trade = Trade.get_by_id(trade_id)
        except Trade.DoesNotExist:
            return {"error": "La operación no existe."}

        asset = trade.asset
        trade.delete_instance()
        self._recalculate_portfolio_asset(asset)
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

        return {
            "symbol": symbol,
            "asset_type": asset_type or "Activo",
            "trade_type": normalized_type,
            "quantity": quantity,
            "price": price,
            "date": trade_date,
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
        }

    def _build_trade_entries(self, asset, exclude_id=None):
        entries = []
        for trade in asset.trades:
            if exclude_id and trade.id == exclude_id:
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
                if strict and quantity > total_quantity + 1e-6:
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

