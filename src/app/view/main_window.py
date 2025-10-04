from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QStackedWidget, QButtonGroup, QFrame,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
import qtawesome as qta
from app.styles import DARK_STYLE, LIGHT_STYLE
from .notification import Notification
from .dashboard_view import DashboardView
from .accounts_view import AccountsView
from .budget_view import BudgetView
from .transactions_view import TransactionsView
from .goals_view import GoalsView
from .analysis_view import AnalysisView
from .portfolio_view import PortfolioView

class MainWindow(QMainWindow):
    def __init__(self):
        # --- INICIO DE LA SOLUCIÓN: Tamaño de ventana ajustado ---
        super().__init__(); self.setWindowTitle("Nebula Finance"); self.resize(1280, 800)
        # --- FIN DE LA SOLUCIÓN ---
        self.is_dark_mode = True; self._create_ui(); self.toggle_theme()

    def _create_ui(self):
        main_widget = QWidget(); self.main_layout = QHBoxLayout(main_widget); self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.setSpacing(0)
        nav_panel = QFrame(); nav_panel.setObjectName("NavPanel"); nav_panel.setFixedWidth(240)
        nav_layout = QVBoxLayout(nav_panel); nav_layout.setContentsMargins(10,10,10,10); nav_layout.setSpacing(10); nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.btn_dashboard = QPushButton("Resumen")
        self.btn_portfolio = QPushButton("Portafolio")
        self.btn_accounts = QPushButton("Cuentas")
        self.btn_budget = QPushButton("Presupuesto")
        self.btn_transactions = QPushButton("Transacciones")
        self.btn_goals = QPushButton("Metas y Deudas")
        self.btn_analysis = QPushButton("Análisis")
        
        buttons = [self.btn_dashboard, self.btn_portfolio, self.btn_accounts, self.btn_budget, self.btn_transactions, self.btn_goals, self.btn_analysis]
        self.button_group = QButtonGroup(); self.button_group.setExclusive(True)
        for btn in buttons: 
            btn.setObjectName("NavButton"); btn.setCheckable(True); btn.setIconSize(QSize(20, 20)); nav_layout.addWidget(btn); self.button_group.addButton(btn)
        
        nav_layout.addStretch()
        self.theme_button = QPushButton(""); self.theme_button.setObjectName("ThemeButton"); self.theme_button.setFixedSize(35,35); nav_layout.addWidget(self.theme_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.content_stack = QStackedWidget()
        self.dashboard_page = DashboardView()
        self.portfolio_page = PortfolioView()
        self.accounts_page = AccountsView()
        self.budget_page = BudgetView()
        self.transactions_page = TransactionsView()
        self.goals_page = GoalsView()
        self.analysis_page = AnalysisView()
        
        self.content_stack.addWidget(self.dashboard_page); self.content_stack.addWidget(self.portfolio_page)
        self.content_stack.addWidget(self.accounts_page); self.content_stack.addWidget(self.budget_page)
        self.content_stack.addWidget(self.transactions_page); self.content_stack.addWidget(self.goals_page)
        self.content_stack.addWidget(self.analysis_page)
        
        self.main_layout.addWidget(nav_panel); self.main_layout.addWidget(self.content_stack); self.setCentralWidget(main_widget)
        self.notification = Notification(self)

    def set_controller(self, controller):
        self.controller = controller; self.btn_dashboard.setChecked(True)
        self.btn_dashboard.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))
        self.btn_portfolio.clicked.connect(lambda: (self.content_stack.setCurrentIndex(1), self.controller.load_portfolio()))
        self.btn_accounts.clicked.connect(lambda: (self.content_stack.setCurrentIndex(2), self.controller.load_accounts()))
        self.btn_budget.clicked.connect(lambda: self.content_stack.setCurrentIndex(3))
        self.btn_transactions.clicked.connect(lambda: self.content_stack.setCurrentIndex(4))
        self.btn_goals.clicked.connect(lambda: self.content_stack.setCurrentIndex(5))
        self.btn_analysis.clicked.connect(lambda: self.content_stack.setCurrentIndex(6))
        self.theme_button.clicked.connect(self.toggle_theme)
        
        self.dashboard_page.quick_add_button.clicked.connect(self.controller.show_quick_transaction_dialog)
        self.portfolio_page.add_trade_button.clicked.connect(self.controller.add_trade)
        self.accounts_page.add_button.clicked.connect(self.controller.add_account)
        self.accounts_page.delete_button.clicked.connect(self.controller.delete_account)
        self.accounts_page.table.cellDoubleClicked.connect(self.controller.edit_account_by_row)
        self.budget_page.add_button.clicked.connect(self.controller.add_budget_entry)
        self.budget_page.delete_button.clicked.connect(self.controller.delete_budget_entry)
        self.budget_page.table.cellDoubleClicked.connect(self.controller.edit_budget_entry_by_row)
        self.transactions_page.add_button.clicked.connect(self.controller.add_transaction)
        self.transactions_page.delete_button.clicked.connect(self.controller.delete_transaction)
        self.transactions_page.recurring_table.cellDoubleClicked.connect(self.controller.edit_recurring_transaction_by_row)
        self.transactions_page.all_table.cellDoubleClicked.connect(lambda r, c: self.controller.edit_transaction_by_row(r, c, self.transactions_page.all_table))
        self.transactions_page.goals_table.cellDoubleClicked.connect(lambda r, c: self.controller.edit_transaction_by_row(r, c, self.transactions_page.goals_table))
        self.transactions_page.debts_table.cellDoubleClicked.connect(lambda r, c: self.controller.edit_transaction_by_row(r, c, self.transactions_page.debts_table))
        self.transactions_page.search_input.textChanged.connect(self.controller.filter_transactions); self.transactions_page.type_filter.currentTextChanged.connect(self.controller.filter_transactions)
        self.transactions_page.category_filter.currentTextChanged.connect(self.controller.filter_transactions); self.transactions_page.sort_by_combo.currentTextChanged.connect(self.controller.filter_transactions)
        self.transactions_page.sort_order_combo.currentTextChanged.connect(self.controller.filter_transactions); self.transactions_page.start_date_filter.dateChanged.connect(self.controller.filter_transactions)
        self.transactions_page.end_date_filter.dateChanged.connect(self.controller.filter_transactions); self.transactions_page.tabs.currentChanged.connect(self.controller.filter_transactions)
        self.goals_page.add_goal_button.clicked.connect(self.controller.add_goal); self.goals_page.add_debt_button.clicked.connect(self.controller.add_debt)
        self.goals_page.edit_goal_requested.connect(self.controller.edit_goal); self.goals_page.delete_goal_requested.connect(self.controller.delete_goal)
        self.goals_page.edit_debt_requested.connect(self.controller.edit_debt); self.goals_page.delete_debt_requested.connect(self.controller.delete_debt)
        
        self.controller.full_refresh(); self.dashboard_page.set_default_month_filter(); self.update_theme_icons()

    def show_notification(self, message, m_type='success'): self.notification.show_message(message, m_type)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode: self.setStyleSheet(DARK_STYLE)
        else: self.setStyleSheet(LIGHT_STYLE)
        self.dashboard_page.update_chart_themes(self.is_dark_mode)
        self.update_theme_icons()

    def update_theme_icons(self):
        icon_color = "#ABB2BF" if self.is_dark_mode else "#6C757D"
        active_color = "#61AFEF" if self.is_dark_mode else "#0d6efd"
        theme_icon = 'fa5s.sun' if self.is_dark_mode else 'fa5s.moon'
        theme_icon_color = "#EAEAEA" if self.is_dark_mode else "#495057"
        
        self.theme_button.setIcon(qta.icon(theme_icon, color=theme_icon_color))
        self.btn_dashboard.setIcon(qta.icon('fa5s.home', color=icon_color, color_active=active_color))
        self.btn_portfolio.setIcon(qta.icon('fa5s.chart-line', color=icon_color, color_active=active_color))
        self.btn_accounts.setIcon(qta.icon('fa5s.wallet', color=icon_color, color_active=active_color))
        self.btn_budget.setIcon(qta.icon('fa5s.calculator', color=icon_color, color_active=active_color))
        self.btn_transactions.setIcon(qta.icon('fa5s.exchange-alt', color=icon_color, color_active=active_color))
        self.btn_goals.setIcon(qta.icon('fa5s.bullseye', color=icon_color, color_active=active_color))
        self.btn_analysis.setIcon(qta.icon('fa5s.chart-pie', color=icon_color, color_active=active_color))

    def resizeEvent(self, event): self.notification.hide(); super().resizeEvent(event)