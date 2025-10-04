from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QGridLayout, QComboBox, QHeaderView)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

class AnalysisView(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- INICIO DE LA SOLUCIÓN: Título añadido ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("Análisis")
        title_label.setObjectName("DashboardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        # --- FIN DE LA SOLUCIÓN ---
        
        net_worth_card = QFrame(); net_worth_card.setObjectName("Card"); net_worth_layout = QVBoxLayout(net_worth_card)
        net_worth_grid = QGridLayout()
        self.total_assets_label = QLabel("$0.00"); self.total_assets_label.setObjectName("KPI_Value")
        self.total_liabilities_label = QLabel("$0.00"); self.total_liabilities_label.setObjectName("KPI_Value")
        self.net_worth_label = QLabel("$0.00"); self.net_worth_label.setObjectName("KPI_Value")
        net_worth_grid.addWidget(QLabel("Total Activos:"), 0, 0); net_worth_grid.addWidget(self.total_assets_label, 0, 1, Qt.AlignmentFlag.AlignRight)
        net_worth_grid.addWidget(QLabel("Total Pasivos:"), 1, 0); net_worth_grid.addWidget(self.total_liabilities_label, 1, 1, Qt.AlignmentFlag.AlignRight)
        net_worth_grid.addWidget(QLabel("<b>Patrimonio Neto:</b>"), 2, 0); net_worth_grid.addWidget(self.net_worth_label, 2, 1, Qt.AlignmentFlag.AlignRight)
        net_worth_layout.addLayout(net_worth_grid)
        
        report_card = QFrame(); report_card.setObjectName("Card"); report_layout = QVBoxLayout(report_card)
        report_header_layout = QHBoxLayout()
        report_header_layout.addWidget(QLabel("<b>Reporte Anual de Gastos por Categoría</b>")); report_header_layout.addStretch()
        report_header_layout.addWidget(QLabel("Año:"))
        current_year = QDate.currentDate().year()
        self.year_selector = QComboBox()
        self.year_selector.addItems([str(y) for y in range(current_year - 5, current_year + 2)])
        self.year_selector.setCurrentText(str(current_year))
        report_header_layout.addWidget(self.year_selector)
        report_layout.addLayout(report_header_layout)
        self.report_table = QTableWidget()
        report_layout.addWidget(self.report_table)

        main_layout.addWidget(net_worth_card); main_layout.addWidget(report_card, 1)

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

    def update_net_worth_display(self, total_assets, total_liabilities, net_worth):
        self.total_assets_label.setText(f"${total_assets:,.2f}"); self.total_liabilities_label.setText(f"${total_liabilities:,.2f}"); self.net_worth_label.setText(f"${net_worth:,.2f}")