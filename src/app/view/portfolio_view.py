from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QDateEdit, QComboBox, QFormLayout, QHeaderView, QTabWidget)
from PySide6.QtCore import Qt, QDate

class PortfolioView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.portfolio_tab = self._create_portfolio_tab()
        self.history_tab = self._create_history_tab()
        self.trade_tab = self._create_trade_tab()

        self.tabs.addTab(self.portfolio_tab, "Portafolio Actual")
        self.tabs.addTab(self.history_tab, "Histórico de Ventas")
        self.tabs.addTab(self.trade_tab, "Registrar Operación")

    def _create_portfolio_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QFrame(); card.setObjectName("Card"); layout.addWidget(card)
        card_layout = QVBoxLayout(card)

        self.portfolio_table = QTableWidget(0, 9)
        self.portfolio_table.setHorizontalHeaderLabels([
            "Símbolo", "Tipo", "Cantidad", "Precio Prom. Compra", "Costo Total", 
            "Precio Actual", "Valor Actual", "G/P ($)", "Variación (%)"
        ])
        card_layout.addWidget(self.portfolio_table)

        summary_card = QFrame(); summary_card.setObjectName("Card")
        summary_layout = QHBoxLayout(summary_card)
        self.costo_total_label = QLabel("Costo Portafolio: $0.00")
        self.valor_actual_label = QLabel("Portafolio Actual: $0.00")
        self.gp_total_label = QLabel("G/P: $0.00")
        summary_layout.addWidget(self.costo_total_label)
        summary_layout.addWidget(self.valor_actual_label)
        summary_layout.addWidget(self.gp_total_label)
        layout.addWidget(summary_card)
        
        return widget

    def _create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        card = QFrame(); card.setObjectName("Card"); layout.addWidget(card)
        card_layout = QVBoxLayout(card)

        self.history_table = QTableWidget(0, 7)
        self.history_table.setHorizontalHeaderLabels([
            "Fecha Venta", "Símbolo", "Cantidad Vendida", "Precio Compra",
            "Precio Venta", "Dinero Recibido", "G/P (%)"
        ])
        card_layout.addWidget(self.history_table)
        return widget

    def _create_trade_tab(self):
        widget = QWidget()
        # --- INICIO DE LA MODIFICACIÓN ---
        layout = QHBoxLayout(widget) # Layout principal horizontal

        # Columna Izquierda: Formulario de Registro
        form_card = QFrame(); form_card.setObjectName("Card"); form_card.setMaximumWidth(400)
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(20, 20, 20, 20)

        self.trade_date_input = QDateEdit(QDate.currentDate())
        self.trade_symbol_input = QLineEdit()
        self.trade_type_input = QLineEdit()
        self.trade_operation_combo = QComboBox(); self.trade_operation_combo.addItems(["Compra", "Venta"])
        self.trade_quantity_input = QLineEdit()
        self.trade_price_input = QLineEdit()
        self.add_trade_button = QPushButton("Registrar Operación")

        form_layout.addRow("Fecha:", self.trade_date_input)
        form_layout.addRow("Símbolo (ej: BTC, AAPL):", self.trade_symbol_input)
        form_layout.addRow("Tipo (ej: Cripto, Acción):", self.trade_type_input)
        form_layout.addRow("Operación:", self.trade_operation_combo)
        form_layout.addRow("Cantidad:", self.trade_quantity_input)
        form_layout.addRow("Precio por Unidad:", self.trade_price_input)
        form_layout.addRow(self.add_trade_button)

        # Columna Derecha: Tabla de activos actuales
        table_card = QFrame(); table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        table_layout.addWidget(QLabel("<b>Activos en Portafolio</b>"))
        self.simple_portfolio_table = QTableWidget(0, 2)
        self.simple_portfolio_table.setHorizontalHeaderLabels(["Símbolo", "Cantidad Actual"])
        self.simple_portfolio_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.simple_portfolio_table)

        layout.addWidget(form_card)
        layout.addWidget(table_card, 1) # El '1' le da más espacio a la tabla
        # --- FIN DE LA MODIFICACIÓN ---
        return widget

    def get_trade_form_data(self):
        return {
            "date": self.trade_date_input.date().toPython(),
            "symbol": self.trade_symbol_input.text(),
            "asset_type": self.trade_type_input.text(),
            "operation": self.trade_operation_combo.currentText(),
            "quantity": self.trade_quantity_input.text(),
            "price": self.trade_price_input.text()
        }

    def clear_trade_form(self):
        self.trade_symbol_input.clear()
        self.trade_type_input.clear()
        self.trade_quantity_input.clear()
        self.trade_price_input.clear()
        self.trade_date_input.setDate(QDate.currentDate())
        self.trade_operation_combo.setCurrentIndex(0)

    def display_portfolio(self, assets):
        self.portfolio_table.setRowCount(0)
        total_costo = 0
        total_valor_actual = 0

        for row, asset in enumerate(assets):
            self.portfolio_table.insertRow(row)
            
            costo_total = asset.total_quantity * asset.avg_cost_price
            valor_actual = asset.total_quantity * asset.current_price
            ganancia_perdida = valor_actual - costo_total
            variacion_pct = (ganancia_perdida / costo_total) * 100 if costo_total > 0 else 0
            
            total_costo += costo_total
            total_valor_actual += valor_actual

            self.portfolio_table.setItem(row, 0, QTableWidgetItem(asset.symbol))
            self.portfolio_table.setItem(row, 1, QTableWidgetItem(asset.asset_type))
            self.portfolio_table.setItem(row, 2, QTableWidgetItem(f"{asset.total_quantity:,.4f}"))
            self.portfolio_table.setItem(row, 3, QTableWidgetItem(f"${asset.avg_cost_price:,.2f}"))
            self.portfolio_table.setItem(row, 4, QTableWidgetItem(f"${costo_total:,.2f}"))
            self.portfolio_table.setItem(row, 5, QTableWidgetItem(f"${asset.current_price:,.2f}"))
            self.portfolio_table.setItem(row, 6, QTableWidgetItem(f"${valor_actual:,.2f}"))
            self.portfolio_table.setItem(row, 7, QTableWidgetItem(f"${ganancia_perdida:,.2f}"))
            self.portfolio_table.setItem(row, 8, QTableWidgetItem(f"{variacion_pct:.2f}%"))
        
        total_gp = total_valor_actual - total_costo
        self.costo_total_label.setText(f"Costo Portafolio: ${total_costo:,.2f}")
        self.valor_actual_label.setText(f"Portafolio Actual: ${total_valor_actual:,.2f}")
        self.gp_total_label.setText(f"G/P: ${total_gp:,.2f}")
    
    # --- INICIO DE NUEVO MÉTODO ---
    def display_simple_portfolio(self, assets):
        self.simple_portfolio_table.setRowCount(0)
        for row, asset in enumerate(assets):
            self.simple_portfolio_table.insertRow(row)
            self.simple_portfolio_table.setItem(row, 0, QTableWidgetItem(asset.symbol))
            self.simple_portfolio_table.setItem(row, 1, QTableWidgetItem(f"{asset.total_quantity:,.4f}"))
    # --- FIN DE NUEVO MÉTODO ---

    def display_history(self, trades):
        self.history_table.setRowCount(0)
        for row, trade in enumerate(trades):
            self.history_table.insertRow(row)
            asset = trade.asset
            dinero_recibido = trade.quantity * trade.price_per_unit
            costo_de_venta = trade.quantity * asset.avg_cost_price 
            gp_pct = ((dinero_recibido - costo_de_venta) / costo_de_venta) * 100 if costo_de_venta > 0 else 0

            self.history_table.setItem(row, 0, QTableWidgetItem(trade.date.strftime('%Y-%m-%d')))
            self.history_table.setItem(row, 1, QTableWidgetItem(asset.symbol))
            self.history_table.setItem(row, 2, QTableWidgetItem(f"{trade.quantity:,.4f}"))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"${asset.avg_cost_price:,.2f}"))
            self.history_table.setItem(row, 4, QTableWidgetItem(f"${trade.price_per_unit:,.2f}"))
            self.history_table.setItem(row, 5, QTableWidgetItem(f"${dinero_recibido:,.2f}"))
            self.history_table.setItem(row, 6, QTableWidgetItem(f"{gp_pct:.2f}%"))