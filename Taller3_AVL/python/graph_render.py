import glob
import os
import shutil
import tempfile
import uuid

import graphviz
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from avl import AVLTree
from styles import (
    EDGE_COLOR,
    HIGHLIGHT_INSERT_BORDER,
    HIGHLIGHT_INSERT_FILL,
    HIGHLIGHT_PLAY_BORDER,
    HIGHLIGHT_PLAY_FILL,
    HIGHLIGHT_ROTATE_BORDER,
    HIGHLIGHT_ROTATE_FILL,
    HIGHLIGHT_SEARCH_BORDER,
    HIGHLIGHT_SEARCH_FILL,
    HIGHLIGHT_VISIT_BORDER,
    HIGHLIGHT_VISIT_FILL,
    NODE_ACTIVE_BORDER,
    NODE_ACTIVE_FILL,
    NODE_ACTIVE_TEXT,
    NODE_INACTIVE_BORDER,
    NODE_INACTIVE_FILL,
    NODE_INACTIVE_TEXT,
)

# Directorio temporal exclusivo para los archivos SVG generados por la aplicación
TEMP_RENDER_DIR = os.path.join(tempfile.gettempdir(), "paa_avl_renders")

# Mapa de estilos según el tipo de resaltado visual
HIGHLIGHT_STYLES = {
    "search": (HIGHLIGHT_SEARCH_FILL, HIGHLIGHT_SEARCH_BORDER),
    "play": (HIGHLIGHT_PLAY_FILL, HIGHLIGHT_PLAY_BORDER),
    "visit": (HIGHLIGHT_VISIT_FILL, HIGHLIGHT_VISIT_BORDER),
    "insert": (HIGHLIGHT_INSERT_FILL, HIGHLIGHT_INSERT_BORDER),
    "rotate": (HIGHLIGHT_ROTATE_FILL, HIGHLIGHT_ROTATE_BORDER),
}


def _ensure_graphviz_in_path():
    """Garantiza que el binario 'dot' de Graphviz esté disponible en PATH en Windows."""
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
    """Limpia los archivos SVG/DOT temporales de ejecuciones anteriores."""
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


def _build_dot_lines(node: dict, lines: list[str], highlights: dict[int, str]):
    """Recorre recursivamente la estructura del árbol para generar nodos y aristas en DOT."""
    val = node["value"]
    active = node.get("active", True)
    node_id = f"n_{val}"

    label = f"{val}" if active else f"{val} (inactivo)"

    if active:
        shape = "circle"
        fill = NODE_ACTIVE_FILL
        border = NODE_ACTIVE_BORDER
        fontcolor = NODE_ACTIVE_TEXT
        style = "filled"
        extra = ""
    else:
        shape = "box"
        fill = NODE_INACTIVE_FILL
        border = NODE_INACTIVE_BORDER
        fontcolor = NODE_INACTIVE_TEXT
        style = "filled,dashed,rounded"
        extra = ', margin="0.14,0.08"'

    penwidth = "2.2"

    # Aplicar resaltado según el rol del nodo en la animación o búsqueda
    mode = highlights.get(val)
    if mode:
        fill, border = HIGHLIGHT_STYLES.get(mode, HIGHLIGHT_STYLES["search"])
        fontcolor = NODE_ACTIVE_TEXT
        penwidth = "3.4"

    lines.append(
        f'    "{node_id}" [shape={shape}, label="{label}", fillcolor="{fill}", color="{border}", '
        f'fontcolor="{fontcolor}", style="{style}", penwidth={penwidth}{extra}];'
    )

    left = node.get("left")
    right = node.get("right")

    if left:
        left_id = f"n_{left['value']}"
        _build_dot_lines(left, lines, highlights)
        lines.append(f'    "{node_id}" -> "{left_id}" [color="{EDGE_COLOR}", penwidth=1.7];')
    elif right:
        # Nodo invisible para mantener la orientación visual izquierda/derecha cuando solo hay hijo derecho
        ghost_left = f"g_l_{val}"
        lines.append(f'    "{ghost_left}" [label="", width=0.1, style=invis];')
        lines.append(f'    "{node_id}" -> "{ghost_left}" [style=invis];')

    if right:
        right_id = f"n_{right['value']}"
        _build_dot_lines(right, lines, highlights)
        lines.append(f'    "{node_id}" -> "{right_id}" [color="{EDGE_COLOR}", penwidth=1.7];')
    elif left:
        # Nodo invisible para mantener la orientación visual izquierda/derecha cuando solo hay hijo izquierdo
        ghost_right = f"g_r_{val}"
        lines.append(f'    "{ghost_right}" [label="", width=0.1, style=invis];')
        lines.append(f'    "{node_id}" -> "{ghost_right}" [style=invis];')


def render_structure(
    structure: dict | None,
    highlight_value: int | None = None,
    highlight_color: str = "search",
    highlights: dict[int, str] | None = None,
) -> str | None:
    """Renderiza una estructura serializada de árbol AVL a SVG temporal usando Graphviz."""
    if not structure:
        return None

    merged_highlights = dict(highlights) if highlights else {}
    if highlight_value is not None:
        merged_highlights[highlight_value] = highlight_color

    os.makedirs(TEMP_RENDER_DIR, exist_ok=True)

    lines = [
        "digraph AVL {",
        '    graph [rankdir=TB, splines=polyline, nodesep=0.45, ranksep=0.65, bgcolor="transparent", pad=0.18];',
        '    node [shape=circle, fontname="Segoe UI Semibold", fontsize=11.5, width=0.68, fixedsize=false, margin=0.06];',
        '    edge [arrowhead=vee, arrowsize=0.72];',
    ]
    _build_dot_lines(structure, lines, merged_highlights)
    lines.append("}")
    dot_source = "\n".join(lines)

    filename = f"avl_{uuid.uuid4().hex[:8]}"
    output_base = os.path.join(TEMP_RENDER_DIR, filename)

    src = graphviz.Source(dot_source, format="svg")
    svg_path = src.render(filename=output_base, cleanup=True)
    return svg_path


def render_tree(
    tree: AVLTree,
    highlight_value: int | None = None,
    highlight_color: str = "search",
    highlights: dict[int, str] | None = None,
) -> str | None:
    """Renderiza el árbol AVL a un archivo SVG temporal usando Graphviz y devuelve su ruta."""
    if tree.is_empty():
        return None
    return render_structure(
        tree.get_tree_structure(),
        highlight_value=highlight_value,
        highlight_color=highlight_color,
        highlights=highlights,
    )


def render_to_pixmap(svg_path: str, width: int, height: int) -> QPixmap:
    """Carga un SVG con QSvgRenderer y lo convierte en un QPixmap escalado manteniendo proporción."""
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        return QPixmap()

    default_size = renderer.defaultSize()
    avail_w = max(width - 24, 200)
    avail_h = max(height - 24, 200)

    if default_size.width() > 0 and default_size.height() > 0:
        scale = min(avail_w / default_size.width(), avail_h / default_size.height())
        scale = min(scale, 1.85)
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
