from PySide6.QtWidgets import QMessageBox, QTableWidget, QDialog
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
from app.model.budget_rule import BudgetRule
from app.view.edit_transaction_dialog import EditTransactionDialog
from app.view.edit_goal_debt_dialog import EditGoalDebtDialog
from app.view.edit_budget_entry_dialog import EditBudgetEntryDialog
from app.view.edit_account_dialog import EditAccountDialog
from app.view.edit_recurring_dialog import EditRecurringDialog
from app.view.quick_transaction_dialog import QuickTransactionDialog
from app.view.edit_parameter_dialog import EditParameterDialog
from app.view.edit_budget_rule_dialog import EditBudgetRuleDialog

import datetime
from collections import defaultdict
from peewee import JOIN, fn
from dateutil.relativedelta import relativedelta

class AppController:
    def __init__(self, view):
        self.view = view
        # El constructor ahora está limpio. Todas las conexiones se manejan en main_window.py

    def full_refresh(self):
        """Refresca todos los datos de la aplicación."""
        self.process_recurring_transactions()
        self.load_parameters_to_views()
        self.update_dashboard()
        self.load_goals_and_debts() # Unificamos la llamada a la función correcta
        self.load_accounts()
        self.filter_transactions()

        
    # --- NUEVA LÓGICA DE PAGINACIÓN Y ELIMINACIÓN ---

    def load_paginated_data(self, page=1):
        """Carga los datos para la vista actual con paginación."""
        current_view_name = self.view.get_current_view_name()
        view_widget = getattr(self.view, f"{current_view_name}_page", None)
        
        if not view_widget or not hasattr(view_widget, 'get_pagination_controls'):
            return

        controls = view_widget.get_pagination_controls()
        items_per_page = controls['items_per_page']
        
        query, display_method = None, None

        if current_view_name == 'accounts':
            query = Account.select()
            display_method = view_widget.display_accounts
        elif current_view_name == 'budget':
            query = BudgetEntry.select().order_by(BudgetEntry.type, BudgetEntry.description)
            display_method = view_widget.display_budget_entries
        # Agrega aquí otras vistas como 'portfolio', etc.

        if query and display_method:
            total_items = query.count()
            total_pages = (total_items + items_per_page - 1) // items_per_page
            
            paginated_query = query.paginate(page, items_per_page)
            display_method(list(paginated_query))
            
            view_widget.update_pagination_ui(page, total_pages, total_items)

    def change_page(self, direction):
        """Cambia a la página siguiente o anterior."""
        current_view_name = self.view.get_current_view_name()
        current_page = self.current_pages.get(current_view_name, 1)
        new_page = current_page + direction
        self.load_paginated_data(page=new_page)

    def change_items_per_page(self):
        """Recarga los datos cuando el usuario cambia el número de items por página."""
        self.load_paginated_data(page=1) # Volvemos a la página 1

    def get_current_view_name(self):
        current_index = self.content_stack.currentIndex()
        view_map = {
            0: 'dashboard', 1: 'portfolio', 2: 'accounts', 3: 'budget',
            4: 'transactions', 5: 'goals', 6: 'analysis', 7: 'settings'
        }
        return view_map.get(current_index)
        
    def delete_selected_items(self):
        """Elimina todos los items seleccionados con checkbox en la tabla activa."""
        current_view_name = self.view.get_current_view_name()
        view_widget = getattr(self.view, f"{current_view_name}_page", None)
        
        if not view_widget or not hasattr(view_widget, 'get_checked_ids'):
            return

        ids_to_delete = view_widget.get_checked_ids()
        if not ids_to_delete:
            self.view.show_notification("No hay elementos seleccionados para eliminar.", "error")
            return

        model_map = {
            'accounts': Account,
            'budget': BudgetEntry,
            'transactions': Transaction,
            'portfolio': PortfolioAsset
            # Agrega otros modelos aquí
        }
        model = model_map.get(current_view_name)

        if not model: return
        
        if QMessageBox.question(self.view, "Confirmar", f"¿Estás seguro de que quieres eliminar {len(ids_to_delete)} elementos?") == QMessageBox.StandardButton.Yes:
            # Aquí podrías añadir lógicas complejas (ej. no eliminar cuentas con transacciones)
            query = model.delete().where(model.id.in_(ids_to_delete))
            deleted_rows = query.execute()
            
            self.full_refresh()
            self.view.show_notification(f"{deleted_rows} elementos eliminados.", "success")


    # --- MÉTODOS PARA REGLAS DE PRESUPUESTO ---
    
    def add_budget_rule(self):
        tab = self.view.settings_page.transaction_types_tab
        name = tab.rule_name_input.text()
        percentage = tab.rule_percentage_input.value()

        if not name:
            self.view.show_notification("El nombre de la regla es obligatorio.", "error")
            return
        
        BudgetRule.create(name=name, percentage=percentage)
        tab.rule_name_input.clear()
        tab.rule_percentage_input.setValue(0)
        self.full_refresh()
        self.view.show_notification("Regla de presupuesto añadida.", "success")

    def delete_budget_rule(self):
        tab = self.view.settings_page.transaction_types_tab
        selected_items = tab.rule_table.selectedItems()
        if not selected_items:
            return

        rule_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if rule_id and QMessageBox.question(self.view, "Confirmar", "¿Eliminar esta regla? Los Tipos de Transacción asociados perderán su regla.") == QMessageBox.StandardButton.Yes:
            # Peewee se encargará de poner en NULL las referencias gracias a on_delete='SET NULL'
            BudgetRule.get_by_id(rule_id).delete_instance()
            self.full_refresh()
            self.view.show_notification("Regla eliminada.", "success")

    def edit_budget_rule_by_row(self, row, column):
        tab = self.view.settings_page.transaction_types_tab
        item = tab.rule_table.item(row, 0)
        if not item: return

        rule_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            rule = BudgetRule.get_by_id(rule_id)
            dialog = EditBudgetRuleDialog({'name': rule.name, 'percentage': rule.percentage}, self.view)
            if dialog.exec():
                data = dialog.get_data()
                if not data['name']:
                    self.view.show_notification("El nombre no puede estar vacío.", "error")
                    return
                rule.name = data['name']
                rule.percentage = data['percentage']
                rule.save()
                self.full_refresh()
                self.view.show_notification("Regla actualizada.", "success")
        except BudgetRule.DoesNotExist:
            self.view.show_notification("No se encontró la regla.", "error")
    
    # --- MÉTODOS PARA PARÁMETROS ---

    def load_parameters(self):
        transaction_types = list(Parameter.select().where(Parameter.group == 'Tipo de Transacción'))
        account_types = list(Parameter.select().where(Parameter.group == 'Tipo de Cuenta'))
        categories = list(Parameter.select().where(Parameter.group == 'Categoría'))
        budget_rules = list(BudgetRule.select())

        self.view.settings_page.display_parameters(self.view.settings_page.transaction_types_tab.param_table, transaction_types, True)
        self.view.settings_page.display_parameters(self.view.settings_page.account_types_tab.table, account_types, False)
        self.view.settings_page.display_parameters(self.view.settings_page.categories_tab.table, categories, False)
        self.view.settings_page.display_budget_rules(self.view.settings_page.transaction_types_tab.rule_table, budget_rules)
        
        self.view.settings_page.update_budget_rule_combo(budget_rules)

    def add_parameter(self, group_name):
        if group_name == 'Tipo de Transacción':
            tab = self.view.settings_page.transaction_types_tab
            value = tab.param_value_input.text()
            budget_rule_id = tab.param_budget_rule_input.currentData()
            
            if not value:
                self.view.show_notification("El nombre es obligatorio.", "error")
                return

            Parameter.create(value=value, group=group_name, budget_rule=budget_rule_id)
            tab.param_value_input.clear()

        else:
            current_tab = self.view.settings_page.tabs.currentWidget()
            data = {"value": current_tab.value_input.text()}
            if not data["value"]:
                self.view.show_notification("El valor es obligatorio.", "error")
                return
            Parameter.create(value=data["value"], group=group_name)
            current_tab.value_input.clear()

        self.full_refresh()
        self.view.show_notification(f"{group_name} añadido con éxito.", "success")

    def delete_parameter(self):
        current_tab_widget = self.view.settings_page.tabs.currentWidget()
        
        table_to_check = getattr(current_tab_widget, 'param_table', getattr(current_tab_widget, 'table', None))
        if not table_to_check: return

        selected_items = table_to_check.selectedItems()
        if not selected_items: return
        
        param_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        param_to_delete = Parameter.get_by_id(param_id)
        if not param_to_delete.is_deletable:
            self.view.show_notification("Este es un parámetro esencial y no se puede eliminar.", "error")
            return

        if QMessageBox.question(self.view, "Confirmar", "¿Eliminar este parámetro?") == QMessageBox.StandardButton.Yes:
            param_to_delete.delete_instance()
            self.full_refresh()
            self.view.show_notification("Parámetro eliminado.", "success")

    def edit_parameter_by_row(self, row, column, table_widget):
        param_id = table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not param_id: return
        
        try:
            param = Parameter.get_by_id(param_id)
            
            # --- INICIO DE LA CORRECCIÓN #1: Obtener la regla de forma segura ---
            current_rule_name = None
            try:
                if param.budget_rule:
                    current_rule_name = param.budget_rule.name
            except BudgetRule.DoesNotExist:
                # La regla asociada no existe, la tratamos como nula
                pass
            
            param_data = {
                'value': param.value, 
                'group': param.group, 
                'is_deletable': param.is_deletable,
                'budget_rule': current_rule_name # Usamos el nombre seguro que obtuvimos
            }
            dialog = EditParameterDialog(param_data, self.view)
            
            # --- INICIO DE LA CORRECCIÓN #2: Poblar el ComboBox ---
            if dialog.budget_rule_input:
                all_rules = list(BudgetRule.select())
                dialog.budget_rule_input.clear()
                dialog.budget_rule_input.addItem("(Ninguna)")
                dialog.budget_rule_input.addItems([rule.name for rule in all_rules])
                
                # Establecemos la regla actual del parámetro en el ComboBox
                if current_rule_name:
                    index = dialog.budget_rule_input.findText(current_rule_name)
                    if index >= 0:
                        dialog.budget_rule_input.setCurrentIndex(index)
            # --- FIN DE LAS CORRECCIONES ---

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
                    rule_name = new_data['budget_rule']
                    rule = BudgetRule.get_or_none(BudgetRule.name == rule_name)
                    param.budget_rule = rule
                param.save()
                
                self.full_refresh()
                self.view.show_notification("Parámetro y registros asociados actualizados.", "success")

        except Parameter.DoesNotExist:
            self.view.show_notification("El parámetro no fue encontrado.", "error")

    
    def _cascade_parameter_update(self, group, old_value, new_value):
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

    def load_parameters_to_views(self):
        categories = [p.value for p in Parameter.select().where(Parameter.group == 'Categoría')]
        transaction_types = [p.value for p in Parameter.select().where(Parameter.group == 'Tipo de Transacción')]
        account_types = [p.value for p in Parameter.select().where(Parameter.group == 'Tipo de Cuenta')]
        budget_transaction_types = [p.value for p in Parameter.select().where(Parameter.group == 'Tipo de Transacción') if p.value.startswith('Ingreso') or p.value.startswith('Gasto')]
        
        # Poblar ComboBox de la página de presupuesto
        self.view.budget_page.type_input.clear()
        self.view.budget_page.type_input.addItems(budget_transaction_types)
        self.view.budget_page.category_input.clear()
        self.view.budget_page.category_input.addItems(categories)

        # Poblar ComboBox del formulario de transacciones
        self.view.transactions_page.category_input.clear()
        self.view.transactions_page.category_input.addItems(categories)
        self.view.transactions_page.type_input.clear()
        self.view.transactions_page.type_input.addItems(transaction_types)

        # Usamos el nuevo método para poblar los menús de los botones de filtro
        self.view.transactions_page.update_menu_items(
            self.view.transactions_page.type_filter_button,
            ["Todos los Tipos"] + sorted(transaction_types)
        )
        self.view.transactions_page.update_menu_items(
            self.view.transactions_page.category_filter_button,
            ["Todas las Categorías"] + sorted(categories)
        )

        # Poblar ComboBox de la página de cuentas
        self.view.accounts_page.type_input.clear()
        self.view.accounts_page.type_input.addItems(account_types)

    def _update_cash_flow_chart(self):
        today = datetime.date.today()
        # Mantenemos la consulta de 12 meses para tener todos los datos disponibles
        start_date_query = (today - relativedelta(months=11)).replace(day=1)

        query = (Transaction
                 .select(fn.strftime('%Y-%m', Transaction.date).alias('month'),
                         fn.SUM(Transaction.amount).alias('total'),
                         Transaction.type)
                 .where(Transaction.date >= start_date_query)
                 .group_by(fn.strftime('%Y-%m', Transaction.date), Transaction.type)
                 .order_by(fn.strftime('%Y-%m', Transaction.date)))

        monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0})
        for row in query:
            if row.type == 'Ingreso':
                monthly_data[row.month]['income'] = row.total
            else:
                monthly_data[row.month]['expense'] += row.total

        month_labels, income_data, expense_data = [], [], []
        
        # --- INICIO DE LA CORRECCIÓN ---
        # Iteramos hacia atrás 5 meses desde el mes actual (6 meses en total)
        for i in range(5, -1, -1):
            current_month_date = today - relativedelta(months=i)
            month_key = current_month_date.strftime('%Y-%m')
            
            month_labels.append(current_month_date.strftime('%b-%y'))
            income_data.append(monthly_data[month_key]['income'])
            expense_data.append(monthly_data[month_key]['expense'])
        # --- FIN DE LA CORRECCIÓN ---

        self.view.dashboard_page.update_cash_flow_chart(month_labels, income_data, expense_data)

        
    # --- MÉTODOS DEL DASHBOARD (MODIFICADO) ---
    def _update_budget_rule_chart(self, transactions, total_income):
        if total_income == 0: total_income = 1
        spending_by_rule = defaultdict(float)
        type_to_rule_map = {p.value: p.budget_rule.name 
                            for p in Parameter.select().join(BudgetRule, on=(Parameter.budget_rule == BudgetRule.id)).where(
                                Parameter.group == 'Tipo de Transacción' and Parameter.budget_rule.is_null(False)
                            )}
        for t in transactions:
            if t.type in type_to_rule_map:
                rule_name = type_to_rule_map[t.type]
                spending_by_rule[rule_name] += t.amount
        budget_data = []
        for rule in BudgetRule.select():
            actual = spending_by_rule.get(rule.name, 0.0)
            ideal_percent = rule.percentage
            percent_of_income = (actual / total_income) * 100 if total_income > 1 else 0
            state = "good"
            if percent_of_income > ideal_percent + 10:
                state = "critical"
            elif percent_of_income > ideal_percent:
                state = "warning"
            budget_data.append({
                "name": rule.name, "ideal_percent": ideal_percent, "actual_percent": percent_of_income,
                "actual_amount": actual, "state": state
            })
        self.view.dashboard_page.update_budget_rule_chart(budget_data)

    # --- MÉTODOS DE ANÁLISIS (MODIFICADO) ---
    def _generate_and_display_budget_analysis(self, year, months):
        if not months:
            self.view.analysis_page.display_budget_analysis([])
            return

        start_date = datetime.date(year, min(months), 1)
        last_month_num = max(months)
        next_month_start = (datetime.date(year, last_month_num, 1) + relativedelta(months=1))
        end_date = next_month_start - relativedelta(days=1)
        
        type_to_rule_map = {}
        query = (Parameter
                .select(Parameter, BudgetRule)
                .join(BudgetRule, on=(Parameter.budget_rule == BudgetRule.id), join_type=JOIN.LEFT_OUTER)
                .where(Parameter.group == 'Tipo de Transacción'))
        for p in query:
            try:
                rule = p.budget_rule
                type_to_rule_map[p.value] = rule
            except BudgetRule.DoesNotExist:
                type_to_rule_map[p.value] = None

        rules = list(BudgetRule.select())

        total_real_income = Transaction.select(fn.SUM(Transaction.amount)).where(
            (Transaction.date.between(start_date, end_date)) & 
            (Transaction.type == 'Ingreso')
        ).scalar() or 0.0

        analysis_data = []
        num_months = len(months)
        for rule in rules:
            types_for_rule = [p for p, r in type_to_rule_map.items() if r == rule]
            
            monthly_budget = 0.0
            if types_for_rule:
                monthly_budget = BudgetEntry.select(fn.SUM(BudgetEntry.budgeted_amount)).where(
                    BudgetEntry.type << types_for_rule
                ).scalar() or 0.0
            
            period_budget = monthly_budget * num_months

            period_real = 0.0
            if types_for_rule:
                period_real = Transaction.select(fn.SUM(Transaction.amount)).where(
                    (Transaction.date.between(start_date, end_date)) &
                    (Transaction.type << types_for_rule)
                ).scalar() or 0.0
            
            income_percentage = (period_real / total_real_income) * 100 if total_real_income > 0 else 0

            analysis_data.append({
                'rule': rule.name,
                'budget': period_budget,
                'real': period_real,
                'income_percentage': income_percentage
            })
        
        self.view.analysis_page.display_budget_analysis(analysis_data)
        
    # --- OTROS MÉTODOS (SIN CAMBIOS SIGNIFICATIVOS) ---
    # ... (Aquí irían el resto de los métodos como add_account, delete_transaction, update_dashboard, etc. que no necesitaron cambios drásticos)
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
            if not data["account_id"] or data["account_id"] == -1:
                self.view.show_notification("Debe seleccionar una cuenta válida.", "error")
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

        if tab_index == 3: # Pestaña de Recurrentes
            query = RecurringTransaction.select()
            return
        else:
            query = Transaction.select() # SIEMPRE empezamos la consulta desde Transaction
            
            if tab_index == 1: # Metas
                query = query.join(Goal, on=(Transaction.goal == Goal.id)).where(Transaction.goal.is_null(False))
            elif tab_index == 2: # Deudas
                query = query.join(Debt, on=(Transaction.debt == Debt.id)).where(Transaction.debt.is_null(False))

        start_date, end_date = filters["start_date"], filters["end_date"]
        query = query.where(Transaction.date.between(start_date, end_date))

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
            BudgetEntry.create(
                description=data["description"], category=data["category"],
                type=data["type"], budgeted_amount=amount,
                due_date=data["due_date"] # Guarda la nueva fecha
            )
            self.view.budget_page.clear_form()
            self.load_paginated_data()
            self.view.show_notification("Entrada de presupuesto añadida.", "success")
        except ValueError:
            self.view.show_notification("El monto debe ser un número.", "error")

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
        try:
            table = self.view.budget_page.table
            entry_id = table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            entry = BudgetEntry.get_by_id(entry_id)
            entry_data = {
                'description': entry.description,
                'budgeted_amount': entry.budgeted_amount,
                'type': entry.type,
                'category': entry.category,
                'due_date': entry.due_date # Pasa la fecha al diálogo de edición
            }

            dialog = EditBudgetEntryDialog(entry_data, self.view)
            
            # Poblar los ComboBox del diálogo
            types = [p.value for p in Parameter.select().where(Parameter.group == 'Tipo de Transacción') if p.value.startswith('Ingreso') or p.value.startswith('Gasto')]
            categories = [p.value for p in Parameter.select().where(Parameter.group == 'Categoría')]
            dialog.type_input.addItems(types)
            dialog.category_input.addItems(categories)
            dialog.type_input.setCurrentText(entry.type)
            dialog.category_input.setCurrentText(entry.category)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.get_data()
                entry.description = new_data['description']
                entry.budgeted_amount = float(new_data['budgeted_amount'])
                entry.type = new_data['type']
                entry.category = new_data['category']
                entry.due_date = new_data['due_date'] # Guarda la fecha editada
                entry.save()
                self.load_paginated_data()
                self.view.show_notification("Entrada de presupuesto actualizada.", "success")
        except (BudgetEntry.DoesNotExist, AttributeError):
            self.view.show_notification("No se pudo editar la entrada seleccionada.", "error")


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
        self._update_cash_flow_chart()

        budgeted_income = sum(b.budgeted_amount for b in BudgetEntry.select().where(BudgetEntry.type.startswith("Ingreso")))
        budgeted_expense = sum(b.budgeted_amount for b in BudgetEntry.select().where(BudgetEntry.type.startswith("Gasto")))
        self.view.dashboard_page.update_budget_vs_real_cards(
            income_data={"budgeted_amount": budgeted_income, "real_amount": total_income},
            expense_data={"budgeted_amount": budgeted_expense, "real_amount": total_expense},
        )
        self._update_dashboard_widgets()
        self.view.dashboard_page.update_accounts_card(list(Account.select()))
        
        if trans:
            self._update_expense_dist_chart(trans)
            self._update_budget_rule_chart(trans, total_income)
            
            # --- INICIO DEL CÓDIGO RESTAURADO ---
            # Esta es la lógica que se había perdido para el gráfico de dona
            expense_by_type = defaultdict(float)
            for t in trans:
                if t.type != "Ingreso":
                    expense_by_type[t.type] += t.amount

            if expense_by_type:
                sorted_expense_type = sorted(expense_by_type.items(), key=lambda i: i[1], reverse=True)
                self.view.dashboard_page.update_expense_type_chart([i[0] for i in sorted_expense_type], [i[1] for i in sorted_expense_type])
            else:
                self.view.dashboard_page.clear_expense_type_chart()
            # --- FIN DEL CÓDIGO RESTAURADO ---
        else:
            self.view.dashboard_page.clear_expense_dist_chart()
            self.view.dashboard_page.clear_budget_rule_chart()
            self.view.dashboard_page.clear_expense_type_chart() # También limpiar aquí
        
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
        start = datetime.date(year, min(months), 1) if months else datetime.date(year, 1, 1)
        if months:
            last_month = max(months)
            try:
                # Intenta crear la fecha del mes siguiente
                next_month_start = (start.replace(month=last_month) + relativedelta(months=1))
                end = next_month_start - relativedelta(days=1)
            except ValueError:
                # Si el mes siguiente no existe (ej. Febrero 30), maneja la excepción
                end = start.replace(month=last_month, day=28) # Asume el día 28 como seguro
                end = (end + relativedelta(days=4)) # Se va a Marzo
                end = end - relativedelta(days=end.day) # Regresa al último día de Febrero
        else:
            end = datetime.date(year, 12, 31)
            
        current = list(Transaction.select().where((Transaction.date >= start) & (Transaction.date <= end)))
        income = sum(t.amount for t in current if t.type == "Ingreso")
        expense = sum(t.amount for t in current if t.type != "Ingreso")
        net = income - expense

        # Placeholder for comparison logic
        income_comp, expense_comp = None, None
        
        self.view.dashboard_page.update_kpis(income, expense, net, income_comp, expense_comp)
        return current, income, expense

    def _update_net_worth_chart(self):
        today = datetime.date.today()
        dates, values = [], []
        for i in range(12, -1, -1):
            month_end = (today - relativedelta(days=i * 30)).replace(day=1)
            next_m = month_end.replace(day=28) + datetime.timedelta(days=4)
            month_end = next_m - datetime.timedelta(days=next_m.day)
            
            if month_end > today:
                month_end = today

            total_balance = Account.select(fn.SUM(Account.initial_balance)).scalar() or 0.0
            for t in Transaction.select().where(Transaction.date <= month_end):
                if t.type == "Ingreso":
                    total_balance += t.amount
                else:
                    total_balance -= t.amount
            
            liabilities = sum(d.total_amount - sum(t.amount for t in Transaction.select().where((Transaction.debt == d) & (Transaction.date <= month_end))) for d in Debt.select())
            dates.append(int(month_end.strftime("%Y%m%d")))
            values.append(total_balance - liabilities)
            
        self.view.dashboard_page.update_net_worth_chart(dates, values)

    def _update_expense_dist_chart(self, transactions):
        expenses = defaultdict(float)
        for t in transactions:
            if t.type.startswith("Gasto") or t.type == "Pago Deuda" or t.type == "Ahorro Meta":
                expenses[t.category] += t.amount
        sorted_exp = sorted(expenses.items(), key=lambda i: i[1], reverse=True)
        self.view.dashboard_page.update_expense_dist_chart([i[0] for i in sorted_exp], [i[1] for i in sorted_exp])

    def add_goal(self):
        data = self.view.goals_page.get_goal_form_data()
        if not data["name"] or not data["target_amount"]:
            self.view.show_notification("Nombre y Monto son obligatorios.", "error")
            return
        try:
            target = float(data["target_amount"])
            Goal.create(name=data["name"], target_amount=target, current_amount=0)
            self.view.goals_page.clear_goal_form()
            self.load_goals_and_debts()
            self.view.show_notification("Meta añadida.", "success")
        except ValueError:
            self.view.show_notification("El monto debe ser un número.", "error")

    def add_debt(self):
        data = self.view.goals_page.get_debt_form_data()
        if not data["name"] or not data["total_amount"]:
            self.view.show_notification("Nombre y Monto son obligatorios.", "error")
            return
        try:
            total = float(data["total_amount"])
            minimum_payment_text = data.get("minimum_payment", "0")
            minimum_payment = float(minimum_payment_text) if minimum_payment_text else 0.0
            Debt.create(name=data["name"], total_amount=total, current_balance=total, minimum_payment=minimum_payment)
            self.view.goals_page.clear_debt_form()
            self.load_goals_and_debts()
            self.view.show_notification("Deuda añadida.", "success")
        except ValueError:
            self.view.show_notification("El monto debe ser un número.", "error")

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
            
    def load_goals_and_debts(self):
        goals = Goal.select()
        goals_data = []
        today = datetime.date.today()

        for goal in goals:
            projected_date_str = "Añade aportes para proyectar"
            
            if goal.current_amount > 0:
                first_transaction = Transaction.select(fn.MIN(Transaction.date)).where(Transaction.goal == goal).scalar()
                
                if first_transaction:
                    start_date = datetime.date.fromisoformat(str(first_transaction))
                    days_saving = (today - start_date).days
                    if days_saving <= 0: days_saving = 1
                    
                    avg_daily_savings = goal.current_amount / days_saving
                    
                    if avg_daily_savings > 0:
                        remaining_amount = goal.target_amount - goal.current_amount
                        if remaining_amount > 0:
                            days_to_go = remaining_amount / avg_daily_savings
                            projected_date = today + datetime.timedelta(days=int(days_to_go))
                            projected_date_str = f"Proyección: {projected_date.strftime('%b %Y')}"
                        else:
                            projected_date_str = "¡Meta Completada!"
            
            goals_data.append({
                'id': goal.id, 'name': goal.name, 'current': goal.current_amount,
                'target': goal.target_amount, 'projected_date': projected_date_str
            })

        debts = Debt.select()
        self.view.goals_page.display_goals(goals_data)
        self.view.goals_page.display_debts(list(debts))
        self.load_transactions_dependencies()

    def load_transactions_dependencies(self):
        """Carga las listas de metas y deudas en los menús desplegables de la página de transacciones."""
        goals = Goal.select()
        debts = Debt.select()
        self.view.transactions_page.update_goal_and_debt_lists(goals, debts)
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
        
        filters = self.view.analysis_page.get_selected_filters()
        year, months = filters["year"], filters["months"]
        
        self._generate_and_display_annual_report(year, months)
        self._generate_and_display_budget_analysis(year, months)

    def _generate_and_display_annual_report(self, year, months):
        if not months:
            self.view.analysis_page.display_annual_report({}, [], year, {}, 0.0)
            return

        start_date = datetime.date(year, min(months), 1)
        last_month_num = max(months)
        next_month_start = (datetime.date(year, last_month_num, 1) + relativedelta(months=1))
        end_date = next_month_start - relativedelta(days=1)

        trans = Transaction.select().where((Transaction.date.between(start_date, end_date)) & (Transaction.type.startswith("Gasto")))
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
