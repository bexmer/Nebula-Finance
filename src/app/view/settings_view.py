from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QComboBox, QFormLayout, QHeaderView, QTabWidget)
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
        self.transaction_types_tab = self._create_parameter_tab("Tipo de Transacción", has_budget_rule=True)
        self.account_types_tab = self._create_parameter_tab("Tipo de Cuenta")
        self.categories_tab = self._create_parameter_tab("Categoría")

        self.tabs.addTab(self.transaction_types_tab, "Tipos de Transacción")
        self.tabs.addTab(self.account_types_tab, "Tipos de Cuenta")
        self.tabs.addTab(self.categories_tab, "Categorías")

    def _create_parameter_tab(self, group_name, has_budget_rule=False):
        # Widget contenedor para la pestaña
        tab_widget = QWidget()
        content_layout = QHBoxLayout(tab_widget)

        # Formulario a la izquierda
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card.setFixedWidth(350)
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        value_input = QLineEdit()
        form_layout.addRow("Valor:", value_input)

        if has_budget_rule:
            budget_rule_input = QComboBox()
            budget_rule_input.addItems(["(Ninguna)", "Esenciales", "Crecimiento", "Estabilidad", "Recompensas"])
            form_layout.addRow("Regla de Presupuesto:", budget_rule_input)
            tab_widget.budget_rule_input = budget_rule_input

        add_button = QPushButton(f"Añadir {group_name}")
        add_button.setObjectName("ActionButton")
        form_layout.addRow(add_button)
        
        # Tabla a la derecha
        table_card = QFrame()
        table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        
        delete_button = QPushButton("Eliminar Selección")
        table_layout.addWidget(delete_button, 0, Qt.AlignmentFlag.AlignRight)

        table = QTableWidget(0, 2 if has_budget_rule else 1)
        headers = ["Valor", "Regla de Presupuesto"] if has_budget_rule else ["Valor"]
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(table)

        content_layout.addWidget(form_card)
        content_layout.addWidget(table_card, 1)

        # Almacenar referencias a los widgets importantes
        tab_widget.value_input = value_input
        tab_widget.add_button = add_button
        tab_widget.delete_button = delete_button
        tab_widget.table = table
        
        return tab_widget
        
    # Métodos para obtener datos y limpiar formularios (adaptados a la nueva estructura)
    def get_form_data(self, tab_widget):
        data = {"value": tab_widget.value_input.text()}
        if hasattr(tab_widget, 'budget_rule_input'):
            rule = tab_widget.budget_rule_input.currentText()
            data['budget_rule'] = None if rule == "(Ninguna)" else rule
        return data

    def clear_form(self, tab_widget):
        tab_widget.value_input.clear()
        if hasattr(tab_widget, 'budget_rule_input'):
            tab_widget.budget_rule_input.setCurrentIndex(0)
    
    # Métodos para mostrar datos en las tablas
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

    def get_selected_parameter_id(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            selected_items = current_tab.table.selectedItems()
            return selected_items[0].data(Qt.ItemDataRole.UserRole) if selected_items else None
        return None