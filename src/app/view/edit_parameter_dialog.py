from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QDialogButtonBox, QLabel, QComboBox)

class EditParameterDialog(QDialog):
    def __init__(self, param_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Parámetro")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.value_input = QLineEdit(param_data['value'])
        
        # Si el parámetro no es editable, el campo de valor se hace de solo lectura.
        if not param_data['is_deletable']:
            self.value_input.setReadOnly(True)

        form_layout.addRow("Grupo:", QLabel(param_data['group']))
        form_layout.addRow("Valor:", self.value_input)

        self.budget_rule_input = None
        if param_data['group'] == 'Tipo de Transacción':
            self.budget_rule_input = QComboBox()
            self.budget_rule_input.addItems(["(Ninguna)", "Esenciales", "Crecimiento", "Estabilidad", "Recompensas"])
            current_rule = param_data.get('budget_rule') or "(Ninguna)"
            self.budget_rule_input.setCurrentText(current_rule)
            form_layout.addRow("Regla de Presupuesto:", self.budget_rule_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

    def get_data(self):
        data = {"value": self.value_input.text()}
        if self.budget_rule_input:
            rule = self.budget_rule_input.currentText()
            data['budget_rule'] = None if rule == "(Ninguna)" else rule
        return data
