"""
Module: graph_view.py
Description: Graphviz rendering utilities for the PERA network.
             Builds DOT graphs, renders SVG, and scales to QPixmap.
"""

import glob
import os
import shutil
import tempfile
import uuid

import graphviz
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from graph import Graph
from styles import (
    EDGE_COLOR,
    EDGE_HIGHLIGHT,
    NODE_CITY_BORDER,
    NODE_CITY_FILL,
    NODE_DEST_BORDER,
    NODE_DEST_FILL,
    NODE_INACTIVE_BORDER,
    NODE_INACTIVE_FILL,
    NODE_ORIGIN_BORDER,
    NODE_ORIGIN_FILL,
)

TEMP_RENDER_DIR = os.path.join(tempfile.gettempdir(), "pera_graph_renders")


def _ensure_graphviz_in_path():
    """Garantiza que el ejecutable 'dot' de Graphviz esté disponible en PATH."""
    if shutil.which("dot"):
        return
    candidates = [
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
    ]
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates.extend(glob.glob(os.path.join(local_app_data, "Programs", "Graphviz", "*", "bin")))
        candidates.append(os.path.join(local_app_data, "Programs", "Graphviz", "bin"))

    for path in candidates:
        if os.path.isfile(os.path.join(path, "dot.exe")):
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
            break


_ensure_graphviz_in_path()


def cleanup_temp_files():
    """Limpia los archivos SVG temporales de renderizados anteriores."""
    if os.path.isdir(TEMP_RENDER_DIR):
        for entry in os.listdir(TEMP_RENDER_DIR):
            full_path = os.path.join(TEMP_RENDER_DIR, entry)
            try:
                if os.path.isfile(full_path):
                    os.remove(full_path)
            except OSError:
                pass
    else:
        os.makedirs(TEMP_RENDER_DIR, exist_ok=True)


def render_graph(
    graph: Graph,
    path: list[str] = None,
    origin: str = None,
    destination: str = None
) -> str | None:
    """
    Construye el grafo en formato DOT y lo renderiza a SVG temporal.
    Resalta los nodos de origen/destino y las aristas pertenecientes a 'path'.
    """
    cities = graph.get_cities()
    if not cities:
        return None

    os.makedirs(TEMP_RENDER_DIR, exist_ok=True)

    # Identificar pares de aristas en la ruta calculada
    path_edges = set()
    if path and len(path) >= 2:
        for i in range(len(path) - 1):
            path_edges.add((path[i], path[i + 1]))

    lines = [
        "digraph PERA {",
        '    graph [rankdir=LR, splines=polyline, nodesep=0.5, ranksep=1.0, bgcolor="transparent"];',
        '    node [fontname="Segoe UI Semibold", fontsize=10, shape=box, style="filled,rounded", margin="0.18,0.12"];',
        '    edge [arrowsize=0.7, fontname="Segoe UI", fontsize=9];',
    ]

    # Renderizar nodos (ciudades)
    for city in cities:
        cid = city["id"]
        name = city["name"]
        active = city.get("active", True)

        label = f"{cid}\\n{name}"
        fontcolor = "#1E293B"

        if not active:
            fill = NODE_INACTIVE_FILL
            border = NODE_INACTIVE_BORDER
            style = "filled,dashed"
            penwidth = "1.5"
            label = f"{cid}\\n{name}\\n(Inactiva)"
            fontcolor = "#64748B"
        elif cid == origin:
            fill = NODE_ORIGIN_FILL
            border = NODE_ORIGIN_BORDER
            style = "filled,rounded"
            penwidth = "3.0"
        elif cid == destination:
            fill = NODE_DEST_FILL
            border = NODE_DEST_BORDER
            style = "filled,rounded"
            penwidth = "3.0"
        else:
            fill = NODE_CITY_FILL
            border = NODE_CITY_BORDER
            style = "filled,rounded"
            penwidth = "1.5"

        lines.append(
            f'    "{cid}" [label="{label}", fillcolor="{fill}", color="{border}", '
            f'fontcolor="{fontcolor}", style="{style}", penwidth={penwidth}];'
        )

    # Renderizar aristas
    for edge in graph.get_edges():
        u = edge["from"]
        v = edge["to"]
        dist = edge.get("distance_km", 0)

        is_highlighted = (u, v) in path_edges

        if is_highlighted:
            color = EDGE_HIGHLIGHT
            penwidth = "3.0"
            fontcolor = EDGE_HIGHLIGHT
        else:
            color = EDGE_COLOR
            penwidth = "1.2"
            fontcolor = "#475569"

        edge_label = f"{dist:.0f} km"
        lines.append(
            f'    "{u}" -> "{v}" [label="{edge_label}", color="{color}", '
            f'penwidth={penwidth}, fontcolor="{fontcolor}"];'
        )

    lines.append("}")
    dot_source = "\n".join(lines)

    filename = f"graph_{uuid.uuid4().hex[:8]}"
    output_base = os.path.join(TEMP_RENDER_DIR, filename)

    try:
        src = graphviz.Source(dot_source, format="svg")
        svg_path = src.render(filename=output_base, cleanup=True)
        return svg_path
    except Exception:
        return None


def render_to_pixmap(svg_path: str, width: int, height: int) -> QPixmap:
    """Carga un SVG y lo convierte en QPixmap manteniendo proporción y suavizado."""
    if not svg_path or not os.path.exists(svg_path):
        return QPixmap()

    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        return QPixmap()

    default_size = renderer.defaultSize()
    avail_w = max(width - 20, 200)
    avail_h = max(height - 20, 200)

    if default_size.width() > 0 and default_size.height() > 0:
        scale = min(avail_w / default_size.width(), avail_h / default_size.height())
        target_w = max(1, int(default_size.width() * scale))
        target_h = max(1, int(default_size.height() * scale))
    else:
        target_w, target_h = avail_w, avail_h

    pixmap = QPixmap(target_w, target_h)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()

    return pixmap
