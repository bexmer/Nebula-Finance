from PySide6.QtWidgets import QMessageBox, QTableWidget
from PySide6.QtCore import QDate, Qt
from app.model.transaction import Transaction; from app.model.goal import Goal; from app.model.debt import Debt; from app.model.budget_entry import BudgetEntry
from app.model.portfolio_asset import PortfolioAsset; from app.model.trade import Trade
from app.model.recurring_transaction import RecurringTransaction
from app.model.account import Account
from app.view.edit_transaction_dialog import EditTransactionDialog
from app.view.edit_goal_debt_dialog import EditGoalDebtDialog
from app.view.edit_budget_entry_dialog import EditBudgetEntryDialog
from app.view.edit_account_dialog import EditAccountDialog
from app.view.edit_recurring_dialog import EditRecurringDialog
from app.view.quick_transaction_dialog import QuickTransactionDialog
import datetime; from collections import defaultdict
from peewee import JOIN, fn
from dateutil.relativedelta import relativedelta

BUDGET_RULES = {"Esenciales": 0.50, "Crecimiento": 0.25, "Estabilidad": 0.15, "Recompensas": 0.10}
CATEGORY_TO_RULE_MAPPING = { "Vivienda": "Esenciales", "Servicios": "Esenciales", "Comida": "Esenciales", "Transporte": "Esenciales", "Salud": "Esenciales", "Educación": "Esenciales", "Ahorro": "Crecimiento", "Pago Deuda": "Estabilidad", "Ocio": "Recompensas", "Otros Gastos": "Recompensas" }

class AppController:
    def __init__(self, view):
        self.view = view
        self.view.dashboard_page.year_filter.currentTextChanged.connect(self.update_dashboard)
        for action in self.view.dashboard_page.month_actions: action.triggered.connect(self.update_dashboard)
        self.view.dashboard_page.all_year_action.triggered.connect(self.update_dashboard)
        self.view.analysis_page.year_selector.currentTextChanged.connect(self.update_analysis_view)
        self.view.budget_page.add_button.clicked.connect(self.add_budget_entry)
        self.view.budget_page.delete_button.clicked.connect(self.delete_budget_entry)
        self.view.budget_page.table.cellDoubleClicked.connect(self.edit_budget_entry_by_row)
        self.view.accounts_page.table.cellDoubleClicked.connect(self.edit_account_by_row)

    def full_refresh(self):
        self.process_recurring_transactions()
        self.load_accounts()
        self.load_transactions()
        self.update_dashboard()
        self.load_goals()
        self.load_debts()
        self.update_analysis_view()
        self.load_budget_entries()
        self.load_portfolio()

    def add_account(self):
        data = self.view.accounts_page.get_form_data()
        if not data["name"] or not data["initial_balance"]:
            self.view.show_notification("Nombre y Saldo Inicial son obligatorios.", "error"); return
        try:
            balance = float(data["initial_balance"])
        except ValueError:
            self.view.show_notification("El saldo debe ser un número válido.", "error"); return
        Account.create(name=data["name"], account_type=data["account_type"], initial_balance=balance, current_balance=balance)
        self.view.accounts_page.clear_form(); self.full_refresh(); self.view.show_notification("Cuenta añadida con éxito.", "success")

    def delete_account(self):
        account_id = self.view.accounts_page.get_selected_account_id()
        if account_id:
            if Transaction.select().where(Transaction.account == account_id).count() > 0:
                self.view.show_notification("No se puede eliminar una cuenta con transacciones asociadas.", "error"); return
            if QMessageBox.question(self.view, "Confirmar", "¿Eliminar esta cuenta?") == QMessageBox.StandardButton.Yes:
                Account.get_by_id(account_id).delete_instance(); self.full_refresh(); self.view.show_notification("Cuenta eliminada.", "success")

    def load_accounts(self):
        accounts = list(Account.select())
        self.view.accounts_page.display_accounts(accounts)
        self.view.transactions_page.update_accounts_list(accounts)

    def edit_account_by_row(self, row, column):
        account_id = self.view.accounts_page.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not account_id: return
        try:
            account = Account.get_by_id(account_id)
            account_data = {"name": account.name, "account_type": account.account_type}
            dialog = EditAccountDialog(account_data, self.view)
            if dialog.exec():
                new_data = dialog.get_data()
                account.name = new_data['name']
                account.account_type = new_data['account_type']
                account.save()
                self.full_refresh()
                self.view.show_notification("Cuenta actualizada.", "success")
        except Account.DoesNotExist:
            self.view.show_notification("La cuenta no fue encontrada.", "error")

    def process_recurring_transactions(self):
        today = datetime.date.today(); rules_updated = False
        first_account = Account.select().first()
        if not first_account: return
        for rule in RecurringTransaction.select():
            start_from = rule.last_processed_date or rule.start_date
            next_due_dates = []
            if rule.frequency == 'Anual':
                try:
                    next_due = datetime.date(start_from.year, rule.month_of_year, rule.day_of_month)
                    if next_due <= start_from: next_due = datetime.date(start_from.year + 1, rule.month_of_year, rule.day_of_month)
                    if next_due <= today: next_due_dates.append(next_due)
                except ValueError: pass
            elif rule.frequency == 'Mensual':
                try:
                    next_due = start_from.replace(day=rule.day_of_month)
                    if next_due <= start_from: next_due += relativedelta(months=1)
                    while next_due <= today: next_due_dates.append(next_due); next_due += relativedelta(months=1)
                except ValueError: pass
            elif rule.frequency == 'Quincenal':
                try:
                    next_due1 = start_from.replace(day=rule.day_of_month)
                    if next_due1 <= start_from: next_due1 += relativedelta(months=1)
                    while next_due1 <= today: next_due_dates.append(next_due1); next_due1 += relativedelta(months=1)
                except ValueError: pass
                try:
                    next_due2 = start_from.replace(day=rule.day_of_month_2)
                    if next_due2 <= start_from: next_due2 += relativedelta(months=1)
                    while next_due2 <= today: next_due_dates.append(next_due2); next_due2 += relativedelta(months=1)
                except (ValueError, TypeError): pass
            for due_date in sorted(list(set(next_due_dates))):
                if not rule.last_processed_date or due_date > rule.last_processed_date:
                    Transaction.create(date=due_date, description=rule.description, amount=rule.amount, type=rule.type, category=rule.category, account=first_account)
                    if rule.type == 'Ingreso': first_account.current_balance += rule.amount
                    else: first_account.current_balance -= rule.amount
                    first_account.save()
                    rule.last_processed_date = due_date; rules_updated = True
            rule.save()
        if rules_updated: self.view.show_notification("Transacciones recurrentes generadas.", "success"); self.full_refresh()

    def load_recurring_rules(self):
        rules = RecurringTransaction.select().order_by(RecurringTransaction.day_of_month)
        next_dates = {}
        for rule in rules:
            last_run = rule.last_processed_date or rule.start_date
            try:
                if rule.frequency == 'Anual':
                    next_due = last_run.replace(month=rule.month_of_year, day=rule.day_of_month)
                    if next_due <= last_run: next_due = next_due.replace(year=last_run.year + 1)
                else:
                    next_due = last_run.replace(day=rule.day_of_month)
                    if next_due <= last_run: next_due += relativedelta(months=1)
                next_dates[rule.id] = next_due.strftime('%Y-%m-%d')
            except (ValueError, TypeError): next_dates[rule.id] = "Fecha Inválida"
        self.view.transactions_page.display_recurring_rules(rules, next_dates)

    def add_trade(self):
        data = self.view.portfolio_page.get_trade_form_data()
        if not all([data['symbol'], data['asset_type'], data['quantity'], data['price']]):
            self.view.show_notification("Todos los campos son obligatorios.", "error"); return
        try:
            quantity = float(data['quantity']); price = float(data['price'])
        except ValueError: self.view.show_notification("Cantidad y Precio deben ser números válidos.", "error"); return
        asset, created = PortfolioAsset.get_or_create(symbol=data['symbol'].upper(), defaults={'asset_type': data['asset_type']})
        if data['operation'] == 'Compra':
            new_total_quantity = asset.total_quantity + quantity
            new_cost = (asset.total_quantity * asset.avg_cost_price) + (quantity * price)
            asset.avg_cost_price = new_cost / new_total_quantity if new_total_quantity > 0 else 0
            asset.total_quantity = new_total_quantity
        else:
            if quantity > asset.total_quantity: self.view.show_notification("No puedes vender más activos de los que posees.", "error"); return
            asset.total_quantity -= quantity
        Trade.create(asset=asset, trade_type=data['operation'], quantity=quantity, price_per_unit=price, date=data['date'])
        asset.current_price = price; asset.save()
        self.view.show_notification("Operación registrada con éxito.", "success")
        self.view.portfolio_page.clear_trade_form(); self.load_portfolio()

    def load_portfolio(self):
        assets = list(PortfolioAsset.select().where(PortfolioAsset.total_quantity > 0))
        self.view.portfolio_page.display_portfolio(assets)
        self.view.portfolio_page.display_simple_portfolio(assets)
        sell_trades = Trade.select().where(Trade.trade_type == 'Venta').order_by(Trade.date.desc())
        self.view.portfolio_page.display_history(sell_trades)
        
    def add_transaction(self):
        data = self.view.transactions_page.get_form_data()
        if data['is_recurring']:
            if not data["description"] or not data["amount"]:
                self.view.show_notification("Descripción y Monto son obligatorios.", "error"); return
            try: amount = float(data["amount"])
            except ValueError: self.view.show_notification("El monto debe ser un número válido.", "error"); return
            RecurringTransaction.create(
                description=data["description"], amount=amount, type=data["type"], category=data["category"],
                frequency=data["frequency"], month_of_year=data.get("month_of_year"),
                day_of_month=data["day_of_month"], day_of_month_2=data.get("day_of_month_2"),
                start_date=data["date"])
            self.view.show_notification("Regla de transacción recurrente añadida.", "success")
        else:
            if not data["account_id"]: self.view.show_notification("Debe seleccionar una cuenta.", "error"); return
            if not data["description"] or not data["amount"]: self.view.show_notification("Descripción y Monto son obligatorios.", "error"); return
            try: amount = float(data["amount"])
            except ValueError: self.view.show_notification("El monto debe ser un número válido.", "error"); return
            try:
                account = Account.get_by_id(data["account_id"])
                if data["type"] == 'Ingreso': account.current_balance += amount
                else: account.current_balance -= amount
                account.save()
            except Account.DoesNotExist: self.view.show_notification("La cuenta seleccionada no es válida.", "error"); return
            goal_id, debt_id = data.get("goal_id"), data.get("debt_id")
            if data["type"] == "Ahorro/Pago Meta/Deuda":
                if goal_id:
                    try: goal = Goal.get_by_id(goal_id); goal.current_amount += amount; goal.save()
                    except Goal.DoesNotExist: pass
                if debt_id:
                    try: debt = Debt.get_by_id(debt_id); debt.current_balance -= amount; debt.save()
                    except Debt.DoesNotExist: pass
            Transaction.create(date=data["date"], description=data["description"], amount=amount, type=data["type"], category=data["category"], goal=goal_id, debt=debt_id, account=data["account_id"])
            self.view.show_notification("¡Transacción añadida!", "success")
        self.view.transactions_page.clear_form(); self.full_refresh()

    def delete_transaction(self):
        selected_id = self.view.transactions_page.get_selected_transaction_id()
        current_tab = self.view.transactions_page.tabs.currentIndex()
        if current_tab == 3:
            if selected_id and QMessageBox.question(self.view, "Confirmar", "¿Eliminar esta regla recurrente?") == QMessageBox.StandardButton.Yes:
                RecurringTransaction.get_by_id(selected_id).delete_instance(); self.full_refresh(); self.view.show_notification("Regla eliminada.", "success")
        else:
            if selected_id and QMessageBox.question(self.view, "Confirmar", "¿Eliminar transacción?") == QMessageBox.StandardButton.Yes: 
                try:
                    transaction = Transaction.get_by_id(selected_id)
                    account = Account.get_by_id(transaction.account_id)
                    if transaction.type == 'Ingreso': account.current_balance -= transaction.amount
                    else: account.current_balance += transaction.amount
                    account.save()
                    if transaction.goal: transaction.goal.current_amount -= transaction.amount; transaction.goal.save()
                    if transaction.debt: transaction.debt.current_balance += transaction.amount; transaction.debt.save()
                    transaction.delete_instance(); self.full_refresh(); self.view.show_notification("Transacción eliminada.", "success")
                except (Transaction.DoesNotExist, Account.DoesNotExist): self.view.show_notification("Error al eliminar.", "error")

    def update_transaction(self, transaction, data):
        try: amount = float(data["amount"])
        except ValueError: self.view.show_notification("El monto debe ser un número válido.", "error"); return
        try:
            old_account = Account.get_by_id(transaction.account_id)
            if transaction.type == 'Ingreso': old_account.current_balance -= transaction.amount
            else: old_account.current_balance += transaction.amount
            old_account.save()
        except Account.DoesNotExist: pass
        try:
            new_account = Account.get_by_id(data["account_id"])
            if data["type"] == 'Ingreso': new_account.current_balance += amount
            else: new_account.current_balance -= amount
            new_account.save()
        except Account.DoesNotExist: pass
        if transaction.goal_id:
            try: old_goal = Goal.get_by_id(transaction.goal_id); old_goal.current_amount -= transaction.amount; old_goal.save()
            except Goal.DoesNotExist: pass
        if transaction.debt_id:
            try: old_debt = Debt.get_by_id(transaction.debt_id); old_debt.current_balance += transaction.amount; old_debt.save()
            except Debt.DoesNotExist: pass
        
        transaction.date, transaction.description, transaction.amount, transaction.type, transaction.category, transaction.goal, transaction.debt, transaction.account = data["date"], data["description"], amount, data["type"], data["category"], data["goal_id"], data["debt_id"], data["account_id"]
        
        if data["goal_id"]:
            try: new_goal = Goal.get_by_id(data["goal_id"]); new_goal.current_amount += amount; new_goal.save()
            except Goal.DoesNotExist: pass
        if data["debt_id"]:
            try: new_debt = Debt.get_by_id(data["debt_id"]); new_debt.current_balance -= amount; new_debt.save()
            except Debt.DoesNotExist: pass
        transaction.save(); self.full_refresh(); self.view.show_notification("Transacción actualizada.", "success")

    def edit_transaction_by_row(self, row, column, table_widget):
        if not table_widget: return
        item = table_widget.item(row, 0)
        if not item: return
        transaction_id = item.data(Qt.ItemDataRole.UserRole)
        if not transaction_id: return
        try:
            transaction = Transaction.get_by_id(transaction_id)
            t_data = {"id": transaction.id, "date": transaction.date.strftime('%Y-%m-%d'), "description": transaction.description, "amount": transaction.amount, "type": transaction.type, "category": transaction.category, "goal_id": transaction.goal_id, "debt_id": transaction.debt_id, "account_id": transaction.account_id}
            goals, debts, accounts = Goal.select(), Debt.select(), Account.select()
            dialog = EditTransactionDialog(t_data, goals, debts, accounts, self.view)
            if dialog.exec(): self.update_transaction(transaction, dialog.get_data())
        except Transaction.DoesNotExist: self.view.show_notification("Transacción no encontrada.", "error")
    
    def load_transactions(self): 
        self.filter_transactions(); 
        goals, debts = Goal.select(), Debt.select()
        self.view.transactions_page.update_goal_and_debt_lists(goals, debts)
        accounts = list(Account.select())
        self.view.transactions_page.update_accounts_list(accounts)

    def filter_transactions(self):
        filters = self.view.transactions_page.get_filters()
        tab_index = filters["current_tab_index"]

        if tab_index == 3:
            self.load_recurring_rules()
            return

        query = Transaction.select()
        
        # --- INICIO DE LA SOLUCIÓN: Lógica de JOIN explícita ---
        if tab_index == 1:
            query = query.join(Goal).where(Transaction.goal.is_null(False))
        elif tab_index == 2:
            query = query.join(Debt).where(Transaction.debt.is_null(False))
        # Para tab_index 0, no se necesita un join específico a Goal o Debt,
        # pero sí a Account para obtener información si fuera necesario.
        # Por seguridad, nos aseguramos que el join a Account esté presente.
        if query.model != Account:
             query = query.join(Account, on=(Transaction.account == Account.id))
        # --- FIN DE LA SOLUCIÓN ---

        start_date, end_date = filters["start_date"], filters["end_date"]
        query = query.where((Transaction.date >= start_date) & (Transaction.date <= end_date))
        
        if filters["search_text"]: query = query.where(Transaction.description.contains(filters["search_text"]))
        if filters["type"] != "Todos los Tipos": query = query.where(Transaction.type == filters["type"])
        if filters["category"] != "Todas las Categorías": query = query.where(Transaction.category == filters["category"])
        
        sort_field = Transaction.date if filters["sort_by"] == "Fecha" else Transaction.amount
        if filters["sort_order"] == "Descendente": query = query.order_by(sort_field.desc())
        else: query = query.order_by(sort_field.asc())
        
        transactions = list(query)

        if tab_index == 0:
            self.view.transactions_page.display_all_transactions(transactions)
        elif tab_index == 1:
            self.view.transactions_page.display_goal_transactions(transactions)
        elif tab_index == 2:
            self.view.transactions_page.display_debt_transactions(transactions)

    def add_budget_entry(self):
        data = self.view.budget_page.get_form_data()
        if not data["description"] or not data["budgeted_amount"]: self.view.show_notification("Descripción y Monto son obligatorios.", "error"); return
        try: amount = float(data["budgeted_amount"])
        except (ValueError, TypeError): self.view.show_notification("El monto debe ser un número válido.", "error"); return
        BudgetEntry.create(description=data["description"], category=data["category"], type=data["type"], budgeted_amount=amount)
        self.view.budget_page.clear_form(); self.full_refresh(); self.view.show_notification("Entrada de presupuesto añadida.", "success")

    def delete_budget_entry(self):
        entry_id = self.view.budget_page.get_selected_entry_id()
        if entry_id and QMessageBox.question(self.view, "Confirmar", "¿Eliminar entrada?") == QMessageBox.StandardButton.Yes:
            BudgetEntry.get_by_id(entry_id).delete_instance(); self.full_refresh(); self.view.show_notification("Entrada eliminada.", "success")

    def load_budget_entries(self):
        entries = BudgetEntry.select().order_by(BudgetEntry.type, BudgetEntry.description)
        self.view.budget_page.display_budget_entries(entries)

    def edit_budget_entry_by_row(self, row, column):
        entry_id = self.view.budget_page.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not entry_id: return
        try:
            entry = BudgetEntry.get_by_id(entry_id)
            entry_data = {"description": entry.description, "budgeted_amount": entry.budgeted_amount, "type": entry.type, "category": entry.category}
            dialog = EditBudgetEntryDialog(entry_data, self.view)
            if dialog.exec(): self.update_budget_entry(entry, dialog.get_data())
        except BudgetEntry.DoesNotExist: self.view.show_notification("Entrada no encontrada.", "error")

    def update_budget_entry(self, entry, data):
        if not data["description"] or not data["budgeted_amount"]: self.view.show_notification("Todos los campos son obligatorios.", "error"); return
        try: amount = float(data["budgeted_amount"])
        except (ValueError, TypeError): self.view.show_notification("El monto debe ser un número válido.", "error"); return
        entry.description, entry.category, entry.type, entry.budgeted_amount = data["description"], data["category"], data["type"], amount
        entry.save(); self.full_refresh(); self.view.show_notification("Entrada de presupuesto actualizada.", "success")

    def update_dashboard(self):
        filters = self.view.dashboard_page.get_selected_filters(); year, months = filters["year"], filters["months"]
        trans, total_income, total_expense = self._update_kpis(year, months); self._update_net_worth_chart()
        budgeted_income = sum(b.budgeted_amount for b in BudgetEntry.select().where(BudgetEntry.type == 'Ingreso Planeado'))
        budgeted_expense = sum(b.budgeted_amount for b in BudgetEntry.select().where(BudgetEntry.type == 'Gasto Planeado'))
        self.view.dashboard_page.update_budget_vs_real_cards(
            income_data={"budgeted_amount": budgeted_income, "real_amount": total_income},
            expense_data={"budgeted_amount": budgeted_expense, "real_amount": total_expense}
        )
        self._update_dashboard_widgets()
        if trans: self._update_expense_dist_chart(trans); self._update_budget_rule_chart(trans, total_income)
        else: self.view.dashboard_page.clear_expense_dist_chart(); self.view.dashboard_page.clear_budget_rule_chart()

    def _update_dashboard_widgets(self):
        today = datetime.date.today(); upcoming_payments = []
        rules = RecurringTransaction.select().order_by(RecurringTransaction.day_of_month)
        for rule in rules:
            last_run = rule.last_processed_date or rule.start_date
            try:
                next_due = last_run.replace(day=rule.day_of_month)
                if next_due <= today: next_due += relativedelta(months=1)
                upcoming_payments.append({"date": next_due, "description": rule.description, "amount": rule.amount})
            except (ValueError, TypeError): pass
        sorted_payments = sorted(upcoming_payments, key=lambda p: p['date'])
        for payment in sorted_payments: payment['date'] = payment['date'].strftime('%Y-%m-%d')
        self.view.dashboard_page.update_upcoming_payments(sorted_payments[:5])
        
        main_goals_query = Goal.select().where(Goal.current_amount < Goal.target_amount).order_by((Goal.current_amount / Goal.target_amount).desc()).limit(3)
        goals_data = [{"name": goal.name, "current": goal.current_amount, "target": goal.target_amount} for goal in main_goals_query]
        self.view.dashboard_page.update_main_goals(goals_data)

    def _update_kpis(self, year, months):
        if not months: self.view.dashboard_page.update_kpis(0, 0, 0); return [], 0, 0
        start = datetime.date(year, min(months), 1); last = max(months)
        if last == 12: end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else: end = datetime.date(year, last + 1, 1) - datetime.timedelta(days=1)
        current = list(Transaction.select().where((Transaction.date >= start) & (Transaction.date <= end)))
        income = sum(t.amount for t in current if t.type == 'Ingreso')
        expense = sum(t.amount for t in current if t.type.startswith('Gasto') or t.type == "Ahorro/Pago Meta/Deuda")
        net = income - expense; income_comp, expense_comp = None, None
        if len(months) == 1:
            prev_end = start - datetime.timedelta(days=1); prev_start = prev_end.replace(day=1)
            prev = Transaction.select().where((Transaction.date >= prev_start) & (Transaction.date <= prev_end))
            prev_income = sum(t.amount for t in prev if t.type == 'Ingreso'); prev_expense = sum(t.amount for t in prev if t.type.startswith('Gasto') or t.type == "Ahorro/Pago Meta/Deuda")
            def get_change(c, p): return ((c - p) / p) * 100 if p > 0 else (100.0 if c > 0 else 0.0)
            income_comp = get_change(income, prev_income); expense_comp = get_change(expense, prev_expense)
        self.view.dashboard_page.update_kpis(income, expense, net, income_comp, expense_comp); return current, income, expense

    def _update_budget_rule_chart(self, transactions, total_income):
        total_expense = sum(t.amount for t in transactions if t.type != 'Ingreso')
        is_overdrawn = total_expense > total_income
        if total_income == 0: total_income = 1
        spending = defaultdict(float)
        for t in transactions:
            if t.type != 'Ingreso':
                if t.type == "Ahorro/Pago Meta/Deuda": rule = "Crecimiento" if t.goal else ("Estabilidad" if t.debt else "Recompensas")
                else: rule = CATEGORY_TO_RULE_MAPPING.get(t.category, "Recompensas")
                spending[rule] += t.amount
        budget_data = []
        for name, ideal in BUDGET_RULES.items():
            actual = spending.get(name, 0.0)
            percent_of_income = (actual / total_income) * 100 if total_income > 1 else 0
            
            state = "good"
            if is_overdrawn:
                state = "critical"
            elif percent_of_income > (ideal * 100) + 10:
                state = "critical"
            elif percent_of_income > ideal * 100:
                state = "warning"

            budget_data.append({
                "name": name, 
                "ideal_percent": ideal * 100, 
                "actual_percent": percent_of_income, 
                "actual_amount": actual, 
                "state": state,
                "is_overdrawn": is_overdrawn
            })
        self.view.dashboard_page.update_budget_rule_chart(budget_data)
        
    def _update_net_worth_chart(self):
        today = datetime.date.today(); dates = []; values = []
        for i in range(12, -1, -1):
            month_end = (today - datetime.timedelta(days=i*30)).replace(day=1); next_m = month_end.replace(day=28) + datetime.timedelta(days=4); month_end = next_m - datetime.timedelta(days=next_m.day)
            total_balance = Account.select(fn.SUM(Account.initial_balance)).scalar() or 0.0
            transactions_up_to_date = Transaction.select().where(Transaction.date <= month_end)
            for t in transactions_up_to_date:
                if t.type == 'Ingreso': total_balance += t.amount
                else: total_balance -= t.amount
            liabilities = sum((d.total_amount - sum(t.amount for t in Transaction.select().where((Transaction.debt == d) & (Transaction.date <= month_end)))) for d in Debt.select())
            dates.append(int(month_end.strftime("%Y%m%d"))); values.append(total_balance - liabilities)
        self.view.dashboard_page.update_net_worth_chart(dates, values)
        
    def _update_expense_dist_chart(self, transactions):
        expenses = defaultdict(float)
        for t in transactions:
            if t.type.startswith("Gasto"): expenses[t.category] += t.amount
        sorted_exp = sorted(expenses.items(), key=lambda i: i[1], reverse=True)
        cats = [i[0] for i in sorted_exp]; amounts = [i[1] for i in sorted_exp]
        self.view.dashboard_page.update_expense_dist_chart(cats, amounts)

    def add_goal(self):
        data = self.view.goals_page.get_goal_form_data()
        if not data["name"] or not data["target_amount"]: self.view.show_notification("Todos los campos son obligatorios.", "error"); return
        try: target = float(data["target_amount"])
        except (ValueError, TypeError): self.view.show_notification("El monto debe ser un número válido.", "error"); return
        Goal.create(name=data["name"], target_amount=target, current_amount=0); self.view.goals_page.clear_goal_form(); self.full_refresh(); self.view.show_notification("¡Meta añadida!", "success")

    def add_debt(self):
        data = self.view.goals_page.get_debt_form_data()
        if not data["name"] or not data["total_amount"] or not data["minimum_payment"]: self.view.show_notification("Todos los campos son obligatorios.", "error"); return
        try: total, min_pay = float(data["total_amount"]), float(data["minimum_payment"])
        except (ValueError, TypeError): self.view.show_notification("Los montos deben ser números válidos.", "error"); return
        Debt.create(name=data["name"], total_amount=total, minimum_payment=min_pay, current_balance=total); self.view.goals_page.clear_debt_form(); self.full_refresh(); self.view.show_notification("¡Deuda añadida!", "success")

    def edit_goal(self, goal_id):
        try:
            goal = Goal.get_by_id(goal_id); g_data = {"name": goal.name, "target_amount": goal.target_amount}
            dialog = EditGoalDebtDialog(g_data, 'goal', self.view)
            if dialog.exec():
                new_data = dialog.get_data(); 
                if not new_data["name"] or not new_data["target_amount"]: self.view.show_notification("Todos los campos son obligatorios.", "error"); return
                goal.name = new_data["name"]; goal.target_amount = float(new_data["target_amount"]); goal.save(); self.full_refresh(); self.view.show_notification("Meta actualizada.", "success")
        except (Goal.DoesNotExist, ValueError): self.view.show_notification("No se pudo editar la meta.", "error")

    def delete_goal(self, goal_id):
        if QMessageBox.question(self.view, "Confirmar", "¿Eliminar meta?") == QMessageBox.StandardButton.Yes:
            Transaction.update(goal=None).where(Transaction.goal == goal_id).execute(); Goal.get_by_id(goal_id).delete_instance(); self.full_refresh(); self.view.show_notification("Meta eliminada.", "success")

    def edit_debt(self, debt_id):
        try:
            debt = Debt.get_by_id(debt_id); d_data = {"name": debt.name, "total_amount": debt.total_amount, "minimum_payment": debt.minimum_payment}
            dialog = EditGoalDebtDialog(d_data, 'debt', self.view)
            if dialog.exec():
                new_data = dialog.get_data(); 
                if not new_data["name"] or not new_data["total_amount"] or not new_data["minimum_payment"]: self.view.show_notification("Todos los campos son obligatorios.", "error"); return
                debt.name = new_data["name"]; debt.total_amount = float(new_data["total_amount"]); debt.minimum_payment = float(new_data["minimum_payment"]); debt.save(); self.full_refresh(); self.view.show_notification("Deuda actualizada.", "success")
        except (Debt.DoesNotExist, ValueError): self.view.show_notification("No se pudo editar la deuda.", "error")

    def delete_debt(self, debt_id):
        if QMessageBox.question(self.view, "Confirmar", "¿Eliminar deuda?") == QMessageBox.StandardButton.Yes:
            Transaction.update(debt=None).where(Transaction.debt == debt_id).execute(); Debt.get_by_id(debt_id).delete_instance(); self.full_refresh(); self.view.show_notification("Deuda eliminada.", "success")

    def load_goals(self): self.view.goals_page.display_goals(Goal.select())
    def load_debts(self): self.view.goals_page.display_debts(Debt.select())
    
    def update_analysis_view(self):
        total_account_balance = Account.select(fn.SUM(Account.current_balance)).scalar() or 0.0
        portfolio_value = PortfolioAsset.select(fn.SUM(PortfolioAsset.total_quantity * PortfolioAsset.current_price)).scalar() or 0.0
        total_assets = total_account_balance + portfolio_value
        total_liabilities = sum(d.current_balance for d in Debt.select())
        self.view.analysis_page.update_net_worth_display(total_assets, total_liabilities, total_assets - total_liabilities)
        year = int(self.view.analysis_page.year_selector.currentText()); self._generate_and_display_annual_report(year)

    def _generate_and_display_annual_report(self, year):
        start = datetime.date(year, 1, 1); end = datetime.date(year, 12, 31)
        trans = Transaction.select().where((Transaction.date >= start) & (Transaction.date <= end) & (Transaction.type.startswith('Gasto')))
        data = defaultdict(lambda: defaultdict(float)); cats = set(); monthly = defaultdict(float); grand = 0.0
        for t in trans: data[t.category][t.date.month]+=t.amount; cats.add(t.category); monthly[t.date.month]+=t.amount; grand+=t.amount
        self.view.analysis_page.display_annual_report(data, sorted(list(cats)), year, monthly, grand)
    
    def show_quick_transaction_dialog(self):
        accounts = list(Account.select())
        if not accounts:
            self.view.show_notification("Para un gasto rápido, primero debes crear una cuenta.", "error")
            return
        dialog = QuickTransactionDialog(accounts, self.view)
        if dialog.exec():
            data = dialog.get_data()
            self.add_quick_transaction(data)

    def add_quick_transaction(self, data):
        if not data["description"] or not data["amount"]:
            self.view.show_notification("Descripción y Monto son obligatorios.", "error"); return
        try:
            amount = float(data["amount"])
        except ValueError:
            self.view.show_notification("El monto debe ser un número válido.", "error"); return
        try:
            account = Account.get_by_id(data["account_id"])
            account.current_balance -= amount
            account.save()
        except Account.DoesNotExist:
            self.view.show_notification("La cuenta seleccionada no es válida.", "error"); return
        Transaction.create(
            date=datetime.date.today(), description=data["description"], amount=amount,
            type="Gasto Variable", category=data["category"], account=data["account_id"]
        )
        self.view.show_notification("Gasto rápido añadido.", "success")
        self.full_refresh()
    
    def edit_recurring_transaction_by_row(self, row, column):
        rule_id = self.view.transactions_page.recurring_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not rule_id: return
        try:
            rule = RecurringTransaction.get_by_id(rule_id)
            rule_data = {
                "description": rule.description, "amount": rule.amount, "type": rule.type,
                "category": rule.category, "frequency": rule.frequency, "day_of_month": rule.day_of_month,
                "day_of_month_2": rule.day_of_month_2, "month_of_year": rule.month_of_year
            }
            dialog = EditRecurringDialog(rule_data, self.view)
            if dialog.exec():
                new_data = dialog.get_data()
                try: amount = float(new_data["amount"])
                except ValueError: self.view.show_notification("El monto debe ser un número válido.", "error"); return
                
                rule.description = new_data["description"]; rule.amount = amount; rule.type = new_data["type"]
                rule.category = new_data["category"]; rule.frequency = new_data["frequency"]
                rule.day_of_month = new_data["day_of_month"]; rule.day_of_month_2 = new_data.get("day_of_month_2")
                rule.month_of_year = new_data.get("month_of_year"); rule.last_processed_date = None
                rule.save()
                
                self.full_refresh(); self.view.show_notification("Regla recurrente actualizada.", "success")
        except RecurringTransaction.DoesNotExist:
            self.view.show_notification("La regla no fue encontrada.", "error")