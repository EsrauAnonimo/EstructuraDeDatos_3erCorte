"""
Module: gui.py
Description: Main GUI window with QTabWidget for the PERA application.
"""

import os
from PyQt6.QtCore import Qt
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
        self.current_svg_path = None
        self.current_path = []
        self.current_origin = None
        self.current_dest = None

        self.setWindowTitle("PERA — Planificador Eficiente de Rutas Automotrices")
        self.resize(1200, 800)
        self.setMinimumSize(950, 650)
        self.setStyleSheet(styles.APP_QSS)

        graph_view.cleanup_temp_files()

        self._init_ui()
        self._load_cities_into_combos()
        self._populate_management_tables()
        self._refresh_graph_display()

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
        self._build_dashboard_tab_placeholder()

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

        # Panel izquierdo (35%)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        config_box = QGroupBox("Parámetros del Viaje")
        config_layout = QVBoxLayout(config_box)
        config_layout.setSpacing(10)

        config_layout.addWidget(QLabel("Ciudad de Origen:"))
        self.combo_origin = QComboBox()
        config_layout.addWidget(self.combo_origin)

        config_layout.addWidget(QLabel("Ciudad de Destino:"))
        self.combo_dest = QComboBox()
        config_layout.addWidget(self.combo_dest)

        config_layout.addWidget(QLabel("Criterio de Optimización:"))
        self.combo_criterion = QComboBox()
        self.combo_criterion.addItems(["Distancia", "Tiempo", "Peajes", "Combustible", "Combinada"])
        config_layout.addWidget(self.combo_criterion)

        self.btn_calculate = QPushButton("Calcular ruta")
        self.btn_calculate.clicked.connect(self._calculate_route)
        config_layout.addWidget(self.btn_calculate)

        left_layout.addWidget(config_box)

        # Tarjeta de resultados
        self.result_box = QGroupBox("Resultado de la Ruta")
        res_layout = QVBoxLayout(self.result_box)
        res_layout.setSpacing(8)

        self.lbl_result_path = QLabel("Ruta: Seleccione origen y destino")
        self.lbl_result_path.setWordWrap(True)
        self.lbl_result_path.setStyleSheet("font-weight: 700; color: #1E293B; font-size: 10.5pt;")

        self.lbl_result_dist = QLabel("Distancia: -")
        self.lbl_result_time = QLabel("Tiempo: -")
        self.lbl_result_toll = QLabel("Peajes: -")
        self.lbl_result_fuel = QLabel("Combustible: -")
        self.lbl_result_total_cost = QLabel("Costo total: -")
        self.lbl_result_total_cost.setStyleSheet("font-weight: 700; color: #16A34A;")

        self.lbl_result_error = QLabel("")
        self.lbl_result_error.setStyleSheet("font-weight: 700; color: #DC2626; font-size: 10.5pt;")
        self.lbl_result_error.setVisible(False)

        res_layout.addWidget(self.lbl_result_path)
        res_layout.addWidget(self.lbl_result_dist)
        res_layout.addWidget(self.lbl_result_time)
        res_layout.addWidget(self.lbl_result_toll)
        res_layout.addWidget(self.lbl_result_fuel)
        res_layout.addWidget(self.lbl_result_total_cost)
        res_layout.addWidget(self.lbl_result_error)
        res_layout.addStretch()

        left_layout.addWidget(self.result_box, stretch=1)

        # Panel derecho (65%) - Visualizador de Grafo
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        graph_box = QGroupBox("Visualización de la Red Vial (Graphviz)")
        graph_box_layout = QVBoxLayout(graph_box)

        self.scroll_graph = QScrollArea()
        self.scroll_graph.setWidgetResizable(True)
        self.scroll_graph.setStyleSheet("background-color: #FAFCFF; border: 1px solid #E2E8F0; border-radius: 8px;")

        self.lbl_graph = QLabel("Cargando grafo...")
        self.lbl_graph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_graph.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_graph.setWidget(self.lbl_graph)

        graph_box_layout.addWidget(self.scroll_graph)
        right_layout.addWidget(graph_box)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 35)
        splitter.setStretchFactor(1, 65)

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
        cities_layout.addWidget(self.tbl_cities)

        btn_row_c = QHBoxLayout()
        self.btn_add_city = QPushButton("Agregar ciudad")
        self.btn_add_city.clicked.connect(self._handle_add_city)

        self.btn_mod_city = QPushButton("Modificar")
        self.btn_mod_city.setObjectName("btnSecondary")
        self.btn_mod_city.clicked.connect(self._handle_modify_city)

        self.btn_toggle_city = QPushButton("Desactivar/Activar")
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

    def _build_dashboard_tab_placeholder(self):
        """Espacio reservado para la pestaña de Dashboard."""
        layout = QVBoxLayout(self.tab_dashboard)
        lbl = QLabel("Pestaña de Dashboard en preparación.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

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
            self.tbl_cities.setItem(row, 4, QTableWidgetItem(f"${c['fuel_price_cop']:,.2f}".replace(",", ".")))
            self.tbl_cities.setItem(row, 5, QTableWidgetItem("Sí" if is_active else "No"))

        # Poblar aristas
        edges = sorted(self.graph.get_edges(), key=lambda e: (e["from"], e["to"]))
        self.tbl_edges.setRowCount(len(edges))
        for row, e in enumerate(edges):
            self.tbl_edges.setItem(row, 0, QTableWidgetItem(e["from"]))
            self.tbl_edges.setItem(row, 1, QTableWidgetItem(e["to"]))
            self.tbl_edges.setItem(row, 2, QTableWidgetItem(f"{e['distance_km']:.1f} km"))
            self.tbl_edges.setItem(row, 3, QTableWidgetItem(f"{e['time_hours']:.2f} h"))
            self.tbl_edges.setItem(row, 4, QTableWidgetItem(f"${e['toll_cost_cop']:,.0f}".replace(",", ".")))
            self.tbl_edges.setItem(row, 5, QTableWidgetItem(f"${e['fuel_cost_cop']:,.0f}".replace(",", ".")))

    def _sync_and_save(self, operation_msg: str):
        """Guarda persistencia en JSON, refresca interfaces y verifica conectividad."""
        saved = save_graph(self.graph, self.data_filepath)
        self._populate_management_tables()
        self._load_cities_into_combos()
        self._refresh_graph_display()

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
        """Llena los combos de origen y destino con las ciudades registradas."""
        current_o = self.combo_origin.currentData()
        current_d = self.combo_dest.currentData()

        self.combo_origin.clear()
        self.combo_dest.clear()

        cities = sorted(self.graph.get_cities(), key=lambda c: c["name"])
        for city in cities:
            status = "" if city.get("active", True) else " (Inactiva)"
            item_text = f"{city['id']} - {city['name']}{status}"
            self.combo_origin.addItem(item_text, city["id"])
            self.combo_dest.addItem(item_text, city["id"])

        if current_o and self.combo_origin.findData(current_o) >= 0:
            self.combo_origin.setCurrentIndex(self.combo_origin.findData(current_o))
        else:
            idx_bog = self.combo_origin.findData("BOG")
            if idx_bog >= 0:
                self.combo_origin.setCurrentIndex(idx_bog)

        if current_d and self.combo_dest.findData(current_d) >= 0:
            self.combo_dest.setCurrentIndex(self.combo_dest.findData(current_d))
        else:
            idx_ctg = self.combo_dest.findData("CTG")
            if idx_ctg >= 0:
                self.combo_dest.setCurrentIndex(idx_ctg)

    def _calculate_route(self):
        """Ejecuta el algoritmo de Dijkstra según los parámetros seleccionados."""
        origin = self.combo_origin.currentData()
        dest = self.combo_dest.currentData()
        criterion_text = self.combo_criterion.currentText()

        if not origin or not dest:
            return

        if origin == dest:
            self.lbl_result_error.setText("El origen y el destino deben ser ciudades diferentes.")
            self.lbl_result_error.setVisible(True)
            self.lbl_result_path.setText("Ruta: Inválida")
            self.lbl_result_dist.setText("Distancia: -")
            self.lbl_result_time.setText("Tiempo: -")
            self.lbl_result_toll.setText("Peajes: -")
            self.lbl_result_fuel.setText("Combustible: -")
            self.lbl_result_total_cost.setText("Costo total: -")
            self.current_path = []
            self._refresh_graph_display()
            return

        weight_map = {
            "Distancia": "distance_km",
            "Tiempo": "time_hours",
            "Peajes": "toll_cost_cop",
            "Combustible": "fuel_cost_cop"
        }

        if criterion_text == "Combinada":
            res = self.graph.shortest_path_combined(origin, dest)
        else:
            weight = weight_map.get(criterion_text, "distance_km")
            res = self.graph.shortest_path(origin, dest, weight)

        self.current_origin = origin
        self.current_dest = dest

        if res is None:
            self.lbl_result_error.setText("Ruta no encontrada")
            self.lbl_result_error.setVisible(True)
            self.lbl_result_path.setText("Ruta: No existe camino disponible")
            self.lbl_result_dist.setText("Distancia: -")
            self.lbl_result_time.setText("Tiempo: -")
            self.lbl_result_toll.setText("Peajes: -")
            self.lbl_result_fuel.setText("Combustible: -")
            self.lbl_result_total_cost.setText("Costo total: -")
            self.current_path = []
            self.status_bar.showMessage(f"No se encontró ruta entre {origin} y {dest}.", 5000)
        else:
            self.lbl_result_error.setVisible(False)
            path = res.get("path", [])
            self.current_path = path

            path_str = " → ".join(path)
            dist = res.get("total_distance_km", 0.0)
            t_hours = res.get("total_time_hours", 0.0)
            toll = res.get("total_toll_cop", 0.0)
            fuel = res.get("total_fuel_cop", 0.0)
            total_money = toll + fuel

            self.lbl_result_path.setText(f"Ruta: {path_str}")
            self.lbl_result_dist.setText(f"Distancia: {dist:.1f} km")
            self.lbl_result_time.setText(f"Tiempo: {t_hours:.2f} h")
            self.lbl_result_toll.setText(f"Peajes: ${toll:,.0f}".replace(",", "."))
            self.lbl_result_fuel.setText(f"Combustible: ${fuel:,.0f}".replace(",", "."))
            self.lbl_result_total_cost.setText(f"Costo total: ${total_money:,.0f} (peajes + combustible)".replace(",", "."))

            self.status_bar.showMessage(f"Ruta óptima calculada ({criterion_text}): {path_str} | Costo total: ${total_money:,.0f}".replace(",", "."), 6000)

        self._refresh_graph_display()

    def _refresh_graph_display(self):
        """Renderiza el grafo y lo proyecta sobre el QLabel correspondiente."""
        svg_path = graph_view.render_graph(
            self.graph,
            path=self.current_path,
            origin=self.current_origin,
            destination=self.current_dest
        )
        self.current_svg_path = svg_path
        self._update_pixmap()

    def _update_pixmap(self):
        """Actualiza el mapa de bits con las dimensiones del contenedor."""
        if not self.current_svg_path or not os.path.exists(self.current_svg_path):
            self.lbl_graph.setText("No hay visualización disponible.")
            return

        w = max(self.scroll_graph.viewport().width(), 500)
        h = max(self.scroll_graph.viewport().height(), 400)
        pix = graph_view.render_to_pixmap(self.current_svg_path, w, h)
        if not pix.isNull():
            self.lbl_graph.setPixmap(pix)

    def resizeEvent(self, event):
        """Ajusta el renderizado al redimensionar la ventana."""
        super().resizeEvent(event)
        self._update_pixmap()
