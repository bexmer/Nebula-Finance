from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QComboBox, QDialogButtonBox, QSpinBox, QLabel)
from PySide6.QtCore import Qt

class EditRecurringDialog(QDialog):
    def __init__(self, rule_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Regla Recurrente")
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # Crear y rellenar los campos del formulario
        self.description_input = QLineEdit(rule_data['description'])
        self.amount_input = QLineEdit(str(rule_data['amount']))
        
        self.type_input = QComboBox()
        self.type_input.addItems(["Ingreso", "Gasto Fijo", "Gasto Variable"])
        self.type_input.setCurrentText(rule_data['type'])
        
        self.category_input = QComboBox()
        self.category_input.addItems(["Nómina", "Freelance", "Otros Ingresos", "Vivienda", "Servicios", "Transporte", "Comida", "Ocio", "Salud", "Educación", "Otros Gastos"])
        self.category_input.setCurrentText(rule_data['category'])

        self.frequency_input = QComboBox()
        self.frequency_input.addItems(["Mensual", "Quincenal", "Anual"])
        self.frequency_input.setCurrentText(rule_data['frequency'])
        
        self.month_input = QSpinBox(); self.month_input.setRange(1, 12)
        self.month_input.setValue(rule_data.get('month_of_year') or 1)

        self.day_input = QSpinBox(); self.day_input.setRange(1, 31)
        self.day_input.setValue(rule_data['day_of_month'])

        self.day2_input = QSpinBox(); self.day2_input.setRange(1, 31)
        self.day2_input.setValue(rule_data.get('day_of_month_2') or 1)

        self.form_layout.addRow("Descripción:", self.description_input)
        self.form_layout.addRow("Monto:", self.amount_input)
        self.form_layout.addRow("Tipo:", self.type_input)
        self.form_layout.addRow("Categoría:", self.category_input)
        self.form_layout.addRow("Frecuencia:", self.frequency_input)
        self.form_layout.addRow("Mes (Anual):", self.month_input)
        self.form_layout.addRow("Día del Mes:", self.day_input)
        self.form_layout.addRow("Segundo Día (Quincenal):", self.day2_input)

        self.frequency_input.currentTextChanged.connect(self._toggle_fields)
        self._toggle_fields(rule_data['frequency'])

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.button_box)

    def _toggle_fields(self, frequency):
        is_anual = (frequency == 'Anual')
        is_quincenal = (frequency == 'Quincenal')
        
        self.form_layout.labelForField(self.month_input).setVisible(is_anual)
        self.month_input.setVisible(is_anual)
        
        self.form_layout.labelForField(self.day2_input).setVisible(is_quincenal)
        self.day2_input.setVisible(is_quincenal)

    def get_data(self):
        data = {
            "description": self.description_input.text(),
            "amount": self.amount_input.text(),
            "type": self.type_input.currentText(),
            "category": self.category_input.currentText(),
            "frequency": self.frequency_input.currentText(),
            "day_of_month": self.day_input.value()
        }
        if data["frequency"] == 'Quincenal':
            data["day_of_month_2"] = self.day2_input.value()
        if data["frequency"] == 'Anual':
            data["month_of_year"] = self.month_input.value()
        return data