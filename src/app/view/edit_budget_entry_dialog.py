from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QComboBox, QDialogButtonBox)

class EditBudgetEntryDialog(QDialog):
    """
    Diálogo emergente para editar una entrada de presupuesto existente.
    """
    def __init__(self, entry_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Entrada de Presupuesto")
        
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Crear y rellenar los campos del formulario con los datos existentes
        self.description_input = QLineEdit(entry_data['description'])
        self.amount_input = QLineEdit(str(entry_data['budgeted_amount']))
        
        self.type_input = QComboBox()
        self.type_input.addItems(["Ingreso Planeado", "Gasto Planeado"])
        self.type_input.setCurrentText(entry_data['type'])
        
        self.category_input = QComboBox()
        self.category_input.addItems(["Nómina", "Freelance", "Otros Ingresos", "Vivienda", "Servicios", "Transporte", "Comida", "Ocio", "Salud", "Educación", "Ahorro", "Pago Deuda", "Otros Gastos"])
        self.category_input.setCurrentText(entry_data['category'])

        form_layout.addRow("Descripción:", self.description_input)
        form_layout.addRow("Monto Presupuestado:", self.amount_input)
        form_layout.addRow("Tipo:", self.type_input)
        form_layout.addRow("Categoría:", self.category_input)

        # Botones de Guardar y Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(self.button_box)

    def get_data(self):
        """Devuelve los datos actualizados del formulario."""
        return {
            "description": self.description_input.text(),
            "budgeted_amount": self.amount_input.text(),
            "type": self.type_input.currentText(),
            "category": self.category_input.currentText()
        }

