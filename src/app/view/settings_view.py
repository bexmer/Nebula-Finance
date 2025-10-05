from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QComboBox, QFormLayout, QHeaderView, QTabWidget, QSpinBox)
from PySide6.QtCore import Qt

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_label = QLabel("Configuración de Parámetros")
        title_label.setObjectName("DashboardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Crear cada pestaña
        self.transaction_types_tab = self._create_transaction_types_tab()
        self.account_types_tab = self._create_parameter_tab("Tipo de Cuenta")
        self.categories_tab = self._create_parameter_tab("Categoría")

        self.tabs.addTab(self.transaction_types_tab, "Tipos de Transacción y Reglas")
        self.tabs.addTab(self.account_types_tab, "Tipos de Cuenta")
        self.tabs.addTab(self.categories_tab, "Categorías")

    def _create_transaction_types_tab(self):
        # Widget contenedor para toda la pestaña
        tab_widget = QWidget()
        main_content_layout = QHBoxLayout(tab_widget)

        # --- Columna Izquierda: Tipos de Transacción ---
        tt_container = QWidget()
        tt_layout = QVBoxLayout(tt_container)
        tt_layout.setContentsMargins(0,0,0,0)
        
        tt_form_card = QFrame(); tt_form_card.setObjectName("Card")
        tt_form_layout = QFormLayout(tt_form_card); tt_form_layout.setContentsMargins(15, 15, 15, 15); tt_form_layout.setSpacing(10)
        
        tt_value_input = QLineEdit()
        tt_budget_rule_input = QComboBox()
        tt_add_button = QPushButton("Añadir Tipo de Transacción"); tt_add_button.setObjectName("ActionButton")

        tt_form_layout.addRow("Nombre:", tt_value_input)
        tt_form_layout.addRow("Regla de Presupuesto:", tt_budget_rule_input)
        tt_form_layout.addRow(tt_add_button)
        
        tt_table_card = QFrame(); tt_table_card.setObjectName("Card")
        tt_table_layout = QVBoxLayout(tt_table_card)
        tt_delete_button = QPushButton("Eliminar Selección")
        tt_table_layout.addWidget(tt_delete_button, 0, Qt.AlignmentFlag.AlignRight)

        tt_table = QTableWidget(0, 2); tt_table.setHorizontalHeaderLabels(["Nombre", "Regla de Presupuesto"])
        tt_table.verticalHeader().setVisible(False)
        tt_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tt_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tt_table_layout.addWidget(tt_table)

        tt_layout.addWidget(tt_form_card)
        tt_layout.addWidget(tt_table_card, 1)

        # --- Columna Derecha: Reglas de Presupuesto ---
        br_container = QWidget()
        br_layout = QVBoxLayout(br_container)
        br_layout.setContentsMargins(0,0,0,0)

        br_form_card = QFrame(); br_form_card.setObjectName("Card")
        br_form_layout = QFormLayout(br_form_card); br_form_layout.setContentsMargins(15, 15, 15, 15); br_form_layout.setSpacing(10)

        br_name_input = QLineEdit()
        br_percentage_input = QSpinBox(); br_percentage_input.setRange(0, 100); br_percentage_input.setSuffix(" %")
        br_add_button = QPushButton("Añadir Regla de Presupuesto"); br_add_button.setObjectName("ActionButton")

        br_form_layout.addRow("Nombre de la Regla:", br_name_input)
        br_form_layout.addRow("Porcentaje:", br_percentage_input)
        br_form_layout.addRow(br_add_button)

        br_table_card = QFrame(); br_table_card.setObjectName("Card")
        br_table_layout = QVBoxLayout(br_table_card)
        br_delete_button = QPushButton("Eliminar Selección")
        br_table_layout.addWidget(br_delete_button, 0, Qt.AlignmentFlag.AlignRight)

        br_table = QTableWidget(0, 2); br_table.setHorizontalHeaderLabels(["Nombre", "Porcentaje"])
        br_table.verticalHeader().setVisible(False)
        br_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        br_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        br_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        br_table_layout.addWidget(br_table)

        br_layout.addWidget(br_form_card)
        br_layout.addWidget(br_table_card, 1)

        main_content_layout.addWidget(tt_container, 1)
        main_content_layout.addWidget(br_container, 1)

        # Almacenar referencias
        tab_widget.value_input = tt_value_input
        tab_widget.budget_rule_input = tt_budget_rule_input
        tab_widget.add_button = tt_add_button
        tab_widget.delete_button = tt_delete_button
        tab_widget.table = tt_table

        tab_widget.rule_name_input = br_name_input
        tab_widget.rule_percentage_input = br_percentage_input
        tab_widget.add_rule_button = br_add_button
        tab_widget.delete_rule_button = br_delete_button
        tab_widget.budget_rule_table = br_table

        return tab_widget

    def _create_parameter_tab(self, group_name):
        tab_widget = QWidget()
        content_layout = QHBoxLayout(tab_widget)

        form_card = QFrame(); form_card.setObjectName("Card"); form_card.setFixedWidth(350)
        form_layout = QFormLayout(form_card); form_layout.setContentsMargins(15, 15, 15, 15); form_layout.setSpacing(10)

        value_input = QLineEdit()
        form_layout.addRow("Nombre:", value_input)

        add_button = QPushButton(f"Añadir {group_name}"); add_button.setObjectName("ActionButton")
        form_layout.addRow(add_button)
        
        table_card = QFrame(); table_card.setObjectName("Card"); table_layout = QVBoxLayout(table_card)
        delete_button = QPushButton("Eliminar Selección")
        table_layout.addWidget(delete_button, 0, Qt.AlignmentFlag.AlignRight)

        table = QTableWidget(0, 1); table.setHorizontalHeaderLabels(["Nombre"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(table)

        content_layout.addWidget(form_card); content_layout.addWidget(table_card, 1)

        tab_widget.value_input = value_input
        tab_widget.add_button = add_button
        tab_widget.delete_button = delete_button
        tab_widget.table = table
        
        return tab_widget
        
    def get_form_data(self, tab_widget):
        data = {"value": tab_widget.value_input.text()}
        if hasattr(tab_widget, 'budget_rule_input'):
            rule = tab_widget.budget_rule_input.currentText()
            data['budget_rule'] = None if rule == "(Ninguna)" else rule
        return data

    def get_budget_rule_form_data(self):
        tab = self.transaction_types_tab
        return {
            "value": tab.rule_name_input.text(),
            "percentage": tab.rule_percentage_input.value()
        }

    def clear_form(self, tab_widget):
        if hasattr(tab_widget, 'value_input'):
            tab_widget.value_input.clear()
        if hasattr(tab_widget, 'budget_rule_input'):
            tab_widget.budget_rule_input.setCurrentIndex(0)
    
    def clear_budget_rule_form(self):
        tab = self.transaction_types_tab
        tab.rule_name_input.clear()
        tab.rule_percentage_input.setValue(0)

    def _display_data_in_table(self, table, parameters, display_rule):
        table.setRowCount(0)
        for row, param in enumerate(parameters):
            table.insertRow(row)
            item = QTableWidgetItem(param.value)
            item.setData(Qt.ItemDataRole.UserRole, param.id)
            table.setItem(row, 0, item)
            if display_rule:
                rule_text = param.budget_rule if param.budget_rule else "(Ninguna)"
                table.setItem(row, 1, QTableWidgetItem(rule_text))

    def display_transaction_types(self, parameters):
        self._display_data_in_table(self.transaction_types_tab.table, parameters, True)

    def display_account_types(self, parameters):
        self._display_data_in_table(self.account_types_tab.table, parameters, False)

    def display_categories(self, parameters):
        self._display_data_in_table(self.categories_tab.table, parameters, False)
    
    def display_budget_rules(self, rules):
        table = self.transaction_types_tab.budget_rule_table
        table.setRowCount(0)
        for row, rule in enumerate(rules):
            table.insertRow(row)
            name_item = QTableWidgetItem(rule.value)
            name_item.setData(Qt.ItemDataRole.UserRole, rule.id)
            table.setItem(row, 0, name_item)
            
            percentage = rule.numeric_value if rule.numeric_value is not None else 0
            percent_item = QTableWidgetItem(f"{percentage * 100:.0f}%")
            table.setItem(row, 1, percent_item)

    def update_budget_rules_combo(self, rule_names):
        combo = self.transaction_types_tab.budget_rule_input
        combo.clear()
        combo.addItem("(Ninguna)")
        combo.addItems(rule_names)

    def get_selected_parameter_id(self, table):
        selected_items = table.selectedItems()
        return selected_items[0].data(Qt.ItemDataRole.UserRole) if selected_items else None

