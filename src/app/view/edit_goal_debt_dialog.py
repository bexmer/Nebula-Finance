from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QPushButton, QDialogButtonBox, QLabel)

class EditGoalDebtDialog(QDialog):
    def __init__(self, item_data, mode, parent=None):
        super().__init__(parent)
        
        self.mode = mode # 'goal' o 'debt'
        title = "Editar Meta" if self.mode == 'goal' else "Editar Deuda"
        self.setWindowTitle(title)
        
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Crear campos del formulario
        self.name_input = QLineEdit(item_data['name'])
        
        if self.mode == 'goal':
            self.target_amount_input = QLineEdit(str(item_data['target_amount']))
            form_layout.addRow("Nombre:", self.name_input)
            form_layout.addRow("Monto Objetivo:", self.target_amount_input)
        else: # mode == 'debt'
            self.total_amount_input = QLineEdit(str(item_data['total_amount']))
            self.minimum_payment_input = QLineEdit(str(item_data['minimum_payment']))
            form_layout.addRow("Nombre:", self.name_input)
            form_layout.addRow("Monto Total:", self.total_amount_input)
            form_layout.addRow("Pago Mínimo:", self.minimum_payment_input)

        # Botones de Guardar y Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(self.button_box)

    def get_data(self):
        data = {"name": self.name_input.text()}
        if self.mode == 'goal':
            data["target_amount"] = self.target_amount_input.text()
        else:
            data["total_amount"] = self.total_amount_input.text()
            data["minimum_payment"] = self.minimum_payment_input.text()
        return data
