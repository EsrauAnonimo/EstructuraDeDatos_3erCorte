"""
Module: styles.py
Description: Design system for PERA: color palette, spacing and the Qt stylesheet (QSS).
"""

import icons

# ==============================================================================
# PALETA
# ==============================================================================
BG = "#F3F6FA"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F8FAFC"   # superficies secundarias (mapa, hover)
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
PRIMARY_PRESSED = "#1E40AF"
PRIMARY_SOFT = "#EFF6FF"  # fondo de elementos seleccionados
NAVY = "#14233B"
SECONDARY = "#60A5FA"
TEXT = "#172338"
MUTED = "#64748B"
SUBTLE = "#94A3B8"
BORDER = "#E2E8F0"
BORDER_STRONG = "#CBD5E1"
SUCCESS = "#22C55E"
SUCCESS_DARK = "#15803D"
WARNING = "#F59E0B"
DANGER = "#EF4444"
DANGER_DARK = "#B91C1C"

FONT_FAMILY = "Segoe UI"

# ==============================================================================
# COLORES DEL MAPA
# ==============================================================================
MAP_BG = SURFACE_ALT
MAP_EDGE = "#CBD5E1"
MAP_EDGE_INACTIVE = "#E2E8F0"
MAP_LABEL = MUTED
MAP_NODE_FILL = SURFACE
MAP_NODE_BORDER = "#1E3A5F"
MAP_NODE_INACTIVE_FILL = "#E2E8F0"
MAP_NODE_INACTIVE_BORDER = SUBTLE
MAP_ROUTE = PRIMARY
MAP_ORIGIN = SUCCESS
MAP_DESTINATION = DANGER


def build_qss() -> str:
    """Construye la hoja de estilos de la aplicación (usa iconos SVG como archivos)."""
    chevron = icons.icon_file("chevron_down", MUTED)
    check = icons.icon_file("check", "#FFFFFF", 3.0)

    return f"""
/* ---------------------------------------------------------------- base */
QMainWindow, QWidget#centralWidget {{
    background-color: {BG};
}}
QWidget {{
    color: {TEXT};
    font-family: "{FONT_FAMILY}";
    font-size: 9.5pt;
}}
QLabel {{
    background: transparent;
}}
QToolTip {{
    background-color: {NAVY};
    color: #F8FAFC;
    border: none;
    padding: 6px 8px;
    font-size: 9pt;
}}

/* ---------------------------------------------------------------- barra superior */
QFrame#topBar {{
    background-color: {NAVY};
}}
QLabel#appName {{
    color: #FFFFFF;
    font-size: 12.5pt;
    font-weight: 700;
}}
QLabel#appTagline {{
    color: {SUBTLE};
    font-size: 8.5pt;
}}
QPushButton#navButton {{
    background: transparent;
    color: #CBD5E1;
    border: none;
    border-radius: 8px;
    padding: 0 14px;
    min-height: 34px;
    max-height: 34px;
    font-weight: 600;
}}
QPushButton#navButton:hover {{
    background-color: rgba(255, 255, 255, 0.07);
    color: #FFFFFF;
}}
QPushButton#navButton:checked {{
    background-color: rgba(96, 165, 250, 0.18);
    color: #FFFFFF;
}}
QLabel#topMeta {{
    color: {SUBTLE};
    font-size: 9pt;
}}
QLabel#badgeOk, QLabel#badgeWarn {{
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 8.5pt;
    font-weight: 600;
}}
QLabel#badgeOk {{
    background-color: rgba(34, 197, 94, 0.16);
    color: #86EFAC;
}}
QLabel#badgeWarn {{
    background-color: rgba(245, 158, 11, 0.18);
    color: #FCD34D;
}}

/* ---------------------------------------------------------------- tarjetas y textos */
QFrame#card {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QFrame#mapSurface {{
    background-color: {MAP_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame#divider {{
    background-color: {BORDER};
    max-height: 1px;
    min-height: 1px;
    border: none;
}}
QLabel#pageTitle {{
    font-size: 14pt;
    font-weight: 700;
}}
QLabel#pageSubtitle, QLabel#muted {{
    color: {MUTED};
}}
QLabel#cardTitle {{
    font-size: 11pt;
    font-weight: 700;
}}
QLabel#sectionLabel {{
    color: {MUTED};
    font-size: 8pt;
    font-weight: 700;
}}
QLabel#hint {{
    color: {MUTED};
    font-size: 8.5pt;
}}
QLabel#countBadge {{
    background-color: {PRIMARY_SOFT};
    color: {PRIMARY};
    border-radius: 9px;
    padding: 1px 8px;
    font-size: 8.5pt;
    font-weight: 700;
}}

/* ---------------------------------------------------------------- botones */
QPushButton {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 0 14px;
    min-height: 34px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {SURFACE_ALT};
    border-color: {BORDER_STRONG};
}}
QPushButton:pressed {{
    background-color: #F1F5F9;
}}
QPushButton:focus {{
    border-color: {SECONDARY};
}}
QPushButton:disabled {{
    color: {SUBTLE};
    background-color: {SURFACE_ALT};
    border-color: {BORDER};
}}
QPushButton#primaryButton {{
    background-color: {PRIMARY};
    color: #FFFFFF;
    border: 1px solid {PRIMARY};
}}
QPushButton#primaryButton:hover {{
    background-color: {PRIMARY_HOVER};
    border-color: {PRIMARY_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: {PRIMARY_PRESSED};
}}
QPushButton#primaryButton:focus {{
    border-color: {PRIMARY_PRESSED};
}}
QPushButton#primaryButton:disabled {{
    background-color: #BFDBFE;
    border-color: #BFDBFE;
    color: #FFFFFF;
}}
QPushButton#dangerButton {{
    color: {DANGER_DARK};
    border-color: #FECACA;
}}
QPushButton#dangerButton:hover {{
    background-color: #FEF2F2;
    border-color: #FCA5A5;
}}
QPushButton#dangerButton:disabled {{
    color: {SUBTLE};
    border-color: {BORDER};
    background-color: {SURFACE_ALT};
}}
QPushButton#chip {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    min-height: 32px;
    padding: 0 10px;
    text-align: left;
    font-weight: 600;
    color: #334155;
}}
QPushButton#chip:hover {{
    border-color: {BORDER_STRONG};
    background-color: {SURFACE_ALT};
}}
QPushButton#chip:checked {{
    background-color: {PRIMARY_SOFT};
    border: 1px solid {PRIMARY};
    color: {PRIMARY};
}}
QPushButton#swapButton {{
    min-height: 32px;
    max-height: 32px;
    min-width: 32px;
    max-width: 32px;
    padding: 0;
    border-radius: 16px;
}}
QPushButton#swapButton:hover {{
    background-color: {PRIMARY_SOFT};
    border-color: #BFDBFE;
}}

/* Controles flotantes del mapa */
QFrame#mapControls {{
    background-color: rgba(255, 255, 255, 0.94);
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QToolButton#mapTool {{
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 5px;
}}
QToolButton#mapTool:hover {{
    background-color: #F1F5F9;
}}
QToolButton#mapTool:checked {{
    background-color: {PRIMARY_SOFT};
}}
QLabel#legendText {{
    color: #334155;
    font-size: 8.5pt;
}}

/* ---------------------------------------------------------------- entradas */
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 0 10px;
    min-height: 34px;
    selection-background-color: #BFDBFE;
    selection-color: {TEXT};
}}
QLineEdit:hover, QDoubleSpinBox:hover, QSpinBox:hover, QComboBox:hover {{
    border-color: {BORDER_STRONG};
}}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {PRIMARY};
}}
QLineEdit:disabled, QComboBox:disabled {{
    color: {MUTED};
    background-color: {SURFACE_ALT};
}}
QLineEdit#searchField {{
    background-color: {SURFACE_ALT};
    min-height: 32px;
}}
QLineEdit#searchField:focus {{
    background-color: {SURFACE};
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox::down-arrow {{
    image: url("{chevron}");
    width: 14px;
    height: 14px;
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: {PRIMARY_SOFT};
    selection-color: {TEXT};
}}
QComboBox QAbstractItemView::item {{
    min-height: 28px;
    padding: 0 8px;
    border-radius: 6px;
}}
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER_STRONG};
    border-radius: 4px;
    background-color: {SURFACE};
}}
QCheckBox::indicator:hover {{
    border-color: {PRIMARY};
}}
QCheckBox::indicator:checked {{
    background-color: {PRIMARY};
    border-color: {PRIMARY};
    image: url("{check}");
}}

/* ---------------------------------------------------------------- tablas */
QTableWidget {{
    background-color: {SURFACE};
    border: none;
    outline: 0;
    selection-background-color: {PRIMARY_SOFT};
    selection-color: {TEXT};
}}
QTableWidget::item {{
    padding: 0 10px;
    border-bottom: 1px solid #F1F5F9;
}}
QTableWidget::item:hover {{
    background-color: {SURFACE_ALT};
}}
QTableWidget::item:selected {{
    background-color: {PRIMARY_SOFT};
    color: {TEXT};
}}
QHeaderView::section {{
    background-color: {SURFACE};
    color: {MUTED};
    font-size: 8pt;
    font-weight: 700;
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px 10px;
}}
QLabel#pillSuccess, QLabel#pillMuted {{
    border-radius: 9px;
    padding: 2px 9px;
    font-size: 8.5pt;
    font-weight: 600;
}}
QLabel#pillSuccess {{
    background-color: #DCFCE7;
    color: {SUCCESS_DARK};
}}
QLabel#pillMuted {{
    background-color: #F1F5F9;
    color: {MUTED};
}}

/* ---------------------------------------------------------------- resultado de ruta */
QLabel#routeTitle {{
    font-size: 11.5pt;
    font-weight: 700;
}}
QFrame#metricTile {{
    background-color: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QLabel#metricLabel {{
    color: {MUTED};
    font-size: 8.5pt;
}}
QLabel#metricValue {{
    font-size: 12pt;
    font-weight: 700;
}}
QFrame#totalTile {{
    background-color: {PRIMARY_SOFT};
    border: 1px solid #BFDBFE;
    border-radius: 10px;
}}
QLabel#totalValue {{
    color: {PRIMARY};
    font-size: 14pt;
    font-weight: 700;
}}
QLabel#legIndex {{
    background-color: {PRIMARY_SOFT};
    color: {PRIMARY};
    border-radius: 10px;
    font-size: 8pt;
    font-weight: 700;
}}
QLabel#legTitle {{
    font-weight: 600;
}}
QFrame#errorBox {{
    background-color: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: 10px;
}}
QLabel#errorText {{
    color: {DANGER_DARK};
    font-weight: 600;
}}
QLabel#emptyTitle {{
    font-weight: 700;
    font-size: 10pt;
}}

/* ---------------------------------------------------------------- dashboard */
QLabel#kpiValue {{
    font-size: 18pt;
    font-weight: 700;
}}
QLabel#kpiIcon {{
    background-color: {PRIMARY_SOFT};
    border-radius: 8px;
}}

/* ---------------------------------------------------------------- scroll y estado */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget#qt_scrollarea_viewport, QWidget#scrollContent {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_STRONG};
    min-height: 28px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {SUBTLE};
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_STRONG};
    min-width: 28px;
    border-radius: 3px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0;
    height: 0;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: transparent;
}}
QStatusBar {{
    background-color: {SURFACE};
    border-top: 1px solid {BORDER};
    color: {MUTED};
    font-size: 8.5pt;
}}
QStatusBar::item {{
    border: none;
}}

/* ---------------------------------------------------------------- diálogos */
QDialog, QMessageBox {{
    background-color: {SURFACE};
}}
QLabel#dialogTitle {{
    font-size: 12pt;
    font-weight: 700;
}}
QSplitter::handle {{
    background: transparent;
}}
"""
