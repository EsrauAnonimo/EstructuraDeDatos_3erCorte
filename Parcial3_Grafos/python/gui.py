"""
Module: gui.py
Description: Main window of PERA: top bar navigation, routes planner with the
             interactive network map, network management and analytics dashboard.
"""

import os

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import graph_view
import icons
import styles
from dashboard import DashboardWidget
from graph import Graph, save_graph
from widgets import (
    RouteResultCard,
    StopMarker,
    MapLegend,
    card,
    divider,
    format_cop,
    format_hours,
    format_km,
    section_label,
    status_pill,
)

# Criterios disponibles: (texto, icono, explicación para el usuario)
CRITERIA = [
    ("Distancia", "ruler", "Busca el camino con menos kilómetros."),
    ("Tiempo", "clock", "Busca el camino que llega más rápido."),
    ("Peajes", "ticket", "Busca el camino que gasta menos en peajes."),
    ("Combustible", "fuel", "Busca el camino que gasta menos gasolina."),
    ("Combinada", "gauge", "Equilibra distancia, tiempo, peajes y combustible (25 % cada uno)."),
]

WEIGHT_MAP = {
    "Distancia": "distance_km",
    "Tiempo": "time_hours",
    "Peajes": "toll_cost_cop",
    "Combustible": "fuel_cost_cop",
}


def _style_dialog_buttons(btn_box: QDialogButtonBox):
    """Botones Guardar (principal) y Cancelar en los diálogos."""
    ok = btn_box.button(QDialogButtonBox.StandardButton.Ok)
    ok.setText("Guardar")
    ok.setObjectName("primaryButton")
    btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")


def _soft_shadow(widget: QWidget, blur: int = 18, alpha: int = 28):
    """Sombra suave para elementos flotantes."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 4)
    effect.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(effect)


def _button(text: str, icon_name: str | None = None, kind: str = "", icon_color: str = styles.TEXT) -> QPushButton:
    """Botón con icono SVG. kind: '' (secundario), 'primaryButton' o 'dangerButton'."""
    btn = QPushButton(text)
    if kind:
        btn.setObjectName(kind)
    if icon_name:
        btn.setIcon(icons.icon(icon_name, icon_color, 16))
        btn.setIconSize(QSize(16, 16))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


# ==============================================================================
# DIÁLOGOS MODALES PARA CRUD
# ==============================================================================

class CityDialog(QDialog):
    """Diálogo modal para agregar o editar los datos de una ciudad."""

    def __init__(self, parent=None, city_data=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Ciudad" if city_data else "Agregar Ciudad")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        form = QFormLayout()
        form.setSpacing(10)

        self.txt_id = QLineEdit()
        self.txt_id.setMaxLength(6)
        self.txt_id.setPlaceholderText("Ej. BOG")

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Ej. Bogotá")
        self.txt_department = QLineEdit()
        self.txt_department.setPlaceholderText("Ej. Cundinamarca")

        self.spn_lat = QDoubleSpinBox()
        self.spn_lat.setRange(-90.0, 90.0)
        self.spn_lat.setDecimals(4)
        self.spn_lat.setSingleStep(0.1)

        self.spn_lon = QDoubleSpinBox()
        self.spn_lon.setRange(-180.0, 180.0)
        self.spn_lon.setDecimals(4)
        self.spn_lon.setSingleStep(0.1)

        self.spn_fuel = QDoubleSpinBox()
        self.spn_fuel.setRange(0.0, 100000.0)
        self.spn_fuel.setDecimals(2)
        self.spn_fuel.setValue(16000.0)
        self.spn_fuel.setPrefix("$ ")

        self.chk_active = QCheckBox("Ciudad Activa en la Red")
        self.chk_active.setChecked(True)

        if city_data:
            self.txt_id.setText(city_data.get("id", ""))
            self.txt_id.setEnabled(False)  # El ID es inmutable en edición
            self.txt_name.setText(city_data.get("name", ""))
            self.txt_department.setText(city_data.get("department", "N/A"))
            self.spn_lat.setValue(city_data.get("lat", 0.0))
            self.spn_lon.setValue(city_data.get("lon", 0.0))
            self.spn_fuel.setValue(city_data.get("fuel_price_cop", 16000.0))
            self.chk_active.setChecked(city_data.get("active", True))

        form.addRow("Identificador (ID):", self.txt_id)
        form.addRow("Nombre de Ciudad:", self.txt_name)
        form.addRow("Departamento:", self.txt_department)
        form.addRow("Latitud:", self.spn_lat)
        form.addRow("Longitud:", self.spn_lon)
        form.addRow("Precio Combustible (COP):", self.spn_fuel)
        form.addRow("Estado:", self.chk_active)
        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        _style_dialog_buttons(btn_box)
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _validate_and_accept(self):
        cid = self.txt_id.text().strip().upper()
        name = self.txt_name.text().strip()
        if not cid:
            QMessageBox.warning(self, "Validación", "El identificador (ID) de la ciudad es obligatorio.")
            return
        if not name:
            QMessageBox.warning(self, "Validación", "El nombre de la ciudad es obligatorio.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "id": self.txt_id.text().strip().upper(),
            "name": self.txt_name.text().strip(),
            "department": self.txt_department.text().strip() or "N/A",
            "lat": self.spn_lat.value(),
            "lon": self.spn_lon.value(),
            "fuel_price_cop": self.spn_fuel.value(),
            "active": self.chk_active.isChecked()
        }


class EdgeDialog(QDialog):
    """Diálogo modal para agregar o editar una arista vial."""

    def __init__(self, parent=None, cities: list[dict] = None, edge_data=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Arista Vial" if edge_data else "Agregar Arista Vial")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        form = QFormLayout()
        form.setSpacing(10)

        self.combo_from = QComboBox()
        self.combo_to = QComboBox()

        cities_sorted = sorted(cities or [], key=lambda c: c["name"])
        for c in cities_sorted:
            item_text = f"{c['id']} - {c['name']}"
            self.combo_from.addItem(item_text, c["id"])
            self.combo_to.addItem(item_text, c["id"])

        self.spn_dist = QDoubleSpinBox()
        self.spn_dist.setRange(1.0, 50000.0)
        self.spn_dist.setDecimals(1)
        self.spn_dist.setValue(100.0)
        self.spn_dist.setSuffix(" km")

        self.spn_time = QDoubleSpinBox()
        self.spn_time.setRange(0.1, 500.0)
        self.spn_time.setDecimals(2)
        self.spn_time.setValue(2.0)
        self.spn_time.setSuffix(" h")

        self.spn_toll = QDoubleSpinBox()
        self.spn_toll.setRange(0.0, 10000000.0)
        self.spn_toll.setDecimals(0)
        self.spn_toll.setValue(0.0)
        self.spn_toll.setPrefix("$ ")

        self.txt_category = QLineEdit("Primaria")
        self.chk_validated = QCheckBox("Ruta validada")
        self.chk_validated.setChecked(True)
        self.txt_source = QLineEdit("Google Maps")

        self.chk_bidirectional = QCheckBox("Crear también sentido inverso")
        self.chk_bidirectional.setChecked(True)

        if edge_data:
            idx_from = self.combo_from.findData(edge_data.get("from"))
            if idx_from >= 0:
                self.combo_from.setCurrentIndex(idx_from)
            idx_to = self.combo_to.findData(edge_data.get("to"))
            if idx_to >= 0:
                self.combo_to.setCurrentIndex(idx_to)

            self.combo_from.setEnabled(False)
            self.combo_to.setEnabled(False)
            self.spn_dist.setValue(edge_data.get("distance_km", 100.0))
            self.spn_time.setValue(edge_data.get("time_hours", 2.0))
            self.spn_toll.setValue(edge_data.get("toll_cost_cop", 0.0))
            self.txt_category.setText(edge_data.get("category", "Primaria"))
            self.chk_validated.setChecked(edge_data.get("validated", True))
            self.txt_source.setText(edge_data.get("source", "Google Maps"))
            self.chk_bidirectional.setText("Aplicar cambios también al sentido inverso")

        form.addRow("Ciudad Origen:", self.combo_from)
        form.addRow("Ciudad Destino:", self.combo_to)
        form.addRow("Distancia:", self.spn_dist)
        form.addRow("Tiempo estimado:", self.spn_time)
        form.addRow("Costo de Peajes (COP):", self.spn_toll)
        form.addRow("Categoría:", self.txt_category)
        form.addRow("Validación:", self.chk_validated)
        form.addRow("Fuente:", self.txt_source)
        form.addRow("Bidireccional:", self.chk_bidirectional)
        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        _style_dialog_buttons(btn_box)
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _validate_and_accept(self):
        u = self.combo_from.currentData()
        v = self.combo_to.currentData()
        if u == v:
            QMessageBox.warning(self, "Validación", "El origen y el destino de la arista no pueden ser iguales.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "from": self.combo_from.currentData(),
            "to": self.combo_to.currentData(),
            "distance_km": self.spn_dist.value(),
            "time_hours": self.spn_time.value(),
            "toll_cost_cop": self.spn_toll.value(),
            "category": self.txt_category.text().strip() or "Primaria",
            "validated": self.chk_validated.isChecked(),
            "source": self.txt_source.text().strip() or "Google Maps",
            "bidirectional": self.chk_bidirectional.isChecked()
        }


# ==============================================================================
# VENTANA PRINCIPAL
# ==============================================================================

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación PERA."""

    PAGE_ROUTES, PAGE_MANAGEMENT, PAGE_DASHBOARD = range(3)

    def __init__(self, graph: Graph, data_filepath: str = "graph_data.json"):
        super().__init__()
        self.graph = graph
        self.data_filepath = data_filepath
        self.current_path = []
        self.current_origin = None
        self.current_dest = None
        self._route_shown = False  # si hay una ruta en pantalla se recalcula al cambiar parámetros
        self._routes_calculated = 0

        self.setWindowTitle("PERA — Planificador Eficiente de Rutas Automotrices")
        self.resize(1380, 860)
        self.setMinimumSize(1100, 680)
        self.setStyleSheet(styles.build_qss())

        self._init_ui()
        self._load_cities_into_combos()
        self._populate_management_tables()
        self._update_network_status()
        self._refresh_graph_display()
        # El dashboard se calcula de forma perezosa al abrir su página

    def _init_ui(self):
        """Barra superior + páginas (Rutas, Gestión, Dashboard) + barra de estado."""
        central = QWidget(self)
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_top_bar())

        self.pages = QStackedWidget()
        self.page_routes = QWidget()
        self.page_management = QWidget()
        self.page_dashboard = QWidget()
        for page in (self.page_routes, self.page_management, self.page_dashboard):
            self.pages.addWidget(page)
        root.addWidget(self.pages, stretch=1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Red vial cargada con éxito.")

        self._build_routes_page()
        self._build_management_page()
        self._build_dashboard_page()
        self.nav_group.idClicked.connect(self._on_page_changed)

    # --------------------------------------------------------------------------
    # BARRA SUPERIOR Y NAVEGACIÓN
    # --------------------------------------------------------------------------
    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setFixedHeight(58)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(8)

        logo = QLabel()
        logo.setPixmap(icons.logo_pixmap(32))
        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        name = QLabel("PERA")
        name.setObjectName("appName")
        tagline = QLabel("Planificador Eficiente de Rutas Automotrices")
        tagline.setObjectName("appTagline")
        name_col.addStretch()
        name_col.addWidget(name)
        name_col.addWidget(tagline)
        name_col.addWidget(QLabel("Universidad Popular del Cesar — Ingeniería de Sistemas"))
        name_col.addStretch()
        layout.addWidget(logo)
        layout.addSpacing(4)
        layout.addLayout(name_col)
        layout.addSpacing(36)

        self.nav_group = QButtonGroup(self)
        for page_id, (icon_name, text) in enumerate([("route", "Rutas"), ("sliders", "Gestión"), ("chart", "Dashboard")]):
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setIcon(icons.icon(icon_name, styles.SUBTLE, 16, checked_color="#FFFFFF"))
            btn.setIconSize(QSize(16, 16))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_group.addButton(btn, page_id)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.nav_group.button(self.PAGE_ROUTES).setChecked(True)

        layout.addStretch()
        self.lbl_net_meta = QLabel()
        self.lbl_net_meta.setObjectName("topMeta")
        self.lbl_net_status = QLabel()
        layout.addWidget(self.lbl_net_meta)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_net_status, alignment=Qt.AlignmentFlag.AlignVCenter)
        return bar

    def _on_page_changed(self, index: int):
        """Cambia de página. El Dashboard solo recalcula lo marcado como sucio (dirty)."""
        self.pages.setCurrentIndex(index)
        self.nav_group.button(index).setChecked(True)
        if index == self.PAGE_DASHBOARD:
            self.dashboard_widget.refresh_if_needed()

    def _update_network_status(self):
        """Resumen real de la red en la barra superior y en el encabezado del mapa."""
        cities = self.graph.get_cities()
        edges = self.graph.get_edges()
        pairs = {tuple(sorted((e["from"], e["to"]))) for e in edges}
        self.lbl_net_meta.setText(f"{len(cities)} ciudades · {len(edges)} conexiones")
        self.lbl_map_subtitle.setText(
            f"{len(cities)} ciudades · {len(pairs)} tramos · posición según coordenadas geográficas"
        )

        connected = self.graph.is_connected()
        self.lbl_net_status.setText("Red conectada" if connected else "Red desconectada")
        self.lbl_net_status.setObjectName("badgeOk" if connected else "badgeWarn")
        self.lbl_net_status.setToolTip(
            "Todas las ciudades activas son alcanzables." if connected
            else "Hay ciudades activas que no se pueden alcanzar."
        )
        # Reaplicar el estilo tras cambiar el objectName
        self.lbl_net_status.style().unpolish(self.lbl_net_status)
        self.lbl_net_status.style().polish(self.lbl_net_status)

    # --------------------------------------------------------------------------
    # PÁGINA 1: RUTAS
    # --------------------------------------------------------------------------
    def _build_routes_page(self):
        layout = QHBoxLayout(self.page_routes)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        layout.addWidget(self._build_planner_panel())
        layout.addWidget(self._build_map_card(), stretch=1)

        # Enter calcula la ruta mientras el foco esté en esta página
        for key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            shortcut = QShortcut(QKeySequence(key), self.page_routes)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(self._calculate_route)

    def _build_planner_panel(self) -> QFrame:
        """Panel lateral: origen/destino, criterio, acciones y resultado."""
        panel = card()
        panel.setFixedWidth(370)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("scrollContent")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        # --- Origen y destino
        lay.addWidget(section_label("Planificar viaje"))
        stops = QGridLayout()
        stops.setHorizontalSpacing(10)
        stops.setVerticalSpacing(8)
        self.combo_origin = QComboBox()
        self.combo_origin.setToolTip("Ciudad de origen")
        self.combo_dest = QComboBox()
        self.combo_dest.setToolTip("Ciudad de destino")
        self.btn_swap = QPushButton()
        self.btn_swap.setObjectName("swapButton")
        self.btn_swap.setIcon(icons.icon("swap", styles.PRIMARY, 16))
        self.btn_swap.setIconSize(QSize(16, 16))
        self.btn_swap.setToolTip("Intercambiar origen y destino")
        self.btn_swap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_swap.clicked.connect(self._swap_cities)
        stops.addWidget(StopMarker(), 0, 0, 2, 1)
        stops.addWidget(self.combo_origin, 0, 1)
        stops.addWidget(self.combo_dest, 1, 1)
        stops.addWidget(self.btn_swap, 0, 2, 2, 1, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(stops)

        # --- Criterio de optimización (botones seleccionables)
        lay.addSpacing(4)
        lay.addWidget(section_label("Criterio de optimización"))
        chips = QGridLayout()
        chips.setSpacing(8)
        self.criterion_group = QButtonGroup(self)
        for i, (text, icon_name, _hint) in enumerate(CRITERIA):
            chip = QPushButton(text)
            chip.setObjectName("chip")
            chip.setCheckable(True)
            chip.setIcon(icons.icon(icon_name, styles.MUTED, 15, checked_color=styles.PRIMARY))
            chip.setIconSize(QSize(15, 15))
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            self.criterion_group.addButton(chip, i)
            if i == len(CRITERIA) - 1:
                chips.addWidget(chip, i // 2, 0, 1, 2)
            else:
                chips.addWidget(chip, i // 2, i % 2)
        self.criterion_group.button(0).setChecked(True)
        lay.addLayout(chips)

        self.lbl_criterion_hint = QLabel()
        self.lbl_criterion_hint.setObjectName("hint")
        self.lbl_criterion_hint.setWordWrap(True)
        lay.addWidget(self.lbl_criterion_hint)

        # --- Acciones
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.btn_calculate = _button("Calcular ruta", "navigation", "primaryButton", "#FFFFFF")
        self.btn_calculate.setMinimumHeight(38)
        self.btn_calculate.setToolTip("Atajo: Enter")
        self.btn_calculate.clicked.connect(self._calculate_route)
        self.btn_clear = _button("Limpiar", "x", icon_color=styles.MUTED)
        self.btn_clear.setMinimumHeight(38)
        self.btn_clear.setToolTip("Quitar la ruta del mapa")
        self.btn_clear.clicked.connect(self._clear_route)
        actions.addWidget(self.btn_calculate, stretch=1)
        actions.addWidget(self.btn_clear)
        lay.addLayout(actions)

        # --- Resultado
        lay.addSpacing(4)
        lay.addWidget(divider())
        lay.addSpacing(2)
        lay.addWidget(section_label("Resultado"))
        self.result_card = RouteResultCard()
        lay.addWidget(self.result_card)
        lay.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

        # Cambiar un parámetro recalcula al instante si ya hay una ruta en pantalla
        self.combo_origin.currentIndexChanged.connect(self._on_params_changed)
        self.combo_dest.currentIndexChanged.connect(self._on_params_changed)
        self.criterion_group.idClicked.connect(self._on_params_changed)
        self._update_criterion_hint()
        return panel

    def _build_map_card(self) -> QFrame:
        """Mapa de la red: encabezado, lienzo, controles y leyenda flotantes."""
        map_card = card()
        lay = QVBoxLayout(map_card)
        lay.setContentsMargins(18, 14, 18, 18)
        lay.setSpacing(12)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(1)
        title = QLabel(graph_view.TITLE)
        title.setObjectName("cardTitle")
        self.lbl_map_subtitle = QLabel()
        self.lbl_map_subtitle.setObjectName("hint")
        titles.addWidget(title)
        titles.addWidget(self.lbl_map_subtitle)
        header.addLayout(titles, stretch=1)

        mouse = QLabel()
        mouse.setPixmap(icons.pixmap("mouse", styles.SUBTLE, 14))
        help_text = QLabel("Clic izq.: origen · Clic der.: destino · Rueda: zoom · Arrastrar: mover")
        help_text.setObjectName("hint")
        header.addWidget(mouse)
        header.addWidget(help_text)
        lay.addLayout(header)

        surface = QFrame()
        surface.setObjectName("mapSurface")
        grid = QGridLayout(surface)
        grid.setContentsMargins(1, 1, 1, 1)

        self.graph_canvas = graph_view.GraphCanvas(surface)
        self.graph_canvas.city_clicked.connect(self._on_graph_city_clicked)
        grid.addWidget(self.graph_canvas, 0, 0)

        # Controles superpuestos al mapa (misma celda de la cuadrícula)
        grid.addWidget(self._floating(self._build_map_controls()), 0, 0,
                       Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        lay.addWidget(surface, stretch=1)
        # Leyenda debajo del mapa: nunca tapa ciudades
        lay.addWidget(MapLegend())
        return map_card

    @staticmethod
    def _floating(widget: QWidget) -> QWidget:
        """Envuelve un widget flotante con margen respecto al borde del mapa."""
        holder = QWidget()
        layout = QVBoxLayout(holder)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(widget)
        return holder

    def _build_map_controls(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("mapControls")
        _soft_shadow(frame)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(2)

        def tool(icon_name, tip, slot, checkable=False):
            btn = QToolButton()
            btn.setObjectName("mapTool")
            btn.setIcon(icons.icon(icon_name, "#334155", 18, checked_color=styles.PRIMARY))
            btn.setIconSize(QSize(18, 18))
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if checkable:
                btn.setCheckable(True)
                btn.setChecked(True)
                btn.toggled.connect(slot)
            else:
                btn.clicked.connect(slot)
            lay.addWidget(btn)
            return btn

        tool("zoom_in", "Acercar", lambda *_: self.graph_canvas.zoom(0.8))
        tool("zoom_out", "Alejar", lambda *_: self.graph_canvas.zoom(1.25))
        tool("fit", "Ver toda la red", lambda *_: self.graph_canvas.reset_view())
        sep = divider()
        sep.setFixedWidth(22)
        lay.addWidget(sep, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.btn_toggle_distances = tool("tag", "Mostrar u ocultar distancias", self.graph_canvas.set_show_distances, True)
        self.btn_toggle_names = tool("type", "Mostrar u ocultar nombres de ciudades", self.graph_canvas.set_show_names, True)
        return frame

    # --------------------------------------------------------------------------
    # PÁGINA 2: GESTIÓN
    # --------------------------------------------------------------------------
    def _build_management_page(self):
        layout = QVBoxLayout(self.page_management)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(16)

        head = QVBoxLayout()
        head.setSpacing(2)
        title = QLabel("Gestión de la red")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Administra ciudades y conexiones viales. Cada cambio se guarda automáticamente en "
            f"{os.path.basename(self.data_filepath)}."
        )
        subtitle.setObjectName("pageSubtitle")
        head.addWidget(title)
        head.addWidget(subtitle)
        layout.addLayout(head)

        # --- Ciudades
        self.tbl_cities = self._make_table(
            ["ID", "Nombre", "Departamento", "Latitud", "Longitud", "Gasolina", "Estado"])
        self.tbl_cities.doubleClicked.connect(self._handle_modify_city)
        self.tbl_cities.itemSelectionChanged.connect(self._update_management_buttons)

        self.btn_add_city = _button("Agregar ciudad", "plus", "primaryButton", "#FFFFFF")
        self.btn_add_city.clicked.connect(self._handle_add_city)
        self.btn_mod_city = _button("Editar", "pencil")
        self.btn_mod_city.clicked.connect(self._handle_modify_city)
        self.btn_toggle_city = _button("Desactivar", "power")
        self.btn_toggle_city.clicked.connect(self._handle_toggle_city)
        self.btn_del_city = _button("Eliminar", "trash", "dangerButton", styles.DANGER_DARK)
        self.btn_del_city.clicked.connect(self._handle_delete_city)
        self.txt_search_cities = self._make_search("Buscar ciudad...")
        self.txt_search_cities.textChanged.connect(lambda: self._filter_table(self.tbl_cities, self.txt_search_cities))

        cities_card, self.lbl_cities_count = self._table_card(
            "Ciudades", self.txt_search_cities, self.tbl_cities,
            [self.btn_add_city, self.btn_mod_city, self.btn_toggle_city], [self.btn_del_city])

        # --- Conexiones
        self.tbl_edges = self._make_table(
            ["Desde", "Hasta", "Distancia", "Tiempo", "Peaje", "Combustible", "Categoría", "Activa", "Validada", "Fuente"])
        self.tbl_edges.doubleClicked.connect(self._handle_modify_edge)
        self.tbl_edges.itemSelectionChanged.connect(self._update_management_buttons)

        self.btn_add_edge = _button("Agregar conexión", "plus", "primaryButton", "#FFFFFF")
        self.btn_add_edge.clicked.connect(self._handle_add_edge)
        self.btn_mod_edge = _button("Editar", "pencil")
        self.btn_mod_edge.clicked.connect(self._handle_modify_edge)
        self.btn_toggle_edge = _button("Desactivar", "power")
        self.btn_toggle_edge.clicked.connect(self._handle_toggle_edge)
        self.btn_del_edge = _button("Eliminar", "trash", "dangerButton", styles.DANGER_DARK)
        self.btn_del_edge.clicked.connect(self._handle_delete_edge)
        self.txt_search_edges = self._make_search("Buscar por ciudad, p. ej. BOG...")
        self.txt_search_edges.textChanged.connect(lambda: self._filter_table(self.tbl_edges, self.txt_search_edges))

        edges_card, self.lbl_edges_count = self._table_card(
            "Conexiones viales", self.txt_search_edges, self.tbl_edges,
            [self.btn_add_edge, self.btn_mod_edge, self.btn_toggle_edge], [self.btn_del_edge])

        cards = QHBoxLayout()
        cards.setSpacing(16)
        cards.addWidget(cities_card, stretch=1)
        cards.addWidget(edges_card, stretch=1)
        layout.addLayout(cards, stretch=1)

    @staticmethod
    def _make_table(headers: list[str]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels([h.upper() for h in headers])
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(38)
        table.setShowGrid(False)
        table.setWordWrap(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setToolTip("Doble clic para editar")
        return table

    @staticmethod
    def _make_search(placeholder: str) -> QLineEdit:
        search = QLineEdit()
        search.setObjectName("searchField")
        search.setPlaceholderText(placeholder)
        search.setClearButtonEnabled(True)
        search.addAction(icons.icon("search", styles.SUBTLE, 16), QLineEdit.ActionPosition.LeadingPosition)
        search.setFixedWidth(230)
        return search

    @staticmethod
    def _table_card(title: str, search: QLineEdit, table: QTableWidget,
                    left_buttons: list, right_buttons: list) -> tuple:
        """Tarjeta de tabla: título + contador + buscador, barra de acciones y tabla."""
        frame = card()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(18, 16, 18, 12)
        lay.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(8)
        lbl = QLabel(title)
        lbl.setObjectName("cardTitle")
        count = QLabel("0")
        count.setObjectName("countBadge")
        head.addWidget(lbl)
        head.addWidget(count)
        head.addStretch()
        head.addWidget(search)
        lay.addLayout(head)

        bar = QHBoxLayout()
        bar.setSpacing(8)
        for btn in left_buttons:
            bar.addWidget(btn)
        bar.addStretch()
        for btn in right_buttons:
            bar.addWidget(btn)
        lay.addLayout(bar)
        lay.addWidget(table, stretch=1)
        return frame, count

    def _build_dashboard_page(self):
        layout = QVBoxLayout(self.page_dashboard)
        layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_widget = DashboardWidget(self.graph, self)
        layout.addWidget(self.dashboard_widget)

    # --------------------------------------------------------------------------
    # POBLACIÓN Y GESTIÓN DE TABLAS
    # --------------------------------------------------------------------------
    @staticmethod
    def _cell(text: str, align_right: bool = False, bold: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if align_right:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if bold:
            font = item.font()
            font.setWeight(600)
            item.setFont(font)
        return item

    def _populate_management_tables(self):
        """Actualiza el contenido de las tablas de gestión con los datos del grafo."""
        cities = sorted(self.graph.get_cities(), key=lambda c: c["id"])
        self.tbl_cities.setRowCount(len(cities))
        for row, c in enumerate(cities):
            is_active = c.get("active", True)
            self.tbl_cities.setItem(row, 0, self._cell(c["id"], bold=True))
            self.tbl_cities.setItem(row, 1, self._cell(c["name"]))
            self.tbl_cities.setItem(row, 2, self._cell(c.get("department", "N/A")))
            self.tbl_cities.setItem(row, 3, self._cell(f"{c['lat']:.4f}"))
            self.tbl_cities.setItem(row, 4, self._cell(f"{c['lon']:.4f}"))
            self.tbl_cities.setItem(row, 5, self._cell(format_cop(c["fuel_price_cop"])))
            # El estado se guarda como dato para que la búsqueda también lo encuentre
            status_item = QTableWidgetItem()
            status_item.setData(Qt.ItemDataRole.UserRole, "Activa" if is_active else "Inactiva")
            self.tbl_cities.setItem(row, 6, status_item)
            self.tbl_cities.setCellWidget(row, 6, status_pill(is_active))

        edges = sorted(self.graph.get_edges(), key=lambda e: (e["from"], e["to"]))
        self.tbl_edges.setRowCount(len(edges))
        for row, e in enumerate(edges):
            self.tbl_edges.setItem(row, 0, self._cell(e["from"], bold=True))
            self.tbl_edges.setItem(row, 1, self._cell(e["to"], bold=True))
            self.tbl_edges.setItem(row, 2, self._cell(f"{e['distance_km']:.1f} km"))
            self.tbl_edges.setItem(row, 3, self._cell(format_hours(e["time_hours"])))
            self.tbl_edges.setItem(row, 4, self._cell(format_cop(e["toll_cost_cop"])))
            self.tbl_edges.setItem(row, 5, self._cell(format_cop(e["fuel_cost_cop"])))
            self.tbl_edges.setItem(row, 6, self._cell(e.get("category", "Primaria")))
            self.tbl_edges.setItem(row, 7, self._cell("Sí" if e.get("active", True) else "No"))
            self.tbl_edges.setItem(row, 8, self._cell("Sí" if e.get("validated", True) else "No"))
            self.tbl_edges.setItem(row, 9, self._cell(e.get("source", "Google Maps")))

        self.lbl_cities_count.setText(str(len(cities)))
        self.lbl_edges_count.setText(str(len(edges)))

        # Mantener el filtro de búsqueda activo tras recargar
        self._filter_table(self.tbl_cities, self.txt_search_cities)
        self._filter_table(self.tbl_edges, self.txt_search_edges)
        self._update_management_buttons()

    @staticmethod
    def _filter_table(table: QTableWidget, search: QLineEdit):
        """Oculta las filas que no contienen el texto buscado en ninguna columna."""
        text = search.text().strip().lower()

        def cell_text(row, col):
            item = table.item(row, col)
            if item is None:
                return ""
            return f"{item.text()} {item.data(Qt.ItemDataRole.UserRole) or ''}".lower()

        for row in range(table.rowCount()):
            visible = not text or any(text in cell_text(row, col) for col in range(table.columnCount()))
            table.setRowHidden(row, not visible)

    def _update_management_buttons(self):
        """Habilita las acciones según la selección y ajusta el texto Activar/Desactivar."""
        city_row = self.tbl_cities.currentRow() if self.tbl_cities.selectedItems() else -1
        has_city = city_row >= 0 and self.tbl_cities.item(city_row, 0) is not None
        for btn in (self.btn_mod_city, self.btn_toggle_city, self.btn_del_city):
            btn.setEnabled(has_city)
        if has_city:
            cid = self.tbl_cities.item(city_row, 0).text()
            active = self.graph.cities.get(cid, {}).get("active", True)
            self.btn_toggle_city.setText("Desactivar" if active else "Activar")
        else:
            self.btn_toggle_city.setText("Desactivar")

        has_edge = bool(self.tbl_edges.selectedItems())
        for btn in (self.btn_mod_edge, self.btn_toggle_edge, self.btn_del_edge):
            btn.setEnabled(has_edge)
        if has_edge:
            row = self.tbl_edges.currentRow()
            u = self.tbl_edges.item(row, 0).text()
            v = self.tbl_edges.item(row, 1).text()
            active = self.graph.adj.get(u, {}).get(v, {}).get("active", True)
            self.btn_toggle_edge.setText("Desactivar" if active else "Activar")
        else:
            self.btn_toggle_edge.setText("Desactivar")

    def _sync_and_save(self, operation_msg: str):
        """Guarda persistencia en JSON, refresca interfaces y verifica conectividad."""
        saved = save_graph(self.graph, self.data_filepath)
        self._populate_management_tables()
        self._load_cities_into_combos()
        self._refresh_graph_display()
        # El grafo cambió: estadísticas, gráficos y mapa quedan pendientes de recalcular
        self.dashboard_widget.mark_graph_dirty()
        self._update_network_status()

        status = f"{operation_msg} | Guardado en {os.path.basename(self.data_filepath)}" if saved else f"{operation_msg} (Error al guardar)"
        self.status_bar.showMessage(status, 5000)

        # Advertencia no bloqueante si el grafo queda desconectado
        if not self.graph.is_connected():
            QMessageBox.warning(
                self,
                "Grafo Desconectado",
                "Atención: El grafo vial ha quedado desconectado tras esta operación.\n"
                "Algunas rutas directas o indirectas podrían no ser transitables."
            )

    # --------------------------------------------------------------------------
    # ACCIONES CRUD DE CIUDADES
    # --------------------------------------------------------------------------
    def _handle_add_city(self):
        dialog = CityDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data["id"] in self.graph.cities:
                QMessageBox.warning(self, "Error", f"La ciudad con ID '{data['id']}' ya existe.")
                return
            self.graph.add_city(
                city_id=data["id"],
                name=data["name"],
                lat=data["lat"],
                lon=data["lon"],
                fuel_price_cop=data["fuel_price_cop"],
                active=data["active"], department=data["department"]
            )
            self._sync_and_save(f"Ciudad {data['id']} agregada.")

    def _handle_modify_city(self):
        selected = self.tbl_cities.currentRow()
        if selected < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una ciudad de la tabla para modificar.")
            return

        cid = self.tbl_cities.item(selected, 0).text()
        city_data = self.graph.cities.get(cid)
        if not city_data:
            return

        dialog = CityDialog(self, city_data=city_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.graph.add_city(
                city_id=cid,
                name=data["name"],
                lat=data["lat"],
                lon=data["lon"],
                fuel_price_cop=data["fuel_price_cop"],
                active=data["active"], department=data["department"]
            )
            self._sync_and_save(f"Ciudad {cid} actualizada.")

    def _handle_toggle_city(self):
        selected = self.tbl_cities.currentRow()
        if selected < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una ciudad para activar o desactivar.")
            return

        cid = self.tbl_cities.item(selected, 0).text()
        current_active = self.graph.cities.get(cid, {}).get("active", True)
        if current_active:
            self.graph.deactivate_city(cid)
            msg = f"Ciudad {cid} desactivada."
        else:
            self.graph.activate_city(cid)
            msg = f"Ciudad {cid} activada."
        self._sync_and_save(msg)

    def _handle_delete_city(self):
        selected = self.tbl_cities.currentRow()
        if selected < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una ciudad para eliminar.")
            return

        cid = self.tbl_cities.item(selected, 0).text()
        confirm = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de eliminar la ciudad '{cid}' y todas sus rutas asociadas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.graph.remove_city(cid)
            self._sync_and_save(f"Ciudad {cid} eliminada.")

    # --------------------------------------------------------------------------
    # ACCIONES CRUD DE ARISTAS
    # --------------------------------------------------------------------------
    def _handle_add_edge(self):
        dialog = EdgeDialog(self, cities=self.graph.get_cities())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            u, v = data["from"], data["to"]
            dist, t_h, toll = data["distance_km"], data["time_hours"], data["toll_cost_cop"]

            self.graph.add_edge(u, v, dist, t_h, toll, category=data["category"], validated=data["validated"], source=data["source"])
            if data["bidirectional"]:
                self.graph.add_edge(v, u, dist, t_h, toll, category=data["category"], validated=data["validated"], source=data["source"])

            self._sync_and_save(f"Arista {u} -> {v} agregada.")

    def _handle_modify_edge(self):
        selected = self.tbl_edges.currentRow()
        if selected < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una arista de la tabla para modificar.")
            return

        u = self.tbl_edges.item(selected, 0).text()
        v = self.tbl_edges.item(selected, 1).text()
        edge = self.graph.adj.get(u, {}).get(v)
        if not edge:
            return

        dialog = EdgeDialog(self, cities=self.graph.get_cities(), edge_data=edge)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            dist, t_h, toll = data["distance_km"], data["time_hours"], data["toll_cost_cop"]
            fuel = round((dist / 35.0) * self.graph.cities[u]["fuel_price_cop"], 2)

            self.graph.modify_edge(u, v, distance_km=dist, time_hours=t_h, toll_cost_cop=toll, fuel_cost_cop=fuel,
                                   category=data["category"], validated=data["validated"], source=data["source"])
            if data["bidirectional"] and v in self.graph.adj and u in self.graph.adj[v]:
                fuel_rev = round((dist / 35.0) * self.graph.cities[v]["fuel_price_cop"], 2)
                self.graph.modify_edge(v, u, distance_km=dist, time_hours=t_h, toll_cost_cop=toll, fuel_cost_cop=fuel_rev)

            self._sync_and_save(f"Arista {u} -> {v} modificada.")

    def _handle_delete_edge(self):
        selected = self.tbl_edges.currentRow()
        if selected < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una arista para eliminar.")
            return

        u = self.tbl_edges.item(selected, 0).text()
        v = self.tbl_edges.item(selected, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Desea eliminar la arista {u} -> {v}?\n(Si existe la ruta inversa, también se preguntará).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.graph.remove_edge(u, v)
            if v in self.graph.adj and u in self.graph.adj[v]:
                del_rev = QMessageBox.question(
                    self,
                    "Sentido inverso",
                    f"¿Desea eliminar también el sentido inverso {v} -> {u}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if del_rev == QMessageBox.StandardButton.Yes:
                    self.graph.remove_edge(v, u)

            self._sync_and_save(f"Arista {u} -> {v} eliminada.")

    def _handle_toggle_edge(self):
        """Cambia el flag activo de la arista seleccionada sin borrarla."""
        selected = self.tbl_edges.currentRow()
        if selected < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una arista para activar o desactivar.")
            return
        u = self.tbl_edges.item(selected, 0).text()
        v = self.tbl_edges.item(selected, 1).text()
        current = self.graph.adj.get(u, {}).get(v, {}).get("active", True)
        self.graph.set_edge_active(u, v, not current)
        self._sync_and_save(f"Arista {u} -> {v} {'activada' if not current else 'desactivada'}.")

    # --------------------------------------------------------------------------
    # MÉTODOS DE SOPORTE Y ACCIONES DE RUTAS
    # --------------------------------------------------------------------------
    def _load_cities_into_combos(self):
        """Llena los combos de origen y destino. Las ciudades inactivas aparecen deshabilitadas."""
        current_o = self.combo_origin.currentData()
        current_d = self.combo_dest.currentData()

        # Se bloquean señales para no disparar recálculos mientras se rellenan
        for combo in (self.combo_origin, self.combo_dest):
            combo.blockSignals(True)
            combo.clear()

        cities = sorted(self.graph.get_cities(), key=lambda c: c["name"])
        for city in cities:
            active = city.get("active", True)
            item_text = f"{city['name']}  ·  {city['id']}" + ("" if active else "  (inactiva)")
            for combo in (self.combo_origin, self.combo_dest):
                combo.addItem(item_text, city["id"])
                if not active:
                    combo.model().item(combo.count() - 1).setEnabled(False)

        for combo, current, default in (
            (self.combo_origin, current_o, "BOG"),
            (self.combo_dest, current_d, "CTG"),
        ):
            idx = combo.findData(current) if current else -1
            if idx < 0:
                idx = combo.findData(default)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def _current_criterion(self) -> str:
        return CRITERIA[max(self.criterion_group.checkedId(), 0)][0]

    def _set_criterion(self, name: str):
        """Selecciona un criterio por nombre (también usado por pruebas)."""
        for i, (text, _icon, _hint) in enumerate(CRITERIA):
            if text == name:
                self.criterion_group.button(i).setChecked(True)
                self._on_params_changed()
                return

    def _update_criterion_hint(self):
        self.lbl_criterion_hint.setText(CRITERIA[max(self.criterion_group.checkedId(), 0)][2])

    def _on_params_changed(self, *_):
        """Cambió origen, destino o criterio."""
        self._update_criterion_hint()
        if self._route_shown:
            self._calculate_route()

    def _swap_cities(self):
        """Intercambia origen y destino."""
        idx_o = self.combo_origin.currentIndex()
        idx_d = self.combo_dest.currentIndex()
        for combo, idx in ((self.combo_origin, idx_d), (self.combo_dest, idx_o)):
            combo.blockSignals(True)
            combo.setCurrentIndex(idx)
            combo.blockSignals(False)
        self._on_params_changed()

    def _on_graph_city_clicked(self, city_id: str, button: int):
        """Clic en el mapa: izquierdo = origen, derecho = destino. Calcula la ruta."""
        city = self.graph.cities.get(city_id)
        if not city:
            return
        if not city.get("active", True):
            self.status_bar.showMessage(f"{city['name']} está inactiva y no se puede usar en una ruta.", 4000)
            return

        is_origin = button == 1
        combo = self.combo_origin if is_origin else self.combo_dest
        combo.blockSignals(True)
        combo.setCurrentIndex(combo.findData(city_id))
        combo.blockSignals(False)
        self.status_bar.showMessage(f"{city['name']} seleccionada como {'origen' if is_origin else 'destino'}.", 3000)
        self._calculate_route()

    def _clear_route(self):
        """Quita la ruta del mapa y vuelve al estado inicial del panel."""
        self._route_shown = False
        self.current_path = []
        self.current_origin = None
        self.current_dest = None
        self.result_card.show_empty()
        self._refresh_graph_display()
        self.dashboard_widget.set_current_path([])
        self.status_bar.showMessage("Ruta limpiada.", 3000)

    def _calculate_route(self):
        """Ejecuta Dijkstra con los parámetros seleccionados y muestra el resultado."""
        origin = self.combo_origin.currentData()
        dest = self.combo_dest.currentData()
        criterion_text = self._current_criterion()
        if not origin or not dest:
            return

        self._route_shown = True
        self.current_origin = origin
        self.current_dest = dest
        self.current_path = []

        res = None
        error = None
        inactive = [c for c in (origin, dest) if not self.graph.cities.get(c, {}).get("active", True)]
        if origin == dest:
            error = "El origen y el destino deben ser ciudades diferentes."
        elif inactive:
            error = (f"La ciudad {', '.join(inactive)} está inactiva. "
                     "Actívala en Gestión o elige otra.")
        else:
            if criterion_text == "Combinada":
                res = self.graph.shortest_path_combined(origin, dest)
            else:
                res = self.graph.shortest_path(origin, dest, WEIGHT_MAP.get(criterion_text, "distance_km"))
            if res is None:
                error = f"No existe un camino disponible entre {origin} y {dest}."

        if error:
            self.result_card.show_error(error)
            self.status_bar.showMessage(error, 5000)
        else:
            path = res.get("path", [])
            self.current_path = path
            legs = [self.graph.adj[path[i]][path[i + 1]] for i in range(len(path) - 1)]
            names = {cid: c["name"] for cid, c in self.graph.cities.items()}
            self.result_card.show_result(res, legs, criterion_text, names)

            self._routes_calculated += 1
            self.dashboard_widget.set_routes_count(self._routes_calculated)

            total_money = res.get("total_toll_cop", 0.0) + res.get("total_fuel_cop", 0.0)
            self.status_bar.showMessage(
                f"Ruta óptima ({criterion_text}): {' → '.join(path)} · "
                f"{format_km(res.get('total_distance_km', 0.0))} · "
                f"{format_hours(res.get('total_time_hours', 0.0))} · {format_cop(total_money)}",
                6000,
            )

        self._refresh_graph_display()
        # Solo se informa la ruta; el mapa Folium se regenera al abrir el Dashboard si cambió
        self.dashboard_widget.set_current_path(self.current_path)

    def _refresh_graph_display(self):
        """Actualiza el lienzo; internamente solo redibuja si el grafo o la ruta cambiaron."""
        self.graph_canvas.update_view(
            self.graph,
            path=self.current_path,
            origin=self.current_origin,
            destination=self.current_dest
        )
