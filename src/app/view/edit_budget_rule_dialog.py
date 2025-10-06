from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QDialogButtonBox, QDoubleSpinBox)

class EditBudgetRuleDialog(QDialog):
    def __init__(self, rule_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Regla de Presupuesto")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(rule_data['name'])
        self.percentage_input = QDoubleSpinBox()
        self.percentage_input.setRange(0, 100)
        self.percentage_input.setSuffix(" %")
        self.percentage_input.setValue(rule_data['percentage'])

        form_layout.addRow("Nombre de la Regla:", self.name_input)
        form_layout.addRow("Porcentaje:", self.percentage_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "percentage": self.percentage_input.value()
        }