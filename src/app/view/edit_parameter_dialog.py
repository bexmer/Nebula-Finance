from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QDialogButtonBox, QLabel, QComboBox)

class EditParameterDialog(QDialog):
    def __init__(self, param_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Parámetro")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.value_input = QLineEdit(param_data['value'])
        
        if not param_data['is_deletable']:
            self.value_input.setReadOnly(True)

        form_layout.addRow("Grupo:", QLabel(param_data['group']))
        form_layout.addRow("Nombre:", self.value_input)

        self.budget_rule_input = None
        if param_data['group'] == 'Tipo de Transacción':
            self.budget_rule_input = QComboBox()
            self.budget_rule_input.addItems(["(Ninguna)"])
            form_layout.addRow("Regla de Presupuesto:", self.budget_rule_input)

        # --- INICIO DE LA SOLUCIÓN ---
        # Inicializamos el atributo SIEMPRE
        self.parent_type_input = None
        # Y solo creamos el widget si el grupo es 'Categoría'
        if param_data['group'] == 'Categoría':
            self.parent_type_input = QComboBox()
            form_layout.addRow("Pertenece a Tipo:", self.parent_type_input)
        # --- FIN DE LA SOLUCIÓN ---

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

    def populate_parent_types(self, transaction_types, current_parent_id):
        """Llena el ComboBox con los tipos de transacción y selecciona el actual."""
        if not self.parent_type_input:
            return
            
        for t_type in transaction_types:
            self.parent_type_input.addItem(t_type.value, userData=t_type.id)
        
        index = self.parent_type_input.findData(current_parent_id)
        if index >= 0:
            self.parent_type_input.setCurrentIndex(index)
            
    def get_data(self):
        data = {"value": self.value_input.text()}
        if self.budget_rule_input:
            rule = self.budget_rule_input.currentText()
            data['budget_rule'] = None if rule == "(Ninguna)" else rule
            
        if self.parent_type_input:
            data['parent_id'] = self.parent_type_input.currentData()
            
        return data