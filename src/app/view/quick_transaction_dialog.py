from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QComboBox, QDialogButtonBox)

class QuickTransactionDialog(QDialog):
    def __init__(self, accounts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gasto Rápido")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.description_input = QLineEdit()
        self.amount_input = QLineEdit()
        
        self.account_input = QComboBox()
        for acc in accounts:
            self.account_input.addItem(acc.name, userData=acc.id)

        self.category_input = QComboBox()
        self.category_input.addItems(["Comida", "Transporte", "Ocio", "Servicios", "Otros Gastos"]) # Categorías de gasto más comunes

        form_layout.addRow("Descripción:", self.description_input)
        form_layout.addRow("Monto:", self.amount_input)
        form_layout.addRow("Pagar con:", self.account_input)
        form_layout.addRow("Categoría:", self.category_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

    def get_data(self):
        return {
            "description": self.description_input.text(),
            "amount": self.amount_input.text(),
            "account_id": self.account_input.currentData(),
            "category": self.category_input.currentText()
        }