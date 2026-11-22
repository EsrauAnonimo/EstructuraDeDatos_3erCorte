"""
Module: gui.py
Description: Main GUI window with QTabWidget for the PERA application.
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from graph import Graph, save_graph
import graph_view
import styles
from dashboard import DashboardWidget
from widgets import RouteResultCard, format_cop, format_hours, format_km

# Criterios disponibles y su explicación para el usuario
CRITERIA_HINTS = {
    "Distancia": "Busca el camino con menos kilómetros.",
    "Tiempo": "Busca el camino que llega más rápido.",
    "Peajes": "Busca el camino que gasta menos en peajes.",
    "Combustible": "Busca el camino que gasta menos gasolina.",
    "Combinada": "Equilibra distancia, tiempo, peajes y combustible (25 % cada uno).",
}

WEIGHT_MAP = {
    "Distancia": "distance_km",
    "Tiempo": "time_hours",
    "Peajes": "toll_cost_cop",
    "Combustible": "fuel_cost_cop",
}


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
            self.spn_lat.setValue(city_data.get("lat", 0.0))
            self.spn_lon.setValue(city_data.get("lon", 0.0))
            self.spn_fuel.setValue(city_data.get("fuel_price_cop", 16000.0))
            self.chk_active.setChecked(city_data.get("active", True))

        form.addRow("Identificador (ID):", self.txt_id)
        form.addRow("Nombre de Ciudad:", self.txt_name)
        form.addRow("Latitud:", self.spn_lat)
        form.addRow("Longitud:", self.spn_lon)
        form.addRow("Precio Combustible (COP):", self.spn_fuel)
        form.addRow("Estado:", self.chk_active)
        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
            self.chk_bidirectional.setText("Aplicar cambios también al sentido inverso")

        form.addRow("Ciudad Origen:", self.combo_from)
        form.addRow("Ciudad Destino:", self.combo_to)
        form.addRow("Distancia:", self.spn_dist)
        form.addRow("Tiempo estimado:", self.spn_time)
        form.addRow("Costo de Peajes (COP):", self.spn_toll)
        form.addRow("Bidireccional:", self.chk_bidirectional)
        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
            "bidirectional": self.chk_bidirectional.isChecked()
        }


# ==============================================================================
# VENTANA PRINCIPAL
# ==============================================================================

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación PERA."""

    def __init__(self, graph: Graph, data_filepath: str = "graph_data.json"):
        super().__init__()
        self.graph = graph
        self.data_filepath = data_filepath
        self.current_path = []
        self.current_origin = None
        self.current_dest = None
        self._route_shown = False  # si hay una ruta en pantalla se recalcula al cambiar parámetros

        self.setWindowTitle("PERA — Planificador Eficiente de Rutas Automotrices")
        self.resize(1280, 820)
        self.setMinimumSize(950, 650)
        self.setStyleSheet(styles.APP_QSS)

        self._init_ui()
        self._load_cities_into_combos()
        self._populate_management_tables()
        self._refresh_graph_display()
        # El dashboard se calcula de forma perezosa al abrir su pestaña

    def _init_ui(self):
        """Inicializa la disposición de la interfaz y pestañas."""
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Encabezado superior
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(4)

        title_label = QLabel("PERA — Planificador Eficiente de Rutas Automotrices")
        title_label.setObjectName("headerTitle")
        subtitle_label = QLabel("Optimización multicriterio sobre la red vial nacional de Colombia (Parcial 3)")
        subtitle_label.setObjectName("headerSubtitle")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addWidget(header_frame)

        # Tab Widget principal
        self.tabs = QTabWidget()
        self.tab_routes = QWidget()
        self.tab_management = QWidget()
        self.tab_dashboard = QWidget()

        self.tabs.addTab(self.tab_routes, "🗺️ Rutas")
        self.tabs.addTab(self.tab_management, "⚙️ Gestión")
        self.tabs.addTab(self.tab_dashboard, "📊 Dashboard")

        main_layout.addWidget(self.tabs, stretch=1)

        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Red vial cargada con éxito.")

        self._build_routes_tab()
        self._build_management_tab()
        self._build_dashboard_tab()
        self.tabs.currentChanged.connect(self._on_tab_changed)

    # --------------------------------------------------------------------------
    # PESTAÑA 1: RUTAS
    # --------------------------------------------------------------------------
    def _build_routes_tab(self):
        """Construye la pestaña de cálculo y visualización de rutas óptimas."""
        routes_layout = QHBoxLayout(self.tab_routes)
        routes_layout.setContentsMargins(14, 14, 14, 14)
        routes_layout.setSpacing(14)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        routes_layout.addWidget(splitter)

        # Panel izquierdo con scroll: parámetros + resultado
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setMinimumWidth(360)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        left_panel = QWidget()
        left_panel.setObjectName("scrollContent")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 6, 0)
        left_layout.setSpacing(12)

        config_box = QGroupBox("Parámetros del Viaje")
        config_layout = QVBoxLayout(config_box)
        config_layout.setSpacing(6)

        config_layout.addWidget(self._field_label("🟢 Origen"))
        self.combo_origin = QComboBox()
        self.combo_origin.setToolTip("Ciudad donde empieza el viaje")
        config_layout.addWidget(self.combo_origin)

        self.btn_swap = QPushButton("⇅  Intercambiar origen y destino")
        self.btn_swap.setObjectName("btnSwap")
        self.btn_swap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_swap.clicked.connect(self._swap_cities)
        config_layout.addWidget(self.btn_swap)

        config_layout.addWidget(self._field_label("🔴 Destino"))
        self.combo_dest = QComboBox()
        self.combo_dest.setToolTip("Ciudad a la que quieres llegar")
        config_layout.addWidget(self.combo_dest)

        config_layout.addSpacing(6)
        config_layout.addWidget(self._field_label("🎯 ¿Qué quieres optimizar?"))
        self.combo_criterion = QComboBox()
        self.combo_criterion.addItems(list(CRITERIA_HINTS))
        config_layout.addWidget(self.combo_criterion)

        self.lbl_criterion_hint = QLabel()
        self.lbl_criterion_hint.setObjectName("hintLabel")
        self.lbl_criterion_hint.setWordWrap(True)
        config_layout.addWidget(self.lbl_criterion_hint)

        config_layout.addSpacing(6)
        btn_row = QHBoxLayout()
        self.btn_calculate = QPushButton("Calcular ruta")
        self.btn_calculate.setToolTip("Atajo: tecla Enter")
        self.btn_calculate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_calculate.clicked.connect(self._calculate_route)

        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setObjectName("btnSecondary")
        self.btn_clear.setToolTip("Quita la ruta del mapa")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_route)

        btn_row.addWidget(self.btn_calculate, stretch=2)
        btn_row.addWidget(self.btn_clear, stretch=1)
        config_layout.addLayout(btn_row)
        left_layout.addWidget(config_box)

        # Tarjeta de resultados (vacío / error / resultado)
        self.result_box = QGroupBox("Resultado de la Ruta")
        res_layout = QVBoxLayout(self.result_box)
        self.result_card = RouteResultCard()
        res_layout.addWidget(self.result_card)
        left_layout.addWidget(self.result_box, stretch=1)

        left_scroll.setWidget(left_panel)

        # Si ya hay una ruta en pantalla, cambiar un parámetro la recalcula al instante
        self.combo_origin.currentIndexChanged.connect(self._on_params_changed)
        self.combo_dest.currentIndexChanged.connect(self._on_params_changed)
        self.combo_criterion.currentIndexChanged.connect(self._on_params_changed)
        self._update_criterion_hint()

        # Enter calcula la ruta mientras el foco esté en esta pestaña
        for key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            shortcut = QShortcut(QKeySequence(key), self.tab_routes)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(self._calculate_route)

        # Panel derecho: mapa interactivo
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        graph_box = QGroupBox("Mapa de la Red Vial")
        graph_box_layout = QVBoxLayout(graph_box)
        graph_box_layout.setSpacing(6)

        self.graph_canvas = graph_view.GraphCanvas(graph_box)
        self.graph_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.graph_canvas.city_clicked.connect(self._on_graph_city_clicked)

        toolbar = QHBoxLayout()
        lbl_map_hint = QLabel(
            "🖱️ Clic izquierdo: origen · Clic derecho: destino · "
            "Pasa el mouse sobre una ciudad para ver sus datos"
        )
        lbl_map_hint.setObjectName("hintLabel")
        self.chk_labels = QCheckBox("Mostrar distancias")
        self.chk_labels.setChecked(True)
        self.chk_labels.toggled.connect(self.graph_canvas.set_show_labels)
        toolbar.addWidget(lbl_map_hint, stretch=1)
        toolbar.addWidget(self.chk_labels)

        graph_box_layout.addLayout(toolbar)
        graph_box_layout.addWidget(self.graph_canvas, stretch=1)
        right_layout.addWidget(graph_box)

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 30)
        splitter.setStretchFactor(1, 70)
        splitter.setSizes([380, 900])

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    # --------------------------------------------------------------------------
    # PESTAÑA 2: GESTIÓN (CRUD Y PERSISTENCIA)
    # --------------------------------------------------------------------------
    def _build_management_tab(self):
        """Construye la pestaña de gestión de red (ciudades y aristas)."""
        mgmt_layout = QHBoxLayout(self.tab_management)
        mgmt_layout.setContentsMargins(14, 14, 14, 14)
        mgmt_layout.setSpacing(14)

        # Grupo Ciudades (Izquierda)
        cities_box = QGroupBox("Gestión de Ciudades (Nodos)")
        cities_layout = QVBoxLayout(cities_box)
        cities_layout.setSpacing(10)

        self.tbl_cities = QTableWidget()
        self.tbl_cities.setColumnCount(6)
        self.tbl_cities.setHorizontalHeaderLabels(["ID", "Nombre", "Latitud", "Longitud", "Gasolina (COP)", "Activa"])
        self.tbl_cities.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_cities.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_cities.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_cities.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_cities.setAlternatingRowColors(True)
        self.tbl_cities.verticalHeader().setVisible(False)
        self.tbl_cities.setToolTip("Doble clic para editar")
        self.tbl_cities.doubleClicked.connect(self._handle_modify_city)
        self.tbl_cities.itemSelectionChanged.connect(self._update_toggle_button)

        self.txt_search_cities = QLineEdit()
        self.txt_search_cities.setPlaceholderText("🔍 Buscar ciudad por ID o nombre...")
        self.txt_search_cities.setClearButtonEnabled(True)
        self.txt_search_cities.textChanged.connect(lambda: self._filter_table(self.tbl_cities, self.txt_search_cities))
        cities_layout.addWidget(self.txt_search_cities)
        cities_layout.addWidget(self.tbl_cities)

        btn_row_c = QHBoxLayout()
        self.btn_add_city = QPushButton("Agregar ciudad")
        self.btn_add_city.clicked.connect(self._handle_add_city)

        self.btn_mod_city = QPushButton("Modificar")
        self.btn_mod_city.setObjectName("btnSecondary")
        self.btn_mod_city.clicked.connect(self._handle_modify_city)

        self.btn_toggle_city = QPushButton("Activar / Desactivar")
        self.btn_toggle_city.setObjectName("btnWarning")
        self.btn_toggle_city.clicked.connect(self._handle_toggle_city)

        self.btn_del_city = QPushButton("Eliminar")
        self.btn_del_city.setObjectName("btnDanger")
        self.btn_del_city.clicked.connect(self._handle_delete_city)

        btn_row_c.addWidget(self.btn_add_city)
        btn_row_c.addWidget(self.btn_mod_city)
        btn_row_c.addWidget(self.btn_toggle_city)
        btn_row_c.addWidget(self.btn_del_city)
        cities_layout.addLayout(btn_row_c)

        # Grupo Aristas (Derecha)
        edges_box = QGroupBox("Gestión de Rutas Viales (Aristas)")
        edges_layout = QVBoxLayout(edges_box)
        edges_layout.setSpacing(10)

        self.tbl_edges = QTableWidget()
        self.tbl_edges.setColumnCount(6)
        self.tbl_edges.setHorizontalHeaderLabels(["Desde", "Hasta", "Distancia", "Tiempo", "Peaje", "Combustible"])
        self.tbl_edges.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_edges.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_edges.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_edges.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_edges.setAlternatingRowColors(True)
        self.tbl_edges.verticalHeader().setVisible(False)
        self.tbl_edges.setToolTip("Doble clic para editar")
        self.tbl_edges.doubleClicked.connect(self._handle_modify_edge)

        self.txt_search_edges = QLineEdit()
        self.txt_search_edges.setPlaceholderText("🔍 Buscar ruta, p. ej. BOG o MDE...")
        self.txt_search_edges.setClearButtonEnabled(True)
        self.txt_search_edges.textChanged.connect(lambda: self._filter_table(self.tbl_edges, self.txt_search_edges))
        edges_layout.addWidget(self.txt_search_edges)
        edges_layout.addWidget(self.tbl_edges)

        btn_row_e = QHBoxLayout()
        self.btn_add_edge = QPushButton("Agregar arista")
        self.btn_add_edge.clicked.connect(self._handle_add_edge)

        self.btn_mod_edge = QPushButton("Modificar")
        self.btn_mod_edge.setObjectName("btnSecondary")
        self.btn_mod_edge.clicked.connect(self._handle_modify_edge)

        self.btn_del_edge = QPushButton("Eliminar")
        self.btn_del_edge.setObjectName("btnDanger")
        self.btn_del_edge.clicked.connect(self._handle_delete_edge)

        btn_row_e.addWidget(self.btn_add_edge)
        btn_row_e.addWidget(self.btn_mod_edge)
        btn_row_e.addWidget(self.btn_del_edge)
        edges_layout.addLayout(btn_row_e)

        mgmt_layout.addWidget(cities_box, stretch=1)
        mgmt_layout.addWidget(edges_box, stretch=1)

    def _build_dashboard_tab(self):
        """Construye la pestaña del Dashboard analítico y mapa interactivo."""
        layout = QVBoxLayout(self.tab_dashboard)
        layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_widget = DashboardWidget(self.graph, self)
        layout.addWidget(self.dashboard_widget)

    def _on_tab_changed(self, index: int):
        """Al abrir el Dashboard solo se recalcula lo marcado como sucio (dirty)."""
        if self.tabs.widget(index) is self.tab_dashboard:
            self.dashboard_widget.refresh_if_needed()

    # --------------------------------------------------------------------------
    # POBLACIÓN Y GESTIÓN DE TABLAS
    # --------------------------------------------------------------------------
    def _populate_management_tables(self):
        """Actualiza el contenido de las tablas de gestión con los datos del grafo."""
        # Poblar ciudades
        cities = sorted(self.graph.get_cities(), key=lambda c: c["id"])
        self.tbl_cities.setRowCount(len(cities))
        for row, c in enumerate(cities):
            is_active = c.get("active", True)
            self.tbl_cities.setItem(row, 0, QTableWidgetItem(c["id"]))
            self.tbl_cities.setItem(row, 1, QTableWidgetItem(c["name"]))
            self.tbl_cities.setItem(row, 2, QTableWidgetItem(f"{c['lat']:.4f}"))
            self.tbl_cities.setItem(row, 3, QTableWidgetItem(f"{c['lon']:.4f}"))
            self.tbl_cities.setItem(row, 4, QTableWidgetItem(format_cop(c["fuel_price_cop"])))
            status_item = QTableWidgetItem("● Activa" if is_active else "○ Inactiva")
            status_item.setForeground(QColor(styles.SUCCESS if is_active else styles.MUTED))
            self.tbl_cities.setItem(row, 5, status_item)

        # Poblar aristas
        edges = sorted(self.graph.get_edges(), key=lambda e: (e["from"], e["to"]))
        self.tbl_edges.setRowCount(len(edges))
        for row, e in enumerate(edges):
            self.tbl_edges.setItem(row, 0, QTableWidgetItem(e["from"]))
            self.tbl_edges.setItem(row, 1, QTableWidgetItem(e["to"]))
            self.tbl_edges.setItem(row, 2, QTableWidgetItem(f"{e['distance_km']:.1f} km"))
            self.tbl_edges.setItem(row, 3, QTableWidgetItem(format_hours(e["time_hours"])))
            self.tbl_edges.setItem(row, 4, QTableWidgetItem(format_cop(e["toll_cost_cop"])))
            self.tbl_edges.setItem(row, 5, QTableWidgetItem(format_cop(e["fuel_cost_cop"])))

        # Mantener el filtro de búsqueda activo tras recargar
        self._filter_table(self.tbl_cities, self.txt_search_cities)
        self._filter_table(self.tbl_edges, self.txt_search_edges)
        self._update_toggle_button()

    @staticmethod
    def _filter_table(table: QTableWidget, search: QLineEdit):
        """Oculta las filas que no contienen el texto buscado en ninguna columna."""
        text = search.text().strip().lower()
        for row in range(table.rowCount()):
            visible = not text or any(
                table.item(row, col) and text in table.item(row, col).text().lower()
                for col in range(table.columnCount())
            )
            table.setRowHidden(row, not visible)

    def _update_toggle_button(self):
        """El botón dice 'Activar' o 'Desactivar' según la ciudad seleccionada."""
        row = self.tbl_cities.currentRow()
        if row < 0 or not self.tbl_cities.item(row, 0):
            self.btn_toggle_city.setText("Activar / Desactivar")
            return
        cid = self.tbl_cities.item(row, 0).text()
        active = self.graph.cities.get(cid, {}).get("active", True)
        self.btn_toggle_city.setText("Desactivar" if active else "Activar")

    def _sync_and_save(self, operation_msg: str):
        """Guarda persistencia en JSON, refresca interfaces y verifica conectividad."""
        saved = save_graph(self.graph, self.data_filepath)
        self._populate_management_tables()
        self._load_cities_into_combos()
        self._refresh_graph_display()
        # El grafo cambió: estadísticas, gráficos y mapa quedan pendientes de recalcular
        self.dashboard_widget.mark_graph_dirty()

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
                active=data["active"]
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
                active=data["active"]
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

            self.graph.add_edge(u, v, dist, t_h, toll)
            if data["bidirectional"]:
                self.graph.add_edge(v, u, dist, t_h, toll)

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

            self.graph.modify_edge(u, v, distance_km=dist, time_hours=t_h, toll_cost_cop=toll, fuel_cost_cop=fuel)
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
            item_text = f"{city['id']} - {city['name']}" + ("" if active else " (inactiva)")
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

    def _update_criterion_hint(self):
        self.lbl_criterion_hint.setText(CRITERIA_HINTS.get(self.combo_criterion.currentText(), ""))

    def _on_params_changed(self):
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
        criterion_text = self.combo_criterion.currentText()
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
                     "Actívala en la pestaña Gestión o elige otra.")
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

            total_money = res.get("total_toll_cop", 0.0) + res.get("total_fuel_cop", 0.0)
            self.status_bar.showMessage(
                f"Ruta óptima ({criterion_text}): {' → '.join(path)} · "
                f"{format_km(res.get('total_distance_km', 0.0))} · "
                f"{format_hours(res.get('total_time_hours', 0.0))} · {format_cop(total_money)}",
                6000,
            )

        self._refresh_graph_display()
        # Solo se informa la ruta; el mapa se regenera al abrir el Dashboard si cambió
        self.dashboard_widget.set_current_path(self.current_path)

    def _refresh_graph_display(self):
        """Actualiza el lienzo; internamente solo redibuja si el grafo o la ruta cambiaron."""
        self.graph_canvas.update_view(
            self.graph,
            path=self.current_path,
            origin=self.current_origin,
            destination=self.current_dest
        )
