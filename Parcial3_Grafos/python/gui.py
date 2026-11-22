"""
Module: gui.py
Description: Main GUI window with QTabWidget for the PERA application.
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from graph import Graph
import graph_view
import styles


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
        self._build_management_tab_placeholder()
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

    def _build_management_tab_placeholder(self):
        """Espacio reservado para la pestaña de Gestión."""
        layout = QVBoxLayout(self.tab_management)
        lbl = QLabel("Pestaña de Gestión en preparación.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

    def _build_dashboard_tab_placeholder(self):
        """Espacio reservado para la pestaña de Dashboard."""
        layout = QVBoxLayout(self.tab_dashboard)
        lbl = QLabel("Pestaña de Dashboard en preparación.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

    # --------------------------------------------------------------------------
    # MÉTODOS DE SOPORTE Y ACCIONES
    # --------------------------------------------------------------------------
    def _load_cities_into_combos(self):
        """Llena los combos de origen y destino con las ciudades registradas."""
        self.combo_origin.clear()
        self.combo_dest.clear()

        cities = sorted(self.graph.get_cities(), key=lambda c: c["name"])
        for city in cities:
            status = "" if city.get("active", True) else " (Inactiva)"
            item_text = f"{city['id']} - {city['name']}{status}"
            self.combo_origin.addItem(item_text, city["id"])
            self.combo_dest.addItem(item_text, city["id"])

        # Seleccionar BOG y CTG por defecto si existen
        idx_bog = self.combo_origin.findData("BOG")
        if idx_bog >= 0:
            self.combo_origin.setCurrentIndex(idx_bog)

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
