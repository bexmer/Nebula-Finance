from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QScrollArea, QProgressBar, QFormLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from functools import partial

class GoalsView(QWidget):
    edit_goal_requested = Signal(int)
    delete_goal_requested = Signal(int)
    edit_debt_requested = Signal(int)
    delete_debt_requested = Signal(int)

    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self); main_layout.setContentsMargins(20, 20, 20, 20); main_layout.setSpacing(20)
        form_container = QWidget(); form_container.setFixedWidth(350)
        form_layout = QVBoxLayout(form_container); form_layout.setContentsMargins(0, 0, 0, 0); form_layout.setSpacing(20)
        goal_frame = QFrame(); goal_frame.setObjectName("Card"); goal_form_layout = QFormLayout(goal_frame)
        goal_form_layout.setContentsMargins(15, 15, 15, 15); goal_form_layout.setSpacing(10); goal_form_layout.addRow(QLabel("<b>Nueva Meta</b>"))
        self.goal_name_input = QLineEdit(); self.goal_target_input = QLineEdit(); self.add_goal_button = QPushButton("Añadir Meta")
        goal_form_layout.addRow("Nombre:", self.goal_name_input); goal_form_layout.addRow("Monto Objetivo:", self.goal_target_input); goal_form_layout.addRow(self.add_goal_button)
        debt_frame = QFrame(); debt_frame.setObjectName("Card"); debt_form_layout = QFormLayout(debt_frame)
        debt_form_layout.setContentsMargins(15, 15, 15, 15); debt_form_layout.setSpacing(10); debt_form_layout.addRow(QLabel("<b>Nueva Deuda</b>"))
        self.debt_name_input = QLineEdit(); self.debt_total_input = QLineEdit(); self.debt_minimum_payment_input = QLineEdit()
        self.add_debt_button = QPushButton("Añadir Deuda")
        debt_form_layout.addRow("Nombre:", self.debt_name_input); debt_form_layout.addRow("Monto Total:", self.debt_total_input); debt_form_layout.addRow("Pago Mínimo:", self.debt_minimum_payment_input); debt_form_layout.addRow(self.add_debt_button)
        form_layout.addWidget(goal_frame); form_layout.addWidget(debt_frame); form_layout.addStretch()
        
        right_container = QWidget(); display_layout = QVBoxLayout(right_container); display_layout.setContentsMargins(0, 0, 0, 0); display_layout.setSpacing(15)
        display_layout.addWidget(QLabel("<b>Mis Metas</b>")); scroll_goals = QScrollArea(); scroll_goals.setWidgetResizable(True)
        self.goals_content_widget = QWidget(); self.goals_list_layout = QVBoxLayout(self.goals_content_widget); self.goals_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_goals.setWidget(self.goals_content_widget); display_layout.addWidget(scroll_goals)
        display_layout.addWidget(QLabel("<b>Mis Deudas</b>")); scroll_debts = QScrollArea(); scroll_debts.setWidgetResizable(True)
        self.debts_content_widget = QWidget(); self.debts_list_layout = QVBoxLayout(self.debts_content_widget); self.debts_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_debts.setWidget(self.debts_content_widget); display_layout.addWidget(scroll_debts)
        main_layout.addWidget(form_container); main_layout.addWidget(right_container, 1)

    def get_goal_form_data(self): return {"name": self.goal_name_input.text(), "target_amount": self.goal_target_input.text()}
    def get_debt_form_data(self): return {"name": self.debt_name_input.text(), "total_amount": self.debt_total_input.text(), "minimum_payment": self.debt_minimum_payment_input.text()}
    def clear_goal_form(self): self.goal_name_input.clear(); self.goal_target_input.clear()
    def clear_debt_form(self): self.debt_name_input.clear(); self.debt_total_input.clear(); self.debt_minimum_payment_input.clear()

    def display_goals(self, goals):
        for i in reversed(range(self.goals_list_layout.count())): self.goals_list_layout.itemAt(i).widget().setParent(None)
        for goal in goals: self.goals_list_layout.addWidget(self._create_goal_card(goal))
    def display_debts(self, debts):
        for i in reversed(range(self.debts_list_layout.count())): self.debts_list_layout.itemAt(i).widget().setParent(None)
        for debt in debts: self.debts_list_layout.addWidget(self._create_debt_card(debt))
    
    def _create_goal_card(self, goal):
        card = QFrame(); card.setObjectName("ListItemCard"); layout = QVBoxLayout(card)
        top_layout = QHBoxLayout(); name_label = QLabel(f"<b>{goal.name}</b>"); top_layout.addWidget(name_label); top_layout.addStretch()
        edit_btn = QPushButton("Editar"); edit_btn.setObjectName("ItemButton"); delete_btn = QPushButton("Eliminar"); delete_btn.setObjectName("ItemButton")
        edit_btn.clicked.connect(partial(self.edit_goal_requested.emit, goal.id))
        delete_btn.clicked.connect(partial(self.delete_goal_requested.emit, goal.id))
        top_layout.addWidget(edit_btn); top_layout.addWidget(delete_btn); layout.addLayout(top_layout)
        
        progress_layout = QHBoxLayout()
        progress_label = QLabel(f"${goal.current_amount:,.2f} / ${goal.target_amount:,.2f}")
        percentage = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0
        percentage_label = QLabel(f"<b>{percentage:.1f}%</b>")
        progress_layout.addWidget(progress_label); progress_layout.addStretch(); progress_layout.addWidget(percentage_label)
        layout.addLayout(progress_layout)

        progress_bar = QProgressBar(); progress_bar.setValue(int(percentage)); progress_bar.setTextVisible(False)
        progress_bar.setProperty("state", "good")
        progress_bar.style().polish(progress_bar)
        layout.addWidget(progress_bar)
        return card

    def _create_debt_card(self, debt):
        card = QFrame(); card.setObjectName("ListItemCard"); layout = QVBoxLayout(card)
        top_layout = QHBoxLayout(); name_label = QLabel(f"<b>{debt.name}</b>"); top_layout.addWidget(name_label); top_layout.addStretch()
        edit_btn = QPushButton("Editar"); edit_btn.setObjectName("ItemButton"); delete_btn = QPushButton("Eliminar"); delete_btn.setObjectName("ItemButton")
        edit_btn.clicked.connect(partial(self.edit_debt_requested.emit, debt.id))
        delete_btn.clicked.connect(partial(self.delete_debt_requested.emit, debt.id))
        top_layout.addWidget(edit_btn); top_layout.addWidget(delete_btn); layout.addLayout(top_layout)

        progress_layout = QHBoxLayout()
        progress_label = QLabel(f"Saldo: ${debt.current_balance:,.2f} de ${debt.total_amount:,.2f}")
        percentage_paid = ((debt.total_amount - debt.current_balance) / debt.total_amount) * 100 if debt.total_amount > 0 else 0
        percentage_label = QLabel(f"<b>{percentage_paid:.1f}% Pagado</b>")
        progress_layout.addWidget(progress_label); progress_layout.addStretch(); progress_layout.addWidget(percentage_label)
        layout.addLayout(progress_layout)

        progress_bar = QProgressBar(); progress_bar.setValue(int(percentage_paid)); progress_bar.setTextVisible(False)
        progress_bar.setProperty("state", "good")
        progress_bar.style().polish(progress_bar)
        layout.addWidget(progress_bar)
        return card