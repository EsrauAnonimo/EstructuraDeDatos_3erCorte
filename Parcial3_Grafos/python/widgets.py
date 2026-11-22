"""
Module: widgets.py
Description: Reusable UI widgets and formatting helpers for the PERA routes panel.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget


# ==============================================================================
# FORMATO DE VALORES
# ==============================================================================

def format_cop(value: float) -> str:
    """Formatea pesos colombianos con punto de miles: 68108 -> '$68.108'."""
    return f"${value:,.0f}".replace(",", ".")


def format_hours(hours: float) -> str:
    """Convierte horas decimales a texto legible: 9.23 -> '9 h 14 min'."""
    total_min = int(round(hours * 60))
    h, m = divmod(total_min, 60)
    if h == 0:
        return f"{m} min"
    return f"{h} h {m:02d} min"


def format_km(km: float) -> str:
    return f"{km:,.0f} km".replace(",", ".")


# ==============================================================================
# TARJETA DE INDICADOR
# ==============================================================================

class StatTile(QFrame):
    """Tarjeta pequeña con un título (icono + texto) y un valor grande."""

    def __init__(self, title: str, highlight: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("statTileTotal" if highlight else "statTile")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("statLabel")
        self.lbl_value = QLabel("-")
        self.lbl_value.setObjectName("statValueTotal" if highlight else "statValue")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

    def set_value(self, text: str):
        self.lbl_value.setText(text)


# ==============================================================================
# TARJETA DE RESULTADO DE RUTA
# ==============================================================================

class RouteResultCard(QWidget):
    """
    Muestra el resultado de una ruta en tres estados:
    vacío (instrucciones), error (mensaje en rojo) o resultado (indicadores + tramos).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Estado vacío
        self.lbl_empty = QLabel(
            "Elige una ciudad de origen y una de destino y pulsa <b>Calcular ruta</b>.<br><br>"
            "También puedes hacer <b>clic izquierdo</b> sobre una ciudad del mapa para "
            "marcarla como origen y <b>clic derecho</b> para el destino."
        )
        self.lbl_empty.setObjectName("emptyState")
        self.lbl_empty.setWordWrap(True)
        self.lbl_empty.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.lbl_empty)

        # Estado de error
        self.error_box = QFrame()
        self.error_box.setObjectName("errorBox")
        err_layout = QVBoxLayout(self.error_box)
        err_layout.setContentsMargins(12, 10, 12, 10)
        self.lbl_error = QLabel()
        self.lbl_error.setObjectName("errorText")
        self.lbl_error.setWordWrap(True)
        err_layout.addWidget(self.lbl_error)
        layout.addWidget(self.error_box)

        # Estado con resultado
        self.result_box = QWidget()
        res_layout = QVBoxLayout(self.result_box)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.setSpacing(10)

        self.lbl_path = QLabel()
        self.lbl_path.setObjectName("routePath")
        self.lbl_path.setWordWrap(True)
        self.lbl_path.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_summary = QLabel()
        self.lbl_summary.setObjectName("hintLabel")
        res_layout.addWidget(self.lbl_path)
        res_layout.addWidget(self.lbl_summary)

        grid = QGridLayout()
        grid.setSpacing(8)
        self.tile_dist = StatTile("📏 Distancia")
        self.tile_time = StatTile("⏱️ Tiempo")
        self.tile_toll = StatTile("🚧 Peajes")
        self.tile_fuel = StatTile("⛽ Combustible")
        self.tile_total = StatTile("💰 Costo total (peajes + combustible)", highlight=True)
        grid.addWidget(self.tile_dist, 0, 0)
        grid.addWidget(self.tile_time, 0, 1)
        grid.addWidget(self.tile_toll, 1, 0)
        grid.addWidget(self.tile_fuel, 1, 1)
        grid.addWidget(self.tile_total, 2, 0, 1, 2)
        res_layout.addLayout(grid)

        lbl_legs_title = QLabel("Itinerario por tramos")
        lbl_legs_title.setObjectName("sectionTitle")
        res_layout.addWidget(lbl_legs_title)

        self.lbl_legs = QLabel()
        self.lbl_legs.setObjectName("legsLabel")
        self.lbl_legs.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_legs.setWordWrap(True)
        res_layout.addWidget(self.lbl_legs)

        layout.addWidget(self.result_box)
        layout.addStretch()

        self.show_empty()

    def _show_only(self, widget):
        for w in (self.lbl_empty, self.error_box, self.result_box):
            w.setVisible(w is widget)

    def show_empty(self):
        self._show_only(self.lbl_empty)

    def show_error(self, message: str):
        self.lbl_error.setText(f"⚠️ {message}")
        self._show_only(self.error_box)

    def show_result(self, result: dict, legs: list[dict], criterion: str, city_names: dict):
        """
        result: diccionario devuelto por Graph.shortest_path*.
        legs: lista de aristas recorridas (from, to, distance_km, time_hours, ...).
        city_names: id -> nombre de la ciudad.
        """
        path = result.get("path", [])
        stops = []
        for i, cid in enumerate(path):
            if i == 0:
                color = "#16A34A"
            elif i == len(path) - 1:
                color = "#DC2626"
            else:
                color = "#1E293B"
            stops.append(f'<span style="color:{color}; font-weight:700;">{cid}</span>')
        self.lbl_path.setText(' <span style="color:#94A3B8;">→</span> '.join(stops))

        origin_name = city_names.get(path[0], path[0]) if path else ""
        dest_name = city_names.get(path[-1], path[-1]) if path else ""
        n_legs = len(legs)
        self.lbl_summary.setText(
            f"{origin_name} → {dest_name} · optimizada por <b>{criterion}</b> · "
            f"{n_legs} tramo{'s' if n_legs != 1 else ''}"
        )

        toll = result.get("total_toll_cop", 0.0)
        fuel = result.get("total_fuel_cop", 0.0)
        self.tile_dist.set_value(format_km(result.get("total_distance_km", 0.0)))
        self.tile_time.set_value(format_hours(result.get("total_time_hours", 0.0)))
        self.tile_toll.set_value(format_cop(toll))
        self.tile_fuel.set_value(format_cop(fuel))
        self.tile_total.set_value(format_cop(toll + fuel))

        # Un tramo por línea (texto que se ajusta al ancho del panel)
        lines = []
        for i, leg in enumerate(legs, start=1):
            lines.append(
                f'<span style="color:#94A3B8;">{i}.</span> <b>{leg["from"]} → {leg["to"]}</b>'
                f'<br><span style="color:#64748B;">&nbsp;&nbsp;&nbsp;&nbsp;{format_km(leg["distance_km"])} · '
                f'{format_hours(leg["time_hours"])} · peaje {format_cop(leg["toll_cost_cop"])}</span>'
            )
        self.lbl_legs.setText("<br>".join(lines))
        self._show_only(self.result_box)
