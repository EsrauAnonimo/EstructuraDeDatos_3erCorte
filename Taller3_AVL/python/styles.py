# Paleta de colores principal de la interfaz
PRIMARY = "#2563EB"
SUCCESS = "#16A34A"
DANGER = "#DC2626"
WARNING = "#F59E0B"
BG = "#F8FAFC"
PANEL = "#FFFFFF"
TEXT = "#1E293B"

# Colores para el dibujo del árbol en Graphviz
NODE_ACTIVE_FILL = "#DBEAFE"
NODE_ACTIVE_BORDER = "#2563EB"
NODE_ACTIVE_TEXT = "#1E293B"

NODE_INACTIVE_FILL = "#E5E7EB"
NODE_INACTIVE_BORDER = "#9CA3AF"
NODE_INACTIVE_TEXT = "#6B7280"

HIGHLIGHT_SEARCH_FILL = "#FDE68A"
HIGHLIGHT_SEARCH_BORDER = "#DC2626"

HIGHLIGHT_PLAY_FILL = "#BBF7D0"
HIGHLIGHT_PLAY_BORDER = "#16A34A"

EDGE_COLOR = "#475569"

# Hoja de estilos Qt (QSS)
APP_QSS = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI", sans-serif;
    font-size: 10.5pt;
}}

QGroupBox {{
    background-color: {PANEL};
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 12px;
    padding: 14px;
    font-weight: 600;
    color: {TEXT};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: {PRIMARY};
}}

QLineEdit, QComboBox {{
    background-color: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-radius: 7px;
    padding: 7px 10px;
    font-size: 10.5pt;
    color: {TEXT};
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1.5px solid {PRIMARY};
}}

QPushButton {{
    background-color: {PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: 7px;
    padding: 8px 14px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #1D4ED8;
}}

QPushButton:pressed {{
    background-color: #1E40AF;
}}

QPushButton:disabled {{
    background-color: #94A3B8;
    color: #F1F5F9;
}}

QPushButton#btnSuccess {{
    background-color: {SUCCESS};
}}
QPushButton#btnSuccess:hover {{
    background-color: #15803D;
}}

QPushButton#btnDanger {{
    background-color: {DANGER};
}}
QPushButton#btnDanger:hover {{
    background-color: #B91C1C;
}}

QPushButton#btnWarning {{
    background-color: {WARNING};
    color: #FFFFFF;
}}
QPushButton#btnWarning:hover {{
    background-color: #D97706;
}}

QPushButton#btnSecondary {{
    background-color: #475569;
}}
QPushButton#btnSecondary:hover {{
    background-color: #334155;
}}

QLabel#traversalValue {{
    background-color: #F1F5F9;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 6px 10px;
    font-family: "Consolas", "Segoe UI", monospace;
    font-size: 10pt;
    color: {TEXT};
}}

QLabel#canvasLabel {{
    background-color: {PANEL};
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 16px;
    color: #64748B;
    font-size: 11pt;
}}

QStatusBar {{
    background-color: {PANEL};
    border-top: 1px solid #E2E8F0;
    color: {TEXT};
    font-weight: 600;
    padding: 4px 10px;
}}
"""
