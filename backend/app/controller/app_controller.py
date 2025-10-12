from collections import defaultdict
import calendar
import datetime
from typing import Optional, Iterable, List
from dateutil.relativedelta import relativedelta
from peewee import fn

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
    
    def get_dashboard_data(self, year: int, months: Optional[Iterable[int]]):
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
            transactions = list(Transaction.select().where(Transaction.date.between(start_date, end_date)))

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
    # --- SECCIÓN: CUENTAS (Accounts) ---
    # =================================================================

    def get_accounts_data_for_view(self):
        """Devuelve una lista de todas las cuentas."""
        return list(Account.select().dicts())

    def add_account(self, data):
        """Crea una nueva cuenta."""
        try:
            balance = float(data.get("initial_balance", 0))
            account = Account.create(
                name=data["name"],
                account_type=data["account_type"],
                initial_balance=balance,
                current_balance=balance
            )
            return account._data
        except (ValueError, KeyError) as e:
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
            trade_type = (trade.trade_type or "").strip().lower()
            normalized_type = "buy" if trade_type == "compra" else "sell" if trade_type == "venta" else trade_type

            history.append(
                {
                    "id": trade.id,
                    "date": trade.date.isoformat() if trade.date else None,
                    "symbol": trade.asset.symbol,
                    "type": normalized_type,
                    "quantity": float(trade.quantity or 0),
                    "price": float(trade.price_per_unit or 0),
                }
            )

        return history

    def add_trade(self, data):
        try:
            quantity = float(data["quantity"])
            price = float(data["price"])
        except ValueError:
            return {"error": "Cantidad y Precio deben ser números válidos."}

        asset, created = PortfolioAsset.get_or_create(
            symbol=data["symbol"].upper(), defaults={"asset_type": data["asset_type"]}
        )
        if data["operation"] == "Compra":
            new_total_quantity = asset.total_quantity + quantity
            new_cost = (asset.total_quantity * asset.avg_cost_price) + (quantity * price)
            asset.avg_cost_price = new_cost / new_total_quantity if new_total_quantity > 0 else 0
            asset.total_quantity = new_total_quantity
        else: # Venta
            if quantity > asset.total_quantity:
                return {"error": "No puedes vender más activos de los que posees."}
            asset.total_quantity -= quantity

        Trade.create(
            asset=asset, trade_type=data["operation"], quantity=quantity,
            price_per_unit=price, date=data["date"],
        )
        asset.current_price = price
        asset.save()
        return asset._data


    # --- Métodos de utilidad internos ---
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

