from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QDateEdit, QComboBox, QPushButton, QDialogButtonBox)
from PySide6.QtCore import QDate

class EditTransactionDialog(QDialog):
    def __init__(self, transaction_data, goals, debts, accounts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Transacción")
        
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.date_input = QDateEdit(QDate.fromString(transaction_data['date'], "yyyy-MM-dd"))
        self.description_input = QLineEdit(transaction_data['description'])
        self.amount_input = QLineEdit(str(transaction_data['amount']))
        
        self.account_input = QComboBox()
        self.update_accounts_list(accounts)
        if transaction_data['account_id']:
            self.account_input.setCurrentIndex(self.account_input.findData(transaction_data['account_id']))

        self.type_input = QComboBox()
        self.type_input.addItems(["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro/Pago Meta/Deuda"])
        self.type_input.setCurrentText(transaction_data['type'])
        
        self.category_input = QComboBox()
        self.category_input.addItems(["Nómina", "Freelance", "Otros Ingresos", "Vivienda", "Servicios", "Transporte", "Comida", "Ocio", "Salud", "Educación", "Ahorro", "Pago Deuda", "Otros Gastos"])
        self.category_input.setCurrentText(transaction_data['category'])

        self.goal_combo = QComboBox()
        self.debt_combo = QComboBox()
        
        self.update_goal_and_debt_lists(goals, debts)
        if transaction_data['goal_id']:
            self.goal_combo.setCurrentIndex(self.goal_combo.findData(transaction_data['goal_id']))
        if transaction_data['debt_id']:
            self.debt_combo.setCurrentIndex(self.debt_combo.findData(transaction_data['debt_id']))
        
        form_layout.addRow("Fecha:", self.date_input)
        form_layout.addRow("Descripción:", self.description_input)
        form_layout.addRow("Monto:", self.amount_input)
        form_layout.addRow("Cuenta:", self.account_input)
        form_layout.addRow("Tipo:", self.type_input)
        form_layout.addRow("Categoría:", self.category_input)
        form_layout.addRow("Asignar a Meta:", self.goal_combo)
        form_layout.addRow("Asignar a Deuda:", self.debt_combo)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(self.button_box)

    def update_accounts_list(self, accounts):
        self.account_input.clear()
        for acc in accounts:
            self.account_input.addItem(acc.name, userData=acc.id)

    def update_goal_and_debt_lists(self, goals, debts):
        self.goal_combo.addItem("Ninguna", userData=None)
        for goal in goals:
            self.goal_combo.addItem(goal.name, userData=goal.id)
        self.debt_combo.addItem("Ninguna", userData=None)
        for debt in debts:
            self.debt_combo.addItem(debt.name, userData=debt.id)
            
    def get_data(self):
        goal_id = self.goal_combo.currentData()
        debt_id = self.debt_combo.currentData()
        if self.goal_combo.currentIndex() > 0:
            debt_id = None

        return {
            "date": self.date_input.date().toPython(),
            "description": self.description_input.text(),
            "amount": self.amount_input.text(),
            "type": self.type_input.currentText(),
            "category": self.category_input.currentText(),
            "goal_id": goal_id,
            "debt_id": debt_id,
            "account_id": self.account_input.currentData()
        }