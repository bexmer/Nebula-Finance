from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QStackedWidget, QButtonGroup, QFrame,
                               QGraphicsDropShadowEffect, QLabel)
from PySide6.QtCore import QSize, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont, QKeySequence, QShortcut
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
from .settings_view import SettingsView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nebula Finance")
        
        self.is_nav_panel_collapsed = False
        self.nav_panel_expanded_width = 240
        self.nav_panel_collapsed_width = 80

        self.is_dark_mode = True
        self._create_ui()
        self.toggle_theme()

    def _create_ui(self):
        main_widget = QWidget()
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        
        self.nav_panel = QFrame()
        self.nav_panel.setObjectName("NavPanel")
        self.nav_panel.setMinimumWidth(self.nav_panel_expanded_width)
        self.nav_panel.setMaximumWidth(self.nav_panel_expanded_width)
        nav_layout = QVBoxLayout(self.nav_panel)
        
        nav_layout.setContentsMargins(10,10,10,10)
        nav_layout.setSpacing(10)
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("NavButton")
        self.toggle_button.setCheckable(False)
        self.toggle_button.clicked.connect(self.toggle_nav_panel)
        self.toggle_layout = QHBoxLayout()
        nav_layout.addLayout(self.toggle_layout)

        self.logo_label = QLabel("NF")
        logo_font = self.logo_label.font()
        logo_font.setPointSize(22)
        logo_font.setBold(True)
        self.logo_label.setFont(logo_font)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setObjectName("LogoLabel")
        self.logo_label.setFixedSize(60, 60)
        nav_layout.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignCenter)
        nav_layout.addSpacing(20)

        self.btn_dashboard = QPushButton("Resumen")
        self.btn_portfolio = QPushButton("Portafolio")
        self.btn_accounts = QPushButton("Cuentas")
        self.btn_budget = QPushButton("Presupuesto")
        self.btn_transactions = QPushButton("Transacciones")
        self.btn_goals = QPushButton("Metas y Deudas")
        self.btn_analysis = QPushButton("Análisis")
        self.btn_settings = QPushButton("Configuración")

        buttons = [self.btn_dashboard, self.btn_portfolio, self.btn_accounts, self.btn_budget, self.btn_transactions, self.btn_goals, self.btn_analysis, self.btn_settings]
        self.button_texts = {btn: btn.text() for btn in buttons}
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        for btn in buttons: 
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setIconSize(QSize(20, 20))
            nav_layout.addWidget(btn)
            self.button_group.addButton(btn)
        
        nav_layout.addStretch()

        self.theme_button = QPushButton("")
        self.theme_button.setObjectName("ThemeButton")
        self.theme_button.setFixedSize(35,35)
        self.theme_layout = QHBoxLayout()
        nav_layout.addLayout(self.theme_layout)
        
        self.content_stack = QStackedWidget()
        self.dashboard_page = DashboardView()
        self.portfolio_page = PortfolioView()
        self.accounts_page = AccountsView()
        self.budget_page = BudgetView()
        self.transactions_page = TransactionsView()
        self.goals_page = GoalsView()
        self.analysis_page = AnalysisView()
        self.settings_page = SettingsView()
        
        self.content_stack.addWidget(self.dashboard_page)
        self.content_stack.addWidget(self.portfolio_page)
        self.content_stack.addWidget(self.accounts_page)
        self.content_stack.addWidget(self.budget_page)
        self.content_stack.addWidget(self.transactions_page)
        self.content_stack.addWidget(self.goals_page)
        self.content_stack.addWidget(self.analysis_page)
        self.content_stack.addWidget(self.settings_page)
        
        self.main_layout.addWidget(self.nav_panel)
        self.main_layout.addWidget(self.content_stack)
        self.setCentralWidget(main_widget)
        self.notification = Notification(self)

        self.animation = QPropertyAnimation(self.nav_panel, b"minimumWidth")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.finished.connect(self.on_animation_finished)
        
        self.update_panel_state()


    def set_controller(self, controller):
        self.controller = controller
        self.btn_dashboard.setChecked(True)

        # Conexiones de Navegación
        self.btn_dashboard.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))
        self.btn_portfolio.clicked.connect(lambda: (self.content_stack.setCurrentIndex(1), self.controller.load_portfolio()))
        self.btn_accounts.clicked.connect(lambda: (self.content_stack.setCurrentIndex(2), self.controller.load_paginated_data()))
        self.btn_budget.clicked.connect(lambda: (self.content_stack.setCurrentIndex(3), self.controller.load_paginated_data()))
        self.btn_transactions.clicked.connect(lambda: (self.content_stack.setCurrentIndex(4), self.controller.load_transactions()))
        self.btn_goals.clicked.connect(lambda: (self.content_stack.setCurrentIndex(5), self.controller.load_goals_and_debts()))
        self.btn_analysis.clicked.connect(lambda: (self.content_stack.setCurrentIndex(6), self.controller.update_analysis_view()))
        self.btn_settings.clicked.connect(lambda: (self.content_stack.setCurrentIndex(7), self.controller.load_parameters()))
        
        # --- INICIO DE LA SOLUCIÓN: ATAJOS DE TECLADO ---

        # 1. Atajos de Navegación Esencial
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(self.btn_dashboard.click)
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(self.btn_portfolio.click)
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(self.btn_accounts.click)
        QShortcut(QKeySequence("Ctrl+4"), self).activated.connect(self.btn_budget.click)
        QShortcut(QKeySequence("Ctrl+5"), self).activated.connect(self.btn_transactions.click)

        # 2. Atajos de Acciones Globales
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.controller.show_quick_transaction_dialog)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.controller.full_refresh)
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.toggle_theme)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.controller.focus_search_bar)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)

        # 3. Atajos de Acciones Contextuales
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.controller.delete_selected_item)
        QShortcut(QKeySequence("F2"), self).activated.connect(self.controller.edit_selected_item)
        QShortcut(QKeySequence("Ctrl+Shift+A"), self).activated.connect(self.controller.trigger_add_new)
        
        # --- FIN DE LA SOLUCIÓN ---
    
        # Conexiones Generales
        self.theme_button.clicked.connect(self.toggle_theme)
        
        # Conexiones Dashboard
        self.dashboard_page.year_filter.currentTextChanged.connect(self.controller.update_dashboard)
        for action in self.dashboard_page.month_actions:
            action.triggered.connect(self.controller.update_dashboard)
        self.dashboard_page.all_year_action.triggered.connect(self.controller.update_dashboard)
        self.dashboard_page.quick_add_button.clicked.connect(self.controller.show_quick_transaction_dialog)

        # Conexiones Portafolio
        self.portfolio_page.add_trade_button.clicked.connect(self.controller.add_trade)
        
        # Conexiones Cuentas
        self.accounts_page.add_button.clicked.connect(self.controller.add_account)
        self.accounts_page.delete_button.clicked.connect(self.controller.delete_account) # Conexión correcta
        self.accounts_page.table.cellDoubleClicked.connect(self.controller.edit_account_by_row)

        # Conexiones Presupuesto
        budget_page = self.budget_page
        budget_page.add_button.clicked.connect(self.controller.add_budget_entry)
        budget_page.delete_button.clicked.connect(self.controller.delete_selected_items) # Conexión correcta
        budget_page.register_payment_button.clicked.connect(self.controller.register_budget_payment)
        budget_page.table.cellDoubleClicked.connect(self.controller.edit_budget_entry_by_row)
        budget_page.prev_button.clicked.connect(lambda: self.controller.change_page(-1))
        budget_page.next_button.clicked.connect(lambda: self.controller.change_page(1))
        budget_page.items_per_page_combo.currentTextChanged.connect(self.controller.change_items_per_page)
        budget_page.type_input.currentTextChanged.connect(self.controller.update_category_dropdowns)

        
        # Conexiones Transacciones
        transactions_page = self.transactions_page
        transactions_page.add_button.clicked.connect(self.controller.add_transaction)
        transactions_page.delete_button.clicked.connect(self.controller.delete_selected_items)
        transactions_page.recurring_table.cellDoubleClicked.connect(self.controller.edit_recurring_transaction_by_row)
        transactions_page.all_table.cellDoubleClicked.connect(lambda r, c: self.controller.edit_transaction_by_row(r, c, transactions_page.all_table))
        transactions_page.goals_table.cellDoubleClicked.connect(lambda r, c: self.controller.edit_transaction_by_row(r, c, transactions_page.goals_table))
        transactions_page.debts_table.cellDoubleClicked.connect(lambda r, c: self.controller.edit_transaction_by_row(r, c, transactions_page.debts_table))
        transactions_page.search_input.textChanged.connect(self.controller.filter_transactions)
        transactions_page.start_date_filter.dateChanged.connect(self.controller.filter_transactions)
        transactions_page.end_date_filter.dateChanged.connect(self.controller.filter_transactions)
        transactions_page.tabs.currentChanged.connect(self.controller.filter_transactions)
        transactions_page.type_input.currentTextChanged.connect(self.controller.update_category_dropdowns)

        
        # Conexiones Metas y Deudas
        goals_page = self.goals_page
        goals_page.add_goal_button.clicked.connect(self.controller.add_goal)
        goals_page.add_debt_button.clicked.connect(self.controller.add_debt)
        goals_page.calculate_strategy_button.clicked.connect(self.controller.calculate_debt_strategies)

        goals_page.edit_goal_requested.connect(self.controller.edit_goal)
        goals_page.delete_goal_requested.connect(self.controller.delete_goal)
        goals_page.edit_debt_requested.connect(self.controller.edit_debt)
        goals_page.delete_debt_requested.connect(self.controller.delete_debt)
        goals_page.calculate_strategy_button.clicked.connect(self.controller.calculate_debt_strategies)    
        # Conexiones Configuración
        settings_page = self.settings_page
        tt_tab = settings_page.transaction_types_tab
        tt_tab.param_add_button.clicked.connect(lambda: self.controller.add_parameter('Tipo de Transacción'))
        tt_tab.param_delete_button.clicked.connect(self.controller.delete_parameter)
        tt_tab.param_table.cellDoubleClicked.connect(lambda r, c: self.controller.edit_parameter_by_row(r, c, tt_tab.param_table))
        tt_tab.rule_add_button.clicked.connect(self.controller.add_budget_rule)
        tt_tab.rule_delete_button.clicked.connect(self.controller.delete_budget_rule)
        tt_tab.rule_table.cellDoubleClicked.connect(self.controller.edit_budget_rule_by_row)
        settings_page.account_types_tab.add_button.clicked.connect(lambda: self.controller.add_parameter('Tipo de Cuenta'))
        settings_page.account_types_tab.delete_button.clicked.connect(self.controller.delete_parameter)
        settings_page.account_types_tab.table.cellDoubleClicked.connect(lambda r, c: self.controller.edit_parameter_by_row(r, c, settings_page.account_types_tab.table))
        settings_page.categories_tab.add_button.clicked.connect(lambda: self.controller.add_parameter('Categoría'))
        settings_page.categories_tab.delete_button.clicked.connect(self.controller.delete_parameter)
        settings_page.categories_tab.table.cellDoubleClicked.connect(lambda r, c: self.controller.edit_parameter_by_row(r, c, settings_page.categories_tab.table))
        
        # Carga inicial
        self.controller.full_refresh()
        self.dashboard_page.set_default_month_filter()
        self.update_theme_icons()
        
    def get_current_view_name(self):
        current_index = self.content_stack.currentIndex()
        view_map = {
            0: 'dashboard',
            1: 'portfolio',
            2: 'accounts',
            3: 'budget',
            4: 'transactions',
            5: 'goals',
            6: 'analysis',
            7: 'settings'
        }
        return view_map.get(current_index)

    def toggle_nav_panel(self):
        self.is_nav_panel_collapsed = not self.is_nav_panel_collapsed
        end_width = self.nav_panel_collapsed_width if self.is_nav_panel_collapsed else self.nav_panel_expanded_width
        
        self.animation.setTargetObject(self.nav_panel)
        self.animation.setEndValue(end_width)

        if self.is_nav_panel_collapsed:
            self.animation.setPropertyName(b"maximumWidth")
            self.nav_panel.setMinimumWidth(end_width)
        else:
            self.animation.setPropertyName(b"minimumWidth")
            self.nav_panel.setMaximumWidth(end_width)
        
        self.animation.start()
        self.update_panel_state()

    def on_animation_finished(self):
        end_width = self.nav_panel_collapsed_width if self.is_nav_panel_collapsed else self.nav_panel_expanded_width
        self.nav_panel.setMinimumWidth(end_width)
        self.nav_panel.setMaximumWidth(end_width)

    def update_panel_state(self):
        def clear_layout(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)

        clear_layout(self.toggle_layout)
        clear_layout(self.theme_layout)

        if self.is_nav_panel_collapsed:
            self.logo_label.setFixedSize(40, 40)
            font = self.logo_label.font(); font.setPointSize(14)
            self.logo_label.setFont(font)
            for btn in self.button_group.buttons():
                btn.setText("")
                btn.setToolTip(self.button_texts.get(btn))
                btn.setProperty("collapsed", True)
                btn.style().polish(btn)
            self.toggle_button.setToolTip("Expandir Menú")

            self.toggle_layout.addStretch()
            self.toggle_layout.addWidget(self.toggle_button)
            self.toggle_layout.addStretch()
            
            self.theme_layout.addStretch()
            self.theme_layout.addWidget(self.theme_button)
            self.theme_layout.addStretch()
        else:
            self.logo_label.setFixedSize(60, 60)
            font = self.logo_label.font(); font.setPointSize(22)
            self.logo_label.setFont(font)
            for btn in self.button_group.buttons():
                btn.setText(self.button_texts.get(btn))
                btn.setToolTip("")
                btn.setProperty("collapsed", False)
                btn.style().polish(btn)
            self.toggle_button.setToolTip("Colapsar Menú")
            
            self.toggle_layout.addWidget(self.toggle_button)
            self.toggle_layout.addStretch()
            
            self.theme_layout.addWidget(self.theme_button)
            self.theme_layout.addStretch()

        self.update_theme_icons()

    def show_notification(self, message, m_type='success'):
        self.notification.show_message(message, m_type)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        stylesheet = DARK_STYLE if self.is_dark_mode else LIGHT_STYLE
        self.setStyleSheet(stylesheet)
        
        logo_label = self.findChild(QLabel, "LogoLabel")
        if logo_label:
            if self.is_dark_mode:
                logo_label.setStyleSheet("border: 3px solid #8A9BFF; border-radius: 30px; color: #8A9BFF; background-color: #232533;")
            else:
                logo_label.setStyleSheet("border: 3px solid #364765; border-radius: 30px; color: #364765; background-color: #f4f4ff;")

        self.dashboard_page.update_chart_themes(self.is_dark_mode)
        self.update_theme_icons()

        current_width = self.nav_panel_collapsed_width if self.is_nav_panel_collapsed else self.nav_panel_expanded_width
        self.nav_panel.setMinimumWidth(current_width)
        self.nav_panel.setMaximumWidth(current_width)

    def update_theme_icons(self):
        icon_color = "#979ba5"
        active_color = "#191A23" if self.is_dark_mode else "#EAEAEA"
        theme_icon_color = "#EAEAEA" if self.is_dark_mode else "#364765"
            
        theme_icon = 'fa5s.sun' if self.is_dark_mode else 'fa5s.moon'
        toggle_icon_name = 'fa5s.angle-double-right' if self.is_nav_panel_collapsed else 'fa5s.angle-double-left'
        
        self.toggle_button.setIcon(qta.icon(toggle_icon_name, color=icon_color))
        self.theme_button.setIcon(qta.icon(theme_icon, color=theme_icon_color))

        self.btn_dashboard.setIcon(qta.icon('fa5s.home', color=icon_color, color_active=active_color))
        self.btn_portfolio.setIcon(qta.icon('fa5s.chart-line', color=icon_color, color_active=active_color))
        self.btn_accounts.setIcon(qta.icon('fa5s.wallet', color=icon_color, color_active=active_color))
        self.btn_budget.setIcon(qta.icon('fa5s.calculator', color=icon_color, color_active=active_color))
        self.btn_transactions.setIcon(qta.icon('fa5s.exchange-alt', color=icon_color, color_active=active_color))
        self.btn_goals.setIcon(qta.icon('fa5s.bullseye', color=icon_color, color_active=active_color))
        self.btn_analysis.setIcon(qta.icon('fa5s.chart-pie', color=icon_color, color_active=active_color))
        self.btn_settings.setIcon(qta.icon('fa5s.cog', color=icon_color, color_active=active_color))

    def resizeEvent(self, event):
        self.notification.hide()
        super().resizeEvent(event)