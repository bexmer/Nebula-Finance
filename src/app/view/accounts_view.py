from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QComboBox, QFormLayout, QHeaderView)
from PySide6.QtCore import Qt

class AccountsView(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- INICIO DE LA SOLUCIÓN ---
        # Inicializamos la variable del controlador para evitar el error
        self.controller = None
        # --- FIN DE LA SOLUCIÓN ---

        main_container_layout = QVBoxLayout(self)
        main_container_layout.setContentsMargins(20, 20, 20, 20)
        main_container_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_label = QLabel("Cuentas")
        title_label.setObjectName("DashboardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_container_layout.addLayout(header_layout)

        content_layout = QHBoxLayout()
        main_container_layout.addLayout(content_layout, 1)
        
        form_card = QFrame(); form_card.setObjectName("Card"); form_card.setFixedWidth(350)
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(15, 15, 15, 15); form_layout.setSpacing(10)

        self.name_input = QLineEdit()
        self.type_input = QComboBox()
        self.balance_input = QLineEdit()
        self.balance_input.setMaxLength(15) # Límite de dígitos
        
        self.add_button = QPushButton("Añadir Cuenta"); self.add_button.setObjectName("ActionButton")
        self.delete_button = QPushButton("Eliminar Selección")

        form_layout.addRow("Nombre de la Cuenta:", self.name_input)
        form_layout.addRow("Tipo de Cuenta:", self.type_input)
        form_layout.addRow("Saldo Inicial:", self.balance_input)
        form_layout.addRow(self.add_button)

        table_card = QFrame(); table_card.setObjectName("Card"); table_layout = QVBoxLayout(table_card)
        table_layout.addWidget(self.delete_button, 0, Qt.AlignmentFlag.AlignRight)
        
        self.table = QTableWidget(0, 3); self.table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Saldo Actual"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.table)

        content_layout.addWidget(form_card); content_layout.addWidget(table_card, 1)

    def get_form_data(self):
        return {
            "name": self.name_input.text(),
            "account_type": self.type_input.currentText(),
            "initial_balance": self.balance_input.text()
        }

    def clear_form(self):
        self.name_input.clear(); self.balance_input.clear()
        self.type_input.setCurrentIndex(0)

    def display_accounts(self, accounts):
        self.table.setRowCount(0)
        for row, account in enumerate(accounts):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(account.name))
            self.table.setItem(row, 1, QTableWidgetItem(account.account_type))
            
            if self.controller:
                display_text, tooltip_text = self.controller.format_currency(account.current_balance)
                balance_item = QTableWidgetItem(display_text)
                balance_item.setToolTip(tooltip_text)
                self.table.setItem(row, 2, balance_item)
            else:
                 self.table.setItem(row, 2, QTableWidgetItem(f"${account.current_balance:,.2f}"))

            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, account.id)

    def get_selected_account_id(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None