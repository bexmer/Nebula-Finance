# Reemplaza el contenido de src/app/view/goals_view.py con este código:

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QFrame, QProgressBar, QGridLayout,
                               QScrollArea, QFormLayout)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta

class GoalItem(QFrame):
    # ... (esta clase no necesita cambios, la puedes dejar como está)
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, goal_data, parent=None):
        super().__init__(parent)
        self.goal_id = goal_data['id']
        self.setObjectName("ListItemCard")
        
        main_layout = QHBoxLayout(self)
        info_layout = QGridLayout()
        info_layout.setColumnStretch(1, 1)

        self.name_label = QLabel(f"<b>{goal_data['name']}</b>")
        
        self.progress_bar = QProgressBar()
        percentage = (goal_data['current'] / goal_data['target'] * 100) if goal_data['target'] > 0 else 0
        self.progress_bar.setValue(int(percentage))
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setProperty("state", "good")
        self.progress_bar.style().polish(self.progress_bar)

        amounts_text = f"${goal_data['current']:,.2f} de ${goal_data['target']:,.2f}"
        self.amounts_label = QLabel(amounts_text)

        self.projection_label = QLabel(goal_data['projected_date'])
        self.projection_label.setObjectName("ProjectionLabel")

        info_layout.addWidget(self.name_label, 0, 0)
        info_layout.addWidget(self.amounts_label, 0, 1, Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(self.progress_bar, 1, 0, 1, 2)
        info_layout.addWidget(self.projection_label, 2, 0, 1, 2, Qt.AlignmentFlag.AlignRight)

        button_layout = QVBoxLayout()
        self.edit_button = QPushButton()
        self.edit_button.setIcon(qta.icon("fa5s.edit"))
        self.delete_button = QPushButton()
        self.delete_button.setIcon(qta.icon("fa5s.trash-alt"))
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()

        main_layout.addLayout(info_layout, 1)
        main_layout.addLayout(button_layout)
        
        self.edit_button.clicked.connect(lambda: self.edit_requested.emit(self.goal_id))
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.goal_id))

# --- INICIO DE LA SOLUCIÓN ---
# Clase para mostrar cada deuda en la lista
class DebtItem(QFrame):
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, debt_data, parent=None):
        super().__init__(parent)
        self.debt_id = debt_data.id
        self.setObjectName("ListItemCard")

        main_layout = QHBoxLayout(self)
        info_layout = QVBoxLayout()

        name_label = QLabel(f"<b>{debt_data.name}</b>")
        
        percentage = 0
        if debt_data.total_amount > 0:
            percentage = (1 - (debt_data.current_balance / debt_data.total_amount)) * 100

        progress_bar = QProgressBar()
        progress_bar.setValue(int(percentage))
        progress_bar.setTextVisible(False)
        progress_bar.setProperty("state", "good")
        progress_bar.style().polish(progress_bar)
        
        amounts_text = f"Pagado: ${debt_data.total_amount - debt_data.current_balance:,.2f} de ${debt_data.total_amount:,.2f}"
        amounts_label = QLabel(amounts_text)

        info_layout.addWidget(name_label)
        info_layout.addWidget(progress_bar)
        info_layout.addWidget(amounts_label)

        button_layout = QVBoxLayout()
        edit_button = QPushButton()
        edit_button.setIcon(qta.icon("fa5s.edit"))
        delete_button = QPushButton()
        delete_button.setIcon(qta.icon("fa5s.trash-alt"))
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()

        main_layout.addLayout(info_layout, 1)
        main_layout.addLayout(button_layout)
        
        edit_button.clicked.connect(lambda: self.edit_requested.emit(self.debt_id))
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.debt_id))

class GoalsView(QWidget):
    edit_goal_requested = Signal(int)
    delete_goal_requested = Signal(int)
    edit_debt_requested = Signal(int)
    delete_debt_requested = Signal(int)

    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_label = QLabel("Metas y Deudas")
        title_label.setObjectName("DashboardTitle")
        header_layout.addWidget(title_label)
        main_layout.addLayout(header_layout)
        
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout, 1)

        form_container = QWidget()
        form_container.setFixedWidth(350)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0); form_layout.setSpacing(20)

        self.goal_form_card = self._create_form_card("Añadir Nueva Meta")
        self.debt_form_card = self._create_form_card("Añadir Nueva Deuda")
        
        form_layout.addWidget(self.goal_form_card)
        form_layout.addWidget(self.debt_form_card)
        form_layout.addStretch()

        list_container = QWidget()
        list_layout = QHBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0); list_layout.setSpacing(20)

        self.goals_list_card = self._create_list_card("Metas Activas")
        self.debts_list_card = self._create_list_card("Deudas Activas")
        
        list_layout.addWidget(self.goals_list_card)
        list_layout.addWidget(self.debts_list_card)

        content_layout.addWidget(form_container)
        content_layout.addWidget(list_container, 1)

    def _create_form_card(self, title):
        # ... (este método no necesita cambios)
        card = QFrame(); card.setObjectName("Card")
        layout = QFormLayout(card); layout.setContentsMargins(15, 15, 15, 15); layout.setSpacing(10)
        layout.addRow(QLabel(f"<b>{title}</b>"))

        if "Meta" in title:
            self.goal_name_input = QLineEdit()
            self.goal_target_input = QLineEdit()
            self.add_goal_button = QPushButton("Añadir Meta"); self.add_goal_button.setObjectName("PrimaryAction")
            layout.addRow("Nombre de la Meta:", self.goal_name_input)
            layout.addRow("Monto Objetivo:", self.goal_target_input)
            layout.addRow(self.add_goal_button)
        else:
            self.debt_name_input = QLineEdit()
            self.debt_total_input = QLineEdit()
            self.debt_min_payment_input = QLineEdit()
            self.add_debt_button = QPushButton("Añadir Deuda"); self.add_debt_button.setObjectName("PrimaryAction")
            layout.addRow("Nombre de la Deuda:", self.debt_name_input)
            layout.addRow("Monto Total:", self.debt_total_input)
            layout.addRow("Pago Mínimo:", self.debt_min_payment_input)
            layout.addRow(self.add_debt_button)
        return card

    def _create_list_card(self, title):
        # ... (este método no necesita cambios)
        card = QFrame(); card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.addWidget(QLabel(f"<b>{title}</b>"))
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(); list_layout = QVBoxLayout(scroll_content)
        list_layout.setSpacing(10); list_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        if "Metas" in title: self.goals_list_layout = list_layout
        else: self.debts_list_layout = list_layout
        return card

    def display_goals(self, goals_data):
        # ... (este método no necesita cambios)
        self._clear_layout(self.goals_list_layout)
        for data in goals_data:
            goal_item = GoalItem(data)
            goal_item.edit_requested.connect(self.edit_goal_requested)
            goal_item.delete_requested.connect(self.delete_goal_requested)
            self.goals_list_layout.insertWidget(self.goals_list_layout.count() - 1, goal_item)

    # Implementación de la función para mostrar deudas
    def display_debts(self, debts):
        self._clear_layout(self.debts_list_layout)
        for debt_data in debts:
            debt_item = DebtItem(debt_data)
            debt_item.edit_requested.connect(self.edit_debt_requested)
            debt_item.delete_requested.connect(self.delete_debt_requested)
            self.debts_list_layout.insertWidget(self.debts_list_layout.count() - 1, debt_item)
    # --- FIN DE LA SOLUCIÓN ---
        
    def _clear_layout(self, layout):
        # ... (este método no necesita cambios)
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def get_goal_form_data(self):
        # ... (este método no necesita cambios)
        return {"name": self.goal_name_input.text(), "target_amount": self.goal_target_input.text()}

    def get_debt_form_data(self):
        # ... (este método no necesita cambios)
        return {"name": self.debt_name_input.text(), "total_amount": self.debt_total_input.text(), "minimum_payment": self.debt_min_payment_input.text()}
    
    def clear_goal_form(self):
        # ... (este método no necesita cambios)
        self.goal_name_input.clear(); self.goal_target_input.clear()

    def clear_debt_form(self):
        # ... (este método no necesita cambios)
        self.debt_name_input.clear(); self.debt_total_input.clear(); self.debt_min_payment_input.clear()