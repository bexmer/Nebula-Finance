from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QGridLayout, QComboBox, QPushButton, QMenu, QProgressBar,
                               QTableWidget, QTableWidgetItem, QHeaderView, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QAction, QFont, QColor
import pyqtgraph as pg
import qtawesome as qta
from datetime import datetime

# --- INICIO DE LA SOLUCIÓN: Tarjeta de Crédito con Logo y Botón de Visibilidad ---
class CreditCardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CreditCardFrame")
        self.setFixedSize(280, 170)
        
        self._balance_hidden = False
        self._current_account = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)

        self.balance_label = QLabel("$0.00")
        self.balance_label.setObjectName("CardBalance")

        self.visibility_button = QPushButton()
        self.visibility_button.setObjectName("CardVisibilityButton")
        self.visibility_button.setFixedSize(30, 30)
        self.visibility_button.clicked.connect(self.toggle_balance_visibility)
        
        self.card_type_label = QLabel("NEBULA")
        self.card_type_label.setObjectName("CardType")
        self.card_type_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.balance_label)
        top_layout.addStretch()
        top_layout.addWidget(self.visibility_button)
        top_layout.addWidget(self.card_type_label)
        
        self.card_number_label = QLabel("**** **** **** 0000")
        self.card_number_label.setObjectName("CardNumber")

        self.holder_name_label = QLabel("N/A")
        self.holder_name_label.setObjectName("CardMainText")
        self.type_name_label = QLabel("N/A")
        self.type_name_label.setObjectName("CardSubText")
        self.type_name_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.holder_name_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.type_name_label)

        layout.addLayout(top_layout)
        layout.addStretch(1)
        layout.addWidget(self.card_number_label)
        layout.addStretch(1)
        layout.addLayout(bottom_layout)
        
        self.update_visibility_icon()

    def set_data(self, account):
        self._current_account = account
        self.update_display()

    def update_display(self):
        if self._current_account:
            if self._balance_hidden:
                self.balance_label.setText("$ * * * * * * * *")
            else:
                self.balance_label.setText(f"${self._current_account.current_balance:,.2f}")
            self.holder_name_label.setText(self._current_account.name)
            self.type_name_label.setText(self._current_account.account_type)
        else:
            self.balance_label.setText("$0.00")
            self.holder_name_label.setText("Sin Cuentas")
            self.type_name_label.setText("N/A")
    
    def toggle_balance_visibility(self):
        self._balance_hidden = not self._balance_hidden
        self.update_display()
        self.update_visibility_icon()

    def update_visibility_icon(self):
        icon_name = 'fa5s.eye-slash' if self._balance_hidden else 'fa5s.eye'
        self.visibility_button.setIcon(qta.icon(icon_name, color='white'))
# --- FIN DE LA SOLUCIÓN ---

class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        strings = []
        for value in values:
            try:
                strings.append(datetime.fromtimestamp(value).strftime('%b %Y'))
            except (OSError, ValueError):
                strings.append('')
        return strings

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        pg.setConfigOption('background', 'transparent')
        
        self.fg_color = '#364765'

        # 1. Contenedor Principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 2. Barra del Título
        header_layout = QHBoxLayout()
        title_label = QLabel("Dashboard")
        title_label.setObjectName("DashboardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        current_year = QDate.currentDate().year()
        self.year_filter = QComboBox()
        self.year_filter.addItems([str(y) for y in range(current_year - 5, current_year + 2)])
        self.year_filter.setCurrentText(str(current_year))
        self.month_filter_button = QPushButton("Mes Actual")
        self._create_month_menu()
        header_layout.addWidget(QLabel("Año:"))
        header_layout.addWidget(self.year_filter)
        header_layout.addWidget(QLabel("Mes:"))
        header_layout.addWidget(self.month_filter_button)
        main_layout.addLayout(header_layout)

        # 3. Creación de todos los widgets
        self.income_kpi = self._create_kpi_card("Ganancias", "$0.00")
        self.expense_kpi = self._create_kpi_card("Gastos", "$0.00")
        self.net_kpi = self._create_kpi_card("Ahorro Neto", "$0.00")
        self.net_worth_chart_card = self._create_chart_card("Evolución de Patrimonio Neto", axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.budget_rule_card = self._create_chart_card("Control de Gastos", has_plot_widget=False)
        self.budget_income_card = self._create_metric_card("Ingresos")
        self.budget_expense_card = self._create_metric_card("Gastos")
        self.main_goals_card = self._create_chart_card("Metas", has_plot_widget=False)
        self.expense_dist_card = self._create_chart_card("Distribución de Gastos")
        self.accounts_card = self._create_accounts_card_container()
        self.current_account_index = 0
        self.accounts_list = []
        self.expense_type_chart_card = self._create_chart_card("Comparación de Gastos por Tipo", plot_type="pie")

        # 4. Construcción del Layout Anidado
        purple_main_layout = QHBoxLayout()
        purple_main_layout.setSpacing(15)
        main_layout.addLayout(purple_main_layout, 1)

        purple_left_widget = QWidget()
        purple_left_layout = QVBoxLayout(purple_left_widget)
        purple_left_layout.setContentsMargins(0, 0, 0, 0)
        purple_left_layout.setSpacing(15)
        purple_main_layout.addWidget(purple_left_widget, 2)

        purple_right_widget = QWidget()
        purple_right_layout = QVBoxLayout(purple_right_widget)
        purple_right_layout.setContentsMargins(0, 0, 0, 0)
        purple_right_layout.setSpacing(15)
        purple_main_layout.addWidget(purple_right_widget, 1)

        red_top_widget = QWidget()
        red_top_layout = QHBoxLayout(red_top_widget)
        red_top_layout.setContentsMargins(0, 0, 0, 0)
        red_top_layout.setSpacing(15)
        purple_left_layout.addWidget(red_top_widget, 2)

        red_bottom_widget = QWidget()
        red_bottom_layout = QHBoxLayout(red_bottom_widget)
        red_bottom_layout.setContentsMargins(0, 0, 0, 0)
        red_bottom_layout.setSpacing(15)
        purple_left_layout.addWidget(red_bottom_widget, 1)

        green_top_left_layout = QVBoxLayout()
        red_top_layout.addLayout(green_top_left_layout, 2)
        red_top_layout.addWidget(self.budget_rule_card, 1)

        green_bottom_left_layout = QVBoxLayout()
        red_bottom_layout.addLayout(green_bottom_left_layout, 1)
        red_bottom_layout.addWidget(self.expense_dist_card, 1)

        kpi_layout = QHBoxLayout()
        kpi_layout.addWidget(self.income_kpi); kpi_layout.addWidget(self.expense_kpi); kpi_layout.addWidget(self.net_kpi)
        green_top_left_layout.addLayout(kpi_layout, 1)
        green_top_left_layout.addWidget(self.net_worth_chart_card, 2)

        budget_vs_real_layout = QHBoxLayout()
        budget_vs_real_layout.addWidget(self.budget_income_card); budget_vs_real_layout.addWidget(self.budget_expense_card)
        green_bottom_left_layout.addLayout(budget_vs_real_layout)
        green_bottom_left_layout.addWidget(self.main_goals_card)

        purple_right_layout.addWidget(self.accounts_card, 1)
        purple_right_layout.addWidget(self.expense_type_chart_card, 2)
        
        self.quick_add_button = QPushButton("+")
        self.quick_add_button.setObjectName("QuickAddButton")
        self.quick_add_button.setFixedSize(QSize(46, 46))
        self.quick_add_button.setParent(self)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25); shadow.setColor(QColor(0, 0, 0, 90)); shadow.setOffset(0, 5)
        self.quick_add_button.setGraphicsEffect(shadow)
    
    def showEvent(self, event):
        super().showEvent(event)
        for card in self.findChildren(QFrame):
            if "Card" in card.objectName() and not card.graphicsEffect():
                self._apply_shadow_to_card(card)

    def _apply_shadow_to_card(self, card):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20); shadow.setColor(QColor(0, 0, 0, 30)); shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        button_size = self.quick_add_button.size()
        self.quick_add_button.move(self.width() - button_size.width() - 20, self.height() - button_size.height() - 20)

    def _create_kpi_card(self, title, default_value):
        card = QFrame(); card.setObjectName("KPI_Card")
        layout = QVBoxLayout(card); layout.setContentsMargins(15, 10, 15, 10); layout.setSpacing(4)
        title_label = QLabel(title); title_label.setObjectName("KPI_Title")
        value_label = QLabel(default_value); value_label.setObjectName("KPI_Value")
        comparison_label = QLabel(""); comparison_label.setObjectName("KPI_Comparison")
        layout.addWidget(title_label); layout.addWidget(value_label); layout.addWidget(comparison_label); layout.addStretch()
        card.value_label, card.comparison_label = value_label, comparison_label
        return card
        
    def _create_metric_card(self, title):
        card = QFrame(); card.setObjectName("MetricCard")
        layout = QVBoxLayout(card); layout.setContentsMargins(12, 12, 12, 12); layout.setSpacing(5)
        title_label = QLabel(title); title_label.setObjectName("MetricTitle")
        value_label = QLabel("$0.00"); value_label.setObjectName("MetricValue")
        comparison_label = QLabel("Real: $0.00"); comparison_label.setObjectName("MetricComparison")
        layout.addWidget(title_label); layout.addWidget(value_label); layout.addWidget(comparison_label); layout.addStretch()
        card.value_label, card.comparison_label = value_label, comparison_label
        return card

    def _create_chart_card(self, title, has_plot_widget=True, axisItems=None, plot_type="bar"):
        card = QFrame(); card.setObjectName("Card")
        layout = QVBoxLayout(card); layout.setContentsMargins(12, 12, 12, 12); layout.setSpacing(8)
        title_label = QLabel(title); title_label.setObjectName("Chart_Title"); layout.addWidget(title_label)
        if has_plot_widget:
            if plot_type == "pie":
                plot_widget = pg.PlotWidget() 
                plot_widget.setAspectLocked(True)
                plot_widget.hideAxis('left')
                plot_widget.hideAxis('bottom')
                layout.addWidget(plot_widget, 1)
                card.plot_widget = plot_widget 
            else: 
                plot_widget = pg.PlotWidget(axisItems=axisItems); plot_widget.showGrid(x=True, y=True, alpha=0.1); layout.addWidget(plot_widget, 1)
                card.plot_widget = plot_widget
        else:
            content_layout = QVBoxLayout(); content_layout.setSpacing(8); layout.addLayout(content_layout, 1)
            card.content_layout = content_layout
        return card
    
    def _create_accounts_card_container(self):
        card = QFrame(); card.setObjectName("Card")
        main_card_layout = QVBoxLayout(card)
        main_card_layout.setContentsMargins(12, 12, 12, 12)
        main_card_layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Cuentas"), 0, Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()
        
        self.prev_account_btn = QPushButton("<")
        self.prev_account_btn.setObjectName("CardNavButton")
        self.prev_account_btn.setFixedSize(25, 25)
        self.prev_account_btn.clicked.connect(self.show_previous_account)
        
        self.next_account_btn = QPushButton(">")
        self.next_account_btn.setObjectName("CardNavButton")
        self.next_account_btn.setFixedSize(25, 25)
        self.next_account_btn.clicked.connect(self.show_next_account)

        header_layout.addWidget(self.prev_account_btn)
        header_layout.addWidget(self.next_account_btn)
        main_card_layout.addLayout(header_layout)

        self.credit_card_widget = CreditCardWidget()
        card_container_layout = QHBoxLayout()
        card_container_layout.addStretch()
        card_container_layout.addWidget(self.credit_card_widget)
        card_container_layout.addStretch()
        main_card_layout.addLayout(card_container_layout, 1)
        
        return card
        
    def show_next_account(self):
        if not self.accounts_list: return
        self.current_account_index = (self.current_account_index + 1) % len(self.accounts_list)
        self._display_current_account()

    def show_previous_account(self):
        if not self.accounts_list: return
        self.current_account_index = (self.current_account_index - 1 + len(self.accounts_list)) % len(self.accounts_list)
        self._display_current_account()

    def _display_current_account(self):
        if self.accounts_list:
            account = self.accounts_list[self.current_account_index]
            self.credit_card_widget.set_data(account)
        else:
            self.credit_card_widget.set_data(None)

    def update_accounts_card(self, accounts):
        self.accounts_list = accounts
        if self.current_account_index >= len(accounts):
            self.current_account_index = 0
        self._display_current_account()

    def update_budget_vs_real_cards(self, income_data, expense_data):
        self.budget_income_card.value_label.setText(f"${income_data['budgeted_amount']:,.2f}")
        self.budget_income_card.comparison_label.setText(f"Real: ${income_data['real_amount']:,.2f}")
        self.budget_expense_card.value_label.setText(f"${expense_data['budgeted_amount']:,.2f}")
        self.budget_expense_card.comparison_label.setText(f"Real: ${expense_data['real_amount']:,.2f}")
        
    def update_kpis(self, income, expense, net_flow, income_comp=None, expense_comp=None):
        self.income_kpi.value_label.setText(f"${income:,.2f}")
        self.expense_kpi.value_label.setText(f"${expense:,.2f}")
        self.net_kpi.value_label.setText(f"${net_flow:,.2f}")
        def format_comp(value, lower_is_better=False):
            if value is None: return ""
            prefix = "▲ " if value >= 0 else "▼ "
            color = "#28A745" if (value >= 0 and not lower_is_better) or (value < 0 and lower_is_better) else "#DC3545"
            return f"<font color='{color}'>{prefix}{abs(value):.1f}%</font>"
        self.income_kpi.comparison_label.setText(format_comp(income_comp))
        self.expense_kpi.comparison_label.setText(format_comp(expense_comp, lower_is_better=True))

    def update_main_goals(self, goals):
        self._clear_layout(self.main_goals_card.content_layout)
        if not goals:
            self.main_goals_card.content_layout.addWidget(QLabel("No hay metas activas."))
            return
        for goal in goals:
            self.main_goals_card.content_layout.addWidget(self._create_goal_bar(goal))
        self.main_goals_card.content_layout.addStretch()

    def _create_goal_bar(self, goal_data):
        widget = QWidget()
        widget.setObjectName("GoalBarContainer")
        layout = QVBoxLayout(widget)
        
        title_layout = QHBoxLayout(); name_label = QLabel(f"<b>{goal_data['name']}</b>")
        percentage = (goal_data['current'] / goal_data['target']) * 100 if goal_data['target'] > 0 else 0
        amount_label = QLabel(f"<b>{percentage:.1f}%</b>")
        title_layout.addWidget(name_label); title_layout.addStretch(); title_layout.addWidget(amount_label)
        
        progress_bar = QProgressBar(); progress_bar.setValue(int(percentage));
        progress_bar.setTextVisible(False)
        progress_bar.setProperty("state", "good"); progress_bar.style().polish(progress_bar)
        
        layout.addLayout(title_layout); layout.addWidget(progress_bar)
        return widget

    def update_upcoming_payments(self, payments):
        pass

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None: widget.deleteLater()
                else:
                    child_layout = item.layout()
                    if child_layout is not None: self._clear_layout(child_layout)

    def update_budget_rule_chart(self, data):
        self._clear_layout(self.budget_rule_card.content_layout)
        for item in data:
            bar = self._create_budget_bar(item)
            self.budget_rule_card.content_layout.addWidget(bar)
        self.budget_rule_card.content_layout.addStretch()

    def _create_budget_bar(self, item_data):
        widget = QWidget()
        widget.setObjectName("BudgetBarContainer")
        layout = QVBoxLayout(widget)
        
        title_layout = QHBoxLayout()
        name_label = QLabel(f"<b>{item_data['name']}</b> ({item_data['ideal_percent']:.0f}%)")
        
        if item_data['state'] == 'critical':
            amount_label = QLabel(f"<font color='#E06C75'>Excedido</font>")
        else:
            amount_label = QLabel(f"${item_data['actual_amount']:,.2f}")

        title_layout.addWidget(name_label); title_layout.addStretch(); title_layout.addWidget(amount_label)

        progress_bar = QProgressBar()
        progress_bar.setTextVisible(False)
        
        if item_data['is_overdrawn']:
            progress_bar.setValue(100)
        else:
            progress_bar.setValue(min(100, int(item_data['actual_percent'])))
        
        progress_bar.setProperty("state", item_data['state'])
        progress_bar.style().polish(progress_bar)

        layout.addLayout(title_layout)
        layout.addWidget(progress_bar)
        
        percent_label = QLabel(f"{item_data['actual_percent']:.1f}% del ingreso")
        percent_label.setObjectName("BudgetPercentLabel")
        percent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(percent_label)

        return widget

    def update_chart_themes(self, is_dark_mode):
        if is_dark_mode:
            self.fg_color = '#EAEAEA'
            accent_color = '#8A9BFF'
        else:
            self.fg_color = '#364765'
            accent_color = '#364765'

        axis_pen = pg.mkPen(color=self.fg_color)
        
        for plot_widget in [self.net_worth_chart_card.plot_widget, self.expense_dist_card.plot_widget, self.expense_type_chart_card.plot_widget]:
            if plot_widget:
                if plot_widget != self.expense_type_chart_card.plot_widget:
                    plot_widget.getPlotItem().getAxis('left').setPen(axis_pen)
                    plot_widget.getPlotItem().getAxis('left').setTextPen(self.fg_color)
                    plot_widget.getPlotItem().getAxis('bottom').setPen(axis_pen)
                    plot_widget.getPlotItem().getAxis('bottom').setTextPen(self.fg_color)
                
                if plot_widget.listDataItems():
                    if isinstance(plot_widget.listDataItems()[0], pg.BarGraphItem):
                        plot_widget.listDataItems()[0].setOpts(brush=accent_color)
                    elif isinstance(plot_widget.listDataItems()[0], pg.PlotDataItem):
                        plot_widget.listDataItems()[0].setPen(pg.mkPen(color=accent_color, width=3))
    
    def _create_month_menu(self):
        self.month_menu = QMenu(self); self.month_actions = []
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.all_year_action = QAction("Todo el Año", self); self.all_year_action.setCheckable(True); self.month_menu.addAction(self.all_year_action); self.month_menu.addSeparator()
        for i, month in enumerate(months): action = QAction(month, self); action.setCheckable(True); action.setData(i + 1); self.month_actions.append(action); self.month_menu.addAction(action)
        self.month_filter_button.setMenu(self.month_menu)
        self.all_year_action.triggered.connect(self._handle_all_year_selection)
        for a in self.month_actions: a.triggered.connect(self._update_month_button_text)

    def _handle_all_year_selection(self):
        for action in self.month_actions: action.setChecked(self.all_year_action.isChecked())
        self._update_month_button_text()
    
    def _update_month_button_text(self):
        selected_months = [a.text() for a in self.month_actions if a.isChecked()]
        if not selected_months: self.month_filter_button.setText("Ningún Mes")
        elif len(selected_months) == 1: self.month_filter_button.setText(selected_months[0]); self.all_year_action.setChecked(False)
        elif len(selected_months) == 12: self.month_filter_button.setText("Todo el Año"); self.all_year_action.setChecked(True)
        else: self.month_filter_button.setText(f"{len(selected_months)} Meses Seleccionados")
        if not all(a.isChecked() for a in self.month_actions) and self.all_year_action.isChecked(): self.all_year_action.setChecked(False)
        self.year_filter.currentTextChanged.emit(self.year_filter.currentText()) 

    def get_selected_filters(self):
        return { "year": int(self.year_filter.currentText()), "months": [a.data() for a in self.month_actions if a.isChecked()] }

    def set_default_month_filter(self):
        current_month_index = QDate.currentDate().month() - 1
        if 0 <= current_month_index < len(self.month_actions):
            self.month_actions[current_month_index].setChecked(True)
        self._update_month_button_text()
    
    def update_net_worth_chart(self, dates, values):
        plot_widget = self.net_worth_chart_card.plot_widget; plot_widget.clear()
        if dates and values:
            timestamps = [datetime.strptime(str(d), "%Y%m%d").timestamp() for d in dates]
            pen_color = '#61AFEF' if self.styleSheet().startswith("DARK_STYLE") else '#364765'
            plot_widget.plot(timestamps, values, pen=pg.mkPen(color=pen_color, width=3))
    
    def update_expense_dist_chart(self, categories, amounts):
        plot_widget = self.expense_dist_card.plot_widget; plot_widget.clear()
        if categories and amounts:
            x_ticks = [list(enumerate(categories))]; axis = plot_widget.getAxis('bottom'); axis.setTicks(x_ticks); axis.setTickFont(QFont("Segoe UI", 8))
            brush_color = '#61AFEF' if self.styleSheet().startswith("DARK_STYLE") else '#364765'
            bar_chart = pg.BarGraphItem(x=range(len(categories)), height=amounts, width=0.6, brush=brush_color); plot_widget.addItem(bar_chart)
    
    def clear_expense_dist_chart(self):
        self.expense_dist_card.plot_widget.clear()
    
    def clear_budget_rule_chart(self):
        self._clear_layout(self.budget_rule_card.content_layout)

    def update_expense_type_chart(self, categories, amounts):
        plot_widget = self.expense_type_chart_card.plot_widget
        plot_widget.clear()
        
        if not categories or not amounts:
            text_item = pg.TextItem("Sin datos de gastos", color=QColor(self.fg_color), anchor=(0.5, 0.5))
            plot_widget.addItem(text_item)
            return

        total_amount = sum(amounts)
        percentages = [(amount / total_amount) for amount in amounts]

        colors = [
            QColor(97, 175, 239, 200), QColor(152, 195, 121, 200),
            QColor(229, 192, 123, 200), QColor(224, 108, 117, 200),
            QColor(198, 120, 221, 200), QColor(84, 110, 122, 200)
        ]

        start_angle = 90
        for i, (category, percentage) in enumerate(zip(categories, percentages)):
            if percentage > 0:
                span_angle = percentage * 360
                
                item = pg.QtGui.QGraphicsEllipseItem(-0.5, -0.5, 1, 1)
                item.setStartAngle(int(start_angle * 16))
                item.setSpanAngle(int(span_angle * 16))
                item.setBrush(colors[i % len(colors)])
                item.setPen(pg.mkPen(None))
                plot_widget.addItem(item)

                start_angle += span_angle
        
        inner_circle = pg.QtGui.QGraphicsEllipseItem(-0.35, -0.35, 0.7, 0.7)
        inner_circle.setBrush(self.palette().window().color())
        inner_circle.setPen(pg.mkPen(None))
        plot_widget.addItem(inner_circle)

    def clear_expense_type_chart(self):
        self.expense_type_chart_card.plot_widget.clear()