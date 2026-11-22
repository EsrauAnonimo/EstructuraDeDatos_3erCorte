"""
Module: styles.py
Description: Theme palette, component styles, and QSS for the PERA application.
"""

# Paleta de colores principal
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
PRIMARY_PRESSED = "#1E40AF"

SUCCESS = "#16A34A"
SUCCESS_HOVER = "#15803D"

DANGER = "#DC2626"
DANGER_HOVER = "#B91C1C"

WARNING = "#F59E0B"
WARNING_HOVER = "#D97706"

BG = "#F8FAFC"
PANEL = "#FFFFFF"
TEXT = "#1E293B"
MUTED = "#64748B"
BORDER = "#E2E8F0"
INPUT_BG = "#FFFFFF"

# Colores para el grafo (matplotlib)
NODE_CITY_FILL = "#DBEAFE"
NODE_CITY_BORDER = "#2563EB"

NODE_ORIGIN_FILL = "#BBF7D0"
NODE_ORIGIN_BORDER = "#16A34A"

NODE_DEST_FILL = "#FDE68A"
NODE_DEST_BORDER = "#DC2626"

NODE_INACTIVE_FILL = "#E5E7EB"
NODE_INACTIVE_BORDER = "#9CA3AF"

EDGE_COLOR = "#475569"
EDGE_HIGHLIGHT = "#DC2626"

# Hoja de estilos Qt (QSS) moderna y profesional
APP_QSS = f"""
QMainWindow, QWidget#centralWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 10pt;
}}

QLabel {{
    background-color: transparent;
    color: {TEXT};
}}

QDialog, QMessageBox, QInputDialog {{
    background-color: {PANEL};
    color: {TEXT};
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}}

/* Barra superior / Header */
QFrame#headerFrame {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #0F172A,
        stop: 0.6 #1E293B,
        stop: 1 #1D4ED8
    );
    border-radius: 12px;
    padding: 12px 20px;
}}

QLabel#headerTitle {{
    color: #FFFFFF;
    font-size: 15pt;
    font-weight: 700;
}}

QLabel#headerSubtitle {{
    color: #94A3B8;
    font-size: 9.5pt;
}}

/* Pestañas (QTabWidget) */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 12px;
    background-color: {PANEL};
    top: -1px;
}}

QTabBar::tab {{
    background-color: #E2E8F0;
    color: #475569;
    border: 1px solid #CBD5E1;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 9px 22px;
    margin-right: 4px;
    font-weight: 600;
    font-size: 10pt;
}}

QTabBar::tab:hover {{
    background-color: #F1F5F9;
    color: {PRIMARY};
}}

QTabBar::tab:selected {{
    background-color: {PANEL};
    color: {PRIMARY};
    border: 1px solid {BORDER};
    border-bottom: 2px solid {PRIMARY};
    font-weight: 700;
}}

/* Contenedores y Tarjetas */
QGroupBox {{
    background-color: {PANEL};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 18px;
    padding-left: 14px;
    padding-right: 14px;
    padding-bottom: 14px;
    font-weight: 700;
    font-size: 10.5pt;
    color: {TEXT};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: {PRIMARY};
}}

/* Botones */
QPushButton {{
    background-color: {PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 10pt;
    font-weight: 600;
    min-height: 22px;
}}

QPushButton:hover {{
    background-color: {PRIMARY_HOVER};
}}

QPushButton:pressed {{
    background-color: {PRIMARY_PRESSED};
}}

QPushButton:disabled {{
    background-color: #CBD5E1;
    color: #94A3B8;
}}

QPushButton#btnSuccess {{
    background-color: {SUCCESS};
}}
QPushButton#btnSuccess:hover {{
    background-color: {SUCCESS_HOVER};
}}

QPushButton#btnDanger {{
    background-color: {DANGER};
}}
QPushButton#btnDanger:hover {{
    background-color: {DANGER_HOVER};
}}

QPushButton#btnWarning {{
    background-color: {WARNING};
}}
QPushButton#btnWarning:hover {{
    background-color: {WARNING_HOVER};
}}

QPushButton#btnSecondary {{
    background-color: #E2E8F0;
    color: #334155;
    border: 1px solid #CBD5E1;
}}
QPushButton#btnSecondary:hover {{
    background-color: #CBD5E1;
}}

/* Entradas de texto y combos */
QLineEdit, QDoubleSpinBox, QSpinBox {{
    background-color: {INPUT_BG};
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 7px 10px;
    color: {TEXT};
    font-size: 10pt;
}}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1.5px solid {PRIMARY};
}}

QComboBox {{
    background-color: {INPUT_BG};
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 7px 12px;
    color: {TEXT};
    font-size: 10pt;
    min-height: 22px;
}}

QComboBox:hover, QComboBox:focus {{
    border: 1.5px solid {PRIMARY};
}}

QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    color: {TEXT};
    border: 1px solid #CBD5E1;
    selection-background-color: #DBEAFE;
    selection-color: {TEXT};
    outline: none;
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 22px;
}}

/* Tablas */
QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: #F1F5F9;
    color: {TEXT};
    selection-background-color: #DBEAFE;
    selection-color: {TEXT};
}}

QHeaderView::section {{
    background-color: #F1F5F9;
    color: #334155;
    font-weight: 700;
    font-size: 9.5pt;
    border: none;
    border-bottom: 1.5px solid #CBD5E1;
    padding: 6px 10px;
}}

/* ScrollBars */
QScrollBar:vertical {{
    border: none;
    background: #F1F5F9;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: #CBD5E1;
    min-height: 24px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Barra de estado */
QStatusBar {{
    background-color: {PANEL};
    border-top: 1px solid {BORDER};
    color: #475569;
    font-size: 9.5pt;
    padding: 4px 12px;
}}
"""
