from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QComboBox, QFormLayout, QHeaderView)
from PySide6.QtCore import Qt

class BudgetView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_container_layout = QVBoxLayout(self)
        main_container_layout.setContentsMargins(20, 20, 20, 20)
        main_container_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_label = QLabel("Presupuesto")
        title_label.setObjectName("DashboardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_container_layout.addLayout(header_layout)

        content_layout = QHBoxLayout()
        main_container_layout.addLayout(content_layout, 1)
        
        form_card = QFrame(); form_card.setObjectName("Card"); form_card.setFixedWidth(350)
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(15, 15, 15, 15); form_layout.setSpacing(10)

        self.description_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.type_input = QComboBox() 
        self.category_input = QComboBox()
        
        self.add_button = QPushButton("Añadir al Presupuesto"); self.add_button.setObjectName("ActionButton")
        self.delete_button = QPushButton("Eliminar Selección")

        form_layout.addRow("Descripción:", self.description_input)
        form_layout.addRow("Monto Presupuestado:", self.amount_input)
        form_layout.addRow("Tipo:", self.type_input)
        form_layout.addRow("Categoría:", self.category_input)
        form_layout.addRow(self.add_button)

        table_card = QFrame(); table_card.setObjectName("Card"); table_layout = QVBoxLayout(table_card)
        table_layout.addWidget(self.delete_button, 0, Qt.AlignmentFlag.AlignRight)
        
        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["Descripción", "Categoría", "Tipo", "Monto Presupuestado"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.table)

        content_layout.addWidget(form_card); content_layout.addWidget(table_card, 1)

    def display_budget_entries(self, entries):
        self.table.setRowCount(0)
        for row, entry in enumerate(entries):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry.description))
            self.table.setItem(row, 1, QTableWidgetItem(entry.category))
            self.table.setItem(row, 2, QTableWidgetItem(entry.type))
            self.table.setItem(row, 3, QTableWidgetItem(f"${entry.budgeted_amount:,.2f}"))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, entry.id)

    def get_form_data(self):
        return {"description": self.description_input.text(), "budgeted_amount": self.amount_input.text(),
                "type": self.type_input.currentText(), "category": self.category_input.currentText()}

    def clear_form(self):
        self.description_input.clear(); self.amount_input.clear()
        self.type_input.setCurrentIndex(0); self.category_input.setCurrentIndex(0)

    def get_selected_entry_id(self):
        selected_items = self.table.selectedItems()
        return selected_items[0].data(Qt.ItemDataRole.UserRole) if selected_items else None
