from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QComboBox, QFormLayout, QHeaderView, QCheckBox, QDateEdit)
from PySide6.QtCore import Qt, QDate

class BudgetView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_label = QLabel("Presupuesto Mensual")
        title_label.setObjectName("DashboardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout, 1)

        # --- Columna Izquierda: Tabla ---
        table_card = QFrame()
        table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)

        action_bar = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("Seleccionar todo")
        action_bar.addWidget(self.select_all_checkbox)
        action_bar.addStretch()
        self.register_payment_button = QPushButton("Registrar Pago")
        self.register_payment_button.setObjectName("PrimaryAction") # Le damos un estilo llamativo
        action_bar.addWidget(self.register_payment_button)
        self.delete_button = QPushButton("Eliminar Selección")
        action_bar.addWidget(self.delete_button)
        table_layout.addLayout(action_bar)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["", "Fecha Estimada", "Descripción", "Categoría", "Monto"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table_layout.addWidget(self.table)

        pagination_widget = self._create_pagination_widget()
        table_layout.addWidget(pagination_widget)

        # --- Columna Derecha: Formulario ---
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card.setFixedWidth(350)
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        self.description_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.amount_input.setMaxLength(15)
        self.type_input = QComboBox() 
        self.category_input = QComboBox()
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        self.add_button = QPushButton("Añadir al Presupuesto")
        self.add_button.setObjectName("PrimaryAction")

        form_layout.addRow("Descripción:", self.description_input)
        form_layout.addRow("Monto Presupuestado:", self.amount_input)
        form_layout.addRow("Tipo:", self.type_input)
        form_layout.addRow("Categoría:", self.category_input)
        form_layout.addRow("Fecha Estimada:", self.date_input)
        form_layout.addRow(self.add_button)

        content_layout.addWidget(table_card, 1)
        content_layout.addWidget(form_card)
        
        self.select_all_checkbox.toggled.connect(self.toggle_all_checkboxes)

    def _create_pagination_widget(self):
        widget = QFrame()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        self.items_per_page_combo = QComboBox()
        self.items_per_page_combo.addItems(['10', '20', '50'])
        self.prev_button = QPushButton("Anterior")
        self.next_button = QPushButton("Siguiente")
        self.page_label = QLabel("Página 1 de 1")
        layout.addWidget(QLabel("Items por página:")); layout.addWidget(self.items_per_page_combo)
        layout.addStretch()
        layout.addWidget(self.prev_button); layout.addWidget(self.page_label); layout.addWidget(self.next_button)
        return widget
        
    def display_budget_entries(self, entries):
        
        self.table.setRowCount(0)
        self.table.clearContents()
        for row, entry in enumerate(entries):
            self.table.insertRow(row)
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check_item.setCheckState(Qt.CheckState.Unchecked)
            check_item.setData(Qt.ItemDataRole.UserRole, entry.id)
            self.table.setItem(row, 0, check_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(entry.due_date.strftime('%Y-%m-%d')))
            self.table.setItem(row, 2, QTableWidgetItem(entry.description))
            self.table.setItem(row, 3, QTableWidgetItem(entry.category))
            self.table.setItem(row, 4, QTableWidgetItem(f"${entry.budgeted_amount:,.2f}"))
            self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, entry.id)

    def get_form_data(self):
        return {"description": self.description_input.text(), 
                "budgeted_amount": self.amount_input.text(),
                "type": self.type_input.currentText(), 
                "category": self.category_input.currentText(),
                "due_date": self.date_input.date().toPython()}

    def clear_form(self):
        self.description_input.clear()
        self.amount_input.clear()
        self.type_input.setCurrentIndex(0)
        self.category_input.setCurrentIndex(0)
        self.date_input.setDate(QDate.currentDate())
        
    def get_checked_ids(self):
        checked_ids = []
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).checkState() == Qt.CheckState.Checked:
                checked_ids.append(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))
        return checked_ids

    def toggle_all_checkboxes(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(state)
            
    def get_pagination_controls(self):
        return {
            'prev_button': self.prev_button, 'next_button': self.next_button,
            'page_label': self.page_label, 'items_per_page_combo': self.items_per_page_combo,
            'items_per_page': int(self.items_per_page_combo.currentText())
        }
        
    def update_pagination_ui(self, page, total_pages, total_items):
        self.page_label.setText(f"Página {page} de {total_pages}")
        self.prev_button.setEnabled(page > 1)
        self.next_button.setEnabled(page < total_pages)
    
    def get_selected_entry_id(self):
        """Obtiene el ID de la entrada de presupuesto seleccionada."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, 1)  # La columna 1 contiene el ID
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None