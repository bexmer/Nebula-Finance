from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QComboBox, QDialogButtonBox)

class EditAccountDialog(QDialog):
    def __init__(self, account_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Cuenta")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(account_data['name'])
        self.type_input = QComboBox()
        self.type_input.addItems(["Cuenta de Ahorros", "Cuenta Corriente", "Tarjeta de Crédito", "Efectivo", "Inversión"])
        self.type_input.setCurrentText(account_data['account_type'])

        form_layout.addRow("Nombre de la Cuenta:", self.name_input)
        form_layout.addRow("Tipo de Cuenta:", self.type_input)
        
        # Nota: El saldo no se puede editar directamente, se calcula con las transacciones.

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "account_type": self.type_input.currentText()
        }