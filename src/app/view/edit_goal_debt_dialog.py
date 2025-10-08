from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QHBoxLayout, QPushButton

class EditGoalDebtDialog(QDialog):
    def __init__(self, is_goal=True, data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar {'Meta' if is_goal else 'Deuda'}")
        
        self.data = data if data else {}
        self.is_goal = is_goal

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(self.data.get('name', ''))
        amount_label = f"Monto {'Objetivo' if is_goal else 'Total'}:"
        self.amount_input = QLineEdit(str(self.data.get('target_amount' if is_goal else 'total_amount', '')))

        form_layout.addRow("Nombre:", self.name_input)
        form_layout.addRow(amount_label, self.amount_input)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.cancel_button = QPushButton("Cancelar")
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

        # --- INICIO DE LA CORRECCIÓN ---
        # Conectamos a funciones explícitas en lugar de los slots por defecto
        self.save_button.clicked.connect(self.save_and_close)
        self.cancel_button.clicked.connect(self.cancel_and_close)
        # --- FIN DE LA CORRECCIÓN ---

    def save_and_close(self):
        self.done(QDialog.DialogCode.Accepted)

    def cancel_and_close(self):
        self.done(QDialog.DialogCode.Rejected)
    
    def get_data(self):
        key = 'target_amount' if self.is_goal else 'total_amount'
        return {
            'name': self.name_input.text(),
            key: self.amount_input.text()
        }