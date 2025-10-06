from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, QPushButton,
    QMenu, QProgressBar, QGraphicsDropShadowEffect, QGridLayout, QStackedWidget
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QAction, QFont, QColor, QBrush
import pyqtgraph as pg
import qtawesome as qta
from datetime import datetime


# ---------------- Tarjeta de crédito ----------------
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
        self.card_type_label.setAlignment(Qt.AlignRight)

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
        self.type_name_label.setAlignment(Qt.AlignRight)

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


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        try:
            return [datetime.fromtimestamp(v).strftime('%b %Y') for v in values]
        except Exception:
            return ['' for v in values]


# ==========================
#        DASHBOARD
# ==========================
class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        pg.setConfigOption('background', 'transparent')

        self.fg_color = '#364765'  # actualizado por update_chart_themes

        # -------- Header --------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

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

        # -------- Cards --------
        self.income_kpi = self._create_kpi_card("Ganancias", "$0.00")
        self.expense_kpi = self._create_kpi_card("Gastos", "$0.00")
        self.net_kpi = self._create_kpi_card("Ahorro Neto", "$0.00")

        self.switchable_chart_card = self._create_switchable_chart_card()

        self.budget_rule_card = self._create_chart_card("Control de Gastos", has_plot_widget=False)
        self.budget_income_card = self._create_metric_card("Ingresos PPTO")
        self.budget_expense_card = self._create_metric_card("Gastos PPTO")
        self.main_goals_card = self._create_chart_card("Metas", has_plot_widget=False)
        self.expense_dist_card = self._create_chart_card("Distribución de Gastos")
        self.accounts_card = self._create_accounts_card_container()
        self.expense_type_chart_card = self._create_chart_card(
            "Gastos por Tipo", plot_type="pie"
        )
        self._legend_widgets = []

        # -------- Layout original restaurado --------
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
        kpi_layout.addWidget(self.income_kpi)
        kpi_layout.addWidget(self.expense_kpi)
        kpi_layout.addWidget(self.net_kpi)
        green_top_left_layout.addLayout(kpi_layout, 1)
        
        green_top_left_layout.addWidget(self.switchable_chart_card, 2)

        budget_vs_real_layout = QHBoxLayout()
        budget_vs_real_layout.addWidget(self.budget_income_card)
        budget_vs_real_layout.addWidget(self.budget_expense_card)
        green_bottom_left_layout.addLayout(budget_vs_real_layout)
        green_bottom_left_layout.addWidget(self.main_goals_card)

        purple_right_layout.addWidget(self.accounts_card, 1)
        purple_right_layout.addWidget(self.expense_type_chart_card, 2)

        # Botón flotante
        self.quick_add_button = QPushButton("+")
        self.quick_add_button.setObjectName("QuickAddButton")
        self.quick_add_button.setFixedSize(QSize(46, 46))
        self.quick_add_button.setParent(self)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 5)
        self.quick_add_button.setGraphicsEffect(shadow)

    def _create_switchable_chart_card(self):
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        self.switchable_chart_title = QLabel("Evolución de Patrimonio Neto")
        self.switchable_chart_title.setObjectName("Chart_Title")
        
        self.prev_chart_btn = QPushButton()
        self.prev_chart_btn.setIcon(qta.icon('fa5s.chevron-left'))
        self.prev_chart_btn.setObjectName("CardNavButton")
        self.prev_chart_btn.setFixedSize(25, 25)
        self.prev_chart_btn.clicked.connect(self.show_previous_chart)

        self.next_chart_btn = QPushButton()
        self.next_chart_btn.setIcon(qta.icon('fa5s.chevron-right'))
        self.next_chart_btn.setObjectName("CardNavButton")
        self.next_chart_btn.setFixedSize(25, 25)
        self.next_chart_btn.clicked.connect(self.show_next_chart)
        
        header_layout.addWidget(self.switchable_chart_title)
        header_layout.addStretch()
        header_layout.addWidget(self.prev_chart_btn)
        header_layout.addWidget(self.next_chart_btn)
        layout.addLayout(header_layout)

        self.chart_stack = QStackedWidget()
        
        self.net_worth_plot = pg.PlotWidget(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.net_worth_plot.showGrid(x=True, y=True, alpha=0.1)
        
        self.cash_flow_plot = pg.PlotWidget()
        self.cash_flow_plot.showGrid(x=True, y=True, alpha=0.1)

        self.chart_stack.addWidget(self.net_worth_plot)
        self.chart_stack.addWidget(self.cash_flow_plot)
        
        layout.addWidget(self.chart_stack)
        
        self.current_chart_index = 0
        self.chart_titles = ["Evolución de Patrimonio Neto", "Flujo de Efectivo Mensual"]
        
        return card

    def show_next_chart(self):
        self.current_chart_index = (self.current_chart_index + 1) % self.chart_stack.count()
        self.chart_stack.setCurrentIndex(self.current_chart_index)
        self.switchable_chart_title.setText(self.chart_titles[self.current_chart_index])

    def show_previous_chart(self):
        self.current_chart_index = (self.current_chart_index - 1 + self.chart_stack.count()) % self.chart_stack.count()
        self.chart_stack.setCurrentIndex(self.current_chart_index)
        self.switchable_chart_title.setText(self.chart_titles[self.current_chart_index])

    def showEvent(self, event):
        super().showEvent(event)
        for card in self.findChildren(QFrame):
            if "Card" in card.objectName() and not card.graphicsEffect():
                self._apply_shadow_to_card(card)

    def _apply_shadow_to_card(self, card):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        button_size = self.quick_add_button.size()
        self.quick_add_button.move(self.width() - button_size.width() - 20,
                                   self.height() - button_size.height() - 20)

    def _create_kpi_card(self, title, default_value):
        card = QFrame()
        card.setObjectName("KPI_Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("KPI_Title")
        value_label = QLabel(default_value)
        value_label.setObjectName("KPI_Value")
        comparison_label = QLabel("")
        comparison_label.setObjectName("KPI_Comparison")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(comparison_label)
        card.value_label, card.comparison_label = value_label, comparison_label
        return card

    def _create_metric_card(self, title):
        card = QFrame()
        card.setObjectName("MetricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(5)
        title_label = QLabel(title)
        title_label.setObjectName("MetricTitle")
        value_label = QLabel("$0.00")
        value_label.setObjectName("MetricValue")
        comparison_label = QLabel("Real: $0.00")
        comparison_label.setObjectName("MetricComparison")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(comparison_label)
        layout.addStretch()
        card.value_label, card.comparison_label = value_label, comparison_label
        return card

    def _create_chart_card(self, title, has_plot_widget=True, axisItems=None, plot_type="bar"):
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("Chart_Title")
        layout.addWidget(title_label)
        if has_plot_widget:
            if plot_type == "pie":
                legend_container = QFrame()
                legend_container.setObjectName("LegendContainer")
                legend_layout = QGridLayout(legend_container)
                legend_layout.setContentsMargins(0, 0, 0, 6)
                legend_layout.setHorizontalSpacing(24)
                legend_layout.setVerticalSpacing(6)
                layout.addWidget(legend_container)
                card.legend_container = legend_container
                card.legend_layout = legend_layout
                plot_widget = pg.PlotWidget()
                plot_widget.setAspectLocked(True)
                plot_widget.hideAxis('left')
                plot_widget.hideAxis('bottom')
                layout.addWidget(plot_widget, 1)
                card.plot_widget = plot_widget
            else:
                plot_widget = pg.PlotWidget(axisItems=axisItems)
                plot_widget.showGrid(x=True, y=True, alpha=0.1)
                layout.addWidget(plot_widget, 1)
                card.plot_widget = plot_widget
        else:
            content_layout = QVBoxLayout()
            content_layout.setSpacing(8)
            layout.addLayout(content_layout, 1)
            card.content_layout = content_layout
        return card

    def _create_accounts_card_container(self):
        card = QFrame()
        card.setObjectName("Card")
        main_card_layout = QVBoxLayout(card)
        main_card_layout.setContentsMargins(12, 12, 12, 12)
        main_card_layout.setSpacing(8)
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Cuentas"), 0, Qt.AlignLeft)
        header_layout.addStretch()
        self.prev_account_btn = QPushButton()
        self.prev_account_btn.setIcon(qta.icon('fa5s.chevron-left'))
        self.prev_account_btn.setObjectName("CardNavButton")
        self.prev_account_btn.setFixedSize(25, 25)
        self.prev_account_btn.clicked.connect(self.show_previous_account)
        self.next_account_btn = QPushButton()
        self.next_account_btn.setIcon(qta.icon('fa5s.chevron-right'))
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
        if not hasattr(self, 'accounts_list') or not self.accounts_list: return
        self.current_account_index = (self.current_account_index + 1) % len(self.accounts_list)
        self._display_current_account()

    def show_previous_account(self):
        if not hasattr(self, 'accounts_list') or not self.accounts_list: return
        self.current_account_index = (self.current_account_index - 1 + len(self.accounts_list)) % len(self.accounts_list)
        self._display_current_account()

    def _display_current_account(self):
        if hasattr(self, 'accounts_list') and self.accounts_list:
            account = self.accounts_list[self.current_account_index]
            self.credit_card_widget.set_data(account)
        else:
            self.credit_card_widget.set_data(None)

    def update_accounts_card(self, accounts):
        self.accounts_list = accounts
        if not hasattr(self, 'current_account_index') or self.current_account_index >= len(accounts):
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
        widget = QWidget(); widget.setObjectName("GoalBarContainer")
        layout = QVBoxLayout(widget)
        title_layout = QHBoxLayout()
        name_label = QLabel(f"<b>{goal_data['name']}</b>")
        percentage = (goal_data['current'] / goal_data['target']) * 100 if goal_data['target'] > 0 else 0
        amount_label = QLabel(f"<b>{percentage:.1f}%</b>")
        title_layout.addWidget(name_label); title_layout.addStretch(); title_layout.addWidget(amount_label)
        progress_bar = QProgressBar(); progress_bar.setValue(int(percentage)); progress_bar.setTextVisible(False)
        progress_bar.setProperty("state", "good"); progress_bar.style().polish(progress_bar)
        layout.addLayout(title_layout); layout.addWidget(progress_bar)
        return widget

    def update_upcoming_payments(self, payments):
        pass

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None: w.deleteLater()
                else:
                    child_layout = item.layout()
                    if child_layout is not None: self._clear_layout(child_layout)

    def _clear_legend(self, layout):
        if layout is None: return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()
        self._legend_widgets = []

    def update_budget_rule_chart(self, data):
        self._clear_layout(self.budget_rule_card.content_layout)
        for item in data:
            bar = self._create_budget_bar(item)
            self.budget_rule_card.content_layout.addWidget(bar)
        self.budget_rule_card.content_layout.addStretch()

    def _create_budget_bar(self, item_data):
        widget = QWidget(); widget.setObjectName("BudgetBarContainer")
        layout = QVBoxLayout(widget)
        title_layout = QHBoxLayout()
        name_label = QLabel(f"<b>{item_data['name']}</b> ({item_data['ideal_percent']:.0f}%)")
        amount_label = QLabel(f"${item_data['actual_amount']:,.2f}")
        if item_data['state'] == 'critical': amount_label.setText(f"<font color='#E06C75'>Excedido</font>")
        title_layout.addWidget(name_label); title_layout.addStretch(); title_layout.addWidget(amount_label)
        progress_bar = QProgressBar(); progress_bar.setTextVisible(False)
        progress_bar.setValue(min(100, int(item_data['actual_percent'])))
        progress_bar.setProperty("state", item_data['state']); progress_bar.style().polish(progress_bar)
        layout.addLayout(title_layout); layout.addWidget(progress_bar)
        percent_label = QLabel(f"{item_data['actual_percent']:.1f}% del ingreso"); percent_label.setObjectName("BudgetPercentLabel"); percent_label.setAlignment(Qt.AlignRight)
        layout.addWidget(percent_label)
        return widget

    def update_chart_themes(self, is_dark_mode):
        self.fg_color = '#FFFFFF' if is_dark_mode else '#364765'
        axis_pen = pg.mkPen(color=self.fg_color)
        plot_widgets_to_theme = [
            self.net_worth_plot,
            self.cash_flow_plot,
            self.expense_dist_card.plot_widget,
            self.expense_type_chart_card.plot_widget
        ]
        for pw in plot_widgets_to_theme:
            if pw and pw != self.expense_type_chart_card.plot_widget:
                pw.getPlotItem().getAxis('left').setPen(axis_pen)
                pw.getPlotItem().getAxis('left').setTextPen(self.fg_color)
                pw.getPlotItem().getAxis('bottom').setPen(axis_pen)
                pw.getPlotItem().getAxis('bottom').setTextPen(self.fg_color)

    def _create_month_menu(self):
        self.month_menu = QMenu(self)
        self.month_actions = []
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.all_year_action = QAction("Todo el Año", self); self.all_year_action.setCheckable(True)
        self.month_menu.addAction(self.all_year_action); self.month_menu.addSeparator()
        for i, month in enumerate(months):
            action = QAction(month, self); action.setCheckable(True); action.setData(i + 1)
            self.month_actions.append(action); self.month_menu.addAction(action)
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
        return {"year": int(self.year_filter.currentText()), "months": [a.data() for a in self.month_actions if a.isChecked()]}

    def set_default_month_filter(self):
        current_month_index = QDate.currentDate().month() - 1
        if 0 <= current_month_index < len(self.month_actions): self.month_actions[current_month_index].setChecked(True)
        self._update_month_button_text()

    def update_net_worth_chart(self, dates, values):
        plot_widget = self.net_worth_plot
        plot_widget.clear()
        if dates and values:
            timestamps = [datetime.strptime(str(d), "%Y%m%d").timestamp() for d in dates]
            pen_color = '#61AFEF' if self.fg_color == '#FFFFFF' else '#364765'
            plot_widget.plot(timestamps, values, pen=pg.mkPen(color=pen_color, width=3))

    def _format_k(self, n):
        if n >= 1000:
            return f'{float(n/1000.0):.1f}'.rstrip('0').rstrip('.') + 'k'
        return f'{n:.0f}'

    def update_expense_dist_chart(self, categories, amounts):
        plot_widget = self.expense_dist_card.plot_widget
        plot_widget.clear()
        if categories and amounts:
            x_ticks = [list(enumerate(categories))]
            axis = plot_widget.getAxis('bottom')
            axis.setTicks(x_ticks)
            axis.setTickFont(QFont("Segoe UI", 8))
            is_dark = (self.fg_color == '#FFFFFF')
            hex_colors = ["#61AFEF", "#E5C07B", "#98C379", "#C678DD", "#E06C75", "#ABB2BF"] if is_dark else ["#3B82F6", "#F59E0B", "#22C55E", "#8B5CF6", "#EF4444", "#9CA3AF"]
            brushes = [QBrush(QColor(hex_colors[i % len(hex_colors)])) for i in range(len(amounts))]
            bar_chart = pg.BarGraphItem(x=range(len(categories)), height=amounts, width=0.6, brushes=brushes)
            plot_widget.addItem(bar_chart)
            max_height = max(amounts) if amounts else 1
            for i, amount in enumerate(amounts):
                if amount > 0:
                    text_content = f"↗ {self._format_k(amount)}"
                    text_item = pg.TextItem(text_content, color="#FFFFFF", anchor=(0.5, 0))
                    text_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    padding = max_height * 0.02
                    text_item.setPos(i, amount - padding)
                    plot_widget.addItem(text_item)
            plot_widget.getPlotItem().getViewBox().enableAutoRange(y=True)

    def clear_expense_dist_chart(self):
        self.expense_dist_card.plot_widget.clear()

    def clear_budget_rule_chart(self):
        if hasattr(self.budget_rule_card, 'content_layout'):
            self._clear_layout(self.budget_rule_card.content_layout)

    def update_expense_type_chart(self, categories, amounts):
        card = self.expense_type_chart_card
        pw = card.plot_widget
        legend = getattr(card, "legend_layout", None)
        is_dark = (self.fg_color == '#FFFFFF')
        fg_hex = "#FFFFFF" if is_dark else "#0F172A"
        fg_sub_hex = "#E5E7EB" if is_dark else "#6B7280"
        card_bg = card.palette().window().color()
        try: pw.setBackground(card_bg)
        except Exception: pw.setBackground((card_bg.red(), card_bg.green(), card_bg.blue()))
        categories = categories or []
        amounts = [float(a) for a in (amounts or [])]
        total_amount = float(sum(amounts))
        pw.clear()
        if not categories or total_amount <= 0:
            txt = pg.TextItem("Sin datos de gastos", color=fg_hex, anchor=(0.5, 0.5))
            pw.addItem(txt); txt.setPos(0, 0)
            pw.setAspectLocked(True); pw.setRange(xRange=(-1.0, 1.0), yRange=(-1.0, 1.0))
            pw.hideAxis('left'); pw.hideAxis('bottom')
            if legend: self._clear_legend(legend)
            return
        parts = [a / total_amount for a in amounts]
        hex_colors = ["#61AFEF", "#E5C07B", "#98C379", "#C678DD", "#E06C75", "#ABB2BF"] if is_dark else ["#3B82F6", "#F59E0B", "#22C55E", "#8B5CF6", "#EF4444", "#9CA3AF"]
        slice_colors = []
        for i in range(len(categories)):
            c = QColor(hex_colors[i % len(hex_colors)]); c.setAlpha(235 if is_dark else 215)
            slice_colors.append(c)
        pw.setAspectLocked(True); pw.setRange(xRange=(-1.05, 1.05), yRange=(-1.05, 1.05))
        pw.hideAxis('left'); pw.hideAxis('bottom')
        outer_r, inner_r, start = 0.92, 0.58, 90.0
        for i, p in enumerate(parts):
            if p <= 0: continue
            span = p * 360.0
            ring = pg.QtWidgets.QGraphicsEllipseItem(-outer_r, -outer_r, 2*outer_r, 2*outer_r)
            ring.setStartAngle(int(start * 16)); ring.setSpanAngle(int(span * 16))
            ring.setBrush(slice_colors[i]); ring.setPen(pg.mkPen(None))
            pw.addItem(ring)
            start += span
        inner = pg.QtWidgets.QGraphicsEllipseItem(-inner_r, -inner_r, 2*inner_r, 2*inner_r)
        inner.setBrush(card_bg); inner.setPen(pg.mkPen(None))
        pw.addItem(inner)
        t_total = pg.TextItem(f"${total_amount:,.0f}", color=fg_hex, anchor=(0.5, 0.5))
        t_total.setFont(QFont("Segoe UI", 17, QFont.Weight.DemiBold))
        pw.addItem(t_total); t_total.setPos(0, 0.12)
        t_label = pg.TextItem("Gastos", color=fg_sub_hex, anchor=(0.5, 0.5))
        t_label.setFont(QFont("Segoe UI", 10))
        pw.addItem(t_label); t_label.setPos(0, -0.10)
        if legend: self._build_or_update_legend(legend, categories, amounts, slice_colors, is_dark)

    def _build_or_update_legend(self, legend_layout, categories, amounts, colors, is_dark):
        rebuild = (len(self._legend_widgets) != len(categories))
        if rebuild:
            self._clear_legend(legend_layout); self._legend_widgets = []
            cols = max(1, min(3, len(categories)))
            for idx in range(len(categories)):
                w = QFrame(); lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(2)
                row_top = QHBoxLayout(); row_top.setContentsMargins(0, 0, 0, 0); row_top.setSpacing(6)
                dot = QFrame(); dot.setFixedSize(10, 10)
                row_top.addWidget(dot); lbl = QLabel(); row_top.addWidget(lbl, 1); row_top.addStretch()
                lay.addLayout(row_top); pct = QLabel(); lay.addWidget(pct); amt = QLabel(); lay.addWidget(amt)
                self._legend_widgets.append((w, dot, lbl, pct, amt))
                r = idx // cols; c = idx % cols
                legend_layout.addWidget(w, r, c)
        total = sum(amounts) if amounts else 0.0
        main_hex = "#FFFFFF" if is_dark else "#0F172A"
        sub_hex = "#E5E7EB" if is_dark else "#6B7280"
        for idx, (cat, amt) in enumerate(zip(categories, amounts)):
            color = colors[idx % len(colors)].name()
            pct_val = (amt / total * 100.0) if total > 0 else 0.0
            w, dot, lbl, pct, amt_lbl = self._legend_widgets[idx]
            dot.setStyleSheet(f"background:{color}; border-radius:5px;")
            lbl.setText(cat); lbl.setStyleSheet(f"color:{main_hex}; font-size:11px;")
            pct.setText(f"{pct_val:.1f}%"); pct.setStyleSheet(f"color:{main_hex}; font-weight:600; font-size:14px;")
            amt_lbl.setText(f"${amt:,.2f}"); amt_lbl.setStyleSheet(f"color:{sub_hex}; font-size:11px;")

    def clear_expense_type_chart(self):
        card = self.expense_type_chart_card
        pw = getattr(card, "plot_widget", None)
        legend = getattr(card, "legend_layout", None)
        if pw:
            pw.clear()
            card_bg = card.palette().window().color()
            try: pw.setBackground(card_bg)
            except Exception: pw.setBackground((card_bg.red(), card_bg.green(), card_bg.blue()))
            pw.setAspectLocked(True); pw.setRange(xRange=(-1.05, 1.05), yRange=(-1.05, 1.05))
            pw.hideAxis('left'); pw.hideAxis('bottom')
        if legend: self._clear_legend(legend)

    def update_cash_flow_chart(self, month_labels, income_data, expense_data):
        plot_widget = self.cash_flow_plot
        plot_widget.clear()
        if not month_labels: return
        
        x_ticks = [list(enumerate(month_labels))]
        axis = plot_widget.getAxis('bottom')
        axis.setTicks(x_ticks)

        # --- CORRECCIÓN PARA ROTAR LAS ETIQUETAS ---
        # Accedemos a los TextItems generados internamente después de setTicks
        if hasattr(axis, '_tickStrings'):
            for tick in axis._tickStrings:
                tick.setAngle(-45)
        
        income_bars = pg.BarGraphItem(x=[i - 0.2 for i in range(len(month_labels))], height=income_data, width=0.4, brush=QColor("#98C379"))
        expense_bars = pg.BarGraphItem(x=[i + 0.2 for i in range(len(month_labels))], height=expense_data, width=0.4, brush=QColor("#E06C75"))
        
        plot_widget.addItem(income_bars)
        plot_widget.addItem(expense_bars)