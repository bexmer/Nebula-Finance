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
    QFrame#Card, QFrame#ListItemCard, QFrame#Chart_Card, QFrame#KPI_Card, QFrame#MetricCard, QFrame#NavPanel {
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
    
    QPushButton#NavButton:checked {
        background-color: #364765; /* Color de fondo solicitado */
        color: #FFFFFF; /* Color de texto blanco para contraste */
    }

    /* Estilo para centrar el ícono cuando el panel está colapsado */
    QPushButton#NavButton[collapsed="true"] {
        text-align: center;
        padding: 11px; /* Padding simétrico para centrar */
    }

    /* --- TEXTO --- */
    QLabel { color: #364765; }
    QLabel#DashboardTitle { 
        font-size: 22px; 
        font-weight: 700; 
        color: #364765;
    }
    QLabel#Chart_Title, QLabel#MetricTitle { font-size: 15px; font-weight: 600; color: #364765; }
    QLabel#KPI_Title, QLabel#MetricComparison { font-size: 12px; color: #979ba5; font-weight: 500; }
    QLabel#KPI_Value { font-size: 20px; font-weight: 700; color: #364765; }
    QLabel#MetricValue { font-size: 22px; font-weight: 700; color: #364765; }
    QLabel#BudgetPercentLabel {
        color: #979ba5;
        font-size: 11px;
    }

    /* --- OTROS BOTONES --- */
    QPushButton {
        background-color: #364765; color: white; border: none;
        padding: 9px 14px; border-radius: 8px; font-weight: 600;
    }
    QPushButton:hover { background-color: #2c3a54; }
    
    QPushButton#ThemeButton {
        background-color: #d5daed; color: #364765;
        font-size: 16px; padding: 5px; border-radius: 15px;
    }
    QPushButton#QuickAddButton {
        background-color: #364765; color: white;
        font-size: 28px; font-weight: 300;
        padding: 0px; padding-bottom: 4px;
        border-radius: 23px;
    }
    
    /* --- BARRAS DE PROGRESO --- */
    QProgressBar {
        border: none;
        background-color: #e8eaf6;
        border-radius: 6px;
        min-height: 12px;
        max-height: 12px;
    }
    QProgressBar::chunk {
        border-radius: 4px;
        margin: 2px;
    }
    QProgressBar[state="good"]::chunk { background-color: #28A745; }
    QProgressBar[state="warning"]::chunk { background-color: #FFC107; }
    QProgressBar[state="critical"]::chunk { background-color: #DC3545; }

    /* --- OTROS WIDGETS --- */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {
        background-color: #f4f4ff; border: 1px solid #d5daed;
        padding: 7px 11px; border-radius: 8px; color: #364765;
    }
    QHeaderView::section {
        background-color: #f4f4ff; padding: 9px 15px; border: none;
        font-weight: 600; color: #364765;
    }

    QComboBox QAbstractItemView {
        background-color: #d5daed;
        border: 1px solid #c5cbe0;
        selection-background-color: #364765;
        selection-color: #FFFFFF;
        color: #364765;
        outline: 0px;
    }
    
    QLabel#NotificationLabel {
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
    }
    QLabel#NotificationLabel[message_type="success"] {
        background-color: #28A745;
        color: #FFFFFF;
    }
    QLabel#NotificationLabel[message_type="error"] {
        background-color: #DC3545;
        color: #FFFFFF;
    }

    QTabWidget::pane { border: none; }
    QTabBar::tab {
        background: transparent;
        color: #979ba5;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        margin-right: 5px;
    }
    QTabBar::tab:hover {
        background-color: #E6F0FF;
        color: #364765;
    }
    QTabBar::tab:selected {
        background-color: #364765;
        color: #FFFFFF;
    }

    /* Estilos para la nueva tarjeta de crédito */
    QFrame#CreditCardFrame {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 #3E517A, stop:1 #2C3A54);
        border-radius: 15px;
    }
    QLabel#CardBalance {
        font-size: 20px;
        font-weight: 700;
        color: #FFFFFF;
    }
    QLabel#CardType {
        font-size: 14px;
        font-weight: 600;
        color: #FFFFFF;
        font-style: italic;
    }
    QLabel#CardNumber {
        font-size: 16px;
        font-weight: 400;
        color: #FFFFFF;
        font-family: "Courier New", Courier, monospace;
    }
    QLabel#CardSubText {
        font-size: 10px;
        color: #D3D3D3;
        text-transform: uppercase;
    }
    QLabel#CardMainText {
        font-size: 13px;
        font-weight: 600;
        color: #FFFFFF;
    }
    QPushButton#CardNavButton {
        background-color: #e8eaf6;
        color: #364765;
        border: none;
        border-radius: 12px;
        font-weight: 700;
    }
    QPushButton#CardNavButton:hover {
        background-color: #d5daed;
    }
     QPushButton#CardVisibilityButton {
        background-color: transparent;
        border: none;
        padding: 0px;
    }
"""

DARK_STYLE = """
    /* --- GENERAL --- */
    QWidget {
        background-color: #191A23;
        color: #EAEAEA;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 13px;
    }
    QFrame { border: none; background-color: transparent; }
    
    /* --- TARJETAS Y NAVEGACIÓN --- */
    QFrame#Card, QFrame#ListItemCard, QFrame#Chart_Card, QFrame#KPI_Card, QFrame#MetricCard, QFrame#NavPanel {
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
    QPushButton#NavButton:checked {
        background-color: #8A9BFF;
        color: #191A23;
    }

    QPushButton#NavButton[collapsed="true"] {
        text-align: center;
        padding: 11px;
    }

    /* --- TEXTO --- */
    QLabel { color: #EAEAEA; }
    QLabel#DashboardTitle {
        font-size: 22px; 
        font-weight: 600; 
        color: #EAEAEA;
    }
    QLabel#Chart_Title, QLabel#MetricTitle { font-size: 14px; font-weight: 600; color: #EAEAEA; }
    QLabel#KPI_Title, QLabel#MetricComparison { font-size: 11px; color: #979ba5; font-weight: 500; }
    QLabel#KPI_Value, QLabel#MetricValue { font-size: 18px; font-weight: 700; color: #EAEAEA; }
    QLabel#BudgetPercentLabel {
        color: #979ba5;
        font-size: 11px;
    }

    /* --- OTROS BOTONES --- */
    QPushButton {
        background-color: #8A9BFF; color: #191A23; border: none;
        padding: 8px 12px; border-radius: 8px; font-weight: 600;
        font-size: 13px;
    }
    QPushButton:hover { background-color: #7A89E8; }
    
    QPushButton#ThemeButton {
        background-color: #3A404D; color: #EAEAEA;
        font-size: 16px; padding: 5px; border-radius: 15px;
    }
    QPushButton#QuickAddButton {
        background-color: #8A9BFF; color: #191A23;
        font-size: 28px; font-weight: 300;
        padding: 0px; padding-bottom: 4px;
        border-radius: 23px;
    }
    
    /* --- BARRAS DE PROGRESO --- */
    QProgressBar {
        border: none;
        background-color: #191A23;
        border-radius: 6px;
        min-height: 12px;
        max-height: 12px;
    }
    QProgressBar::chunk {
        border-radius: 4px;
        margin: 2px;
    }
    QProgressBar[state="good"]::chunk { background-color: #98C379; }
    QProgressBar[state="warning"]::chunk { background-color: #E5C07B; }
    QProgressBar[state="critical"]::chunk { background-color: #E06C75; }
    
    /* --- OTROS WIDGETS --- */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {
        background-color: #232533; border: 1px solid #3A404D;
        padding: 7px 11px; border-radius: 8px; color: #EAEAEA;
    }
    QHeaderView::section {
        background-color: #232533; padding: 8px 15px; border: none;
        font-weight: 600; color: #EAEAEA;
    }

    QComboBox QAbstractItemView {
        background-color: #232533;
        border: 1px solid #3A404D;
        selection-background-color: #8A9BFF;
        selection-color: #191A23;
        color: #EAEAEA;
        outline: 0px;
    }

    QLabel#NotificationLabel {
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
    }
    QLabel#NotificationLabel[message_type="success"] {
        background-color: #98C379;
        color: #191A23;
    }
    QLabel#NotificationLabel[message_type="error"] {
        background-color: #E06C75;
        color: #191A23;
    }

    QTabWidget::pane { border: none; }
    QTabBar::tab {
        background: transparent;
        color: #979ba5;
        padding: 8px 18px;
        border-radius: 8px;
        font-weight: 600;
        margin-right: 5px;
    }
    QTabBar::tab:hover {
        background-color: #3A404D;
        color: #EAEAEA;
    }
    QTabBar::tab:selected {
        background-color: #8A9BFF;
        color: #191A23;
    }

    /* Estilos para la nueva tarjeta de crédito */
    QFrame#CreditCardFrame {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 #5C6784, stop:1 #3A404D);
        border-radius: 15px;
    }
    QLabel#CardBalance {
        font-size: 20px;
        font-weight: 700;
        color: #FFFFFF;
    }
    QLabel#CardType {
        font-size: 14px;
        font-weight: 600;
        color: #FFFFFF;
        font-style: italic;
    }
    QLabel#CardNumber {
        font-size: 16px;
        font-weight: 400;
        color: #FFFFFF;
        font-family: "Courier New", Courier, monospace;
    }
    QLabel#CardSubText {
        font-size: 10px;
        color: #D3D3D3;
        text-transform: uppercase;
    }
    QLabel#CardMainText {
        font-size: 13px;
        font-weight: 600;
        color: #FFFFFF;
    }
    QPushButton#CardNavButton {
        background-color: #3A404D;
        color: #EAEAEA;
        border: none;
        border-radius: 12px;
        font-weight: 700;
    }
    QPushButton#CardNavButton:hover {
        background-color: #4C566A;
    }
    QPushButton#CardVisibilityButton {
        background-color: transparent;
        border: none;
        padding: 0px;
    }
"""