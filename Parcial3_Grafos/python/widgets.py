"""
Module: widgets.py
Description: Reusable UI components and formatting helpers for PERA.
"""

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

import icons
import styles


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
# PIEZAS BÁSICAS
# ==============================================================================

def card() -> QFrame:
    """Contenedor blanco con borde suave (tarjeta)."""
    frame = QFrame()
    frame.setObjectName("card")
    return frame


def divider() -> QFrame:
    line = QFrame()
    line.setObjectName("divider")
    return line


def section_label(text: str) -> QLabel:
    """Rótulo de sección en mayúsculas con espaciado de letras."""
    label = QLabel(text.upper())
    label.setObjectName("sectionLabel")
    font = label.font()
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.6)
    label.setFont(font)
    return label


def icon_label(name: str, color: str, size: int = 16) -> QLabel:
    label = QLabel()
    label.setPixmap(icons.pixmap(name, color, size))
    label.setFixedSize(size, size)
    return label


def status_pill(active: bool) -> QWidget:
    """Píldora de estado para celdas de tabla (Activa / Inactiva)."""
    holder = QWidget()
    layout = QHBoxLayout(holder)
    layout.setContentsMargins(8, 0, 8, 0)
    pill = QLabel("Activa" if active else "Inactiva")
    pill.setObjectName("pillSuccess" if active else "pillMuted")
    layout.addWidget(pill, alignment=Qt.AlignmentFlag.AlignVCenter)
    layout.addStretch()
    return holder


# ==============================================================================
# MARCADOR ORIGEN -> DESTINO (punto verde, línea punteada, punto rojo)
# ==============================================================================

class StopMarker(QWidget):
    """Dibuja el conector vertical entre el selector de origen y el de destino."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(18)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.width() / 2
        top, bottom = 17.0, self.height() - 17.0

        pen = QPen(QColor(styles.BORDER_STRONG), 1.5, Qt.PenStyle.DotLine)
        p.setPen(pen)
        p.drawLine(QPointF(cx, top + 7), QPointF(cx, bottom - 7))

        p.setPen(QPen(QColor(styles.SUCCESS), 3))
        p.setBrush(QColor(styles.SURFACE))
        p.drawEllipse(QPointF(cx, top), 5, 5)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(styles.DANGER))
        p.drawEllipse(QPointF(cx, bottom), 6, 6)
        p.setBrush(QColor(styles.SURFACE))
        p.drawEllipse(QPointF(cx, bottom), 2.2, 2.2)
        p.end()


# ==============================================================================
# TARJETA DE MÉTRICA (resultado de ruta) Y KPI (dashboard)
# ==============================================================================

class MetricTile(QFrame):
    """Métrica compacta: icono + rótulo arriba, valor abajo."""

    def __init__(self, icon_name: str, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("metricTile")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(3)

        head = QHBoxLayout()
        head.setSpacing(6)
        head.addWidget(icon_label(icon_name, styles.MUTED, 14))
        lbl = QLabel(title)
        lbl.setObjectName("metricLabel")
        head.addWidget(lbl)
        head.addStretch()

        self.lbl_value = QLabel("-")
        self.lbl_value.setObjectName("metricValue")
        layout.addLayout(head)
        layout.addWidget(self.lbl_value)

    def set_value(self, text: str):
        self.lbl_value.setText(text)


class KpiCard(QFrame):
    """Indicador del dashboard: icono, rótulo, valor grande y una nota."""

    def __init__(self, icon_name: str, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        badge = QLabel()
        badge.setObjectName("kpiIcon")
        badge.setFixedSize(40, 40)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setPixmap(icons.pixmap(icon_name, styles.PRIMARY, 20))
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)

        text = QVBoxLayout()
        text.setSpacing(0)
        lbl_title = QLabel(title)
        lbl_title.setObjectName("muted")
        self.lbl_value = QLabel("-")
        self.lbl_value.setObjectName("kpiValue")
        self.lbl_note = QLabel("")
        self.lbl_note.setObjectName("hint")
        text.addWidget(lbl_title)
        text.addWidget(self.lbl_value)
        text.addWidget(self.lbl_note)
        layout.addLayout(text, stretch=1)

    def set_data(self, value: str, note: str = ""):
        self.lbl_value.setText(value)
        self.lbl_note.setText(note)


# ==============================================================================
# LEYENDA DEL MAPA
# ==============================================================================

def _legend_swatch(kind: str) -> QPixmap:
    """Pequeño símbolo de la leyenda dibujado con QPainter."""
    ratio, w, h = 2.0, 22, 14
    pm = QPixmap(int(w * ratio), int(h * ratio))
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(ratio, ratio)
    c = QPointF(w / 2, h / 2)

    if kind == "route":
        p.setPen(QPen(QColor("#FFFFFF"), 6, cap=Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(2, c.y()), QPointF(w - 2, c.y()))
        p.setPen(QPen(QColor(styles.MAP_ROUTE), 3, cap=Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(2, c.y()), QPointF(w - 2, c.y()))
    else:
        fills = {
            "origin": (styles.MAP_ORIGIN, "#FFFFFF", Qt.PenStyle.SolidLine, 5.5),
            "destination": (styles.MAP_DESTINATION, "#FFFFFF", Qt.PenStyle.SolidLine, 5.5),
            "via": ("#FFFFFF", styles.MAP_ROUTE, Qt.PenStyle.SolidLine, 4.5),
            "city": (styles.MAP_NODE_FILL, styles.MAP_NODE_BORDER, Qt.PenStyle.SolidLine, 4),
            "inactive": (styles.MAP_NODE_INACTIVE_FILL, styles.MAP_NODE_INACTIVE_BORDER, Qt.PenStyle.DashLine, 4),
        }
        fill, border, style, r = fills[kind]
        p.setPen(QPen(QColor(border), 1.8, style))
        p.setBrush(QColor(fill))
        p.drawEllipse(c, r, r)
    p.end()
    pm.setDevicePixelRatio(ratio)
    return pm


class MapLegend(QFrame):
    """Leyenda flotante sobre el mapa."""

    ITEMS = [
        ("origin", "Origen"),
        ("destination", "Destino"),
        ("via", "Ciudad intermedia"),
        ("city", "Ciudad"),
        ("inactive", "Inactiva"),
        ("route", "Ruta calculada"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(6)
        for kind, text in self.ITEMS:
            swatch = QLabel()
            swatch.setPixmap(_legend_swatch(kind))
            lbl = QLabel(text)
            lbl.setObjectName("legendText")
            layout.addWidget(swatch)
            layout.addWidget(lbl)
            layout.addSpacing(10)
        layout.addStretch()


# ==============================================================================
# RESULTADO DE RUTA
# ==============================================================================

class LegRow(QWidget):
    """Una fila del itinerario: número, tramo, peaje y distancia/tiempo."""

    def __init__(self, index: int, leg: dict, names: dict, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(10)

        num = QLabel(str(index))
        num.setObjectName("legIndex")
        num.setFixedSize(20, 20)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(num, alignment=Qt.AlignmentFlag.AlignTop)

        left = QVBoxLayout()
        left.setSpacing(0)
        title = QLabel(f"{leg['from']} → {leg['to']}")
        title.setObjectName("legTitle")
        title.setToolTip(f"{names.get(leg['from'], leg['from'])} → {names.get(leg['to'], leg['to'])}")
        sub = QLabel(f"Peaje {format_cop(leg['toll_cost_cop'])}")
        sub.setObjectName("hint")
        left.addWidget(title)
        left.addWidget(sub)
        layout.addLayout(left, stretch=1)

        right = QVBoxLayout()
        right.setSpacing(0)
        dist = QLabel(format_km(leg["distance_km"]))
        dist.setObjectName("legTitle")
        dist.setAlignment(Qt.AlignmentFlag.AlignRight)
        time = QLabel(format_hours(leg["time_hours"]))
        time.setObjectName("hint")
        time.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(dist)
        right.addWidget(time)
        layout.addLayout(right)


class RouteResultCard(QWidget):
    """
    Muestra el resultado de una ruta en tres estados:
    vacío (instrucciones), error (mensaje) o resultado (métricas + itinerario).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Estado vacío
        self.empty_box = QWidget()
        empty = QVBoxLayout(self.empty_box)
        empty.setContentsMargins(4, 18, 4, 8)
        empty.setSpacing(6)
        empty.addWidget(icon_label("route", styles.SUBTLE, 28), alignment=Qt.AlignmentFlag.AlignHCenter)
        t = QLabel("Sin ruta calculada")
        t.setObjectName("emptyTitle")
        t.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        d = QLabel("Elige origen, destino y criterio, o haz clic sobre las ciudades del mapa.")
        d.setObjectName("hint")
        d.setWordWrap(True)
        d.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        empty.addWidget(t)
        empty.addWidget(d)
        layout.addWidget(self.empty_box)

        # --- Estado de error
        self.error_box = QFrame()
        self.error_box.setObjectName("errorBox")
        err = QHBoxLayout(self.error_box)
        err.setContentsMargins(12, 10, 12, 10)
        err.setSpacing(10)
        err.addWidget(icon_label("alert", styles.DANGER, 18), alignment=Qt.AlignmentFlag.AlignTop)
        self.lbl_error = QLabel()
        self.lbl_error.setObjectName("errorText")
        self.lbl_error.setWordWrap(True)
        err.addWidget(self.lbl_error, stretch=1)
        layout.addWidget(self.error_box)

        # --- Estado con resultado
        self.result_box = QWidget()
        res = QVBoxLayout(self.result_box)
        res.setContentsMargins(0, 0, 0, 0)
        res.setSpacing(10)

        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("routeTitle")
        self.lbl_title.setWordWrap(True)
        self.lbl_path = QLabel()
        self.lbl_path.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_path.setWordWrap(True)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_path)
        res.addLayout(title_box)

        grid = QGridLayout()
        grid.setSpacing(8)
        self.tile_dist = MetricTile("ruler", "Distancia")
        self.tile_time = MetricTile("clock", "Tiempo")
        self.tile_toll = MetricTile("ticket", "Peajes")
        self.tile_fuel = MetricTile("fuel", "Combustible")
        grid.addWidget(self.tile_dist, 0, 0)
        grid.addWidget(self.tile_time, 0, 1)
        grid.addWidget(self.tile_toll, 1, 0)
        grid.addWidget(self.tile_fuel, 1, 1)
        res.addLayout(grid)

        total = QFrame()
        total.setObjectName("totalTile")
        tl = QHBoxLayout(total)
        tl.setContentsMargins(12, 10, 12, 10)
        tl.addWidget(icon_label("wallet", styles.PRIMARY, 18))
        tcol = QVBoxLayout()
        tcol.setSpacing(0)
        tcap = QLabel("Costo total estimado")
        tcap.setObjectName("metricLabel")
        tsub = QLabel("Peajes + combustible")
        tsub.setObjectName("hint")
        tcol.addWidget(tcap)
        tcol.addWidget(tsub)
        tl.addLayout(tcol, stretch=1)
        self.lbl_total = QLabel("-")
        self.lbl_total.setObjectName("totalValue")
        tl.addWidget(self.lbl_total)
        res.addWidget(total)

        # Solo para el criterio "Combinada": índice que minimizó Dijkstra
        self.lbl_combined = QLabel()
        self.lbl_combined.setObjectName("hint")
        res.addWidget(self.lbl_combined)

        res.addWidget(section_label("Itinerario"))
        self.legs_layout = QVBoxLayout()
        self.legs_layout.setSpacing(0)
        res.addLayout(self.legs_layout)

        layout.addWidget(self.result_box)
        self.show_empty()

    def _show_only(self, widget):
        for w in (self.empty_box, self.error_box, self.result_box):
            w.setVisible(w is widget)

    def show_empty(self):
        self._show_only(self.empty_box)

    def show_error(self, message: str):
        self.lbl_error.setText(message)
        self._show_only(self.error_box)

    def show_result(self, result: dict, legs: list[dict], criterion: str, city_names: dict):
        """
        result: diccionario devuelto por Graph.shortest_path*.
        legs: aristas recorridas (from, to, distance_km, time_hours, toll_cost_cop, ...).
        city_names: id -> nombre de la ciudad.
        """
        path = result.get("path", [])
        if path:
            self.lbl_title.setText(f"{city_names.get(path[0], path[0])} → {city_names.get(path[-1], path[-1])}")

        stops = []
        for i, cid in enumerate(path):
            if i == 0:
                color = styles.SUCCESS_DARK
            elif i == len(path) - 1:
                color = styles.DANGER_DARK
            else:
                color = styles.TEXT
            stops.append(f'<span style="color:{color}; font-weight:600;">{cid}</span>')
        n = len(legs)
        self.lbl_path.setText(
            f' <span style="color:{styles.SUBTLE};">›</span> '.join(stops)
            + f'<span style="color:{styles.MUTED};">&nbsp;&nbsp;·&nbsp;&nbsp;{criterion} · '
              f'{n} tramo{"s" if n != 1 else ""}</span>'
        )

        toll = result.get("total_toll_cop", 0.0)
        fuel = result.get("total_fuel_cop", 0.0)
        self.tile_dist.set_value(format_km(result.get("total_distance_km", 0.0)))
        self.tile_time.set_value(format_hours(result.get("total_time_hours", 0.0)))
        self.tile_toll.set_value(format_cop(toll))
        self.tile_fuel.set_value(format_cop(fuel))
        self.lbl_total.setText(format_cop(toll + fuel))

        combined = result.get("total_combined_cost")
        self.lbl_combined.setVisible(combined is not None)
        if combined is not None:
            self.lbl_combined.setText(f"Índice combinado minimizado: {combined:.4f}")

        # Reconstruir el itinerario
        while self.legs_layout.count():
            row = self.legs_layout.takeAt(0).widget()
            if row:
                row.setParent(None)  # se oculta de inmediato
                row.deleteLater()
        for i, leg in enumerate(legs, start=1):
            self.legs_layout.addWidget(LegRow(i, leg, city_names))

        self._show_only(self.result_box)
