from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QComboBox, QFormLayout, QHeaderView, QTabWidget, QDoubleSpinBox)
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

        self.transaction_types_tab = self._create_transaction_rules_tab()
        self.account_types_tab = self._create_parameter_tab("Tipo de Cuenta")
        self.categories_tab = self._create_parameter_tab("Categoría")

        self.tabs.addTab(self.transaction_types_tab, "Tipos de Transacción y Reglas")
        self.tabs.addTab(self.account_types_tab, "Tipos de Cuenta")
        self.tabs.addTab(self.categories_tab, "Categorías")

    def _create_transaction_rules_tab(self):
        """Crea la pestaña especial dividida en dos."""
        tab_widget = QWidget()
        main_hbox = QHBoxLayout(tab_widget)

        # --- Columna Izquierda: Tipos de Transacción ---
        param_widget = self._create_parameter_tab_content("Tipo de Transacción", has_budget_rule=True)
        
        # --- Columna Derecha: Reglas de Presupuesto ---
        rules_widget = QWidget()
        rules_vbox = QVBoxLayout(rules_widget)
        rules_vbox.setContentsMargins(0, 0, 0, 0)
        rules_vbox.setSpacing(15)

        # Formulario para Reglas
        rule_form_card = QFrame(); rule_form_card.setObjectName("Card")
        rule_form_layout = QFormLayout(rule_form_card)
        rule_form_layout.setContentsMargins(15, 15, 15, 15); rule_form_layout.setSpacing(10)
        
        rule_name_input = QLineEdit()
        rule_percentage_input = QDoubleSpinBox()
        rule_percentage_input.setRange(0, 100); rule_percentage_input.setSuffix(" %")
        add_rule_button = QPushButton("Añadir Regla de Presupuesto"); add_rule_button.setObjectName("ActionButton")
        
        rule_form_layout.addRow("Nombre de la Regla:", rule_name_input)
        rule_form_layout.addRow("Porcentaje:", rule_percentage_input)
        rule_form_layout.addRow(add_rule_button)

        # Tabla para Reglas
        rule_table_card = QFrame(); rule_table_card.setObjectName("Card")
        rule_table_layout = QVBoxLayout(rule_table_card)
        
        delete_rule_button = QPushButton("Eliminar Selección")
        rule_table_layout.addWidget(delete_rule_button, 0, Qt.AlignmentFlag.AlignRight)

        rule_table = QTableWidget(0, 2)
        rule_table.setHorizontalHeaderLabels(["Nombre", "Porcentaje"])
        rule_table.verticalHeader().setVisible(False)
        rule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        rule_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        rule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        rule_table_layout.addWidget(rule_table)

        rules_vbox.addWidget(rule_form_card)
        rules_vbox.addWidget(rule_table_card, 1)

        # Añadir ambas columnas al layout principal
        main_hbox.addWidget(param_widget, 1)
        main_hbox.addWidget(rules_widget, 1)

        # Guardar referencias para el controlador
        tab_widget.param_value_input = param_widget.value_input
        tab_widget.param_add_button = param_widget.add_button
        tab_widget.param_delete_button = param_widget.delete_button
        tab_widget.param_table = param_widget.table
        tab_widget.param_budget_rule_input = param_widget.budget_rule_input

        tab_widget.rule_name_input = rule_name_input
        tab_widget.rule_percentage_input = rule_percentage_input
        tab_widget.rule_add_button = add_rule_button
        tab_widget.rule_delete_button = delete_rule_button
        tab_widget.rule_table = rule_table

        return tab_widget

    def _create_parameter_tab_content(self, group_name, has_budget_rule=False):
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0); vbox.setSpacing(15)

        form_card = QFrame(); form_card.setObjectName("Card")
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(15, 15, 15, 15); form_layout.setSpacing(10)

        value_input = QLineEdit()
        form_layout.addRow("Nombre:", value_input)

        if group_name == 'Categoría':
            parent_type_input = QComboBox()
            form_layout.addRow("Pertenece a Tipo:", parent_type_input)
            container.parent_type_input = parent_type_input
        
        if has_budget_rule:
            budget_rule_input = QComboBox()
            form_layout.addRow("Regla de Presupuesto:", budget_rule_input)
            container.budget_rule_input = budget_rule_input

        add_button = QPushButton(f"Añadir {group_name}"); add_button.setObjectName("ActionButton")
        form_layout.addRow(add_button)
        
        table_card = QFrame(); table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        
        delete_button = QPushButton("Eliminar Selección")
        table_layout.addWidget(delete_button, 0, Qt.AlignmentFlag.AlignRight)

        cols = 1
        headers = ["Nombre"]
        if has_budget_rule:
            cols += 1; headers.append("Regla Presupuesto")
        if group_name == 'Categoría':
            cols += 1; headers.append("Tipo Padre")

        table = QTableWidget(0, cols); table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(table)

        vbox.addWidget(form_card); vbox.addWidget(table_card, 1)

        container.value_input = value_input; container.add_button = add_button
        container.delete_button = delete_button; container.table = table
        
        return container
    
    def update_parent_type_combo(self, transaction_types):
        if hasattr(self.categories_tab, 'parent_type_input'):
            combo = self.categories_tab.parent_type_input
            combo.clear()
            for t_type in transaction_types:
                combo.addItem(t_type.value, userData=t_type.id)

    def _create_parameter_tab(self, group_name):
        """Crea una pestaña estándar con una sola columna."""
        tab_widget = QWidget()
        content_layout = QHBoxLayout(tab_widget)
        param_content = self._create_parameter_tab_content(group_name, has_budget_rule=False)
        content_layout.addWidget(param_content)
        
        # Mapear widgets para consistencia
        tab_widget.value_input = param_content.value_input
        tab_widget.add_button = param_content.add_button
        tab_widget.delete_button = param_content.delete_button
        tab_widget.table = param_content.table
        
        return tab_widget

    # (El resto de la clase permanece igual, pero la actualizo para mayor claridad)
    def display_parameters(self, table, parameters, display_rule):
        table.setRowCount(0)
        col_count = table.columnCount()
        for row, param in enumerate(parameters):
            table.insertRow(row)
            item = QTableWidgetItem(param.value); item.setData(Qt.ItemDataRole.UserRole, param.id)
            table.setItem(row, 0, item)
            
            col_idx = 1
            if display_rule: # Para Tipos de Transacción
                rule_name = "(Ninguna)"
                try:
                    if param.budget_rule: rule_name = param.budget_rule.name
                except Exception: pass
                table.setItem(row, col_idx, QTableWidgetItem(rule_name))
                col_idx += 1
            
            if param.group == 'Categoría' and col_count > 1: # Para Categorías
                parent_name = "(Ninguno)"
                try:
                    if param.parent: parent_name = param.parent.value
                except Exception: pass
                table.setItem(row, col_idx, QTableWidgetItem(parent_name))
                
    def display_budget_rules(self, table, rules):
        table.setRowCount(0)
        for row, rule in enumerate(rules):
            table.insertRow(row)
            name_item = QTableWidgetItem(rule.name)
            name_item.setData(Qt.ItemDataRole.UserRole, rule.id)
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(f"{rule.percentage:.2f} %"))
    
    def update_budget_rule_combo(self, rules):
        combo = self.transaction_types_tab.param_budget_rule_input
        combo.clear()
        combo.addItem("(Ninguna)", userData=None)
        for rule in rules:
            combo.addItem(rule.name, userData=rule.id)