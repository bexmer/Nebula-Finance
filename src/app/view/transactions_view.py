from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QDateEdit, QComboBox, QFormLayout, QHeaderView, QGridLayout,
                               QTabWidget, QCheckBox, QSpinBox, QMenu)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QAction
from functools import partial

class TransactionsView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_container_layout = QVBoxLayout(self)
        main_container_layout.setContentsMargins(20, 20, 20, 20)
        main_container_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_label = QLabel("Transacciones")
        title_label.setObjectName("DashboardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_container_layout.addLayout(header_layout)

        content_layout = QHBoxLayout()
        main_container_layout.addLayout(content_layout, 1)
        
        # --- FORMULARIO IZQUIERDO ---
        form_card = QFrame(); form_card.setObjectName("Card"); form_card.setFixedWidth(350)
        self.form_layout = QFormLayout(form_card)
        self.form_layout.setContentsMargins(15, 15, 15, 15); self.form_layout.setSpacing(10)

        self.date_input = QDateEdit(QDate.currentDate()); self.date_input.setCalendarPopup(True)
        self.description_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.account_input = QComboBox()
        self.type_input = QComboBox()
        self.category_input = QComboBox()
        
        self.goal_combo = QComboBox(); self.debt_combo = QComboBox()
        self.goal_label = QLabel("Asignar a Meta:"); self.debt_label = QLabel("Asignar a Deuda:")
        
        self.recurring_checkbox = QCheckBox("Es una transacción recurrente")
        
        self.frequency_label = QLabel("Frecuencia:")
        self.frequency_input = QComboBox(); self.frequency_input.addItems(["Mensual", "Quincenal", "Anual"])
        
        self.month_label = QLabel("Mes (Anual):")
        self.month_input = QSpinBox(); self.month_input.setRange(1, 12)

        self.day_label = QLabel("Día del Mes:")
        self.day_input = QSpinBox(); self.day_input.setRange(1, 31)

        self.day2_label = QLabel("Segundo Día (Quincenal):")
        self.day2_input = QSpinBox(); self.day2_input.setRange(1, 31)

        self.add_button = QPushButton("Añadir Transacción"); self.add_button.setObjectName("PrimaryAction")

        self.form_layout.addRow("Fecha:", self.date_input)
        self.form_layout.addRow("Descripción:", self.description_input)
        self.form_layout.addRow("Monto:", self.amount_input)
        self.form_layout.addRow("Cuenta:", self.account_input)
        self.form_layout.addRow("Tipo:", self.type_input)
        self.form_layout.addRow("Categoría:", self.category_input)
        self.form_layout.addRow(self.goal_label, self.goal_combo)
        self.form_layout.addRow(self.debt_label, self.debt_combo)
        self.form_layout.addRow(self.recurring_checkbox)
        
        self.form_layout.addRow(self.frequency_label, self.frequency_input)
        self.form_layout.addRow(self.month_label, self.month_input)
        self.form_layout.addRow(self.day_label, self.day_input)
        self.form_layout.addRow(self.day2_label, self.day2_input)
        self.form_layout.addRow(self.add_button)
        
        self.type_input.currentTextChanged.connect(self._toggle_assignment_combos)
        self.recurring_checkbox.toggled.connect(self._toggle_recurring_fields)
        self.frequency_input.currentTextChanged.connect(self._toggle_recurring_fields)
        self._toggle_recurring_fields(False)
        self._toggle_assignment_combos(self.type_input.currentText())

        # --- TABLA DERECHA ---
        table_card = QFrame(); table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        
        filter_bar_layout = QGridLayout()
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Buscar por descripción...")
        
        self.type_filter_button = self._create_filter_button_with_menu("Todos los Tipos", [])
        self.category_filter_button = self._create_filter_button_with_menu("Todas las Categorías", [])
        self.sort_by_button = self._create_filter_button_with_menu("Fecha", ["Fecha", "Monto"])
        self.sort_order_button = self._create_filter_button_with_menu("Descendente", ["Descendente", "Ascendente"])

        self.start_date_filter = QDateEdit(QDate.currentDate().addMonths(-1)); self.start_date_filter.setCalendarPopup(True)
        self.end_date_filter = QDateEdit(QDate.currentDate()); self.end_date_filter.setCalendarPopup(True)
        
        filter_bar_layout.addWidget(self.search_input, 0, 0, 1, 6)
        filter_bar_layout.addWidget(QLabel("Desde:"), 1, 0); filter_bar_layout.addWidget(self.start_date_filter, 1, 1)
        filter_bar_layout.addWidget(QLabel("Hasta:"), 1, 2); filter_bar_layout.addWidget(self.end_date_filter, 1, 3)
        filter_bar_layout.addWidget(QLabel("Tipo:"), 2, 0); filter_bar_layout.addWidget(self.type_filter_button, 2, 1)
        filter_bar_layout.addWidget(QLabel("Categoría:"), 2, 2); filter_bar_layout.addWidget(self.category_filter_button, 2, 3)
        filter_bar_layout.addWidget(QLabel("Ordenar por:"), 3, 0); filter_bar_layout.addWidget(self.sort_by_button, 3, 1)
        filter_bar_layout.addWidget(self.sort_order_button, 3, 2, 1, 2)
        table_layout.addLayout(filter_bar_layout)
        
        action_bar = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("Seleccionar todo")
        action_bar.addWidget(self.select_all_checkbox)
        action_bar.addStretch()
        self.delete_button = QPushButton("Eliminar Selección")
        table_layout.addLayout(action_bar)
        
        self.tabs = QTabWidget()
        self.all_tab = QWidget(); all_layout = QVBoxLayout(self.all_tab); self.all_table = self._create_table(["Fecha", "Descripción", "Monto", "Tipo", "Categoría"]); all_layout.addWidget(self.all_table)
        self.goals_tab = QWidget(); goals_layout = QVBoxLayout(self.goals_tab); self.goals_table = self._create_table(["Fecha", "Meta", "Categoría", "Descripción", "Monto Aportado"]); goals_layout.addWidget(self.goals_table)
        self.debts_tab = QWidget(); debts_layout = QVBoxLayout(self.debts_tab); self.debts_table = self._create_table(["Fecha", "Deuda", "Categoría", "Descripción", "Monto Pagado"]); debts_layout.addWidget(self.debts_table)
        self.recurring_tab = QWidget(); recurring_layout = QVBoxLayout(self.recurring_tab); self.recurring_table = self._create_table(["Descripción", "Monto", "Categoría", "Día del Mes", "Próxima Fecha"]); recurring_layout.addWidget(self.recurring_table)
        self.tabs.addTab(self.all_tab, "Todas"); self.tabs.addTab(self.goals_tab, "Aportes a Metas"); self.tabs.addTab(self.debts_tab, "Pagos a Deudas"); self.tabs.addTab(self.recurring_tab, "Recurrentes")
        table_layout.addWidget(self.tabs)

        pagination_widget = self._create_pagination_widget()
        table_layout.addWidget(pagination_widget)
        
        content_layout.addWidget(form_card); content_layout.addWidget(table_card, 1)
        
        self.select_all_checkbox.toggled.connect(self.toggle_all_checkboxes)

    def _create_pagination_widget(self):
        widget = QFrame()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        self.items_per_page_combo = QComboBox()
        self.items_per_page_combo.addItems(['10', '20', '50'])
        
        self.prev_button = QPushButton("Anterior")
        self.next_button = QPushButton("Siguiente")
        self.page_label = QLabel("Página 1 de 1")

        layout.addWidget(QLabel("Items por página:"))
        layout.addWidget(self.items_per_page_combo)
        layout.addStretch()
        layout.addWidget(self.prev_button)
        layout.addWidget(self.page_label)
        layout.addWidget(self.next_button)
        
        return widget

    def _create_filter_button_with_menu(self, initial_text, items):
        button = QPushButton(initial_text)
        button.setObjectName("FilterButton")
        menu = QMenu(self)
        button.setMenu(menu)
        button.menu = menu
        self.update_menu_items(button, items)
        return button

    def update_menu_items(self, button, items):
        button.menu.clear()
        for item_text in items:
            action = QAction(item_text, self)
            action.triggered.connect(partial(self.update_button_text_and_filter, button, item_text))
            button.menu.addAction(action)

    def update_button_text_and_filter(self, button, text):
        button.setText(text)
        self.search_input.textChanged.emit(self.search_input.text())

    def _toggle_recurring_fields(self, checked=None):
        if checked is None: checked = self.recurring_checkbox.isChecked()
        is_recurring = self.recurring_checkbox.isChecked()
        frequency = self.frequency_input.currentText()
        self.frequency_label.setVisible(is_recurring); self.frequency_input.setVisible(is_recurring)
        self.month_label.setVisible(is_recurring and frequency == 'Anual'); self.month_input.setVisible(is_recurring and frequency == 'Anual')
        self.day_label.setVisible(is_recurring); self.day_input.setVisible(is_recurring)
        self.day2_label.setVisible(is_recurring and frequency == 'Quincenal'); self.day2_input.setVisible(is_recurring and frequency == 'Quincenal')
        label_fecha = self.form_layout.labelForField(self.date_input)
        if label_fecha: label_fecha.setText("Fecha de Inicio:" if is_recurring else "Fecha:")
        self.add_button.setText("Añadir Regla Recurrente" if is_recurring else "Añadir Transacción")

    def _create_table(self, headers):
        table = QTableWidget(0, len(headers) + 1)
        table.setHorizontalHeaderLabels([""] + headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        return table

    def _toggle_assignment_combos(self, text):
        show_goals = (text == "Ahorro Meta")
        show_debts = (text == "Pago Deuda")
        self.goal_label.setVisible(show_goals)
        self.goal_combo.setVisible(show_goals)
        self.debt_label.setVisible(show_debts)
        self.debt_combo.setVisible(show_debts)
    
    def display_recurring_rules(self, rules, next_dates):
        self.recurring_table.setRowCount(0)
        for row, rule in enumerate(rules):
            self.recurring_table.insertRow(row)
            check_item = QTableWidgetItem(); check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled); check_item.setCheckState(Qt.CheckState.Unchecked); check_item.setData(Qt.ItemDataRole.UserRole, rule.id)
            self.recurring_table.setItem(row, 0, check_item)
            self.recurring_table.setItem(row, 1, QTableWidgetItem(rule.description))
            self.recurring_table.setItem(row, 2, QTableWidgetItem(f"${rule.amount:,.2f}"))
            self.recurring_table.setItem(row, 3, QTableWidgetItem(rule.category))
            self.recurring_table.setItem(row, 4, QTableWidgetItem(str(rule.day_of_month)))
            self.recurring_table.setItem(row, 5, QTableWidgetItem(next_dates.get(rule.id, 'N/A')))
            self.recurring_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, rule.id)

    def display_all_transactions(self, transactions):
        self.all_table.setRowCount(0)
        for row, trans in enumerate(transactions):
            self.all_table.insertRow(row)
            check_item = QTableWidgetItem(); check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled); check_item.setCheckState(Qt.CheckState.Unchecked); check_item.setData(Qt.ItemDataRole.UserRole, trans.id)
            self.all_table.setItem(row, 0, check_item)
            self.all_table.setItem(row, 1, QTableWidgetItem(trans.date.strftime('%Y-%m-%d')))
            self.all_table.setItem(row, 2, QTableWidgetItem(trans.description))
            self.all_table.setItem(row, 3, QTableWidgetItem(f"${trans.amount:,.2f}"))
            self.all_table.setItem(row, 4, QTableWidgetItem(trans.type))
            self.all_table.setItem(row, 5, QTableWidgetItem(trans.category))
            self.all_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, trans.id)

    def display_goal_transactions(self, transactions):
        self.goals_table.setRowCount(0)
        for row, trans in enumerate(transactions):
            self.goals_table.insertRow(row)
            check_item = QTableWidgetItem(); check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled); check_item.setCheckState(Qt.CheckState.Unchecked); check_item.setData(Qt.ItemDataRole.UserRole, trans.id)
            self.goals_table.setItem(row, 0, check_item)
            self.goals_table.setItem(row, 1, QTableWidgetItem(trans.date.strftime('%Y-%m-%d')))
            self.goals_table.setItem(row, 2, QTableWidgetItem(trans.goal.name))
            self.goals_table.setItem(row, 3, QTableWidgetItem(trans.category))
            self.goals_table.setItem(row, 4, QTableWidgetItem(trans.description))
            self.goals_table.setItem(row, 5, QTableWidgetItem(f"${trans.amount:,.2f}"))
            self.goals_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, trans.id)

    def display_debt_transactions(self, transactions):
        self.debts_table.setRowCount(0)
        for row, trans in enumerate(transactions):
            self.debts_table.insertRow(row)
            check_item = QTableWidgetItem(); check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled); check_item.setCheckState(Qt.CheckState.Unchecked); check_item.setData(Qt.ItemDataRole.UserRole, trans.id)
            self.debts_table.setItem(row, 0, check_item)
            self.debts_table.setItem(row, 1, QTableWidgetItem(trans.date.strftime('%Y-%m-%d')))
            self.debts_table.setItem(row, 2, QTableWidgetItem(trans.debt.name))
            self.debts_table.setItem(row, 3, QTableWidgetItem(trans.category))
            self.debts_table.setItem(row, 4, QTableWidgetItem(trans.description))
            self.debts_table.setItem(row, 5, QTableWidgetItem(f"${trans.amount:,.2f}"))
            self.debts_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, trans.id)

    def update_accounts_list(self, accounts):
        self.account_input.clear()
        for acc in accounts: self.account_input.addItem(f"{acc.name} (${acc.current_balance:,.2f})", userData=acc.id)

    def update_goal_and_debt_lists(self, goals, debts):
        self.goal_combo.clear(); self.debt_combo.clear()
        self.goal_combo.addItem("Ninguna", userData=None)
        [self.goal_combo.addItem(g.name, userData=g.id) for g in goals]
        self.debt_combo.addItem("Ninguna", userData=None)
        [self.debt_combo.addItem(d.name, userData=d.id) for d in debts]
        
    def get_form_data(self):
        goal_id = self.goal_combo.currentData() if self.type_input.currentText() == "Ahorro Meta" else None
        debt_id = self.debt_combo.currentData() if self.type_input.currentText() == "Pago Deuda" else None
        data = { "date": self.date_input.date().toPython(), "description": self.description_input.text(), "amount": self.amount_input.text(), "type": self.type_input.currentText(), "category": self.category_input.currentText(), "goal_id": goal_id, "debt_id": debt_id, "is_recurring": self.recurring_checkbox.isChecked(), "account_id": self.account_input.currentData() }
        if data["is_recurring"]:
            data["frequency"] = self.frequency_input.currentText()
            data["day_of_month"] = self.day_input.value()
            if data["frequency"] == 'Quincenal': data["day_of_month_2"] = self.day2_input.value()
            if data["frequency"] == 'Anual': data["month_of_year"] = self.month_input.value()
        return data

    def clear_form(self):
        self.description_input.clear(); self.amount_input.clear(); self.date_input.setDate(QDate.currentDate())
        self.type_input.setCurrentIndex(0); self.category_input.setCurrentIndex(0); self.goal_combo.setCurrentIndex(0); self.debt_combo.setCurrentIndex(0)
        self.recurring_checkbox.setChecked(False)

    def get_selected_transaction_id(self):
        current_table = self.tabs.currentWidget().findChild(QTableWidget)
        if not current_table: return None
        selected_items = current_table.selectedItems()
        if not selected_items: return None
        return current_table.item(selected_items[0].row(), 1).data(Qt.ItemDataRole.UserRole)
    
    def get_filters(self):
        return {"search_text": self.search_input.text(), "type": self.type_filter_button.text(), "category": self.category_filter_button.text(), "sort_by": self.sort_by_button.text(), "sort_order": self.sort_order_button.text(), "start_date": self.start_date_filter.date().toPython(), "end_date": self.end_date_filter.date().toPython(), "current_tab_index": self.tabs.currentIndex()}

    def toggle_all_checkboxes(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        current_table = self.tabs.currentWidget().findChild(QTableWidget)
        if current_table:
            for row in range(current_table.rowCount()):
                current_table.item(row, 0).setCheckState(state)

    def get_checked_ids(self):
        checked_ids = []
        current_table = self.tabs.currentWidget().findChild(QTableWidget)
        if current_table:
            for row in range(current_table.rowCount()):
                if current_table.item(row, 0).checkState() == Qt.CheckState.Checked:
                    checked_ids.append(current_table.item(row, 0).data(Qt.ItemDataRole.UserRole))
        return checked_ids

    def get_pagination_controls(self):
        return {
            'prev_button': self.prev_button, 'next_button': self.next_button,
            'page_label': self.page_label, 'items_per_page_combo': self.items_per_page_combo,
            'items_per_page': int(self.items_per_page_combo.currentText())
        }
        
    def update_pagination_ui(self, page, total_pages, total_items):
        self.page_label.setText(f"Página {page} de {total_pages}")
        self.prev_button.setEnabled(page > 1)
        self.next_button.setEnabled(page < total_pages)