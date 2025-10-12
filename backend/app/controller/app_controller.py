from collections import defaultdict
import datetime
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
    
    def get_dashboard_data(self, year, months):
        """Agrega y devuelve todos los datos necesarios para el Dashboard."""
        
        # Lógica de KPIs (Ingresos, Gastos, Ahorro)
        kpis = self._get_dashboard_kpis(year, months)

        # Lógica para Gráfico de Patrimonio Neto
        net_worth_data = self._get_net_worth_data_for_chart()
        
        # Lógica para Gráfico de Flujo de Efectivo
        cash_flow_data = self._get_cash_flow_data_for_chart(year, months)

        # Lógica para Resumen de Metas
        goals_summary = self.get_goals_summary()

        # Lógica para Cuentas
        accounts_summary = self.get_accounts_data_for_view()
        
        dashboard_data = {
            "kpis": kpis,
            "net_worth_chart": net_worth_data,
            "cash_flow_chart": cash_flow_data,
            "goals_summary": goals_summary,
            "accounts_summary": accounts_summary,
            # ... se pueden añadir más datos aquí (presupuesto, distribución de gastos, etc.)
        }
        return dashboard_data

    def _get_dashboard_kpis(self, year, months):
        """Calcula los KPIs de ingresos, gastos y ahorro para el período seleccionado."""
        start_date, end_date = self._get_date_range(year, months)
        
        # Periodo actual
        current_trans = list(Transaction.select().where(Transaction.date.between(start_date, end_date)))
        income = sum(t.amount for t in current_trans if t.type == "Ingreso")
        expense = sum(t.amount for t in current_trans if t.type != "Ingreso")
        net = income - expense

        # Periodo anterior para comparación
        num_months = len(months) if months else 12
        previous_start = start_date - relativedelta(months=num_months)
        previous_end = start_date - relativedelta(days=1)
        
        previous_trans = list(Transaction.select().where(Transaction.date.between(previous_start, previous_end)))
        prev_income = sum(t.amount for t in previous_trans if t.type == "Ingreso")
        prev_expense = sum(t.amount for t in previous_trans if t.type != "Ingreso")

        income_comp = ((income - prev_income) / prev_income * 100) if prev_income > 0 else None
        expense_comp = ((expense - prev_expense) / prev_expense * 100) if prev_expense > 0 else None
        
        return {
            "income": income, "expense": expense, "net": net,
            "income_comparison": income_comp, "expense_comparison": expense_comp
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

    def _get_cash_flow_data_for_chart(self, year, months):
        """Prepara los datos para el gráfico de flujo de efectivo mensual."""
        start_date, _ = self._get_date_range(year, months)

        query = (Transaction
                 .select(fn.strftime('%Y-%m', Transaction.date).alias('month'), 
                         fn.SUM(Transaction.amount).alias('total'), 
                         Transaction.type)
                 .where(Transaction.date >= start_date)
                 .group_by(fn.strftime('%Y-%m', Transaction.date), Transaction.type)
                 .order_by(fn.strftime('%Y-%m', Transaction.date)))

        monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0})
        for row in query.dicts():
            if row['type'] == 'Ingreso':
                monthly_data[row['month']]['income'] = row['total']
            else:
                monthly_data[row['month']]['expense'] += row['total']
        
        return dict(sorted(monthly_data.items()))


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
    # --- SECCIÓN: METAS Y DEUDAS (Goals & Debts) ---
    # =================================================================

    def get_goals_summary(self):
        """Devuelve un resumen de las metas para el dashboard."""
        goals_data = []
        for g in Goal.select().where(Goal.current_amount < Goal.target_amount).limit(3):
            goals_data.append(g._data)
        return goals_data

    def get_all_goals(self):
        """Devuelve todas las metas con su progreso."""
        return list(Goal.select().dicts())
        
    def get_all_debts(self):
        """Devuelve todas las deudas con su progreso."""
        return list(Debt.select().dicts())

    def add_goal(self, data):
        try:
            target = float(data['target_amount'])
            goal = Goal.create(name=data['name'], target_amount=target, current_amount=0)
            return goal._data
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
        """Obtiene todos los activos del portafolio."""
        return list(PortfolioAsset.select().where(PortfolioAsset.total_quantity > 0).dicts())

    def get_trade_history(self):
        """Obtiene el historial de ventas."""
        return list(Trade.select().join(PortfolioAsset).where(Trade.trade_type == "Venta").order_by(Trade.date.desc()).dicts(True))

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
            _, last_day = datetime.date(year, max_month, 1).replace(day=28) + datetime.timedelta(days=4)
            end_date = datetime.date(year, max_month, last_day)
        return start_date, end_date

