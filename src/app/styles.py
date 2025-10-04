# --- INICIO DE LA SOLUCIÓN ---
LIGHT_STYLE = """
    /* --- GENERAL --- */
    QWidget {
        background-color: #F5F7FA; /* Fondo principal más suave */
        color: #344767;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px; /* Tamaño de fuente base reducido */
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
        background-color: transparent; border: none; color: #6C757D;
        padding: 11px 15px; text-align: left; border-radius: 8px; font-size: 14px;
    }
    QPushButton#NavButton:hover { background-color: #F0F2F5; color: #344767; }
    QPushButton#NavButton:checked { background-color: #E6F0FF; color: #0d6efd; font-weight: 600; }

    /* --- TÍTULOS Y TEXTO --- */
    QLabel#DashboardTitle { font-size: 22px; font-weight: 700; color: #212529; }
    QLabel#Chart_Title, QLabel#MetricTitle { font-size: 15px; font-weight: 600; color: #344767; }
    QLabel#KPI_Title { font-size: 12px; color: #6C757D; font-weight: 500; }
    QLabel#KPI_Value { font-size: 20px; font-weight: 700; color: #212529; }
    QLabel#MetricValue { font-size: 22px; font-weight: 700; color: #212529; }
    QLabel#MetricComparison { font-size: 13px; font-weight: 600; color: #6C757D; }

    /* --- BOTONES --- */
    QPushButton {
        background-color: #0d6efd; color: white; border: none;
        padding: 9px 14px; border-radius: 8px; font-weight: 600;
    }
    QPushButton:hover { background-color: #0b5ed7; }
    
    QPushButton#ThemeButton {
        background-color: #E9ECEF; color: #495057;
        font-size: 16px; padding: 5px; border-radius: 15px;
    }
    QPushButton#QuickAddButton {
        background-color: #0d6efd; color: white;
        font-size: 28px; font-weight: 300;
        padding: 0px; padding-bottom: 4px; /* Ajuste para centrar el '+' */
        border-radius: 23px; /* Un poco más pequeño */
    }
    
    /* --- CAMPOS DE FORMULARIO --- */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {
        background-color: #FFFFFF; border: 1px solid #DEE2E6;
        padding: 7px 11px; border-radius: 8px; color: #344767;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus { border-color: #80BDFF; }
    
    /* --- TABLAS --- */
    QTableWidget {
        background-color: #FFFFFF; border: 1px solid #E0E0E0;
        border-radius: 12px; gridline-color: #E0E0E0; color: #344767;
        selection-background-color: #E6F0FF; selection-color: #0d6efd;
    }
    QHeaderView::section {
        background-color: #F7F8FA; padding: 9px 15px; border: none;
        font-weight: 600; color: #495057;
    }
"""

DARK_STYLE = """
    /* --- GENERAL --- */
    QWidget {
        background-color: #1F242E;
        color: #EAEAEA;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px;
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
        padding: 11px 15px; text-align: left; border-radius: 8px; font-size: 14px;
    }
    QPushButton#NavButton:hover { background-color: #3A404D; color: #EAEAEA; }
    QPushButton#NavButton:checked { background-color: #3A404D; color: #61AFEF; font-weight: 600; }
    
    /* --- TÍTULOS Y TEXTO --- */
    QLabel#DashboardTitle { font-size: 22px; font-weight: 600; color: #EAEAEA; }
    QLabel#Chart_Title, QLabel#MetricTitle { font-size: 15px; font-weight: 600; color: #EAEAEA; }
    QLabel#KPI_Title { font-size: 12px; color: #ABB2BF; font-weight: 500; }
    QLabel#KPI_Value { font-size: 20px; font-weight: 700; color: #EAEAEA; }
    QLabel#MetricValue { font-size: 22px; font-weight: 700; color: #EAEAEA; }
    QLabel#MetricComparison { font-size: 13px; font-weight: 600; color: #ABB2BF; }

    /* --- BOTONES --- */
    QPushButton {
        background-color: #61AFEF; color: #1F242E; border: none;
        padding: 9px 14px; border-radius: 8px; font-weight: 600;
    }
    QPushButton:hover { background-color: #569CD6; }
    QPushButton#ThemeButton {
        background-color: #3A404D; color: #EAEAEA;
        font-size: 16px; padding: 5px; border-radius: 15px;
    }
    QPushButton#QuickAddButton {
        background-color: #61AFEF; color: #1F242E;
        font-size: 28px; font-weight: 300;
        padding: 0px; padding-bottom: 4px;
        border-radius: 23px;
    }
    
    /* --- CAMPOS DE FORMULARIO --- */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {
        background-color: #2D323C; border: 1px solid #4C566A;
        padding: 7px 11px; border-radius: 8px; color: #EAEAEA;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus { border-color: #61AFEF; }

    /* --- TABLAS --- */
    QTableWidget {
        background-color: #282D38; border: 1px solid #3A404D;
        border-radius: 12px; gridline-color: #3A404D; color: #EAEAEA;
        selection-background-color: #3A404D; selection-color: #61AFEF;
    }
    QHeaderView::section {
        background-color: #3A404D; padding: 9px 15px; border: none;
        font-weight: 600; color: #EAEAEA;
    }
"""
# --- FIN DE LA SOLUCIÓN ---