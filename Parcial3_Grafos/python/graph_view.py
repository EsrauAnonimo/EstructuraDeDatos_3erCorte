"""
Module: graph_view.py
Description: Matplotlib rendering of the PERA road network embedded in PyQt6.
             Cities are placed using real lat/lon scaled to the canvas; road
             segments are clean lines with distance labels at the midpoint.
"""

import matplotlib
from matplotlib import font_manager, patheffects
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QToolTip

import styles
from graph import Graph


def _use_ui_font():
    """Usa la tipografía de la interfaz en matplotlib si está instalada (Windows)."""
    try:
        font_manager.findfont(font_manager.FontProperties(family="Segoe UI"), fallback_to_default=False)
        matplotlib.rcParams["font.family"] = "Segoe UI"
    except ValueError:
        pass  # se mantiene la fuente por defecto de matplotlib


_use_ui_font()

TITLE = "Red de Rutas - PERA"

# Tamaños (puntos)
NODE_SIZE = 64            # área del marcador (pt^2)
NODE_RADIUS_PTS = (NODE_SIZE ** 0.5) / 2
ENDPOINT_SIZE = 150
ROUTE_WIDTH = 3.2
ROUTE_CASING = 7.0
LABEL_MIN_GAP = 0.07      # no se rotulan tramos más cortos que esto (coordenadas normalizadas)

# Márgenes de la vista por defecto (coordenadas normalizadas)
VIEW_MARGIN_X = 0.10
VIEW_MARGIN_Y = 0.07


def _halo(width=3.0, color=styles.MAP_BG):
    """Contorno del color del fondo para que el texto se lea sobre las líneas."""
    return [patheffects.withStroke(linewidth=width, foreground=color)]


def graph_signature(graph: Graph) -> int:
    """Hash del estado del grafo (ciudades + aristas). Cambia si el grafo cambia."""
    cities = tuple(sorted(
        (c["id"], c["name"], c["lat"], c["lon"], c.get("active", True))
        for c in graph.get_cities()
    ))
    edges = tuple(sorted(
        (e["from"], e["to"], e.get("distance_km", 0))
        for e in graph.get_edges()
    ))
    return hash((cities, edges))


def _layout_positions(cities: dict, min_gap: float = 0.08, steps: int = 60) -> dict:
    """
    Normaliza lat/lon reales a [0, 1] y separa un poco los nodos que quedan
    demasiado juntos (p. ej. el Eje Cafetero) para que no se solapen.
    """
    lons = [c["lon"] for c in cities.values()]
    lats = [c["lat"] for c in cities.values()]
    span_x = (max(lons) - min(lons)) or 1.0
    span_y = (max(lats) - min(lats)) or 1.0
    pos = {
        cid: [(c["lon"] - min(lons)) / span_x, (c["lat"] - min(lats)) / span_y]
        for cid, c in cities.items()
    }

    ids = list(pos)
    for _ in range(steps):
        moved = False
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                dx = pos[b][0] - pos[a][0]
                dy = pos[b][1] - pos[a][1]
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < min_gap:
                    # Empuja ambos nodos en direcciones opuestas
                    if dist == 0:
                        dx, dy, dist = 1.0, 0.0, 1.0
                    push = (min_gap - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    pos[a][0] -= ux * push
                    pos[a][1] -= uy * push
                    pos[b][0] += ux * push
                    pos[b][1] += uy * push
                    moved = True
        if not moved:
            break
    return {cid: (p[0], p[1]) for cid, p in pos.items()}


def _label_side(cid: str, pos: dict) -> str:
    """Coloca el nombre del lado contrario a la ciudad vecina más cercana."""
    x, y = pos[cid]
    others = [p for k, p in pos.items() if k != cid]
    if not others:
        return "right"
    nx, _ = min(others, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
    if x > 0.88:
        return "left"
    if x < 0.12:
        return "right"
    return "left" if nx > x else "right"


def _path_edges(path: list[str] | None) -> list[tuple[str, str]]:
    """Convierte una ruta [A, B, C] en la lista de aristas [(A,B), (B,C)]."""
    if not path or len(path) < 2:
        return []
    return [(path[i], path[i + 1]) for i in range(len(path) - 1)]


def default_limits(pos: dict) -> tuple:
    xs = [p[0] for p in pos.values()] or [0.0, 1.0]
    ys = [p[1] for p in pos.values()] or [0.0, 1.0]
    return ((min(xs) - VIEW_MARGIN_X, max(xs) + VIEW_MARGIN_X),
            (min(ys) - VIEW_MARGIN_Y, max(ys) + VIEW_MARGIN_Y))


def _draw_name(ax, xy, name: str, side: str, color: str, zorder: float = 4, weight: str = "semibold"):
    """Nombre de la ciudad junto al nodo, con halo para leerse sobre las líneas."""
    return ax.annotate(name, xy, xytext=(9 if side == "right" else -9, 0), textcoords="offset points",
                       ha="left" if side == "right" else "right", va="center", fontsize=8.5,
                       fontweight=weight, color=color, zorder=zorder, path_effects=_halo(3.5))


def draw_network(ax, graph: Graph, show_distances: bool = True, show_names: bool = True) -> dict:
    """
    Dibuja la red base (tramos, distancias y ciudades) sin la ruta.
    Retorna posiciones y etiquetas para luego superponer la ruta.
    """
    ax.clear()
    ax.set_facecolor(styles.MAP_BG)
    ax.axis("off")

    cities = {c["id"]: c for c in graph.get_cities()}
    base = {"cities": cities, "pos": {}, "labels": {}, "names": {}}
    if not cities:
        return base

    pos = _layout_positions(cities)
    base["pos"] = pos

    def is_active(cid):
        return cities[cid].get("active", True)

    # Agrupar aristas dirigidas en tramos (par de ciudades)
    pairs = {}
    for edge in graph.get_edges():
        u, v = edge["from"], edge["to"]
        if u in pos and v in pos:
            pairs.setdefault(tuple(sorted((u, v))), {})[(u, v)] = edge

    active_lines, inactive_lines = [], []
    for (a, b), directed in pairs.items():
        segment = [pos[a], pos[b]]
        usable = is_active(a) and is_active(b)
        (active_lines if usable else inactive_lines).append(segment)

        # Tramos de un solo sentido: flecha pequeña indicando la dirección
        if len(directed) == 1:
            (u, v), = directed.keys()
            ax.add_patch(FancyArrowPatch(
                pos[u], pos[v], arrowstyle="-|>", mutation_scale=9,
                shrinkA=NODE_RADIUS_PTS, shrinkB=NODE_RADIUS_PTS + 1,
                color=styles.SUBTLE, linewidth=0, zorder=1.5,
            ))

        dists = sorted({round(e.get("distance_km", 0)) for e in directed.values()})
        text = "/".join(f"{d:.0f}" for d in dists) + " km"
        xy = ((pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2)
        base["labels"][(a, b)] = (xy, text)

        length = ((pos[a][0] - pos[b][0]) ** 2 + (pos[a][1] - pos[b][1]) ** 2) ** 0.5
        if show_distances and length >= LABEL_MIN_GAP:
            ax.text(xy[0], xy[1], text, fontsize=7, color=styles.MAP_LABEL, ha="center", va="center",
                    zorder=2, path_effects=_halo())

    ax.add_collection(LineCollection(active_lines, colors=styles.MAP_EDGE, linewidths=1.3,
                                     capstyle="round", zorder=1))
    if inactive_lines:
        ax.add_collection(LineCollection(inactive_lines, colors=styles.MAP_EDGE_INACTIVE, linewidths=1.2,
                                         linestyles=(0, (4, 3)), zorder=1))

    # Ciudades
    for cid, (x, y) in pos.items():
        active = is_active(cid)
        ax.scatter([x], [y], s=NODE_SIZE, zorder=3,
                   facecolors=styles.MAP_NODE_FILL if active else styles.MAP_NODE_INACTIVE_FILL,
                   edgecolors=styles.MAP_NODE_BORDER if active else styles.MAP_NODE_INACTIVE_BORDER,
                   linewidths=1.6, linestyles="-" if active else "--")
        if show_names:
            side = _label_side(cid, pos)
            name = cities[cid]["name"] + ("" if active else " (inactiva)")
            base["names"][cid] = (name, side)
            _draw_name(ax, (x, y), name, side, styles.TEXT if active else styles.SUBTLE)

    (x0, x1), (y0, y1) = default_limits(pos)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    return base


def draw_route_overlay(ax, base: dict, path=None, origin=None, destination=None, animated=False) -> list:
    """
    Dibuja encima de la red base solo lo que depende de la ruta:
    tramos de la ruta (con borde blanco y flecha), sus distancias,
    ciudades intermedias, origen y destino.
    Retorna los artistas creados para poder quitarlos después.
    """
    pos, cities = base["pos"], base["cities"]
    overlay = []

    def add(artist):
        artist.set_animated(animated)
        overlay.append(artist)
        return artist

    legs = [(u, v) for u, v in _path_edges(path) if u in pos and v in pos]
    for u, v in legs:
        # Borde blanco (casing) + línea de la ruta con flecha de dirección
        add(ax.add_patch(FancyArrowPatch(pos[u], pos[v], arrowstyle="-", shrinkA=0, shrinkB=0,
                                         color="#FFFFFF", linewidth=ROUTE_CASING, zorder=5,
                                         capstyle="round")))
    for u, v in legs:
        add(ax.add_patch(FancyArrowPatch(pos[u], pos[v], arrowstyle="-|>", mutation_scale=15,
                                         shrinkA=0, shrinkB=NODE_RADIUS_PTS + 3,
                                         color=styles.MAP_ROUTE, linewidth=ROUTE_WIDTH, zorder=6,
                                         capstyle="round", joinstyle="round")))
    for u, v in legs:
        pair = tuple(sorted((u, v)))
        if pair in base["labels"]:
            xy, text = base["labels"][pair]
            add(ax.text(xy[0], xy[1], text, fontsize=7.5, fontweight="bold", color=styles.MAP_ROUTE,
                        ha="center", va="center", zorder=7,
                        bbox={"boxstyle": "round,pad=0.25", "fc": "#FFFFFF", "ec": "#BFDBFE", "lw": 0.8}))

    # Ciudades intermedias: anillo azul
    for cid in (path[1:-1] if path else []):
        if cid in pos:
            add(ax.scatter([pos[cid][0]], [pos[cid][1]], s=NODE_SIZE + 26, zorder=8,
                           facecolors="#FFFFFF", edgecolors=styles.MAP_ROUTE, linewidths=2.4))

    # Origen y destino: puntos de color con borde blanco
    for cid, color in ((origin, styles.MAP_ORIGIN), (destination, styles.MAP_DESTINATION)):
        if cid in cities and cities[cid].get("active", True):
            add(ax.scatter([pos[cid][0]], [pos[cid][1]], s=ENDPOINT_SIZE, zorder=9,
                           facecolors=color, edgecolors="#FFFFFF", linewidths=2.5))

    # Los nombres de las ciudades de la ruta se repintan encima de la línea
    for cid in dict.fromkeys([*(path or []), origin, destination]):
        if cid in base["names"]:
            name, side = base["names"][cid]
            add(_draw_name(ax, pos[cid], name, side, styles.TEXT, zorder=10, weight="bold"))
    return overlay


def render_graph(graph: Graph, path=None, origin=None, destination=None) -> Figure:
    """Construye y retorna una Figure de matplotlib con la red y la ruta resaltada."""
    fig = Figure(figsize=(9, 7), dpi=100, facecolor=styles.MAP_BG)
    ax = fig.add_axes((0, 0, 1, 0.94))
    fig.suptitle(TITLE, fontsize=12, fontweight="bold", color=styles.TEXT)
    base = draw_network(ax, graph)
    draw_route_overlay(ax, base, path, origin, destination)
    return fig


class GraphCanvas(FigureCanvasQTAgg):
    """
    Lienzo Qt del mapa con caché en dos niveles:
    - La red base solo se vuelve a dibujar si el grafo cambió (firma/hash) o cambia la vista.
    - La ruta es una capa 'animated': al cambiar, se restaura el fondo cacheado
      y solo se pinta la ruta (blitting).
    Interacción: tooltip y clic en ciudades, rueda para zoom y arrastre para mover.
    """

    # Emite (id_ciudad, botón): 1 = clic izquierdo, 3 = clic derecho
    city_clicked = pyqtSignal(str, int)

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(9, 7), dpi=100, facecolor=styles.MAP_BG)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_axes((0, 0, 1, 1))

        self._base = None
        self._overlay = []
        self._background = None   # imagen cacheada de la red base
        self._graph_key = None
        self._route_key = None
        self._last_args = None    # (graph, path, origin, destination) del último update_view
        self._limits = None       # vista actual (zoom/desplazamiento); None = vista completa
        self._show_distances = True
        self._show_names = True
        self._hover_city = None
        self._pan_start = None

        self.mpl_connect("draw_event", self._on_draw)
        self.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.mpl_connect("button_press_event", self._on_mouse_press)
        self.mpl_connect("button_release_event", self._on_mouse_release)
        self.mpl_connect("scroll_event", self._on_scroll)
        self.setMouseTracking(True)

    # ------------------------------------------------------------------ render
    def _on_draw(self, event):
        # Tras cada render completo (inicio, resize, zoom) se recaptura el fondo
        self._background = self.copy_from_bbox(self.fig.bbox)
        self._draw_overlay_artists()

    def _draw_overlay_artists(self):
        for artist in self._overlay:
            self.ax.draw_artist(artist)

    def update_view(self, graph: Graph, path=None, origin=None, destination=None) -> bool:
        """Actualiza la vista si algo cambió. Retorna True si hubo redibujo."""
        self._last_args = (graph, path, origin, destination)
        graph_key = graph_signature(graph)
        route_key = (tuple(path or []), origin, destination)

        if graph_key == self._graph_key and route_key == self._route_key:
            return False  # nada cambió: se reutiliza lo ya dibujado

        if graph_key != self._graph_key:
            self._base = draw_network(self.ax, graph, self._show_distances, self._show_names)
            self._apply_limits()
            self._background = None
            self._graph_key = graph_key
        else:
            for artist in self._overlay:
                artist.remove()

        self._overlay = draw_route_overlay(self.ax, self._base, path, origin, destination, animated=True)
        self._route_key = route_key

        if self._background is None:
            self.draw_idle()  # render completo; _on_draw cachea el fondo y pinta la ruta
        else:
            # Solo cambió la ruta: fondo cacheado + capa de ruta
            self.restore_region(self._background)
            self._draw_overlay_artists()
            self.blit(self.fig.bbox)
        return True

    def _rebuild(self):
        """Redibuja la red base conservando la ruta y la vista actuales."""
        self._graph_key = None
        if self._last_args:
            self.update_view(*self._last_args)

    # ------------------------------------------------------------------ opciones de vista
    def set_show_distances(self, show: bool):
        self._show_distances = bool(show)
        self._rebuild()

    def set_show_names(self, show: bool):
        self._show_names = bool(show)
        self._rebuild()

    def _apply_limits(self):
        if self._limits:
            self.ax.set_xlim(*self._limits[0])
            self.ax.set_ylim(*self._limits[1])

    def _set_limits(self, xlim, ylim):
        self._limits = (tuple(xlim), tuple(ylim))
        self._apply_limits()
        self._background = None
        self.draw_idle()

    def zoom(self, factor: float, center=None):
        """factor < 1 acerca, > 1 aleja. 'center' en coordenadas de datos."""
        (x0, x1), (y0, y1) = self.ax.get_xlim(), self.ax.get_ylim()
        cx, cy = center or ((x0 + x1) / 2, (y0 + y1) / 2)
        # Limitar el zoom para no perderse
        new_w = min(max((x1 - x0) * factor, 0.12), 1.6)
        scale = new_w / (x1 - x0)
        self._set_limits(
            (cx - (cx - x0) * scale, cx + (x1 - cx) * scale),
            (cy - (cy - y0) * scale, cy + (y1 - cy) * scale),
        )

    def reset_view(self):
        """Encuadra toda la red."""
        if self._base and self._base["pos"]:
            self._set_limits(*default_limits(self._base["pos"]))
            self._limits = None

    # ------------------------------------------------------------------ interacción
    def _city_at(self, event) -> str | None:
        """Retorna la ciudad bajo el cursor (o None) comparando en píxeles."""
        if not self._base or not self._base["pos"] or event.x is None:
            return None
        radius_px = (NODE_RADIUS_PTS + 4) * self.fig.dpi / 72
        to_px = self.ax.transData.transform
        for cid, xy in self._base["pos"].items():
            px, py = to_px(xy)
            if (px - event.x) ** 2 + (py - event.y) ** 2 <= radius_px ** 2:
                return cid
        return None

    def _on_mouse_move(self, event):
        # Arrastre para desplazar la vista
        if self._pan_start is not None and event.x is not None:
            x0, y0, xlim, ylim = self._pan_start
            inv = self.ax.transData.inverted()
            (dx0, dy0), (dx1, dy1) = inv.transform((x0, y0)), inv.transform((event.x, event.y))
            dx, dy = dx1 - dx0, dy1 - dy0
            if abs(event.x - x0) + abs(event.y - y0) > 3:
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self._set_limits((xlim[0] - dx, xlim[1] - dx), (ylim[0] - dy, ylim[1] - dy))
            return

        cid = self._city_at(event)
        if cid == self._hover_city:
            return
        self._hover_city = cid
        if cid is None:
            self.unsetCursor()
            QToolTip.hideText()
            return
        city = self._base["cities"][cid]
        state = "Activa" if city.get("active", True) else "Inactiva"
        fuel = f"${city.get('fuel_price_cop', 0):,.0f}".replace(",", ".")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        QToolTip.showText(
            QCursor.pos(),
            f"<b>{city['name']}</b> &nbsp;<span style='color:#94A3B8'>{cid}</span><br>"
            f"Estado: {state}<br>Gasolina: {fuel} COP/galón<br>"
            "<span style='color:#94A3B8'>Clic izq.: origen · Clic der.: destino</span>",
            self,
        )

    def _on_mouse_press(self, event):
        cid = self._city_at(event)
        if cid and event.button in (1, 3):
            self.city_clicked.emit(cid, int(event.button))
        elif event.button == 1 and event.x is not None:
            self._pan_start = (event.x, event.y, self.ax.get_xlim(), self.ax.get_ylim())

    def _on_mouse_release(self, event):
        if self._pan_start is not None:
            self._pan_start = None
            self.unsetCursor()

    def _on_scroll(self, event):
        if event.xdata is None:
            return
        self.zoom(0.85 if event.button == "up" else 1 / 0.85, (event.xdata, event.ydata))
