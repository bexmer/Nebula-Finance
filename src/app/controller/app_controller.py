from PySide6.QtWidgets import QMessageBox, QTableWidget
from PySide6.QtCore import QDate, Qt, QCoreApplication
from app.model.transaction import Transaction
from app.model.goal import Goal
from app.model.debt import Debt
from app.model.budget_entry import BudgetEntry
from app.model.portfolio_asset import PortfolioAsset
from app.model.trade import Trade
from app.model.recurring_transaction import RecurringTransaction
from app.model.account import Account
from app.model.parameter import Parameter
from app.view.edit_transaction_dialog import EditTransactionDialog
from app.view.edit_goal_debt_dialog import EditGoalDebtDialog
from app.view.edit_budget_entry_dialog import EditBudgetEntryDialog
from app.view.edit_account_dialog import EditAccountDialog
from app.view.edit_recurring_dialog import EditRecurringDialog
from app.view.quick_transaction_dialog import QuickTransactionDialog
from app.view.edit_parameter_dialog import EditParameterDialog

import datetime
from collections import defaultdict
from peewee import JOIN, fn
from dateutil.relativedelta import relativedelta

BUDGET_RULES = {
    "Esenciales": 0.50,
    "Crecimiento": 0.25,
    "Estabilidad": 0.15,
    "Recompensas": 0.10,
}

class AppController:
    def __init__(self, view):
        self.view = view

        # Conexiones de la interfaz
        self.view.dashboard_page.year_filter.currentTextChanged.connect(self.update_dashboard)
        for action in self.view.dashboard_page.month_actions:
            action.triggered.connect(self.update_dashboard)
        self.view.dashboard_page.all_year_action.triggered.connect(self.update_dashboard)
        self.view.analysis_page.year_selector.currentTextChanged.connect(self.update_analysis_view)
        
        # Conexiones para cada pestaña de configuración
        self.view.settings_page.transaction_types_tab.add_button.clicked.connect(
            lambda: self.add_parameter('Tipo de Transacción')
        )
        self.view.settings_page.account_types_tab.add_button.clicked.connect(
            lambda: self.add_parameter('Tipo de Cuenta')
        )
        self.view.settings_page.categories_tab.add_button.clicked.connect(
            lambda: self.add_parameter('Categoría')
        )

        self.view.settings_page.transaction_types_tab.delete_button.clicked.connect(self.delete_parameter)
        self.view.settings_page.account_types_tab.delete_button.clicked.connect(self.delete_parameter)
        self.view.settings_page.categories_tab.delete_button.clicked.connect(self.delete_parameter)


    def full_refresh(self):
        self.process_recurring_transactions()
        self.load_parameters_to_views()
        self.load_accounts()
        self.load_transactions()
        self.update_dashboard()
        self.load_goals()
        self.load_debts()
        self.update_analysis_view()
        self.load_budget_entries()
        self.load_portfolio()
        self.load_parameters()

    def load_parameters(self):
        transaction_types = list(Parameter.select().where(Parameter.group == 'Tipo de Transacción'))
        account_types = list(Parameter.select().where(Parameter.group == 'Tipo de Cuenta'))
        categories = list(Parameter.select().where(Parameter.group == 'Categoría'))

        self.view.settings_page.display_transaction_types(transaction_types)
        self.view.settings_page.display_account_types(account_types)
        self.view.settings_page.display_categories(categories)

    def add_parameter(self, group_name):
        current_tab = self.view.settings_page.tabs.currentWidget()
        data = self.view.settings_page.get_form_data(current_tab)
        
        if not data["value"]:
            self.view.show_notification("El valor es obligatorio.", "error")
            return

        Parameter.create(
            value=data["value"], 
            group=group_name, 
            budget_rule=data.get('budget_rule')
        )
        
        self.view.settings_page.clear_form(current_tab)
        self.full_refresh()
        self.view.show_notification("Parámetro añadido con éxito.", "success")

    def delete_parameter(self):
        parameter_id = self.view.settings_page.get_selected_parameter_id()
        if not parameter_id: return
        
        param_to_delete = Parameter.get_by_id(parameter_id)
        if not param_to_delete.is_deletable:
            self.view.show_notification("Este es un parámetro esencial y no se puede eliminar.", "error")
            return

        if QMessageBox.question(self.view, "Confirmar", "¿Eliminar este parámetro?") == QMessageBox.StandardButton.Yes:
            param_to_delete.delete_instance()
            self.full_refresh()
            self.view.show_notification("Parámetro eliminado.", "success")
    
    def _cascade_parameter_update(self, group, old_value, new_value):
        """
        Actualiza todas las tablas que usan un parámetro cuando este cambia.
        """
        if group == 'Categoría':
            Transaction.update(category=new_value).where(Transaction.category == old_value).execute()
            BudgetEntry.update(category=new_value).where(BudgetEntry.category == old_value).execute()
            RecurringTransaction.update(category=new_value).where(RecurringTransaction.category == old_value).execute()
        elif group == 'Tipo de Cuenta':
            Account.update(account_type=new_value).where(Account.account_type == old_value).execute()
        elif group == 'Tipo de Transacción':
            Transaction.update(type=new_value).where(Transaction.type == old_value).execute()
            BudgetEntry.update(type=new_value).where(BudgetEntry.type == old_value).execute()
            RecurringTransaction.update(type=new_value).where(RecurringTransaction.type == old_value).execute()

    def edit_parameter_by_row(self, row, column):
        param_id = self.view.settings_page.get_selected_parameter_id()
        if not param_id: return
        
        try:
            param = Parameter.get_by_id(param_id)
            
            param_data = {
                'value': param.value, 
                'group': param.group, 
                'is_deletable': param.is_deletable,
                'budget_rule': param.budget_rule
            }
            dialog = EditParameterDialog(param_data, self.view)
            
            if dialog.exec():
                new_data = dialog.get_data()
                new_value = new_data["value"]
                
                if not new_value:
                    self.view.show_notification("El valor no puede estar vacío.", "error")
                    return
                
                old_value = param.value
                
                if old_value != new_value:
                    self._cascade_parameter_update(param.group, old_value, new_value)
                
                param.value = new_value
                if 'budget_rule' in new_data:
                    param.budget_rule = new_data['budget_rule']
                param.save()
                
                self.full_refresh()
                self.view.show_notification("Parámetro y registros asociados actualizados.", "success")

        except Parameter.DoesNotExist:
            self.view.show_notification("El parámetro no fue encontrado.", "error")

    def load_parameters_to_views(self):
        categories = [p.value for p in Parameter.select().where(Parameter.group == 'Categoría')]
        transaction_types = [p.value for p in Parameter.select().where(Parameter.group == 'Tipo de Transacción')]
        account_types = [p.value for p in Parameter.select().where(Parameter.group == 'Tipo de Cuenta')]

        # --- INICIO DE LA CORRECCIÓN ---
        # Unificar los tipos de transacción en la vista de presupuesto
        budget_transaction_types = [p.value for p in Parameter.select().where(Parameter.group == 'Tipo de Transacción') if p.value.startswith('Ingreso') or p.value.startswith('Gasto')]
        
        self.view.budget_page.type_input.clear()
        self.view.budget_page.type_input.addItems(budget_transaction_types)
        # --- FIN DE LA CORRECCIÓN ---

        # Actualizar vista de Transacciones
        self.view.transactions_page.category_input.clear()
        self.view.transactions_page.category_input.addItems(categories)
        self.view.transactions_page.type_input.clear()
        self.view.transactions_page.type_input.addItems(transaction_types)
        
        self.view.transactions_page.category_filter.clear()
        self.view.transactions_page.category_filter.addItem("Todas las Categorías")
        self.view.transactions_page.category_filter.addItems(sorted(categories))

        self.view.transactions_page.type_filter.clear()
        self.view.transactions_page.type_filter.addItem("Todos los Tipos")
        self.view.transactions_page.type_filter.addItems(transaction_types)

        # Actualizar vista de Presupuesto
        self.view.budget_page.category_input.clear()
        self.view.budget_page.category_input.addItems(categories)

        # Actualizar vista de Cuentas
        self.view.accounts_page.type_input.clear()
        self.view.accounts_page.type_input.addItems(account_types)

    def show_quick_transaction_dialog(self):
        accounts = list(Account.select())
        if not accounts:
            self.view.show_notification("Para un gasto rápido, primero debes crear una cuenta.", "error")
            return
        
        categories = [p.value for p in Parameter.select().where(Parameter.group == 'Categoría')]
        
        dialog = QuickTransactionDialog(accounts, categories, self.view)
        if dialog.exec():
            data = dialog.get_data()
            self.add_quick_transaction(data)

    def add_account(self):
        data = self.view.accounts_page.get_form_data()
        if not data["name"] or not data["initial_balance"]:
            self.view.show_notification("Nombre y Saldo Inicial son obligatorios.", "error")
            return
        try:
            balance = float(data["initial_balance"])
        except ValueError:
            self.view.show_notification("El saldo debe ser un número válido.", "error")
            return
        Account.create(
            name=data["name"],
            account_type=data["account_type"],
            initial_balance=balance,
            current_balance=balance,
        )
        self.view.accounts_page.clear_form()
        self.full_refresh()
        self.view.show_notification("Cuenta añadida con éxito.", "success")

    def delete_account(self):
        account_id = self.view.accounts_page.get_selected_account_id()
        if account_id:
            if Transaction.select().where(Transaction.account == account_id).count() > 0:
                self.view.show_notification(
                    "No se puede eliminar una cuenta con transacciones asociadas.", "error"
                )
                return
            if (
                QMessageBox.question(self.view, "Confirmar", "¿Eliminar esta cuenta?")
                == QMessageBox.StandardButton.Yes
            ):
                Account.get_by_id(account_id).delete_instance()
                self.full_refresh()
                self.view.show_notification("Cuenta eliminada.", "success")

    def load_accounts(self):
        accounts = list(Account.select())
        self.view.accounts_page.display_accounts(accounts)
        self.view.transactions_page.update_accounts_list(accounts)

    def edit_account_by_row(self, row, column):
        account_id = self.view.accounts_page.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not account_id:
            return
        try:
            account = Account.get_by_id(account_id)
            account_data = {"name": account.name, "account_type": account.account_type}
            dialog = EditAccountDialog(account_data, self.view)
            if dialog.exec():
                new_data = dialog.get_data()
                account.name = new_data["name"]
                account.account_type = new_data["account_type"]
                account.save()
                self.full_refresh()
                self.view.show_notification("Cuenta actualizada.", "success")
        except Account.DoesNotExist:
            self.view.show_notification("La cuenta no fue encontrada.", "error")

    def process_recurring_transactions(self) -> bool:
        today = datetime.date.today()
        rules_updated = False
        first_account = Account.select().first()
        if not first_account:
            return False

        for rule in RecurringTransaction.select():
            start_from = rule.last_processed_date or rule.start_date
            next_due_dates = []

            if rule.frequency == "Anual":
                try:
                    next_due = datetime.date(start_from.year, rule.month_of_year, rule.day_of_month)
                    if next_due <= start_from:
                        next_due = datetime.date(
                            start_from.year + 1, rule.month_of_year, rule.day_of_month
                        )
                    if next_due <= today:
                        next_due_dates.append(next_due)
                except ValueError:
                    pass

            elif rule.frequency == "Mensual":
                try:
                    next_due = start_from.replace(day=rule.day_of_month)
                    if next_due <= start_from:
                        next_due += relativedelta(months=1)
                    while next_due <= today:
                        next_due_dates.append(next_due)
                        next_due += relativedelta(months=1)
                except ValueError:
                    pass

            elif rule.frequency == "Quincenal":
                try:
                    next_due1 = start_from.replace(day=rule.day_of_month)
                    if next_due1 <= start_from:
                        next_due1 += relativedelta(months=1)
                    while next_due1 <= today:
                        next_due_dates.append(next_due1)
                        next_due1 += relativedelta(months=1)
                except ValueError:
                    pass
                try:
                    next_due2 = start_from.replace(day=rule.day_of_month_2)
                    if next_due2 <= start_from:
                        next_due2 += relativedelta(months=1)
                    while next_due2 <= today:
                        next_due_dates.append(next_due2)
                        next_due2 += relativedelta(months=1)
                except (ValueError, TypeError):
                    pass

            for due_date in sorted(list(set(next_due_dates))):
                if not rule.last_processed_date or due_date > rule.last_processed_date:
                    Transaction.create(
                        date=due_date, description=rule.description, amount=rule.amount,
                        type=rule.type, category=rule.category, account=first_account,
                    )
                    if rule.type == "Ingreso":
                        first_account.current_balance += rule.amount
                    else:
                        first_account.current_balance -= rule.amount
                    first_account.save()
                    rule.last_processed_date = due_date
                    rules_updated = True

            rule.save()

        if rules_updated:
            self.view.show_notification("Transacciones recurrentes generadas.", "success")
        return rules_updated

    def load_recurring_rules(self):
        rules = RecurringTransaction.select().order_by(RecurringTransaction.day_of_month)
        next_dates = {}
        for rule in rules:
            last_run = rule.last_processed_date or rule.start_date
            try:
                if rule.frequency == "Anual":
                    next_due = last_run.replace(month=rule.month_of_year, day=rule.day_of_month)
                    if next_due <= last_run:
                        next_due = next_due.replace(year=last_run.year + 1)
                else:
                    next_due = last_run.replace(day=rule.day_of_month)
                    if next_due <= last_run:
                        next_due += relativedelta(months=1)
                next_dates[rule.id] = next_due.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                next_dates[rule.id] = "Fecha Inválida"
        self.view.transactions_page.display_recurring_rules(rules, next_dates)

    def add_trade(self):
        data = self.view.portfolio_page.get_trade_form_data()
        if not all([data["symbol"], data["asset_type"], data["quantity"], data["price"]]):
            self.view.show_notification("Todos los campos son obligatorios.", "error")
            return
        try:
            quantity = float(data["quantity"])
            price = float(data["price"])
        except ValueError:
            self.view.show_notification("Cantidad y Precio deben ser números válidos.", "error")
            return

        asset, created = PortfolioAsset.get_or_create(
            symbol=data["symbol"].upper(), defaults={"asset_type": data["asset_type"]}
        )
        if data["operation"] == "Compra":
            new_total_quantity = asset.total_quantity + quantity
            new_cost = (asset.total_quantity * asset.avg_cost_price) + (quantity * price)
            asset.avg_cost_price = new_cost / new_total_quantity if new_total_quantity > 0 else 0
            asset.total_quantity = new_total_quantity
        else:
            if quantity > asset.total_quantity:
                self.view.show_notification(
                    "No puedes vender más activos de los que posees.", "error"
                )
                return
            asset.total_quantity -= quantity

        Trade.create(
            asset=asset, trade_type=data["operation"], quantity=quantity,
            price_per_unit=price, date=data["date"],
        )
        asset.current_price = price
        asset.save()
        self.view.show_notification("Operación registrada con éxito.", "success")
        self.view.portfolio_page.clear_trade_form()
        self.load_portfolio()

    def load_portfolio(self):
        assets = list(PortfolioAsset.select().where(PortfolioAsset.total_quantity > 0))
        self.view.portfolio_page.display_portfolio(assets)
        self.view.portfolio_page.display_simple_portfolio(assets)
        sell_trades = Trade.select().where(Trade.trade_type == "Venta").order_by(Trade.date.desc())
        self.view.portfolio_page.display_history(sell_trades)

    def add_transaction(self):
        data = self.view.transactions_page.get_form_data()

        if data["is_recurring"]:
            if not data["description"] or not data["amount"]:
                self.view.show_notification("Descripción y Monto son obligatorios.", "error")
                return
            try:
                amount = float(data["amount"])
            except ValueError:
                self.view.show_notification("El monto debe ser un número válido.", "error")
                return

            RecurringTransaction.create(
                description=data["description"], amount=amount, type=data["type"],
                category=data["category"], frequency=data["frequency"],
                month_of_year=data.get("month_of_year"), day_of_month=data["day_of_month"],
                day_of_month_2=data.get("day_of_month_2"), start_date=data["date"],
            )
            self.view.show_notification("Regla de transacción recurrente añadida.", "success")
        else:
            if not data["account_id"]:
                self.view.show_notification("Debe seleccionar una cuenta.", "error")
                return
            if not data["description"] or not data["amount"]:
                self.view.show_notification("Descripción y Monto son obligatorios.", "error")
                return
            try:
                amount = float(data["amount"])
            except ValueError:
                self.view.show_notification("El monto debe ser un número válido.", "error")
                return

            try:
                account = Account.get_by_id(data["account_id"])
                if data["type"] == "Ingreso":
                    account.current_balance += amount
                else:
                    account.current_balance -= amount
                account.save()
            except Account.DoesNotExist:
                self.view.show_notification("La cuenta seleccionada no es válida.", "error")
                return

            goal_id, debt_id = data.get("goal_id"), data.get("debt_id")
            
            if data["type"] == "Ahorro Meta" and goal_id:
                try:
                    goal = Goal.get_by_id(goal_id)
                    goal.current_amount += amount
                    goal.save()
                except Goal.DoesNotExist: pass
            elif data["type"] == "Pago Deuda" and debt_id:
                try:
                    debt = Debt.get_by_id(debt_id)
                    debt.current_balance -= amount
                    debt.save()
                except Debt.DoesNotExist: pass

            Transaction.create(
                date=data["date"], description=data["description"], amount=amount,
                type=data["type"], category=data["category"], goal=goal_id,
                debt=debt_id, account=data["account_id"],
            )
            self.view.show_notification("¡Transacción añadida!", "success")

        self.view.transactions_page.clear_form()
        self.full_refresh()

    def delete_transaction(self):
        selected_id = self.view.transactions_page.get_selected_transaction_id()
        current_tab = self.view.transactions_page.tabs.currentIndex()

        if current_tab == 3:
            if selected_id and QMessageBox.question(
                self.view, "Confirmar", "¿Eliminar esta regla recurrente?"
            ) == QMessageBox.StandardButton.Yes:
                RecurringTransaction.get_by_id(selected_id).delete_instance()
                self.full_refresh()
                self.view.show_notification("Regla eliminada.", "success")
        else:
            if selected_id and QMessageBox.question(
                self.view, "Confirmar", "¿Eliminar transacción?"
            ) == QMessageBox.StandardButton.Yes:
                try:
                    transaction = Transaction.get_by_id(selected_id)
                    account = Account.get_by_id(transaction.account_id)
                    if transaction.type == "Ingreso":
                        account.current_balance -= transaction.amount
                    else:
                        account.current_balance += transaction.amount
                    account.save()

                    if transaction.goal:
                        transaction.goal.current_amount -= transaction.amount
                        transaction.goal.save()
                    if transaction.debt:
                        transaction.debt.current_balance += transaction.amount
                        transaction.debt.save()

                    transaction.delete_instance()
                    self.full_refresh()
                    self.view.show_notification("Transacción eliminada.", "success")
                except (Transaction.DoesNotExist, Account.DoesNotExist):
                    self.view.show_notification("Error al eliminar.", "error")

    def update_transaction(self, transaction, data):
        try:
            amount = float(data["amount"])
        except ValueError:
            self.view.show_notification("El monto debe ser un número válido.", "error")
            return

        try:
            old_account = Account.get_by_id(transaction.account_id)
            if transaction.type == "Ingreso":
                old_account.current_balance -= transaction.amount
            else:
                old_account.current_balance += transaction.amount
            old_account.save()
        except Account.DoesNotExist: pass

        try:
            new_account = Account.get_by_id(data["account_id"])
            if data["type"] == "Ingreso":
                new_account.current_balance += amount
            else:
                new_account.current_balance -= amount
            new_account.save()
        except Account.DoesNotExist: pass

        if transaction.goal_id:
            try:
                old_goal = Goal.get_by_id(transaction.goal_id)
                old_goal.current_amount -= transaction.amount
                old_goal.save()
            except Goal.DoesNotExist: pass
        if transaction.debt_id:
            try:
                old_debt = Debt.get_by_id(transaction.debt_id)
                old_debt.current_balance += transaction.amount
                old_debt.save()
            except Debt.DoesNotExist: pass

        transaction.date, transaction.description, transaction.amount = data["date"], data["description"], amount
        transaction.type, transaction.category = data["type"], data["category"]
        transaction.goal, transaction.debt, transaction.account = data["goal_id"], data["debt_id"], data["account_id"]

        if data["goal_id"]:
            try:
                new_goal = Goal.get_by_id(data["goal_id"])
                new_goal.current_amount += amount
                new_goal.save()
            except Goal.DoesNotExist: pass
        if data["debt_id"]:
            try:
                new_debt = Debt.get_by_id(data["debt_id"])
                new_debt.current_balance -= amount
                new_debt.save()
            except Debt.DoesNotExist: pass

        transaction.save()
        self.full_refresh()
        self.view.show_notification("Transacción actualizada.", "success")

    def edit_transaction_by_row(self, row, column, table_widget):
        if not table_widget: return
        item = table_widget.item(row, 0)
        if not item: return
        transaction_id = item.data(Qt.ItemDataRole.UserRole)
        if not transaction_id: return
        try:
            transaction = Transaction.get_by_id(transaction_id)
            t_data = {
                "id": transaction.id, "date": transaction.date.strftime("%Y-%m-%d"),
                "description": transaction.description, "amount": transaction.amount,
                "type": transaction.type, "category": transaction.category,
                "goal_id": transaction.goal_id, "debt_id": transaction.debt_id,
                "account_id": transaction.account_id,
            }
            goals, debts, accounts = Goal.select(), Debt.select(), Account.select()
            dialog = EditTransactionDialog(t_data, goals, debts, accounts, self.view)
            if dialog.exec():
                self.update_transaction(transaction, dialog.get_data())
        except Transaction.DoesNotExist:
            self.view.show_notification("Transacción no encontrada.", "error")

    def load_transactions(self):
        self.filter_transactions()
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

        query = Transaction.select().join(Account, on=(Transaction.account == Account.id))

        if tab_index == 1: query = query.join(Goal).where(Transaction.goal.is_null(False))
        elif tab_index == 2: query = query.join(Debt).where(Transaction.debt.is_null(False))

        start_date, end_date = filters["start_date"], filters["end_date"]
        query = query.where((Transaction.date >= start_date) & (Transaction.date <= end_date))

        if filters["search_text"]: query = query.where(Transaction.description.contains(filters["search_text"]))
        if filters["type"] != "Todos los Tipos": query = query.where(Transaction.type == filters["type"])
        if filters["category"] != "Todas las Categorías": query = query.where(Transaction.category == filters["category"])

        sort_field = Transaction.date if filters["sort_by"] == "Fecha" else Transaction.amount
        query = query.order_by(sort_field.desc() if filters["sort_order"] == "Descendente" else sort_field.asc())

        transactions = list(query)

        if tab_index == 0: self.view.transactions_page.display_all_transactions(transactions)
        elif tab_index == 1: self.view.transactions_page.display_goal_transactions(transactions)
        elif tab_index == 2: self.view.transactions_page.display_debt_transactions(transactions)

    def add_budget_entry(self):
        data = self.view.budget_page.get_form_data()
        if not data["description"] or not data["budgeted_amount"]:
            self.view.show_notification("Descripción y Monto son obligatorios.", "error")
            return
        try:
            amount = float(data["budgeted_amount"])
        except (ValueError, TypeError):
            self.view.show_notification("El monto debe ser un número válido.", "error")
            return
        BudgetEntry.create(
            description=data["description"], category=data["category"],
            type=data["type"], budgeted_amount=amount,
        )
        self.view.budget_page.clear_form()
        self.full_refresh()
        self.view.show_notification("Entrada de presupuesto añadida.", "success")

    def delete_budget_entry(self):
        entry_id = self.view.budget_page.get_selected_entry_id()
        if entry_id and QMessageBox.question(self.view, "Confirmar", "¿Eliminar entrada?") == QMessageBox.StandardButton.Yes:
            BudgetEntry.get_by_id(entry_id).delete_instance()
            self.full_refresh()
            self.view.show_notification("Entrada eliminada.", "success")

    def load_budget_entries(self):
        entries = BudgetEntry.select().order_by(BudgetEntry.type, BudgetEntry.description)
        self.view.budget_page.display_budget_entries(entries)

    def edit_budget_entry_by_row(self, row, column):
        entry_id = self.view.budget_page.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not entry_id: return
        try:
            entry = BudgetEntry.get_by_id(entry_id)
            entry_data = {
                "description": entry.description, "budgeted_amount": entry.budgeted_amount,
                "type": entry.type, "category": entry.category,
            }
            dialog = EditBudgetEntryDialog(entry_data, self.view)
            if dialog.exec():
                self.update_budget_entry(entry, dialog.get_data())
        except BudgetEntry.DoesNotExist:
            self.view.show_notification("Entrada no encontrada.", "error")

    def update_budget_entry(self, entry, data):
        if not data["description"] or not data["budgeted_amount"]:
            self.view.show_notification("Todos los campos son obligatorios.", "error")
            return
        try:
            amount = float(data["budgeted_amount"])
        except (ValueError, TypeError):
            self.view.show_notification("El monto debe ser un número válido.", "error")
            return
        entry.description, entry.category, entry.type = data["description"], data["category"], data["type"]
        entry.budgeted_amount = amount
        entry.save()
        self.full_refresh()
        self.view.show_notification("Entrada de presupuesto actualizada.", "success")

    def update_dashboard(self):
        filters = self.view.dashboard_page.get_selected_filters()
        year, months = filters["year"], filters["months"]

        trans, total_income, total_expense = self._update_kpis(year, months)
        self._update_net_worth_chart()

        # --- INICIO DE LA CORRECCIÓN ---
        # Ahora se utilizan los tipos de transacción dinámicos
        budgeted_income = sum(b.budgeted_amount for b in BudgetEntry.select().where(BudgetEntry.type.startswith("Ingreso")))
        budgeted_expense = sum(b.budgeted_amount for b in BudgetEntry.select().where(BudgetEntry.type.startswith("Gasto")))
        # --- FIN DE LA CORRECCIÓN ---
        
        self.view.dashboard_page.update_budget_vs_real_cards(
            income_data={"budgeted_amount": budgeted_income, "real_amount": total_income},
            expense_data={"budgeted_amount": budgeted_expense, "real_amount": total_expense},
        )
        self._update_dashboard_widgets()

        self.view.dashboard_page.update_accounts_card(list(Account.select()))

        if trans:
            self._update_expense_dist_chart(trans)
            self._update_budget_rule_chart(trans, total_income)
            
            expense_by_type = defaultdict(float)
            for t in trans:
                if t.type != "Ingreso":
                    expense_by_type[t.type] += t.amount

            if expense_by_type:
                sorted_expense_type = sorted(expense_by_type.items(), key=lambda i: i[1], reverse=True)
                self.view.dashboard_page.update_expense_type_chart([i[0] for i in sorted_expense_type], [i[1] for i in sorted_expense_type])
            else:
                self.view.dashboard_page.clear_expense_type_chart()
        else:
            self.view.dashboard_page.clear_expense_dist_chart()
            self.view.dashboard_page.clear_budget_rule_chart()
            self.view.dashboard_page.clear_expense_type_chart()
            
        QCoreApplication.processEvents()

    def _update_dashboard_widgets(self):
        today = datetime.date.today()
        upcoming_payments = []
        for rule in RecurringTransaction.select().order_by(RecurringTransaction.day_of_month):
            last_run = rule.last_processed_date or rule.start_date
            try:
                next_due = last_run.replace(day=rule.day_of_month)
                if next_due <= today:
                    next_due += relativedelta(months=1)
                upcoming_payments.append({"date": next_due, "description": rule.description, "amount": rule.amount})
            except (ValueError, TypeError): pass
        
        sorted_payments = sorted(upcoming_payments, key=lambda p: p["date"])
        for p in sorted_payments: p["date"] = p["date"].strftime("%Y-%m-%d")
        self.view.dashboard_page.update_upcoming_payments(sorted_payments[:5])

        goals_data = [
            {"name": g.name, "current": g.current_amount, "target": g.target_amount}
            for g in Goal.select().where(Goal.current_amount < Goal.target_amount).order_by((Goal.current_amount / Goal.target_amount).desc()).limit(3)
        ]
        self.view.dashboard_page.update_main_goals(goals_data)

    def _update_kpis(self, year, months):
        if not months:
            self.view.dashboard_page.update_kpis(0, 0, 0)
            return [], 0, 0

        start = datetime.date(year, min(months), 1)
        last = max(months)
        end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1) if last == 12 else datetime.date(year, last + 1, 1) - datetime.timedelta(days=1)
        
        current = list(Transaction.select().where((Transaction.date >= start) & (Transaction.date <= end)))
        income = sum(t.amount for t in current if t.type == "Ingreso")
        expense = sum(t.amount for t in current if t.type != "Ingreso")
        net = income - expense

        income_comp, expense_comp = None, None
        if len(months) == 1:
            prev_end = start - datetime.timedelta(days=1)
            prev_start = prev_end.replace(day=1)
            prev = Transaction.select().where((Transaction.date >= prev_start) & (Transaction.date <= prev_end))
            prev_income = sum(t.amount for t in prev if t.type == "Ingreso")
            prev_expense = sum(t.amount for t in prev if t.type != "Ingreso")
            
            get_change = lambda c, p: ((c - p) / p) * 100 if p > 0 else (100.0 if c > 0 else 0.0)
            income_comp = get_change(income, prev_income)
            expense_comp = get_change(expense, prev_expense)

        self.view.dashboard_page.update_kpis(income, expense, net, income_comp, expense_comp)
        return current, income, expense

    def _update_budget_rule_chart(self, transactions, total_income):
        if total_income == 0: total_income = 1

        spending_by_rule = defaultdict(float)
        
        # --- INICIO DE LA CORRECCIÓN ---
        # Mapeo dinámico de tipo de transacción a regla de presupuesto
        type_to_rule_map = {p.value: p.budget_rule for p in Parameter.select().where(Parameter.group == 'Tipo de Transacción')}
        
        for t in transactions:
            if t.type in type_to_rule_map and type_to_rule_map[t.type]:
                spending_by_rule[type_to_rule_map[t.type]] += t.amount
        # --- FIN DE LA CORRECCIÓN ---

        budget_data = []
        for name, ideal in BUDGET_RULES.items():
            actual = spending_by_rule.get(name, 0.0)
            percent_of_income = (actual / total_income) * 100 if total_income > 1 else 0
            
            state = "good"
            # --- INICIO DE LA CORRECCIÓN ---
            # El estado "critical" ahora depende solo del porcentaje de la regla
            if percent_of_income > (ideal * 100) + 10:
                state = "critical"
            # --- FIN DE LA CORRECCIÓN ---
            elif percent_of_income > ideal * 100:
                state = "warning"
            
            budget_data.append({
                "name": name, "ideal_percent": ideal * 100, "actual_percent": percent_of_income,
                "actual_amount": actual, "state": state, "is_overdrawn": False,  # Ya no se usa
            })
        self.view.dashboard_page.update_budget_rule_chart(budget_data)


    def _update_net_worth_chart(self):
        today = datetime.date.today()
        dates, values = [], []
        for i in range(12, -1, -1):
            month_end = (today - datetime.timedelta(days=i * 30)).replace(day=1)
            next_m = month_end.replace(day=28) + datetime.timedelta(days=4)
            month_end = next_m - datetime.timedelta(days=next_m.day)

            total_balance = Account.select(fn.SUM(Account.initial_balance)).scalar() or 0.0
            for t in Transaction.select().where(Transaction.date <= month_end):
                total_balance += t.amount if t.type == "Ingreso" else -t.amount

            liabilities = sum(d.total_amount - sum(t.amount for t in Transaction.select().where((Transaction.debt == d) & (Transaction.date <= month_end))) for d in Debt.select())
            dates.append(int(month_end.strftime("%Y%m%d")))
            values.append(total_balance - liabilities)

        self.view.dashboard_page.update_net_worth_chart(dates, values)

    def _update_expense_dist_chart(self, transactions):
        expenses = defaultdict(float)
        for t in transactions:
            if t.type.startswith("Gasto"):
                expenses[t.category] += t.amount
        sorted_exp = sorted(expenses.items(), key=lambda i: i[1], reverse=True)
        self.view.dashboard_page.update_expense_dist_chart([i[0] for i in sorted_exp], [i[1] for i in sorted_exp])

    def add_goal(self):
        data = self.view.goals_page.get_goal_form_data()
        if not data["name"] or not data["target_amount"]:
            self.view.show_notification("Todos los campos son obligatorios.", "error")
            return
        try:
            target = float(data["target_amount"])
        except (ValueError, TypeError):
            self.view.show_notification("El monto debe ser un número válido.", "error")
            return
        Goal.create(name=data["name"], target_amount=target, current_amount=0)
        self.view.goals_page.clear_goal_form()
        self.full_refresh()
        self.view.show_notification("¡Meta añadida!", "success")

    def add_debt(self):
        data = self.view.goals_page.get_debt_form_data()
        if not data["name"] or not data["total_amount"] or not data["minimum_payment"]:
            self.view.show_notification("Todos los campos son obligatorios.", "error")
            return
        try:
            total, min_pay = float(data["total_amount"]), float(data["minimum_payment"])
        except (ValueError, TypeError):
            self.view.show_notification("Los montos deben ser números válidos.", "error")
            return
        Debt.create(name=data["name"], total_amount=total, minimum_payment=min_pay, current_balance=total)
        self.view.goals_page.clear_debt_form()
        self.full_refresh()
        self.view.show_notification("¡Deuda añadida!", "success")

    def edit_goal(self, goal_id):
        try:
            goal = Goal.get_by_id(goal_id)
            g_data = {"name": goal.name, "target_amount": goal.target_amount}
            dialog = EditGoalDebtDialog(g_data, "goal", self.view)
            if dialog.exec():
                new_data = dialog.get_data()
                if not new_data["name"] or not new_data["target_amount"]:
                    self.view.show_notification("Todos los campos son obligatorios.", "error")
                    return
                goal.name = new_data["name"]
                goal.target_amount = float(new_data["target_amount"])
                goal.save()
                self.full_refresh()
                self.view.show_notification("Meta actualizada.", "success")
        except (Goal.DoesNotExist, ValueError):
            self.view.show_notification("No se pudo editar la meta.", "error")

    def delete_goal(self, goal_id):
        if QMessageBox.question(self.view, "Confirmar", "¿Eliminar meta?") == QMessageBox.StandardButton.Yes:
            Transaction.update(goal=None).where(Transaction.goal == goal_id).execute()
            Goal.get_by_id(goal_id).delete_instance()
            self.full_refresh()
            self.view.show_notification("Meta eliminada.", "success")

    def edit_debt(self, debt_id):
        try:
            debt = Debt.get_by_id(debt_id)
            d_data = {"name": debt.name, "total_amount": debt.total_amount, "minimum_payment": debt.minimum_payment}
            dialog = EditGoalDebtDialog(d_data, "debt", self.view)
            if dialog.exec():
                new_data = dialog.get_data()
                if not all(new_data.get(k) for k in ["name", "total_amount", "minimum_payment"]):
                    self.view.show_notification("Todos los campos son obligatorios.", "error")
                    return
                debt.name = new_data["name"]
                debt.total_amount = float(new_data["total_amount"])
                debt.minimum_payment = float(new_data["minimum_payment"])
                debt.save()
                self.full_refresh()
                self.view.show_notification("Deuda actualizada.", "success")
        except (Debt.DoesNotExist, ValueError):
            self.view.show_notification("No se pudo editar la deuda.", "error")

    def delete_debt(self, debt_id):
        if QMessageBox.question(self.view, "Confirmar", "¿Eliminar deuda?") == QMessageBox.StandardButton.Yes:
            Transaction.update(debt=None).where(Transaction.debt == debt_id).execute()
            Debt.get_by_id(debt_id).delete_instance()
            self.full_refresh()
            self.view.show_notification("Deuda eliminada.", "success")

    def load_goals(self):
        self.view.goals_page.display_goals(Goal.select())

    def load_debts(self):
        self.view.goals_page.display_debts(Debt.select())

    def update_analysis_view(self):
        total_account_balance = Account.select(fn.SUM(Account.current_balance)).scalar() or 0.0
        portfolio_value = (PortfolioAsset.select(fn.SUM(PortfolioAsset.total_quantity * PortfolioAsset.current_price)).scalar() or 0.0)
        total_assets = total_account_balance + portfolio_value
        total_liabilities = sum(d.current_balance for d in Debt.select())
        self.view.analysis_page.update_net_worth_display(total_assets, total_liabilities, total_assets - total_liabilities)
        year = int(self.view.analysis_page.year_selector.currentText())
        self._generate_and_display_annual_report(year)

    def _generate_and_display_annual_report(self, year):
        start, end = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
        trans = Transaction.select().where((Transaction.date.between(start, end)) & (Transaction.type.startswith("Gasto")))
        data, cats, monthly, grand = defaultdict(lambda: defaultdict(float)), set(), defaultdict(float), 0.0
        for t in trans:
            data[t.category][t.date.month] += t.amount
            cats.add(t.category)
            monthly[t.date.month] += t.amount
            grand += t.amount
        self.view.analysis_page.display_annual_report(data, sorted(list(cats)), year, monthly, grand)

    def add_quick_transaction(self, data):
        if not data["description"] or not data["amount"]:
            self.view.show_notification("Descripción y Monto son obligatorios.", "error")
            return
        try:
            amount = float(data["amount"])
        except ValueError:
            self.view.show_notification("El monto debe ser un número válido.", "error")
            return
        try:
            account = Account.get_by_id(data["account_id"])
            account.current_balance -= amount
            account.save()
        except Account.DoesNotExist:
            self.view.show_notification("La cuenta seleccionada no es válida.", "error")
            return
        Transaction.create(
            date=datetime.date.today(), description=data["description"], amount=amount,
            type="Gasto Variable", category=data["category"], account=data["account_id"],
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
                "day_of_month_2": rule.day_of_month_2, "month_of_year": rule.month_of_year,
            }
            dialog = EditRecurringDialog(rule_data, self.view)
            if dialog.exec():
                new_data = dialog.get_data()
                try: amount = float(new_data["amount"])
                except ValueError:
                    self.view.show_notification("El monto debe ser un número válido.", "error")
                    return

                rule.description, rule.amount, rule.type = new_data["description"], amount, new_data["type"]
                rule.category, rule.frequency, rule.day_of_month = new_data["category"], new_data["frequency"], new_data["day_of_month"]
                rule.day_of_month_2 = new_data.get("day_of_month_2")
                rule.month_of_year = new_data.get("month_of_year")
                rule.last_processed_date = None
                rule.save()

                self.full_refresh()
                self.view.show_notification("Regla recurrente actualizada.", "success")
        except RecurringTransaction.DoesNotExist:
            self.view.show_notification("La regla no fue encontrada.", "error")