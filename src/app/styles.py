LIGHT_STYLE = """
    /* --- GENERAL --- */
    QWidget {
        background-color: #F7F8FA; /* Fondo principal claro */
        color: #344767;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 14px;
    }
    QFrame {
        border: none;
        background-color: transparent;
    }

    /* --- TARJETAS (Cards) --- */
    QFrame#Card, QFrame#ListItemCard, QFrame#Chart_Card, QFrame#KPI_Card, QFrame#MetricCard {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E9ECEF;
    }

    /* --- PANEL DE NAVEGACIÓN --- */
    QFrame#NavPanel {
        background-color: #FFFFFF;
        border-right: 1px solid #E9ECEF;
    }
    QPushButton#NavButton {
        background-color: transparent;
        border: none;
        color: #6C757D;
        padding: 12px 15px;
        text-align: left;
        border-radius: 8px;
        font-size: 15px;
    }
    QPushButton#NavButton:hover {
        background-color: #F0F2F5;
        color: #344767;
    }
    QPushButton#NavButton:checked {
        background-color: #E6F0FF;
        color: #0d6efd;
        font-weight: 600;
    }

    /* --- TÍTULOS --- */
    QLabel#DashboardTitle {
        font-size: 24px;
        font-weight: 700;
        color: #212529;
    }
    QLabel#Chart_Title, QFrame#MetricCard QLabel {
        font-size: 16px;
        font-weight: 600;
        color: #344767;
    }
    QLabel#KPI_Title {
        font-size: 13px;
        color: #6C757D;
        font-weight: 500;
    }
    QLabel#KPI_Value, QFrame#MetricCard QLabel#MetricValue {
        font-size: 24px;
        font-weight: 700;
        color: #212529;
    }
    QLabel#KPI_Comparison {
        font-size: 12px;
        font-weight: 600;
    }
    QLabel#KPI_Comparison[state="positive"] { color: #28A745; }
    QLabel#KPI_Comparison[state="negative"] { color: #DC3545; }
    
    /* --- BOTONES --- */
    QPushButton {
        background-color: #0d6efd; color: white; border: none;
        padding: 10px 15px; border-radius: 8px; font-weight: 600;
    }
    QPushButton:hover { background-color: #0b5ed7; }
    
    QPushButton#ThemeButton {
        background-color: #E9ECEF; color: #495057;
        font-size: 18px; padding: 5px; border-radius: 17px;
    }
    QPushButton#QuickAddButton {
        background-color: #0d6efd; color: white;
        font-size: 32px; font-weight: bold; padding-bottom: 5px;
        border-radius: 25px;
    }
    
    /* --- CAMPOS DE FORMULARIO --- */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {
        background-color: #FFFFFF; border: 1px solid #DEE2E6;
        padding: 8px 12px; border-radius: 8px; color: #344767;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
        border-color: #80BDFF;
    }
    
    /* --- TABLAS --- */
    QTableWidget {
        background-color: #FFFFFF; border: 1px solid #E0E0E0;
        border-radius: 12px; gridline-color: #E0E0E0; color: #344767;
        selection-background-color: #E6F0FF; selection-color: #0d6efd;
    }
    QHeaderView::section {
        background-color: #F7F8FA; padding: 10px 15px; border: none;
        font-weight: 600; color: #495057;
    }
    
    /* --- BARRAS DE PROGRESO --- */
    QProgressBar {
        border: none; background-color: #E9ECEF; border-radius: 8px;
        text-align: center; color: #FFFFFF; min-height: 18px; font-weight: 600; font-size: 12px;
    }
    QProgressBar::chunk { border-radius: 8px; }
    QProgressBar[state="good"]::chunk { background-color: #28A745; }
    QProgressBar[state="warning"]::chunk { background-color: #FFC107; }
    QProgressBar[state="critical"]::chunk { background-color: #DC3545; }
    
    /* --- PESTAÑAS (Tabs) --- */
    QTabWidget::pane { border: none; }
    QTabBar::tab {
        background: #F0F2F5; color: #6C757D; padding: 10px 15px;
        border-top-left-radius: 8px; border-top-right-radius: 8px;
        margin-right: 2px; font-weight: 500;
    }
    QTabBar::tab:hover { background: #E9ECEF; }
    QTabBar::tab:selected { 
        background: #FFFFFF; color: #0d6efd; font-weight: 600; 
        border-bottom: 3px solid #0d6efd; margin-bottom: -3px;
    }
"""

DARK_STYLE = """
    /* --- GENERAL --- */
    QWidget {
        background-color: #1F242E;
        color: #EAEAEA;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 14px;
    }
    QFrame { border: none; background-color: transparent; }
    /* --- TARJETAS (Cards) --- */
    QFrame#Card, QFrame#ListItemCard, QFrame#Chart_Card, QFrame#KPI_Card, QFrame#MetricCard {
        background-color: #282D38;
        border-radius: 12px;
        border: 1px solid #3A404D;
    }
    /* --- PANEL DE NAVEGACIÓN --- */
    QFrame#NavPanel {
        background-color: #282D38;
        border-right: 1px solid #3A404D;
    }
    QPushButton#NavButton {
        background-color: transparent; border: none; color: #ABB2BF;
        padding: 12px 15px; text-align: left; border-radius: 8px; font-size: 15px;
    }
    QPushButton#NavButton:hover { background-color: #3A404D; color: #EAEAEA; }
    QPushButton#NavButton:checked { background-color: #3A404D; color: #61AFEF; font-weight: 600; }
    /* --- TÍTULOS --- */
    QLabel#DashboardTitle, QLabel#Chart_Title { font-size: 20px; font-weight: 600; color: #EAEAEA; }
    QLabel#KPI_Title, QFrame#MetricCard QLabel { font-size: 13px; color: #ABB2BF; font-weight: 500; }
    QLabel#KPI_Value, QFrame#MetricCard QLabel#MetricValue { font-size: 24px; font-weight: 700; color: #EAEAEA; }
    QLabel#KPI_Comparison { font-size: 12px; font-weight: 600; color: #98C379; }
    QLabel#KPI_Comparison[state="negative"] { color: #E06C75; }
    /* --- BOTONES --- */
    QPushButton {
        background-color: #61AFEF; color: #1F242E; border: none;
        padding: 10px 15px; border-radius: 8px; font-weight: 600;
    }
    QPushButton:hover { background-color: #569CD6; }
    QPushButton#ThemeButton {
        background-color: #3A404D; color: #EAEAEA;
        font-size: 18px; padding: 5px; border-radius: 17px;
    }
    QPushButton#QuickAddButton {
        background-color: #61AFEF; color: #1F242E;
        font-size: 32px; font-weight: bold; padding-bottom: 5px;
        border-radius: 25px;
    }
    /* --- CAMPOS DE FORMULARIO --- */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {
        background-color: #2D323C; border: 1px solid #4C566A;
        padding: 8px 12px; border-radius: 8px; color: #EAEAEA;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus { border-color: #61AFEF; }
    /* --- TABLAS --- */
    QTableWidget {
        background-color: #282D38; border: 1px solid #3A404D;
        border-radius: 12px; gridline-color: #3A404D; color: #EAEAEA;
        selection-background-color: #3A404D; selection-color: #61AFEF;
    }
    QHeaderView::section {
        background-color: #3A404D; padding: 10px 15px; border: none;
        font-weight: 600; color: #EAEAEA;
    }
    /* --- BARRAS DE PROGRESO --- */
    QProgressBar {
        border: none; background-color: #3A404D; border-radius: 8px;
        text-align: center; color: #EAEAEA; min-height: 18px; font-weight: 600; font-size: 12px;
    }
    QProgressBar::chunk { border-radius: 8px; }
    QProgressBar[state="good"]::chunk { background-color: #98C379; }
    QProgressBar[state="warning"]::chunk { background-color: #E5C07B; }
    QProgressBar[state="critical"]::chunk { background-color: #E06C75; }
    /* --- PESTAÑAS (Tabs) --- */
    QTabWidget::pane { border: none; }
    QTabBar::tab {
        background: #2D323C; color: #ABB2BF; padding: 10px 15px;
        border-top-left-radius: 8px; border-top-right-radius: 8px;
        margin-right: 2px; font-weight: 500;
    }
    QTabBar::tab:hover { background: #3A404D; }
    QTabBar::tab:selected { 
        background: #282D38; color: #61AFEF; font-weight: 600; 
        border-bottom: 3px solid #61AFEF; margin-bottom: -3px;
    }
"""