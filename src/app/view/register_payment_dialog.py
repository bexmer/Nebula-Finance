from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel,
                               QComboBox, QDialogButtonBox)

class RegisterPaymentDialog(QDialog):
    def __init__(self, accounts, total_amount, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Pago de Presupuesto")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Muestra el monto total para confirmación
        amount_label = QLabel(f"<b>${total_amount:,.2f}</b>")
        
        self.account_input = QComboBox()
        if not accounts:
            self.account_input.addItem("No hay cuentas disponibles")
            self.account_input.setEnabled(False)
        else:
            for acc in accounts:
                self.account_input.addItem(f"{acc.name} (${acc.current_balance:,.2f})", userData=acc.id)

        form_layout.addRow("Monto Total a Pagar:", amount_label)
        form_layout.addRow("Pagar con la Cuenta:", self.account_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Deshabilitar el botón OK si no hay cuentas
        if not accounts:
            button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

    def get_selected_account_id(self):
        """Devuelve el ID de la cuenta seleccionada."""
        return self.account_input.currentData()