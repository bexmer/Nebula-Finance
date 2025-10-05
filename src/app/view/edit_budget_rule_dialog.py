from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QDialogButtonBox)

class EditBudgetRuleDialog(QDialog):
    def __init__(self, rule_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Regla de Presupuesto")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(rule_data['value'])
        # Mostramos el porcentaje como un número entero (ej. 50 en lugar de 0.5)
        self.percentage_input = QLineEdit(str(rule_data['numeric_value'] * 100))

        form_layout.addRow("Nombre de la Regla:", self.name_input)
        form_layout.addRow("Porcentaje (%):", self.percentage_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

    def get_data(self):
        """Devuelve los datos actualizados del formulario."""
        return {
            "value": self.name_input.text(),
            "percentage": self.percentage_input.text()
        }
