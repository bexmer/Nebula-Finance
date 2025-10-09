from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QDialogButtonBox)

class EditGoalDebtDialog(QDialog):
    def __init__(self, data, item_type="goal", parent=None):
        super().__init__(parent)
        self.item_type = item_type
        is_goal = (self.item_type == "goal")
        self.setWindowTitle(f"Editar {'Meta' if is_goal else 'Deuda'}")
        
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Campo para el nombre
        self.name_input = QLineEdit(data.get('name', ''))
        form_layout.addRow("Nombre:", self.name_input)

        # Campo para el monto (objetivo o total)
        amount_label = f"Monto {'Objetivo' if is_goal else 'Total'}:"
        self.amount_input = QLineEdit(str(data.get('target_amount' if is_goal else 'total_amount', '')))
        form_layout.addRow(amount_label, self.amount_input)

        # --- INICIO DE LA SOLUCIÓN ---
        # Añadir el campo para pago mínimo solo si es una deuda
        self.min_payment_input = None
        if not is_goal:
            self.min_payment_input = QLineEdit(str(data.get('minimum_payment', '')))
            form_layout.addRow("Pago Mínimo:", self.min_payment_input)
        # --- FIN DE LA SOLUCIÓN ---

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

    def get_data(self):
        is_goal = (self.item_type == "goal")
        data = {'name': self.name_input.text()}
        
        # --- INICIO DE LA SOLUCIÓN ---
        # Devolver los datos correctos según si es meta o deuda
        if is_goal:
            data['target_amount'] = self.amount_input.text()
        else:
            data['total_amount'] = self.amount_input.text()
            if self.min_payment_input:
                data['minimum_payment'] = self.min_payment_input.text()
        return data
        # --- FIN DE LA SOLUCIÓN ---