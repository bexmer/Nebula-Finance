from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                               QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QTabWidget,
                               QGridLayout, QPushButton, QMenu)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QBrush, QColor, QAction
import pyqtgraph as pg
from dateutil.relativedelta import relativedelta
import datetime

class AnalysisView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # --- Cabecera con selector de año y mes ---
        header_layout = QHBoxLayout()
        title_label = QLabel("Análisis Financiero")
        title_label.setObjectName("DashboardTitle")
        
        current_year = QDate.currentDate().year()
        self.year_selector = QComboBox()
        self.year_selector.addItems([str(y) for y in range(current_year - 5, current_year + 2)])
        self.year_selector.setCurrentText(str(current_year))
        
        self.month_filter_button = QPushButton("Todo el Año")
        self.month_filter_button.setObjectName("FilterButton")
        self._create_month_menu()
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Año:"))
        header_layout.addWidget(self.year_selector)
        header_layout.addWidget(QLabel("Mes:"))
        header_layout.addWidget(self.month_filter_button)
        main_layout.addLayout(header_layout)

        # --- Patrimonio Neto ---
        net_worth_card = QFrame(); net_worth_card.setObjectName("Card")
        net_worth_layout = QVBoxLayout(net_worth_card)
        net_worth_grid = QGridLayout()
        self.total_assets_label = QLabel("$0.00"); self.total_assets_label.setObjectName("KPI_Value")
        self.total_liabilities_label = QLabel("$0.00"); self.total_liabilities_label.setObjectName("KPI_Value")
        self.net_worth_label = QLabel("$0.00"); self.net_worth_label.setObjectName("KPI_Value")
        net_worth_grid.addWidget(QLabel("Total Activos:"), 0, 0); net_worth_grid.addWidget(self.total_assets_label, 0, 1, Qt.AlignmentFlag.AlignRight)
        net_worth_grid.addWidget(QLabel("Total Pasivos:"), 1, 0); net_worth_grid.addWidget(self.total_liabilities_label, 1, 1, Qt.AlignmentFlag.AlignRight)
        net_worth_grid.addWidget(QLabel("<b>Patrimonio Neto:</b>"), 2, 0); net_worth_grid.addWidget(self.net_worth_label, 2, 1, Qt.AlignmentFlag.AlignRight)
        net_worth_layout.addLayout(net_worth_grid)
        main_layout.addWidget(net_worth_card)

        # --- Pestañas ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)

        self.annual_report_tab = self._create_annual_report_tab()
        self.tabs.addTab(self.annual_report_tab, "Reporte Anual de Gastos")

        self.budget_analysis_tab = self._create_budget_analysis_tab()
        self.tabs.addTab(self.budget_analysis_tab, "Análisis de Presupuesto")

    def _create_annual_report_tab(self):
        report_card = QFrame()
        report_card.setObjectName("Card")
        report_layout = QVBoxLayout(report_card)
        report_layout.addWidget(QLabel("<b>Reporte Anual de Gastos por Categoría</b>"))
        self.report_table = QTableWidget()
        report_layout.addWidget(self.report_table)
        return report_card
    
    def _create_budget_analysis_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(15)

        table_card = QFrame(); table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        table_layout.addWidget(QLabel("<b>Comparativa Anual: Presupuesto vs. Real por Reglas</b>"))
        self.budget_comparison_table = QTableWidget()
        table_layout.addWidget(self.budget_comparison_table)
        
        charts_container = QHBoxLayout()
        charts_container.setSpacing(15)
        
        self.vs_chart = self._create_chart_card("Gasto Real vs. Presupuestado")
        self.dist_chart = self._create_chart_card("Distribución por Regla sobre Ingreso Real")
        
        charts_container.addWidget(self.vs_chart)
        charts_container.addWidget(self.dist_chart)
        
        layout.addWidget(table_card, 1)
        layout.addLayout(charts_container, 1)
        
        return widget

    def _create_chart_card(self, title):
        card = QFrame(); card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        title_label = QLabel(title); title_label.setObjectName("Chart_Title")
        layout.addWidget(title_label)
        
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('transparent')
        plot_widget.showGrid(x=True, y=True, alpha=0.1)
        layout.addWidget(plot_widget)
        
        card.plot_widget = plot_widget
        return card

    def _create_month_menu(self):
        self.month_menu = QMenu(self)
        self.month_actions = []
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        self.all_year_action = QAction("Todo el Año", self)
        self.all_year_action.setCheckable(True)
        self.all_year_action.setChecked(True)
        self.month_menu.addAction(self.all_year_action)
        self.month_menu.addSeparator()

        for i, month in enumerate(months):
            action = QAction(month, self)
            action.setCheckable(True)
            action.setData(i + 1)
            action.setChecked(True)
            self.month_actions.append(action)
            self.month_menu.addAction(action)

        self.month_filter_button.setMenu(self.month_menu)
        self.all_year_action.triggered.connect(self._handle_all_year_selection)
        for a in self.month_actions:
            a.triggered.connect(self._update_month_button_text)

    def _handle_all_year_selection(self):
        is_checked = self.all_year_action.isChecked()
        for action in self.month_actions:
            action.setChecked(is_checked)
        self._update_month_button_text()

    def _update_month_button_text(self):
        selected_months = [a.text() for a in self.month_actions if a.isChecked()]
        
        if len(selected_months) == 12:
            self.month_filter_button.setText("Todo el Año")
            self.all_year_action.setChecked(True)
        elif len(selected_months) == 1:
            self.month_filter_button.setText(selected_months[0])
            self.all_year_action.setChecked(False)
        elif not selected_months:
            self.month_filter_button.setText("Ningún Mes")
            self.all_year_action.setChecked(False)
        else:
            self.month_filter_button.setText(f"{len(selected_months)} Meses")
            self.all_year_action.setChecked(False)

        self.year_selector.currentTextChanged.emit(self.year_selector.currentText())

    def get_selected_filters(self):
        year = int(self.year_selector.currentText())
        months = [a.data() for a in self.month_actions if a.isChecked()]
        return {"year": year, "months": months}

    def update_net_worth_display(self, total_assets, total_liabilities, net_worth):
        self.total_assets_label.setText(f"${total_assets:,.2f}")
        self.total_liabilities_label.setText(f"${total_liabilities:,.2f}")
        self.net_worth_label.setText(f"${net_worth:,.2f}")

    def display_annual_report(self, data, categories, year, monthly_totals, grand_total):
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        self.report_table.clear(); self.report_table.setRowCount(len(categories) + 1); self.report_table.setColumnCount(14)
        self.report_table.setHorizontalHeaderLabels(["Categoría"] + months + ["Total Anual"])
        for row, category in enumerate(categories):
            self.report_table.setItem(row, 0, QTableWidgetItem(category)); row_total = 0.0
            for col, month_num in enumerate(range(1, 13), 1):
                amount = data.get(category, {}).get(month_num, 0.0); item = QTableWidgetItem(f"${amount:,.2f}" if amount > 0 else "-")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.report_table.setItem(row, col, item); row_total += amount
            total_item = QTableWidgetItem(f"${row_total:,.2f}"); total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.report_table.setItem(row, 13, total_item)
        totals_row_index = len(categories); bold_font = QFont(); bold_font.setBold(True)
        total_label_item = QTableWidgetItem("Total Mensual"); total_label_item.setFont(bold_font)
        self.report_table.setItem(totals_row_index, 0, total_label_item)
        for col, month_num in enumerate(range(1, 13), 1):
            total_amount = monthly_totals.get(month_num, 0.0); item = QTableWidgetItem(f"${total_amount:,.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); item.setFont(bold_font)
            self.report_table.setItem(totals_row_index, col, item)
        grand_total_item = QTableWidgetItem(f"${grand_total:,.2f}")
        grand_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); grand_total_item.setFont(bold_font)
        self.report_table.setItem(totals_row_index, 13, grand_total_item)
        self.report_table.resizeColumnsToContents(); self.report_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def display_budget_analysis(self, analysis_data):
        table = self.budget_comparison_table
        table.clear()
        table.setRowCount(len(analysis_data))
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Regla", "Presupuesto (Anual)", "Gasto Real (Anual)", "Diferencia", "Cumplimiento"])

        for row, data in enumerate(analysis_data):
            diff = data['budget'] - data['real']
            compliance = (data['real'] / data['budget']) * 100 if data['budget'] > 0 else 0
            diff_color = QColor("#28A745") if diff >= 0 else QColor("#DC3545")
            
            table.setItem(row, 0, QTableWidgetItem(data['rule']))
            table.setItem(row, 1, QTableWidgetItem(f"${data['budget']:,.2f}"))
            table.setItem(row, 2, QTableWidgetItem(f"${data['real']:,.2f}"))
            
            diff_item = QTableWidgetItem(f"${diff:,.2f}")
            diff_item.setForeground(QBrush(diff_color))
            table.setItem(row, 3, diff_item)
            
            table.setItem(row, 4, QTableWidgetItem(f"{compliance:.1f}%"))

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        rules = [d['rule'] for d in analysis_data]
        budget_values = [d['budget'] for d in analysis_data]
        real_values = [d['real'] for d in analysis_data]
        income_dist_values = [d['income_percentage'] for d in analysis_data]

        self._update_bar_chart(self.vs_chart.plot_widget, rules, budget_values, real_values, label="Gasto ($)")
        self._update_bar_chart(self.dist_chart.plot_widget, rules, income_dist_values, label="Porcentaje del Ingreso (%)")

    def _update_bar_chart(self, plot_widget, rules, values1, values2=None, label=""):
        plot_widget.clear()
        
        x_ticks = [list(enumerate(rules))]
        plot_widget.getAxis('bottom').setTicks(x_ticks)
        
        if values2:
            bar1 = pg.BarGraphItem(x=[i - 0.2 for i in range(len(rules))], height=values1, width=0.4, brush=QColor("#3B82F6"), name='Presupuesto')
            bar2 = pg.BarGraphItem(x=[i + 0.2 for i in range(len(rules))], height=values2, width=0.4, brush=QColor("#22C55E"), name='Real')
            plot_widget.addItem(bar1)
            plot_widget.addItem(bar2)
        else:
            bar = pg.BarGraphItem(x=range(len(rules)), height=values1, width=0.6, brush=QColor("#8B5CF6"))
            plot_widget.addItem(bar)
        
        plot_widget.getAxis('left').setLabel(label)