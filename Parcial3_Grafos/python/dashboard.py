"""
Module: dashboard.py
Description: Road-network analytics dashboard: KPIs, descriptive statistics,
             matplotlib charts and an interactive Folium map (QWebEngineView).
"""

import os
import statistics
import tempfile

import folium
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

import styles
from graph import Graph
from widgets import KpiCard, card, format_km, section_label


def _clean_fmt(template: str, value: float) -> str:
    return template.format(value).replace(",", ".")


def _style_axes(ax, title: str, xlabel: str = "", ylabel: str = ""):
    """Estilo común de los gráficos: sin bordes superiores, rejilla suave y título a la izquierda."""
    ax.set_title(title, loc="left", fontsize=10, fontweight="semibold", color=styles.TEXT, pad=10)
    ax.set_xlabel(xlabel, fontsize=8.5, color=styles.MUTED)
    ax.set_ylabel(ylabel, fontsize=8.5, color=styles.MUTED)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(styles.BORDER)
    ax.tick_params(colors=styles.MUTED, labelsize=7.5, length=0, pad=4)
    ax.grid(axis="y", color="#EEF2F7", linewidth=1)
    ax.set_axisbelow(True)


class DashboardWidget(QWidget):
    """Dashboard de análisis de la red vial (estadísticas, gráficos y mapa Folium)."""

    def __init__(self, graph: Graph, parent=None):
        super().__init__(parent)
        self.graph = graph
        self.current_path = []
        # Flags dirty: qué partes del dashboard deben recalcularse en el próximo refresco
        self._stats_dirty = True
        self._map_dirty = True
        self._map_path = os.path.join(tempfile.gettempdir(), "pera_network_map.html")
        self._map_fallback = None

        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container.setObjectName("scrollContent")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(16)

        # --- Encabezado de página
        title = QLabel("Análisis de la red vial")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Indicadores calculados a partir de las ciudades y conexiones registradas.")
        subtitle.setObjectName("pageSubtitle")
        head = QVBoxLayout()
        head.setSpacing(2)
        head.addWidget(title)
        head.addWidget(subtitle)
        layout.addLayout(head)

        # --- KPIs
        kpis = QHBoxLayout()
        kpis.setSpacing(14)
        self.kpi_cities = KpiCard("pin", "Ciudades")
        self.kpi_edges = KpiCard("link", "Conexiones dirigidas")
        self.kpi_length = KpiCard("globe", "Longitud de la red")
        self.kpi_routes = KpiCard("route", "Rutas calculadas")
        self.kpi_routes.set_data("0", "en esta sesión")
        for kpi in (self.kpi_cities, self.kpi_edges, self.kpi_length, self.kpi_routes):
            kpis.addWidget(kpi, stretch=1)
        layout.addLayout(kpis)

        # --- Gráficos (2x2)
        charts_card = card()
        charts = QGridLayout(charts_card)
        charts.setContentsMargins(16, 14, 16, 16)
        charts.setHorizontalSpacing(18)
        charts.setVerticalSpacing(12)
        charts.addWidget(section_label("Análisis gráfico multicriterio"), 0, 0, 1, 2)

        self.fig_hist, self.canvas_hist = self._make_chart()
        self.fig_tolls, self.canvas_tolls = self._make_chart()
        self.fig_fuel, self.canvas_fuel = self._make_chart()
        self.fig_scatter, self.canvas_scatter = self._make_chart()
        charts.addWidget(self.canvas_hist, 1, 0)
        charts.addWidget(self.canvas_tolls, 1, 1)
        charts.addWidget(self.canvas_fuel, 2, 0)
        charts.addWidget(self.canvas_scatter, 2, 1)
        layout.addWidget(charts_card)

        # --- Estadísticas descriptivas
        stats_card = card()
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(16, 14, 16, 12)
        stats_layout.setSpacing(8)
        self.lbl_stats_title = section_label("Estadísticas descriptivas")
        stats_layout.addWidget(self.lbl_stats_title)

        self.tbl_stats = QTableWidget()
        self.tbl_stats.setColumnCount(6)
        self.tbl_stats.setHorizontalHeaderLabels(["CRITERIO", "MEDIA", "MEDIANA", "MÁX", "MÍN", "DESV. EST."])
        self.tbl_stats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_stats.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.tbl_stats.verticalHeader().setVisible(False)
        self.tbl_stats.verticalHeader().setDefaultSectionSize(34)
        self.tbl_stats.setShowGrid(False)
        self.tbl_stats.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_stats.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tbl_stats.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tbl_stats.setFixedHeight(4 * 34 + 36)
        self.tbl_stats.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        stats_layout.addWidget(self.tbl_stats)
        layout.addWidget(stats_card)

        # --- Mapa Folium
        map_card = card()
        map_layout = QVBoxLayout(map_card)
        map_layout.setContentsMargins(16, 14, 16, 16)
        map_layout.setSpacing(10)
        map_layout.addWidget(section_label("Mapa geográfico interactivo"))
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.web_view.setMinimumHeight(400)
        self.web_view.loadFinished.connect(self._on_map_loaded)
        map_layout.addWidget(self.web_view)
        self._map_layout = map_layout
        layout.addWidget(map_card)

        scroll.setWidget(container)
        root.addWidget(scroll)
        # No se calcula nada aquí: se hace al abrir la pestaña (refresh_if_needed)

    @staticmethod
    def _make_chart():
        fig = Figure(figsize=(5, 3.2), dpi=90, facecolor=styles.SURFACE)
        canvas = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        canvas.setMinimumHeight(270)
        return fig, canvas

    # --------------------------------------------------------------------------
    # CONTROL DE REFRESCO (flags dirty)
    # --------------------------------------------------------------------------
    def set_current_path(self, path: list[str]):
        """Guarda la ruta calculada. El mapa solo se marca sucio si la ruta cambió."""
        new_path = list(path or [])
        if new_path != self.current_path:
            self.current_path = new_path
            self._map_dirty = True
            if self.isVisible():
                self.refresh_if_needed()

    def set_routes_count(self, count: int):
        """Actualiza el contador de rutas calculadas (no recalcula nada más)."""
        self.kpi_routes.set_data(str(count), "en esta sesión")

    def mark_graph_dirty(self):
        """El grafo cambió (CRUD): estadísticas, gráficos y mapa deben recalcularse."""
        self._stats_dirty = True
        self._map_dirty = True
        if self.isVisible():
            self.refresh_if_needed()

    def refresh_if_needed(self):
        """Recalcula solo las partes marcadas como sucias."""
        if self._stats_dirty:
            self._update_kpis()
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
    # DATOS
    # --------------------------------------------------------------------------
    def _route_pairs(self, edges: list[dict]) -> list[dict]:
        """Agrupa las aristas dirigidas en pares de ciudades (tramos)."""
        route_pairs = {}
        for e in edges:
            pair_key = tuple(sorted([e["from"], e["to"]]))
            if pair_key not in route_pairs:
                route_pairs[pair_key] = {
                    "label": f"{pair_key[0]}-{pair_key[1]}",
                    "toll": e["toll_cost_cop"],
                    "fuel_sum": e["fuel_cost_cop"],
                    "count": 1,
                    "distance": e["distance_km"],
                    "time": e["time_hours"],
                }
            else:
                route_pairs[pair_key]["fuel_sum"] += e["fuel_cost_cop"]
                route_pairs[pair_key]["count"] += 1
        pairs = list(route_pairs.values())
        for p in pairs:
            p["avg_fuel"] = p["fuel_sum"] / max(p["count"], 1)
        return pairs

    def _update_kpis(self):
        cities = self.graph.get_cities()
        edges = self.graph.get_edges()
        active = sum(1 for c in cities if c.get("active", True))
        pairs = self._route_pairs(edges)
        inactive = len(cities) - active

        self.kpi_cities.set_data(
            str(len(cities)),
            f"{active} activas" + (f" · {inactive} inactiva{'s' if inactive != 1 else ''}" if inactive else ""),
        )
        self.kpi_edges.set_data(str(len(edges)), f"{len(pairs)} tramos entre ciudades")
        self.kpi_length.set_data(format_km(sum(p["distance"] for p in pairs)), f"suma de los {len(pairs)} tramos")

    # --------------------------------------------------------------------------
    # CÁLCULO DE ESTADÍSTICAS
    # --------------------------------------------------------------------------
    def _update_statistics_table(self):
        edges = self.graph.get_edges()
        self.lbl_stats_title.setText(f"ESTADÍSTICAS DESCRIPTIVAS · {len(edges)} ARISTAS DIRIGIDAS")
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

            label_item = QTableWidgetItem(label)
            font = label_item.font()
            font.setWeight(600)
            label_item.setFont(font)
            self.tbl_stats.setItem(row, 0, label_item)
            self.tbl_stats.setItem(row, 1, QTableWidgetItem(_clean_fmt(fmt_avg, avg_val)))
            self.tbl_stats.setItem(row, 2, QTableWidgetItem(_clean_fmt(fmt_avg, med_val)))
            self.tbl_stats.setItem(row, 3, QTableWidgetItem(_clean_fmt(fmt_val, max_val)))
            self.tbl_stats.setItem(row, 4, QTableWidgetItem(_clean_fmt(fmt_val, min_val)))
            self.tbl_stats.setItem(row, 5, QTableWidgetItem(_clean_fmt(fmt_avg, std_val)))

    # --------------------------------------------------------------------------
    # RENDERIZADO DE GRÁFICOS MATPLOTLIB
    # --------------------------------------------------------------------------
    def _update_charts(self):
        edges = self.graph.get_edges()
        if not edges:
            return
        pairs_list = self._route_pairs(edges)
        n_pairs = len(pairs_list)

        # 1. Histograma de distancias
        self.fig_hist.clear()
        ax1 = self.fig_hist.add_subplot(111)
        distances = [e["distance_km"] for e in edges]
        ax1.hist(distances, bins=8, color=styles.PRIMARY, alpha=0.9, rwidth=0.86)
        _style_axes(ax1, "Distribución de distancias de la red", "Distancia (km)", "Frecuencia (aristas)")
        self.fig_hist.tight_layout()
        self.canvas_hist.draw()

        # 2. Peajes por tramo (de mayor a menor)
        self.fig_tolls.clear()
        ax2 = self.fig_tolls.add_subplot(111)
        pairs_by_toll = sorted(pairs_list, key=lambda x: x["toll"], reverse=True)
        ax2.bar([p["label"] for p in pairs_by_toll], [p["toll"] / 1000.0 for p in pairs_by_toll],
                color=styles.NAVY, width=0.68)
        _style_axes(ax2, f"Costo de peajes por ruta ({n_pairs} pares)", ylabel="Peaje (miles COP)")
        ax2.tick_params(axis="x", rotation=60, labelsize=7)
        self.fig_tolls.tight_layout()
        self.canvas_tolls.draw()

        # 3. Combustible promedio por tramo (de mayor a menor)
        self.fig_fuel.clear()
        ax3 = self.fig_fuel.add_subplot(111)
        pairs_by_fuel = sorted(pairs_list, key=lambda x: x["avg_fuel"], reverse=True)
        ax3.bar([p["label"] for p in pairs_by_fuel], [p["avg_fuel"] / 1000.0 for p in pairs_by_fuel],
                color=styles.SECONDARY, width=0.68)
        _style_axes(ax3, f"Costo promedio de combustible por ruta ({n_pairs} pares)",
                    ylabel="Combustible (miles COP)")
        ax3.tick_params(axis="x", rotation=60, labelsize=7)
        self.fig_fuel.tight_layout()
        self.canvas_fuel.draw()

        # 4. Dispersión tiempo vs distancia
        self.fig_scatter.clear()
        ax4 = self.fig_scatter.add_subplot(111)
        ax4.scatter([e["distance_km"] for e in edges], [e["time_hours"] for e in edges],
                    color=styles.PRIMARY, edgecolors="#FFFFFF", linewidths=0.8, alpha=0.85, s=42)
        _style_axes(ax4, "Relación tiempo vs. distancia", "Distancia (km)", "Tiempo (horas)")
        ax4.grid(axis="x", color="#EEF2F7", linewidth=1)
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
        colombia_map = folium.Map(location=[6.0, -74.5], zoom_start=6, tiles="OpenStreetMap")

        # Marcadores para cada ciudad
        for cid, city in cities.items():
            active = city.get("active", True)
            popup_html = (
                f"<b>{city['name']} ({cid})</b><br>"
                f"Estado: {'Activa' if active else 'Inactiva'}<br>"
                f"Gasolina: ${city['fuel_price_cop']:,.2f} COP".replace(",", ".")
            )
            folium.CircleMarker(
                location=[city["lat"], city["lon"]],
                radius=7,
                color="#FFFFFF" if active else styles.SUBTLE,
                weight=2,
                fill=True,
                fill_color=styles.MAP_NODE_BORDER if active else styles.MAP_NODE_INACTIVE_FILL,
                fill_opacity=1.0,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{cid} - {city['name']}",
            ).add_to(colombia_map)

        # Aristas como líneas grises (unificando pares)
        drawn_pairs = set()
        for edge in self.graph.get_edges():
            u, v = edge["from"], edge["to"]
            if u in cities and v in cities:
                pair = tuple(sorted([u, v]))
                if pair not in drawn_pairs:
                    drawn_pairs.add(pair)
                    folium.PolyLine(
                        locations=[[cities[u]["lat"], cities[u]["lon"]], [cities[v]["lat"], cities[v]["lon"]]],
                        color="#64748B",
                        weight=2,
                        opacity=0.55,
                        tooltip=f"{u} ↔ {v} ({edge['distance_km']:.0f} km)",
                    ).add_to(colombia_map)

        # Si hay una ruta calculada, resaltarla
        if self.current_path and len(self.current_path) >= 2:
            path_coords = [[cities[c]["lat"], cities[c]["lon"]] for c in self.current_path if c in cities]
            if len(path_coords) >= 2:
                folium.PolyLine(locations=path_coords, color="#FFFFFF", weight=9, opacity=0.9).add_to(colombia_map)
                folium.PolyLine(
                    locations=path_coords,
                    color=styles.PRIMARY,
                    weight=5,
                    opacity=0.95,
                    tooltip=f"Ruta óptima: {' → '.join(self.current_path)}",
                ).add_to(colombia_map)

        # Guardar en archivo temporal y cargar en QWebEngineView
        colombia_map.save(self._map_path)
        html_path = os.path.abspath(self._map_path)
        if os.path.exists(html_path):
            self.web_view.load(QUrl.fromLocalFile(html_path))

    def _on_map_loaded(self, ok: bool):
        """Registra la carga y muestra HTML básico si QtWebEngine falla."""
        print(f"[PERA] Mapa Folium cargado: {ok}")
        if ok or self._map_fallback is not None:
            return
        warning = QLabel("No se pudo cargar el mapa. Verifica que PyQt6-WebEngine esté instalado.")
        warning.setWordWrap(True)
        self._map_fallback = QTextBrowser()
        self._map_fallback.setOpenExternalLinks(True)
        self._map_fallback.setMinimumHeight(400)
        self._map_fallback.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._map_layout.insertWidget(1, warning)
        self._map_fallback.setHtml(f"<h3>Mapa de rutas PERA</h3><p>{warning.text()}</p><p>El archivo Folium fue generado en: {self._map_path}</p>")
        self._map_layout.replaceWidget(self.web_view, self._map_fallback)
        self.web_view.hide()
