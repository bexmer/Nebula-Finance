from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                               QGridLayout, QComboBox, QPushButton, QMenu, QProgressBar,
                               QTableWidget, QTableWidgetItem, QHeaderView, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QAction, QFont, QColor
import pyqtgraph as pg
from datetime import datetime

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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

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

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        main_layout.addLayout(grid_layout, 1)
        
        # --- INICIO DE LA SOLUCIÓN: Reestructuración según nuevo boceto ---
        
        # 1. Definición de todos los widgets del dashboard
        self.income_kpi = self._create_kpi_card("Ganancias", "$0.00")
        self.expense_kpi = self._create_kpi_card("Gastos", "$0.00")
        self.net_kpi = self._create_kpi_card("Ahorro Neto", "$0.00")
        self.net_worth_chart_card = self._create_chart_card("Evolución de Patrimonio Neto", axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.budget_rule_card = self._create_chart_card("Control de Gastos", has_plot_widget=False)
        self.budget_income_card = self._create_metric_card("Ingresos")
        self.budget_expense_card = self._create_metric_card("Gastos")
        self.main_goals_card = self._create_chart_card("Metas", has_plot_widget=False)
        self.expense_dist_card = self._create_chart_card("Distribución de Gastos")

        # 2. Creación de layouts intermedios para agrupar widgets
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        kpi_layout.addWidget(self.income_kpi)
        kpi_layout.addWidget(self.expense_kpi)
        kpi_layout.addWidget(self.net_kpi)

        budget_vs_real_layout = QHBoxLayout()
        budget_vs_real_layout.setSpacing(20)
        budget_vs_real_layout.addWidget(self.budget_income_card)
        budget_vs_real_layout.addWidget(self.budget_expense_card)

        # 3. Posicionamiento en el Grid siguiendo la estructura del boceto
        #    La función es .addWidget(widget, fila, columna, expansión_filas, expansión_columnas)

        # Columna Izquierda (Verde)
        grid_layout.addLayout(kpi_layout, 0, 0, 1, 1)               # Fila 0, Col 0
        grid_layout.addWidget(self.net_worth_chart_card, 1, 0, 1, 1) # Fila 1, Col 0
        grid_layout.addLayout(budget_vs_real_layout, 2, 0, 1, 1)     # Fila 2, Col 0
        grid_layout.addWidget(self.main_goals_card, 3, 0, 1, 1)      # Fila 3, Col 0
        
        # Columna Derecha (Verde)
        grid_layout.addWidget(self.budget_rule_card, 0, 1, 2, 1)  # Ocupa Fila 0 y 1, en Col 1
        grid_layout.addWidget(self.expense_dist_card, 2, 1, 2, 1)  # Ocupa Fila 2 y 3, en Col 1

        # 4. Ajuste de proporciones de las filas y columnas
        grid_layout.setColumnStretch(0, 2) # La columna izquierda es el doble de ancha que la derecha
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(1, 1)    # La fila de la gráfica principal es más alta
        grid_layout.setRowStretch(3, 1)    # La fila de metas también tiene más espacio

        # --- FIN DE LA SOLUCIÓN ---

        self.quick_add_button = QPushButton("+")
        self.quick_add_button.setObjectName("QuickAddButton")
        self.quick_add_button.setFixedSize(QSize(46, 46))
        self.quick_add_button.setParent(self)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 5)
        self.quick_add_button.setGraphicsEffect(shadow)
    
    def showEvent(self, event):
        super().showEvent(event)
        for card in self.findChildren(QFrame):
            if "Card" in card.objectName():
                if not card.graphicsEffect():
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
        self.quick_add_button.move(self.width() - button_size.width() - 20, self.height() - button_size.height() - 20)

    def _create_kpi_card(self, title, default_value):
        card = QFrame(); card.setObjectName("KPI_Card"); layout = QVBoxLayout(card); layout.setContentsMargins(15, 10, 15, 10); layout.setSpacing(4)
        title_label = QLabel(title); title_label.setObjectName("KPI_Title")
        value_label = QLabel(default_value); value_label.setObjectName("KPI_Value")
        comparison_label = QLabel(""); comparison_label.setObjectName("KPI_Comparison")
        layout.addWidget(title_label); layout.addWidget(value_label); layout.addWidget(comparison_label); layout.addStretch()
        card.value_label, card.comparison_label = value_label, comparison_label
        return card
        
    def _create_metric_card(self, title):
        card = QFrame(); card.setObjectName("MetricCard"); layout = QVBoxLayout(card); layout.setContentsMargins(15, 15, 15, 15); layout.setSpacing(5)
        title_label = QLabel(title); title_label.setObjectName("MetricTitle")
        value_label = QLabel("$0.00"); value_label.setObjectName("MetricValue")
        comparison_label = QLabel("Real: $0.00"); comparison_label.setObjectName("MetricComparison")
        layout.addWidget(title_label); layout.addWidget(value_label); layout.addWidget(comparison_label); layout.addStretch()
        card.value_label, card.comparison_label = value_label, comparison_label
        return card

    def _create_chart_card(self, title, has_plot_widget=True, axisItems=None):
        card = QFrame(); card.setObjectName("Card"); layout = QVBoxLayout(card); layout.setContentsMargins(15, 15, 15, 15); layout.setSpacing(10)
        title_label = QLabel(title); title_label.setObjectName("Chart_Title"); layout.addWidget(title_label)
        if has_plot_widget:
            plot_widget = pg.PlotWidget(axisItems=axisItems); plot_widget.showGrid(x=True, y=True, alpha=0.1); layout.addWidget(plot_widget, 1)
            card.plot_widget = plot_widget
        else:
            content_layout = QVBoxLayout(); content_layout.setSpacing(10); layout.addLayout(content_layout, 1)
            card.content_layout = content_layout
        return card

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
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setContentsMargins(0, 5, 0, 5)
        title_layout = QHBoxLayout(); name_label = QLabel(f"<b>{goal_data['name']}</b>")
        percentage = (goal_data['current'] / goal_data['target']) * 100 if goal_data['target'] > 0 else 0
        amount_label = QLabel(f"<b>{percentage:.1f}%</b>")
        title_layout.addWidget(name_label); title_layout.addStretch(); title_layout.addWidget(amount_label)
        progress_bar = QProgressBar(); progress_bar.setValue(int(percentage));
        progress_bar.setTextVisible(False)
        progress_bar.setProperty("state", "good"); progress_bar.style().polish(progress_bar)
        layout.addLayout(title_layout); layout.addWidget(progress_bar); return widget

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
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setContentsMargins(0, 5, 0, 5)
        title_layout = QHBoxLayout(); name_label = QLabel(f"<b>{item_data['name']}</b> ({item_data['ideal_percent']:.0f}%)")
        amount_label = QLabel(f"${item_data['actual_amount']:,.2f}")
        title_layout.addWidget(name_label); title_layout.addStretch(); title_layout.addWidget(amount_label)
        progress_bar = QProgressBar(); progress_bar.setTextVisible(True)
        if item_data['is_overdrawn']:
            progress_bar.setValue(100); progress_bar.setFormat("Excedido"); progress_bar.setProperty("state", "critical")
        else:
            progress_bar.setValue(min(100, int(item_data['actual_percent']))); progress_bar.setFormat(f"{item_data['actual_percent']:.1f}%")
            if item_data['actual_percent'] > item_data['ideal_percent']:
                progress_bar.setProperty("state", "warning")
            else:
                progress_bar.setProperty("state", "good")
        progress_bar.style().polish(progress_bar)
        layout.addLayout(title_layout); layout.addWidget(progress_bar); return widget

    def update_chart_themes(self, is_dark_mode):
        fg_color = '#EAEAEA' if is_dark_mode else '#344767'
        axis_pen = pg.mkPen(color=fg_color)
        for plot_widget in [self.net_worth_chart_card.plot_widget, self.expense_dist_card.plot_widget]:
            if plot_widget:
                plot_widget.getPlotItem().getAxis('left').setPen(axis_pen); plot_widget.getPlotItem().getAxis('left').setTextPen(fg_color)
                plot_widget.getPlotItem().getAxis('bottom').setPen(axis_pen); plot_widget.getPlotItem().getAxis('bottom').setTextPen(fg_color)
                if plot_widget.listDataItems():
                    color = '#61AFEF' if is_dark_mode else '#0d6efd'
                    if isinstance(plot_widget.listDataItems()[0], pg.BarGraphItem):
                        plot_widget.listDataItems()[0].setOpts(brush=color)
                    else:
                        plot_widget.listDataItems()[0].setPen(pg.mkPen(color=color, width=3))
    
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
            pen_color = '#61AFEF' if self.styleSheet().startswith("DARK_STYLE") else '#0d6efd'
            plot_widget.plot(timestamps, values, pen=pg.mkPen(color=pen_color, width=3))
    
    def update_expense_dist_chart(self, categories, amounts):
        plot_widget = self.expense_dist_card.plot_widget; plot_widget.clear()
        if categories and amounts:
            x_ticks = [list(enumerate(categories))]; axis = plot_widget.getAxis('bottom'); axis.setTicks(x_ticks); axis.setTickFont(QFont("Segoe UI", 8))
            brush_color = '#61AFEF' if self.styleSheet().startswith("DARK_STYLE") else '#0d6efd'
            bar_chart = pg.BarGraphItem(x=range(len(categories)), height=amounts, width=0.6, brush=brush_color); plot_widget.addItem(bar_chart)
    
    def clear_expense_dist_chart(self):
        self.expense_dist_card.plot_widget.clear()
    
    def clear_budget_rule_chart(self):
        self._clear_layout(self.budget_rule_card.content_layout)