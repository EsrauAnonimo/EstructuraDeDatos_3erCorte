"""
Module: graph_view.py
Description: Matplotlib rendering of the PERA network embedded in PyQt6.
             Nodes are placed using real lat/lon coordinates scaled to the canvas;
             edges are arrows with the distance label at the midpoint.
"""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

from graph import Graph
from styles import (
    NODE_CITY_BORDER,
    NODE_CITY_FILL,
    NODE_DEST_BORDER,
    NODE_DEST_FILL,
    NODE_INACTIVE_BORDER,
    NODE_INACTIVE_FILL,
    NODE_ORIGIN_BORDER,
    NODE_ORIGIN_FILL,
)

TITLE = "Red de Rutas - PERA"

# Estilo de aristas
EDGE_DEFAULT_COLOR = "#94A3B8"
EDGE_DEFAULT_WIDTH = 0.8
EDGE_PATH_COLOR = "#DC2626"
EDGE_PATH_WIDTH = 2.5
EDGE_CURVE = 0.12  # curvatura para separar u->v de v->u

# Estilo de nodos (tamaño en puntos^2 del marcador)
NODE_SIZE = 620
NODE_RADIUS_PTS = (NODE_SIZE ** 0.5) / 2


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


def _path_edges(path: list[str] | None) -> list[tuple[str, str]]:
    """Convierte una ruta [A, B, C] en la lista de aristas [(A,B), (B,C)]."""
    if not path or len(path) < 2:
        return []
    return [(path[i], path[i + 1]) for i in range(len(path) - 1)]


def _node_style(city: dict, origin: str | None, destination: str | None) -> dict:
    """Devuelve relleno, borde, grosor y tipo de línea del nodo según su rol."""
    cid = city["id"]
    if not city.get("active", True):
        return {"fill": NODE_INACTIVE_FILL, "border": NODE_INACTIVE_BORDER, "width": 1.5, "style": "--"}
    if cid == origin:
        return {"fill": NODE_ORIGIN_FILL, "border": NODE_ORIGIN_BORDER, "width": 3.0, "style": "-"}
    if cid == destination:
        return {"fill": NODE_DEST_FILL, "border": NODE_DEST_BORDER, "width": 3.0, "style": "-"}
    return {"fill": NODE_CITY_FILL, "border": NODE_CITY_BORDER, "width": 1.2, "style": "-"}


def _make_arrow(start, end, color, width, animated=False) -> FancyArrowPatch:
    """Flecha curva entre dos nodos, recortada al radio del círculo."""
    return FancyArrowPatch(
        start, end,
        arrowstyle="-|>",
        mutation_scale=10 if width < 2 else 14,
        connectionstyle=f"arc3,rad={EDGE_CURVE}",
        shrinkA=NODE_RADIUS_PTS,
        shrinkB=NODE_RADIUS_PTS,
        color=color,
        linewidth=width,
        zorder=1,
        animated=animated,
    )


def _draw_node(ax, city: dict, xy, origin=None, destination=None, animated=False) -> list:
    """Dibuja el círculo de una ciudad y su ID. Retorna los dos artistas."""
    st = _node_style(city, origin, destination)
    node = ax.scatter(
        [xy[0]], [xy[1]], s=NODE_SIZE, zorder=3, animated=animated,
        facecolors=st["fill"], edgecolors=st["border"],
        linewidths=st["width"], linestyles=st["style"],
    )
    text = ax.text(xy[0], xy[1], city["id"], fontsize=6.5, fontweight="bold", color="#1E293B",
                   ha="center", va="center", zorder=4, animated=animated)
    return [node, text]


def draw_network(ax, graph: Graph) -> dict:
    """
    Dibuja la red base: todas las aristas en gris y los nodos sin origen/destino.
    Retorna posiciones y etiquetas para luego superponer la ruta.
    """
    ax.clear()
    ax.set_title(TITLE, fontsize=12, fontweight="bold", color="#1E293B")
    # Sin aspecto igual: lat/lon se escalan a todo el lienzo y los nodos cercanos se separan
    ax.axis("off")

    cities = {c["id"]: c for c in graph.get_cities()}
    base = {"cities": cities, "pos": {}, "labels": {}}
    if not cities:
        return base

    # Posición = lat/lon reales escaladas al lienzo (x = longitud, y = latitud)
    pos = _layout_positions(cities)
    base["pos"] = pos

    # Aristas dirigidas como flechas curvas (u->v y v->u no se solapan)
    distances = {}
    for edge in graph.get_edges():
        u, v = edge["from"], edge["to"]
        if u not in pos or v not in pos:
            continue
        ax.add_patch(_make_arrow(pos[u], pos[v], EDGE_DEFAULT_COLOR, EDGE_DEFAULT_WIDTH))
        distances.setdefault(tuple(sorted((u, v))), set()).add(round(edge.get("distance_km", 0)))

    # Una etiqueta de distancia por par de ciudades, en el punto medio
    for (a, b), dist_set in distances.items():
        xy = ((pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2)
        text = "/".join(f"{d:.0f}" for d in sorted(dist_set)) + " km"
        ax.text(xy[0], xy[1], text, fontsize=6.5, color="#475569", ha="center", va="center", zorder=2,
                bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.8})
        base["labels"][(a, b)] = (xy, text)

    for cid, xy in pos.items():
        _draw_node(ax, cities[cid], xy)

    # Margen alrededor de los nodos
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 0.06, max(xs) + 0.06)
    ax.set_ylim(min(ys) - 0.05, max(ys) + 0.05)

    # Leyenda mínima
    def marker(fill, border):
        return Line2D([], [], marker="o", linestyle="none", markersize=9,
                      markerfacecolor=fill, markeredgecolor=border, markeredgewidth=2)

    handles = [
        marker(NODE_ORIGIN_FILL, NODE_ORIGIN_BORDER),
        marker(NODE_DEST_FILL, NODE_DEST_BORDER),
        marker(NODE_CITY_FILL, NODE_CITY_BORDER),
        marker(NODE_INACTIVE_FILL, NODE_INACTIVE_BORDER),
        Line2D([], [], color=EDGE_PATH_COLOR, linewidth=EDGE_PATH_WIDTH),
    ]
    ax.legend(handles, ["Origen", "Destino", "Ciudad", "Inactiva", "Ruta calculada"],
              loc="upper right", fontsize=7, framealpha=0.9)
    return base


def draw_route_overlay(ax, base: dict, path=None, origin=None, destination=None, animated=False) -> list:
    """
    Dibuja encima de la red base solo lo que depende de la ruta:
    aristas rojas, sus etiquetas y los nodos origen/destino.
    Retorna los artistas creados para poder quitarlos después.
    """
    pos, cities = base["pos"], base["cities"]
    overlay = []

    for u, v in _path_edges(path):
        if u not in pos or v not in pos:
            continue
        arrow = _make_arrow(pos[u], pos[v], EDGE_PATH_COLOR, EDGE_PATH_WIDTH, animated)
        arrow.set_zorder(2)
        ax.add_patch(arrow)
        overlay.append(arrow)

        pair = tuple(sorted((u, v)))
        if pair in base["labels"]:
            xy, text = base["labels"][pair]
            overlay.append(ax.text(
                xy[0], xy[1], text, fontsize=6.5, fontweight="bold", color=EDGE_PATH_COLOR,
                ha="center", va="center", zorder=2.5, animated=animated,
                bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none"},
            ))

    for cid in (origin, destination):
        if cid in cities:
            overlay.extend(_draw_node(ax, cities[cid], pos[cid], origin, destination, animated))
    return overlay


def render_graph(graph: Graph, path=None, origin=None, destination=None) -> Figure:
    """Construye y retorna una Figure de matplotlib con la red y la ruta resaltada."""
    fig = Figure(figsize=(8, 8), dpi=100, facecolor="#FAFCFF")
    ax = fig.add_subplot(111)
    base = draw_network(ax, graph)
    draw_route_overlay(ax, base, path, origin, destination)
    return fig


class GraphCanvas(FigureCanvasQTAgg):
    """
    Lienzo Qt con caché en dos niveles:
    - La red base solo se vuelve a dibujar si el grafo cambió (firma/hash).
    - La ruta es una capa 'animated': al cambiar, se restaura el fondo cacheado
      y solo se pintan las flechas rojas y los nodos origen/destino (blitting).
    """

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 8), dpi=100, facecolor="#FAFCFF")
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.01)
        self._base = None
        self._overlay = []
        self._background = None  # imagen cacheada de la red base
        self._graph_key = None
        self._route_key = None
        # Tras cada render completo (inicio, resize) se recaptura el fondo
        self.mpl_connect("draw_event", self._on_draw)

    def _on_draw(self, event):
        self._background = self.copy_from_bbox(self.fig.bbox)
        self._draw_overlay_artists()

    def _draw_overlay_artists(self):
        for artist in self._overlay:
            self.ax.draw_artist(artist)

    def update_view(self, graph: Graph, path=None, origin=None, destination=None) -> bool:
        """Actualiza la vista si algo cambió. Retorna True si hubo redibujo."""
        graph_key = graph_signature(graph)
        route_key = (tuple(path or []), origin, destination)

        if graph_key == self._graph_key and route_key == self._route_key:
            return False  # nada cambió: se reutiliza lo ya dibujado

        if graph_key != self._graph_key:
            self._base = draw_network(self.ax, graph)  # ax.clear() también quita la ruta anterior
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
