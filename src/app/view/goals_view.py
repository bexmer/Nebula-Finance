from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QFrame, QProgressBar, QGridLayout,
                               QScrollArea, QFormLayout, QTabWidget, QTableWidget,
                               QTableWidgetItem, QHeaderView, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect

class GoalItem(QFrame):
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    def __init__(self, goal_data, controller, parent=None):
        super().__init__(parent)
        self.goal_id = goal_data['id']
        self.setObjectName("ListItemCard")
        main_layout = QHBoxLayout(self)
        info_layout = QGridLayout()
        info_layout.setColumnStretch(1, 1)
        current_text, current_tip = controller.format_currency(goal_data['current'])
        target_text, target_tip = controller.format_currency(goal_data['target'])
        amounts_text = f"{current_text} de {target_text}"
        
        self.amounts_label = QLabel(amounts_text)
        self.amounts_label.setToolTip(f"{current_tip} de {target_tip}")

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

class DebtItem(QFrame):
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    def __init__(self, debt_data, controller, parent=None):
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

        # --- INICIO DE LA SOLUCIÓN ---
         # Es necesario pasar el formateador a esta clase
        controller = parent.parent().parent().parent().controller # Navegamos hasta la vista para encontrar el controlador
        
        paid_amount_text, _ = controller.format_currency(debt_data.total_amount - debt_data.current_balance)
        total_amount_text, _ = controller.format_currency(debt_data.total_amount)
        min_payment_text, _ = controller.format_currency(debt_data.minimum_payment)

        amounts_text = (f"Pagado: {paid_amount_text} de {total_amount_text} "
                        f"| <b>Pago Mínimo:</b> {min_payment_text} "
                        f"| <b>Interés:</b> {debt_data.interest_rate:.2f}%")
        # --- FIN DE LA SOLUCIÓN ---

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
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        self.main_tabs = QTabWidget()
        main_layout.addWidget(self.main_tabs, 1)

        summary_widget = self._create_summary_tab()
        self.main_tabs.addTab(summary_widget, "Resumen")

        strategy_widget = self._create_strategy_tab()
        self.main_tabs.addTab(strategy_widget, "Estrategia de Deudas")

    def _create_summary_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 10, 0, 0)
        
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)
        
        self.goal_form_card = self._create_form_card("Añadir Nueva Meta")
        self.debt_form_card = self._create_form_card("Añadir Nueva Deuda")
        top_layout.addWidget(self.goal_form_card)
        top_layout.addWidget(self.debt_form_card)
        
        main_layout.addLayout(top_layout)

        bottom_card = QFrame(); bottom_card.setObjectName("Card")
        bottom_layout = QVBoxLayout(bottom_card)
        
        list_tabs = QTabWidget()
        goals_list_widget, self.goals_list_layout = self._create_list_widget()
        debts_list_widget, self.debts_list_layout = self._create_list_widget()
        
        list_tabs.addTab(goals_list_widget, "Metas Activas")
        list_tabs.addTab(debts_list_widget, "Deudas Activas")
        
        bottom_layout.addWidget(list_tabs)
        main_layout.addWidget(bottom_card, 1)
        return widget

    def _create_strategy_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 10, 0, 0)
        main_layout.setSpacing(15)

        control_card = QFrame(); control_card.setObjectName("Card")
        control_layout = QHBoxLayout(control_card)
        control_layout.setContentsMargins(15, 15, 15, 15)
        
        control_layout.addWidget(QLabel("<b>Pago Mensual Adicional:</b>"))
        self.extra_payment_input = QDoubleSpinBox()
        self.extra_payment_input.setPrefix("$ ")
        self.extra_payment_input.setRange(0, 100000)
        self.extra_payment_input.setValue(100)
        control_layout.addWidget(self.extra_payment_input)
        
        self.calculate_strategy_button = QPushButton("Calcular Estrategias")
        self.calculate_strategy_button.setObjectName("PrimaryAction")
        control_layout.addWidget(self.calculate_strategy_button)
        control_layout.addStretch()
        main_layout.addWidget(control_card)

        plans_layout = QHBoxLayout()
        plans_layout.setSpacing(20)

        snowball_card = QFrame(); snowball_card.setObjectName("Card")
        snowball_layout = QVBoxLayout(snowball_card)
        snowball_layout.addWidget(QLabel("<b>Método Bola de Nieve (Menor Saldo Primero)</b>"))
        self.snowball_summary_label = QLabel("Pagarás todo en: N/A")
        snowball_layout.addWidget(self.snowball_summary_label)
        self.snowball_table = QTableWidget()
        snowball_layout.addWidget(self.snowball_table)

        avalanche_card = QFrame(); avalanche_card.setObjectName("Card")
        avalanche_layout = QVBoxLayout(avalanche_card)
        avalanche_layout.addWidget(QLabel("<b>Método Avalancha (Mayor Interés Primero)</b>"))
        self.avalanche_summary_label = QLabel("Pagarás todo en: N/A")
        avalanche_layout.addWidget(self.avalanche_summary_label)
        self.avalanche_table = QTableWidget()
        avalanche_layout.addWidget(self.avalanche_table)
        
        plans_layout.addWidget(snowball_card)
        plans_layout.addWidget(avalanche_card)
        
        main_layout.addLayout(plans_layout, 1)
        return widget

    def _create_form_card(self, title):
        card = QFrame(); card.setObjectName("Card")
        layout = QFormLayout(card)
        layout.setContentsMargins(15, 15, 15, 15); layout.setSpacing(10)
        
        title_label = QLabel(f"<b>{title}</b>"); title_label.setStyleSheet("margin-bottom: 10px;")
        layout.addRow(title_label)

        if "Meta" in title:
            self.goal_name_input = QLineEdit()
            self.goal_target_input = QLineEdit()
            self.goal_target_input.setMaxLength(15)
            self.add_goal_button = QPushButton("Añadir Meta"); self.add_goal_button.setObjectName("PrimaryAction")
            layout.addRow("Nombre de la Meta:", self.goal_name_input)
            layout.addRow("Monto Objetivo:", self.goal_target_input)
            layout.addRow(self.add_goal_button)
        else:
            self.debt_name_input = QLineEdit()
            self.debt_total_input = QLineEdit()
            self.debt_total_input.setMaxLength(15)
            self.debt_min_payment_input = QLineEdit()
            self.debt_min_payment_input.setMaxLength(15)
            self.debt_interest_rate_input = QDoubleSpinBox()
            self.debt_interest_rate_input.setSuffix(" %")
            self.debt_interest_rate_input.setRange(0, 100)
            self.add_debt_button = QPushButton("Añadir Deuda"); self.add_debt_button.setObjectName("PrimaryAction")
            layout.addRow("Nombre de la Deuda:", self.debt_name_input)
            layout.addRow("Monto Total:", self.debt_total_input)
            layout.addRow("Pago Mínimo:", self.debt_min_payment_input)
            layout.addRow("Tasa de Interés Anual:", self.debt_interest_rate_input)
            layout.addRow(self.add_debt_button)
            
        return card

    def _create_list_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("ListScrollArea")
        
        scroll_content = QWidget()
        list_layout = QVBoxLayout(scroll_content)
        list_layout.setContentsMargins(5, 5, 5, 5)
        list_layout.setSpacing(10)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        return widget, list_layout


    def display_goals(self, goals):
        self._clear_layout(self.goals_list_layout)

        # --- INICIO DE LA SOLUCIUÓN ---
        delay = 0
        for goal_data in goals:
            goal_item = GoalItem(goal_data, self.controller)
            goal_item.edit_requested.connect(self.edit_goal_requested)
            goal_item.delete_requested.connect(self.delete_goal_requested)

            # 1. Preparar el widget para la animación
            opacity_effect = QGraphicsOpacityEffect(goal_item)
            goal_item.setGraphicsEffect(opacity_effect)
            goal_item.graphicsEffect().setOpacity(0) # Inicia invisible

            self.goals_list_layout.addWidget(goal_item)

            # 2. Crear la animación
            anim = QPropertyAnimation(goal_item.graphicsEffect(), b"opacity")
            anim.setDuration(400)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

            # 3. Ejecutar la animación con un pequeño retraso para un efecto escalonado
            QTimer.singleShot(delay, anim.start)
            delay += 50 # Cada item aparece 50ms después del anterior
        # --- FIN DE LA SOLUCIUÓN ---

        self.goals_list_layout.addStretch()

    def display_debts(self, debts):
        self._clear_layout(self.debts_list_layout)
        for debt_data in debts:
            # Asegúrate de que se pasa self.controller aquí
            debt_item = DebtItem(debt_data, self.controller) 
            debt_item.edit_requested.connect(self.edit_debt_requested)
            debt_item.delete_requested.connect(self.delete_debt_requested)
            self.debts_list_layout.addWidget(debt_item)
        self.debts_list_layout.addStretch()
        
    def _clear_layout(self, layout):
        while (item := layout.takeAt(0)) is not None:
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                pass

    def get_goal_form_data(self):
        return {"name": self.goal_name_input.text(), "target_amount": self.goal_target_input.text()}

    def get_debt_form_data(self):
        return {
            "name": self.debt_name_input.text(), 
            "total_amount": self.debt_total_input.text(), 
            "minimum_payment": self.debt_min_payment_input.text(),
            "interest_rate": self.debt_interest_rate_input.value()
        }
    
    def clear_goal_form(self):
        self.goal_name_input.clear()
        self.goal_target_input.clear()

    def clear_debt_form(self):
        self.debt_name_input.clear()
        self.debt_total_input.clear()
        self.debt_min_payment_input.clear()
        self.debt_interest_rate_input.setValue(0)

    def display_strategy_plan(self, table, plan_data, summary_text):
        summary_label = self.snowball_summary_label if table == self.snowball_table else self.avalanche_summary_label
        summary_label.setText(f"<b>{summary_text}</b>")
        
        table.clear()
        table.setRowCount(len(plan_data))
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Fecha de Pago", "Deuda Liquidada", "Saldo Total Restante"])
        
        for row, step in enumerate(plan_data):
            table.setItem(row, 0, QTableWidgetItem(step['date']))
            table.setItem(row, 1, QTableWidgetItem(step['paid_off']))
            table.setItem(row, 2, QTableWidgetItem(f"${step['remaining_balance']:,.2f}"))
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)