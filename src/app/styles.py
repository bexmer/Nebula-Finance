LIGHT_STYLE = """
    /* --- GENERAL --- */
    QWidget {
        background-color: #d5daed;
        color: #364765;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px;
    }
    QFrame {
        border: none;
        background-color: transparent;
    }

    /* --- TARJETAS Y NAVEGACIÓN --- */
    QFrame#Card, QFrame#ListItemCard, QFrame#Chart_Card, QFrame#MetricCard, QFrame#NavPanel {
        background-color: #f4f4ff;
        border-radius: 12px;
        border: 1px solid #E9ECEF;
    }
    
    QWidget#BudgetBarContainer, QWidget#GoalBarContainer {
        background-color: #e8eaf6;
        border-radius: 8px;
        padding: 10px;
    }

    /* --- BOTONES DE NAVEGACIÓN --- */
    QPushButton#NavButton {
        background-color: transparent; border: none; color: #979ba5;
        padding: 11px 15px; text-align: left; border-radius: 8px; font-size: 14px; font-weight: 600;
    }
    QPushButton#NavButton:hover { background-color: #E6F0FF; color: #364765; }
    QPushButton#NavButton:checked { background-color: #364765; color: #FFFFFF; }
    QPushButton#NavButton[collapsed="true"] { text-align: center; padding: 11px; }

    /* --- TEXTO --- */
    QLabel { color: #364765; }
    QLabel#DashboardTitle { 
        font-size: 22px; 
        font-weight: 700; 
        color: #364765;
    }
    QLabel#Chart_Title, QLabel#MetricTitle { font-size: 15px; font-weight: 600; color: #364765; }
    QLabel#Chart_Subtitle { font-size: 12px; color: #6b7280; font-weight: 500; }
    QLabel#KPI_Comparison, QLabel#MetricComparison { font-size: 12px; color: #979ba5; font-weight: 500; }
    QLabel#MetricValue { font-size: 22px; font-weight: 700; color: #364765; }
    QLabel#BudgetPercentLabel {
        color: #979ba5;
        font-size: 11px;
    }

    /* --- ESTILOS KPI MEJORADOS --- */
    QFrame#KPI_Card { background-color: #f4f4ff; border-radius: 12px; border: 1px solid #E9ECEF; }
    QLabel#KPI_Icon { background-color: transparent; border-radius: 0; }
    QLabel#KPI_Value { font-size: 22px; font-weight: 700; color: #364765; }
    QLabel#KPI_Title { font-size: 12px; color: #979ba5; font-weight: 500; }

    /* --- BOTONES DE ACCIÓN Y FILTROS --- */
    QPushButton {
        background-color: #364765; color: white; border: none;
        padding: 9px 14px; border-radius: 8px; font-weight: 600;
    }
    QPushButton:hover { background-color: #2c3a54; }
    QPushButton#PrimaryAction { background-color: #0d6efd; color: white; }
    QPushButton#PrimaryAction:hover { background-color: #0b5ed7; }
    QPushButton#FilterButton {
        background-color: transparent; color: #364765; border: 1px solid #ced4da;
        text-align: left; padding-right: 20px;
    }
    QPushButton#FilterButton:hover { background-color: #e9ecef; }
    QPushButton#FilterButton::menu-indicator { position: absolute; right: 7px; top: 50%; margin-top: -4px; }
    
    QPushButton#ThemeButton { background-color: #d5daed; color: #364765; font-size: 16px; padding: 5px; border-radius: 15px; }
    QPushButton#QuickAddButton {
        background-color: #364765; color: white; font-size: 28px; font-weight: 300;
        padding: 0px; padding-bottom: 4px; border-radius: 23px;
    }
    
    /* --- CHECKBOXES --- */
    QCheckBox::indicator, QTableWidget::indicator {
        border: 1px solid #979ba5;
        width: 14px;
        height: 14px;
        border-radius: 4px;
        background-color: #f4f4ff;
    }
    QCheckBox::indicator:hover, QTableWidget::indicator:hover {
        border: 2px solid #364765;
    }
    QCheckBox::indicator:checked, QTableWidget::indicator:checked {
        background-color: #364765;
        border: 2px solid #364765;
    }

    /* --- BARRAS DE PROGRESO --- */
    QProgressBar { border: none; background-color: #e8eaf6; border-radius: 6px; min-height: 12px; max-height: 12px; }
    QProgressBar::chunk { border-radius: 4px; margin: 2px; }
    QProgressBar[state="good"]::chunk { background-color: #28A745; }
    QProgressBar[state="warning"]::chunk { background-color: #FFC107; }
    QProgressBar[state="critical"]::chunk { background-color: #DC3545; }

    /* --- WIDGETS DE ENTRADA --- */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {
        background-color: #f4f4ff; border: 1px solid #d5daed;
        padding: 7px 11px; border-radius: 8px; color: #364765;
    }

    QComboBox#ChartRangeCombo {
        min-width: 150px;
    }
    
    /* --- ESTILOS DE TABLA --- */
    QTableWidget { background-color: #f4f4ff; border: none; border-radius: 8px; gridline-color: transparent; }
    QHeaderView::section {
        background-color: transparent; padding: 10px 15px; border: none;
        border-bottom: 2px solid #e0e4f4; font-weight: 600; color: #979ba5; text-align: left;
    }
    QTableWidget::item { padding-left: 15px; border: none; border-bottom: 1px solid #e0e4f4; }
    QTableWidget::item:selected { background-color: #e0e4f4; color: #364765; }

    /* --- MENÚS --- */
    QMenu { background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 8px; padding: 5px; }
    QMenu::item { padding: 8px 20px; border-radius: 6px; }
    QMenu::item:selected { background-color: #f0f2f5; }
    QComboBox QAbstractItemView {
        background-color: #d5daed; border: 1px solid #c5cbe0;
        selection-background-color: #364765; selection-color: #FFFFFF;
        color: #364765; outline: 0px;
    }
    
    /* --- OTROS --- */
    QLabel#NotificationLabel { padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 600; }
    QLabel#NotificationLabel[message_type="success"] { background-color: #28A745; color: #FFFFFF; }
    QLabel#NotificationLabel[message_type="error"] { background-color: #DC3545; color: #FFFFFF; }
    QTabWidget::pane { border: none; }
    QTabBar::tab {
        background: transparent; color: #979ba5; padding: 10px 20px;
        border-radius: 8px; font-weight: 600; margin-right: 5px;
    }
    QTabBar::tab:hover { background-color: #E6F0FF; color: #364765; }
    QTabBar::tab:selected { background-color: #364765; color: #FFFFFF; }

    /* Estilos Tarjeta de Crédito */
    QFrame#CreditCardFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3E517A, stop:1 #2C3A54); border-radius: 15px; }
    QLabel#CardBalance { font-size: 20px; font-weight: 700; color: #FFFFFF; }
    QLabel#CardType { font-size: 14px; font-weight: 600; color: #FFFFFF; font-style: italic; }
    QLabel#CardNumber { font-size: 16px; font-weight: 400; color: #FFFFFF; font-family: "Courier New", Courier, monospace; }
    QLabel#CardSubText { font-size: 10px; color: #D3D3D3; text-transform: uppercase; }
    QLabel#CardMainText { font-size: 13px; font-weight: 600; color: #FFFFFF; }
    QPushButton#CardNavButton { background-color: #e8eaf6; color: #364765; border: none; border-radius: 12px; font-weight: 700; }
    QPushButton#CardNavButton:hover { background-color: #d5daed; }
    QPushButton#CardVisibilityButton { background-color: transparent; border: none; padding: 0px; }
    
    QLabel#ProjectionLabel {
    font-size: 11px;
    color: #979ba5; /* Un color gris suave */
    font-style: italic;
}
"""

DARK_STYLE = """
QLabel#ProjectionLabel {
    font-size: 11px;
    color: #979ba5; /* Mismo color, funciona bien en ambos temas */
    font-style: italic;
}
    /* --- GENERAL --- */
    QWidget {
        background-color: #191A23;
        color: #EAEAEA;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px;
    }
    QFrame { border: none; background-color: transparent; }
    
    /* --- TARJETAS Y NAVEGACIÓN --- */
    QFrame#Card, QFrame#ListItemCard, QFrame#Chart_Card, QFrame#MetricCard, QFrame#NavPanel {
        background-color: #232533;
        border-radius: 12px;
        border: 1px solid #3A404D;
    }
    
    QWidget#BudgetBarContainer, QWidget#GoalBarContainer {
        background-color: #191A23;
        border-radius: 8px;
        padding: 8px;
    }
    
    /* --- BOTONES DE NAVEGACIÓN --- */
    QPushButton#NavButton {
        background-color: transparent; border: none; color: #979ba5;
        padding: 11px 15px; text-align: left; border-radius: 8px; font-size: 14px; font-weight: 600;
    }
    QPushButton#NavButton:hover { background-color: #3A404D; color: #EAEAEA; }
    QPushButton#NavButton:checked { background-color: #8A9BFF; color: #191A23; }
    QPushButton#NavButton[collapsed="true"] { text-align: center; padding: 11px; }

    /* --- TEXTO --- */
    QLabel { color: #EAEAEA; }
    QLabel#DashboardTitle { font-size: 22px; font-weight: 600; color: #EAEAEA; }
    QLabel#Chart_Title, QLabel#MetricTitle { font-size: 14px; font-weight: 600; color: #EAEAEA; }
    QLabel#Chart_Subtitle { font-size: 11px; color: #A3A3A3; font-weight: 500; }
    QLabel#KPI_Comparison, QLabel#MetricComparison { font-size: 11px; color: #979ba5; font-weight: 500; }
    QLabel#MetricValue { font-size: 18px; font-weight: 700; color: #EAEAEA; }
    QLabel#BudgetPercentLabel { color: #979ba5; font-size: 11px; }

    /* --- ESTILOS KPI MEJORADOS --- */
    QFrame#KPI_Card { background-color: #232533; border-radius: 12px; border: 1px solid #3A404D; }
    QLabel#KPI_Icon { background-color: transparent; border-radius: 0; }
    QLabel#KPI_Value { font-size: 22px; font-weight: 700; color: #EAEAEA; }
    QLabel#KPI_Title { font-size: 11px; color: #979ba5; font-weight: 500; }

    /* --- BOTONES DE ACCIÓN Y FILTROS --- */
    QPushButton {
        background-color: #8A9BFF; color: #191A23; border: none;
        padding: 8px 12px; border-radius: 8px; font-weight: 600;
        font-size: 13px;
    }
    QPushButton:hover { background-color: #7A89E8; }
    QPushButton#PrimaryAction { background-color: #4e80ee; color: #ffffff; }
    QPushButton#PrimaryAction:hover { background-color: #4673d6; }
    QPushButton#FilterButton {
        background-color: transparent; color: #EAEAEA; border: 1px solid #474a4d;
        text-align: left; padding-right: 20px;
    }
    QPushButton#FilterButton:hover { background-color: #3a3b3c; }
    QPushButton#FilterButton::menu-indicator { position: absolute; right: 7px; top: 50%; margin-top: -4px; }
    
    QPushButton#ThemeButton {
        background-color: #3A404D; color: #EAEAEA;
        font-size: 16px; padding: 5px; border-radius: 15px;
    }
    QPushButton#QuickAddButton {
        background-color: #8A9BFF; color: #191A23;
        font-size: 28px; font-weight: 300;
        padding: 0px; padding-bottom: 4px; border-radius: 23px;
    }

    /* --- CHECKBOXES --- */
    QCheckBox::indicator, QTableWidget::indicator {
        border: 1px solid #979ba5;
        width: 14px;
        height: 14px;
        border-radius: 4px;
        background-color: transparent;
    }
    QCheckBox::indicator:hover, QTableWidget::indicator:hover {
        border: 2px solid #8A9BFF;
    }
    QCheckBox::indicator:checked, QTableWidget::indicator:checked {
        background-color: #8A9BFF;
        border: 2px solid #8A9BFF;
    }
    
    /* --- BARRAS DE PROGRESO --- */
    QProgressBar { border: none; background-color: #191A23; border-radius: 6px; min-height: 12px; max-height: 12px; }
    QProgressBar::chunk { border-radius: 4px; margin: 2px; }
    QProgressBar[state="good"]::chunk { background-color: #98C379; }
    QProgressBar[state="warning"]::chunk { background-color: #E5C07B; }
    QProgressBar[state="critical"]::chunk { background-color: #E06C75; }
    
    /* --- WIDGETS DE ENTRADA --- */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {
        background-color: #232533; border: 1px solid #3A404D;
        padding: 7px 11px; border-radius: 8px; color: #EAEAEA;
    }

    QComboBox#ChartRangeCombo {
        min-width: 150px;
    }
    
    /* --- ESTILOS DE TABLA --- */
    QTableWidget { background-color: #232533; border: none; border-radius: 8px; gridline-color: transparent; }
    QHeaderView::section {
        background-color: transparent; padding: 10px 15px; border: none;
        border-bottom: 2px solid #3A404D; font-weight: 600; color: #979ba5; text-align: left;
    }
    QTableWidget::item { padding-left: 15px; border: none; border-bottom: 1px solid #3A404D; }
    QTableWidget::item:selected { background-color: #3A404D; color: #EAEAEA; }

    /* --- MENÚS --- */
    QMenu { background-color: #242526; border: 1px solid #3a3b3c; border-radius: 8px; padding: 5px; }
    QMenu::item { padding: 8px 20px; border-radius: 6px; }
    QMenu::item:selected { background-color: #3a3b3c; }
    QComboBox QAbstractItemView {
        background-color: #232533; border: 1px solid #3A404D;
        selection-background-color: #8A9BFF; selection-color: #191A23;
        color: #EAEAEA; outline: 0px;
    }
    
    /* --- OTROS --- */
    QLabel#NotificationLabel { padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 600; }
    QLabel#NotificationLabel[message_type="success"] { background-color: #98C379; color: #191A23; }
    QLabel#NotificationLabel[message_type="error"] { background-color: #E06C75; color: #191A23; }
    QTabWidget::pane { border: none; }
    QTabBar::tab {
        background: transparent; color: #979ba5; padding: 8px 18px;
        border-radius: 8px; font-weight: 600; margin-right: 5px;
    }
    QTabBar::tab:hover { background-color: #3A404D; color: #EAEAEA; }
    QTabBar::tab:selected { background-color: #8A9BFF; color: #191A23; }

    /* Estilos Tarjeta de Crédito */
    QFrame#CreditCardFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5C6784, stop:1 #3A404D); border-radius: 15px; }
    QLabel#CardBalance { font-size: 20px; font-weight: 700; color: #FFFFFF; }
    QLabel#CardType { font-size: 14px; font-weight: 600; color: #FFFFFF; font-style: italic; }
    QLabel#CardNumber { font-size: 16px; font-weight: 400; color: #FFFFFF; font-family: "Courier New", Courier, monospace; }
    QLabel#CardSubText { font-size: 10px; color: #D3D3D3; text-transform: uppercase; }
    QLabel#CardMainText { font-size: 13px; font-weight: 600; color: #FFFFFF; }
    QPushButton#CardNavButton { background-color: #3A404D; color: #EAEAEA; border: none; border-radius: 12px; font-weight: 700; }
    QPushButton#CardNavButton:hover { background-color: #4C566A; }
    QPushButton#CardVisibilityButton { background-color: transparent; border: none; padding: 0px; }
"""
