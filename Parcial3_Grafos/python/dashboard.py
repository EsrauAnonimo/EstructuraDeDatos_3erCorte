"""
Module: dashboard.py
Description: Analytics dashboard with descriptive statistics, matplotlib charts,
             and an interactive Folium map embedded in QWebEngineView for PERA.
"""

import os
import statistics
import tempfile

import folium
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from graph import Graph


class DashboardWidget(QWidget):
    """Widget de Dashboard que integra estadísticas, gráficos matplotlib y mapa Folium."""

    def __init__(self, graph: Graph, parent=None):
        super().__init__(parent)
        self.graph = graph
        self.current_path = []
        # Flags dirty: qué partes del dashboard deben recalcularse en el próximo refresco
        self._stats_dirty = True
        self._map_dirty = True
        self._map_path = os.path.join(tempfile.gettempdir(), "pera_network_map.html")

        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # ScrollArea vertical para contener todas las secciones
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container.setObjectName("scrollContent")
        self.layout_container = QVBoxLayout(container)
        self.layout_container.setContentsMargins(14, 14, 14, 14)
        self.layout_container.setSpacing(18)

        # ----------------------------------------------------------------------
        # SECCIÓN 1: ESTADÍSTICAS DESCRIPTIVAS
        # ----------------------------------------------------------------------
        stats_box = QGroupBox("Estadísticas Descriptivas de la Red (38 Aristas Dirigidas)")
        stats_layout = QVBoxLayout(stats_box)
        stats_layout.setContentsMargins(12, 16, 12, 12)

        self.tbl_stats = QTableWidget()
        self.tbl_stats.setColumnCount(6)
        self.tbl_stats.setHorizontalHeaderLabels([
            "Criterio", "Media", "Mediana", "Máx", "Mín", "Desv. Est."
        ])
        self.tbl_stats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_stats.verticalHeader().setVisible(False)
        self.tbl_stats.setFixedHeight(170)
        self.tbl_stats.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        stats_layout.addWidget(self.tbl_stats)

        self.layout_container.addWidget(stats_box)

        # ----------------------------------------------------------------------
        # SECCIÓN 2: GRÁFICOS MATPLOTLIB (GRID 2x2)
        # ----------------------------------------------------------------------
        charts_box = QGroupBox("Análisis Gráfico Multicriterio")
        charts_grid = QGridLayout(charts_box)
        charts_grid.setContentsMargins(12, 16, 12, 12)
        charts_grid.setSpacing(14)

        # Figura 1: Histograma de distancias
        self.fig_hist = Figure(figsize=(5, 3.4), dpi=90, facecolor="#FFFFFF")
        self.canvas_hist = FigureCanvas(self.fig_hist)
        self.canvas_hist.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas_hist.setMinimumHeight(280)
        charts_grid.addWidget(self.canvas_hist, 0, 0)

        # Figura 2: Barras de peajes por ruta (19 pares ordenados)
        self.fig_tolls = Figure(figsize=(5, 3.4), dpi=90, facecolor="#FFFFFF")
        self.canvas_tolls = FigureCanvas(self.fig_tolls)
        self.canvas_tolls.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas_tolls.setMinimumHeight(280)
        charts_grid.addWidget(self.canvas_tolls, 0, 1)

        # Figura 3: Barras de combustible por ruta (19 pares ordenados)
        self.fig_fuel = Figure(figsize=(5, 3.4), dpi=90, facecolor="#FFFFFF")
        self.canvas_fuel = FigureCanvas(self.fig_fuel)
        self.canvas_fuel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas_fuel.setMinimumHeight(280)
        charts_grid.addWidget(self.canvas_fuel, 1, 0)

        # Figura 4: Relación Tiempo vs Distancia
        self.fig_scatter = Figure(figsize=(5, 3.4), dpi=90, facecolor="#FFFFFF")
        self.canvas_scatter = FigureCanvas(self.fig_scatter)
        self.canvas_scatter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas_scatter.setMinimumHeight(280)
        charts_grid.addWidget(self.canvas_scatter, 1, 1)

        self.layout_container.addWidget(charts_box)

        # ----------------------------------------------------------------------
        # SECCIÓN 3: MAPA INTERACTIVO FOLIUM (QWebEngineView)
        # ----------------------------------------------------------------------
        map_box = QGroupBox("Mapa Geográfico Interactivo de la Red Vial (Folium)")
        map_layout = QVBoxLayout(map_box)
        map_layout.setContentsMargins(12, 16, 12, 12)

        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(480)
        map_layout.addWidget(self.web_view)

        self.layout_container.addWidget(map_box)

        scroll.setWidget(container)
        root_layout.addWidget(scroll)
        # No se calcula nada aquí: se hace al abrir la pestaña (refresh_if_needed)

    def set_current_path(self, path: list[str]):
        """Guarda la ruta calculada. El mapa solo se marca sucio si la ruta cambió."""
        new_path = list(path or [])
        if new_path != self.current_path:
            self.current_path = new_path
            self._map_dirty = True
            if self.isVisible():
                self.refresh_if_needed()

    def mark_graph_dirty(self):
        """El grafo cambió (CRUD): estadísticas, gráficos y mapa deben recalcularse."""
        self._stats_dirty = True
        self._map_dirty = True
        if self.isVisible():
            self.refresh_if_needed()

    def refresh_if_needed(self):
        """Recalcula solo las partes marcadas como sucias."""
        if self._stats_dirty:
            self._update_statistics_table()
            self._update_charts()
            self._stats_dirty = False
        if self._map_dirty:
            self._update_folium_map()
            self._map_dirty = False

    def refresh_dashboard(self, path: list[str] = None):
        """Fuerza el recálculo completo (estadísticas, gráficos y mapa)."""
        if path is not None:
            self.current_path = list(path)
        self._stats_dirty = True
        self._map_dirty = True
        self.refresh_if_needed()

    # --------------------------------------------------------------------------
    # CÁLCULO DE ESTADÍSTICAS
    # --------------------------------------------------------------------------
    def _update_statistics_table(self):
        edges = self.graph.get_edges()
        if not edges:
            self.tbl_stats.setRowCount(0)
            return

        criteria_defs = [
            ("Distancia (km)", "distance_km", "{:.1f}", "{:.1f}"),
            ("Tiempo (horas)", "time_hours", "{:.2f}", "{:.2f}"),
            ("Peajes (COP)", "toll_cost_cop", "${:,.0f}", "${:,.0f}"),
            ("Combustible (COP)", "fuel_cost_cop", "${:,.0f}", "${:,.0f}"),
        ]

        self.tbl_stats.setRowCount(len(criteria_defs))

        for row, (label, key, fmt_avg, fmt_val) in enumerate(criteria_defs):
            vals = [e[key] for e in edges]
            if not vals:
                continue

            avg_val = statistics.mean(vals)
            med_val = statistics.median(vals)
            max_val = max(vals)
            min_val = min(vals)
            std_val = statistics.stdev(vals) if len(vals) > 1 else 0.0

            def clean_fmt(template, v):
                return template.format(v).replace(",", ".")

            self.tbl_stats.setItem(row, 0, QTableWidgetItem(label))
            self.tbl_stats.setItem(row, 1, QTableWidgetItem(clean_fmt(fmt_avg, avg_val)))
            self.tbl_stats.setItem(row, 2, QTableWidgetItem(clean_fmt(fmt_avg, med_val)))
            self.tbl_stats.setItem(row, 3, QTableWidgetItem(clean_fmt(fmt_val, max_val)))
            self.tbl_stats.setItem(row, 4, QTableWidgetItem(clean_fmt(fmt_val, min_val)))
            self.tbl_stats.setItem(row, 5, QTableWidgetItem(clean_fmt(fmt_avg, std_val)))

    # --------------------------------------------------------------------------
    # RENDERIZADO DE GRÁFICOS MATPLOTLIB
    # --------------------------------------------------------------------------
    def _update_charts(self):
        edges = self.graph.get_edges()
        if not edges:
            return

        # 1. Histograma de Distancias
        self.fig_hist.clear()
        ax1 = self.fig_hist.add_subplot(111)
        distances = [e["distance_km"] for e in edges]
        ax1.hist(distances, bins=8, color="#2563EB", edgecolor="#1E293B", alpha=0.85, rwidth=0.88)
        ax1.set_title("Distribución de Distancias de la Red", fontsize=10, fontweight="bold", color="#1E293B", pad=8)
        ax1.set_xlabel("Distancia (km)", fontsize=8.5, color="#475569")
        ax1.set_ylabel("Frecuencia (aristas)", fontsize=8.5, color="#475569")
        ax1.grid(axis="y", linestyle="--", alpha=0.5)
        ax1.tick_params(axis="both", labelsize=8)
        self.fig_hist.tight_layout()
        self.canvas_hist.draw()

        # Extraer los 19 pares base no dirigidos
        route_pairs = {}
        for e in edges:
            u, v = e["from"], e["to"]
            pair_key = tuple(sorted([u, v]))
            if pair_key not in route_pairs:
                route_pairs[pair_key] = {
                    "label": f"{pair_key[0]}-{pair_key[1]}",
                    "toll": e["toll_cost_cop"],
                    "fuel_sum": e["fuel_cost_cop"],
                    "count": 1,
                    "distance": e["distance_km"],
                    "time": e["time_hours"]
                }
            else:
                route_pairs[pair_key]["fuel_sum"] += e["fuel_cost_cop"]
                route_pairs[pair_key]["count"] += 1

        pairs_list = list(route_pairs.values())
        for p in pairs_list:
            p["avg_fuel"] = p["fuel_sum"] / max(p["count"], 1)

        # 2. Barras de Peajes (ordenadas de mayor a menor)
        self.fig_tolls.clear()
        ax2 = self.fig_tolls.add_subplot(111)
        pairs_by_toll = sorted(pairs_list, key=lambda x: x["toll"], reverse=True)
        toll_labels = [p["label"] for p in pairs_by_toll]
        toll_vals = [p["toll"] / 1000.0 for p in pairs_by_toll]  # Miles de COP

        bars2 = ax2.bar(toll_labels, toll_vals, color="#16A34A", edgecolor="#15803D", alpha=0.88)
        ax2.set_title("Costo de Peajes por Ruta (19 pares)", fontsize=10, fontweight="bold", color="#1E293B", pad=8)
        ax2.set_ylabel("Peaje (Miles COP)", fontsize=8.5, color="#475569")
        ax2.tick_params(axis="x", rotation=55, labelsize=7.5)
        ax2.tick_params(axis="y", labelsize=8)
        ax2.grid(axis="y", linestyle="--", alpha=0.5)
        self.fig_tolls.tight_layout()
        self.canvas_tolls.draw()

        # 3. Barras de Combustible (ordenadas de mayor a menor)
        self.fig_fuel.clear()
        ax3 = self.fig_fuel.add_subplot(111)
        pairs_by_fuel = sorted(pairs_list, key=lambda x: x["avg_fuel"], reverse=True)
        fuel_labels = [p["label"] for p in pairs_by_fuel]
        fuel_vals = [p["avg_fuel"] / 1000.0 for p in pairs_by_fuel]  # Miles de COP

        ax3.bar(fuel_labels, fuel_vals, color="#D97706", edgecolor="#B45309", alpha=0.88)
        ax3.set_title("Costo Promedio Combustible por Ruta (19 pares)", fontsize=10, fontweight="bold", color="#1E293B", pad=8)
        ax3.set_ylabel("Combustible (Miles COP)", fontsize=8.5, color="#475569")
        ax3.tick_params(axis="x", rotation=55, labelsize=7.5)
        ax3.tick_params(axis="y", labelsize=8)
        ax3.grid(axis="y", linestyle="--", alpha=0.5)
        self.fig_fuel.tight_layout()
        self.canvas_fuel.draw()

        # 4. Dispersión Tiempo vs Distancia
        self.fig_scatter.clear()
        ax4 = self.fig_scatter.add_subplot(111)
        scatter_dist = [e["distance_km"] for e in edges]
        scatter_time = [e["time_hours"] for e in edges]

        ax4.scatter(scatter_dist, scatter_time, color="#6366F1", edgecolors="#4338CA", alpha=0.85, s=40)
        ax4.set_title("Relación Tiempo vs. Distancia", fontsize=10, fontweight="bold", color="#1E293B", pad=8)
        ax4.set_xlabel("Distancia (km)", fontsize=8.5, color="#475569")
        ax4.set_ylabel("Tiempo (horas)", fontsize=8.5, color="#475569")
        ax4.grid(True, linestyle="--", alpha=0.5)
        ax4.tick_params(axis="both", labelsize=8)
        self.fig_scatter.tight_layout()
        self.canvas_scatter.draw()

    # --------------------------------------------------------------------------
    # MAPA FOLIUM
    # --------------------------------------------------------------------------
    def _update_folium_map(self):
        cities = {c["id"]: c for c in self.graph.get_cities()}
        if not cities:
            return

        # Centro aproximado de Colombia
        colombia_map = folium.Map(
            location=[6.0, -74.5],
            zoom_start=6,
            tiles="OpenStreetMap"
        )

        # Marcadores para cada ciudad
        for cid, city in cities.items():
            active = city.get("active", True)
            marker_color = "blue" if active else "gray"
            icon_name = "info-sign" if active else "remove-sign"

            popup_html = (
                f"<b>{city['name']} ({cid})</b><br>"
                f"Estado: {'Activa' if active else 'Inactiva'}<br>"
                f"Gasolina: ${city['fuel_price_cop']:,.2f} COP".replace(",", ".")
            )

            folium.Marker(
                location=[city["lat"], city["lon"]],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{cid} - {city['name']}",
                icon=folium.Icon(color=marker_color, icon=icon_name)
            ).add_to(colombia_map)

        # Aristas como PolyLines grises (unificando pares)
        drawn_pairs = set()
        for edge in self.graph.get_edges():
            u, v = edge["from"], edge["to"]
            if u in cities and v in cities:
                pair = tuple(sorted([u, v]))
                if pair not in drawn_pairs:
                    drawn_pairs.add(pair)
                    locs = [
                        [cities[u]["lat"], cities[u]["lon"]],
                        [cities[v]["lat"], cities[v]["lon"]]
                    ]
                    tooltip_text = f"{u} ↔ {v} ({edge['distance_km']:.0f} km)"
                    folium.PolyLine(
                        locations=locs,
                        color="#64748B",
                        weight=2.5,
                        opacity=0.6,
                        tooltip=tooltip_text
                    ).add_to(colombia_map)

        # Si hay una ruta calculada previamente, resaltarla en rojo
        if self.current_path and len(self.current_path) >= 2:
            path_coords = []
            for cid in self.current_path:
                if cid in cities:
                    path_coords.append([cities[cid]["lat"], cities[cid]["lon"]])
            if len(path_coords) >= 2:
                folium.PolyLine(
                    locations=path_coords,
                    color="#DC2626",
                    weight=5.5,
                    opacity=0.9,
                    tooltip=f"Ruta óptima: {' → '.join(self.current_path)}"
                ).add_to(colombia_map)

        # Guardar en archivo temporal y cargar en QWebEngineView
        colombia_map.save(self._map_path)
        self.web_view.load(QUrl.fromLocalFile(self._map_path))
