# Reemplaza todo el contenido de este archivo con el siguiente código corregido:

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QComboBox, QDialogButtonBox, QDateEdit)
from PySide6.QtCore import QDate
import datetime

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
        # Los items se añaden desde el controlador
        
        self.category_input = QComboBox()
        # Los items se añaden desde el controlador

        # --- INICIO DE LA SOLUCIÓN ---
        # Asegurarse de que la fecha es un objeto QDate para el widget
        due_date = entry_data.get('due_date', datetime.date.today())
        if isinstance(due_date, datetime.date):
             due_date = QDate(due_date.year, due_date.month, due_date.day)
        self.date_input = QDateEdit(due_date)
        self.date_input.setCalendarPopup(True)
        # --- FIN DE LA SOLUCIÓN ---

        form_layout.addRow("Descripción:", self.description_input)
        form_layout.addRow("Monto Presupuestado:", self.amount_input)
        form_layout.addRow("Tipo:", self.type_input)
        form_layout.addRow("Categoría:", self.category_input)
        form_layout.addRow("Fecha Estimada:", self.date_input)

        # Botones de Guardar y Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(self.button_box)

    def get_data(self):
        """Devuelve los datos actualizados del formulario."""
        # --- INICIO DE LA SOLUCIÓN ---
        return {
            "description": self.description_input.text(),
            "budgeted_amount": self.amount_input.text(),
            "type": self.type_input.currentText(),
            "category": self.category_input.currentText(),
            "due_date": self.date_input.date().toPython() # Devolver el objeto de fecha
        }
        # --- FIN DE LA SOLUCIÓN ---