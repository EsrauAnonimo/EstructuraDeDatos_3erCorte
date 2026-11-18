# Paleta de colores principal de la interfaz
PRIMARY = "#2563EB"
SUCCESS = "#10B981"
DANGER = "#EF4444"
WARNING = "#F59E0B"
INDIGO = "#6366F1"
CYAN = "#0EA5E9"
BG = "#F1F5F9"
PANEL = "#FFFFFF"
TEXT = "#0F172A"
MUTED = "#64748B"

# Colores para el dibujo del árbol en Graphviz
NODE_ACTIVE_FILL = "#EFF6FF"
NODE_ACTIVE_BORDER = "#2563EB"
NODE_ACTIVE_TEXT = "#0F172A"

NODE_INACTIVE_FILL = "#E5E7EB"
NODE_INACTIVE_BORDER = "#9CA3AF"
NODE_INACTIVE_TEXT = "#6B7280"

HIGHLIGHT_SEARCH_FILL = "#FDE68A"
HIGHLIGHT_SEARCH_BORDER = "#DC2626"

HIGHLIGHT_PLAY_FILL = "#BBF7D0"
HIGHLIGHT_PLAY_BORDER = "#16A34A"

HIGHLIGHT_VISIT_FILL = "#E0E7FF"
HIGHLIGHT_VISIT_BORDER = "#4F46E5"

HIGHLIGHT_INSERT_FILL = "#A7F3D0"
HIGHLIGHT_INSERT_BORDER = "#059669"

HIGHLIGHT_ROTATE_FILL = "#FED7AA"
HIGHLIGHT_ROTATE_BORDER = "#EA580C"

EDGE_COLOR = "#64748B"

# Hoja de estilos Qt (QSS) moderna y limpia
APP_QSS = f"""
QMainWindow, QWidget#centralWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI", sans-serif;
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

QSpinBox {{
    background-color: #F8FAFC;
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px 10px;
    color: {TEXT};
}}

QMessageBox QPushButton, QInputDialog QPushButton {{
    min-width: 84px;
    padding: 7px 14px;
}}

QFrame#headerBar {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #0F172A,
        stop: 0.55 #1E293B,
        stop: 1 #1D4ED8
    );
    border-radius: 14px;
}}

QLabel#headerTitle {{
    color: #FFFFFF;
    font-size: 13.5pt;
    font-weight: 700;
}}

QLabel#headerSubtitle {{
    color: #CBD5E1;
    font-size: 9.5pt;
}}

QLabel#statBadge {{
    background-color: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.24);
    border-radius: 9px;
    padding: 5px 12px;
    color: #F8FAFC;
    font-size: 9.5pt;
    font-weight: 600;
}}

QFrame#card {{
    background-color: {PANEL};
    border: 1px solid #E2E8F0;
    border-radius: 14px;
}}

QLabel#cardTitle {{
    color: {TEXT};
    font-size: 11pt;
    font-weight: 700;
}}

QLabel#fieldLabel {{
    color: #475569;
    font-size: 9.5pt;
    font-weight: 600;
}}

QFrame#softDivider {{
    background-color: #E2E8F0;
    max-height: 1px;
    border: none;
}}

QLineEdit {{
    background-color: #F8FAFC;
    border: 1.5px solid #CBD5E1;
    border-radius: 9px;
    padding: 8px 12px;
    font-size: 10.5pt;
    color: {TEXT};
    min-height: 22px;
}}

QLineEdit:focus {{
    background-color: #FFFFFF;
    border: 1.5px solid {PRIMARY};
}}

QComboBox {{
    background-color: #F8FAFC;
    border: 1.5px solid #CBD5E1;
    border-radius: 9px;
    padding: 6px 10px;
    font-size: 9.8pt;
    color: {TEXT};
    min-height: 22px;
}}

QComboBox:hover, QComboBox:focus {{
    border: 1.5px solid {PRIMARY};
    background-color: #FFFFFF;
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
    background-color: #FFFFFF;
    color: {TEXT};
    padding: 6px 10px;
    border-radius: 6px;
    min-height: 22px;
}}

QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {{
    background-color: #DBEAFE;
    color: {TEXT};
}}

QCheckBox {{
    background-color: transparent;
    color: #334155;
    font-size: 9.5pt;
    font-weight: 600;
    spacing: 8px;
}}

QPushButton {{
    background-color: {PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: 9px;
    padding: 8px 12px;
    font-size: 9.8pt;
    font-weight: 600;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: #1D4ED8;
}}

QPushButton:pressed {{
    background-color: #1E40AF;
}}

QPushButton:disabled {{
    background-color: #CBD5E1;
    color: #F8FAFC;
}}

QPushButton#btnSuccess {{
    background-color: {SUCCESS};
}}
QPushButton#btnSuccess:hover {{
    background-color: #059669;
}}

QPushButton#btnDanger {{
    background-color: {DANGER};
}}
QPushButton#btnDanger:hover {{
    background-color: #DC2626;
}}

QPushButton#btnSoftDanger {{
    background-color: #FEF2F2;
    color: #DC2626;
    border: 1.5px solid #FECACA;
}}
QPushButton#btnSoftDanger:hover {{
    background-color: #FEE2E2;
    border-color: #FCA5A5;
}}

QPushButton#btnWarning {{
    background-color: {WARNING};
    color: #FFFFFF;
}}
QPushButton#btnWarning:hover {{
    background-color: #D97706;
}}

QPushButton#btnIndigo {{
    background-color: {INDIGO};
}}
QPushButton#btnIndigo:hover {{
    background-color: #4F46E5;
}}

QPushButton#btnPlay {{
    background-color: {CYAN};
}}
QPushButton#btnPlay:hover {{
    background-color: #0284C7;
}}

QPushButton#btnSecondary {{
    background-color: #64748B;
}}
QPushButton#btnSecondary:hover {{
    background-color: #475569;
}}

QFrame#treeFrame {{
    background-color: #FAFCFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 12px;
}}

QLabel#traversalValue {{
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 7px 10px;
    font-family: "Consolas", "Segoe UI", monospace;
    font-size: 9.5pt;
    color: {TEXT};
    min-height: 18px;
}}

QLabel#animBanner {{
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 9px;
    padding: 8px 12px;
    color: #334155;
    font-size: 9.8pt;
    font-weight: 600;
}}

QLabel#legendChip {{
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 8.5pt;
    font-weight: 600;
    color: #475569;
}}

QStatusBar {{
    background-color: {PANEL};
    border-top: 1px solid #E2E8F0;
    color: #475569;
    font-size: 9.5pt;
    font-weight: 600;
    padding: 4px 14px;
}}
"""
