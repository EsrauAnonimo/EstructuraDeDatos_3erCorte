import math

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import QSizePolicy, QWidget

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

# Colores por estado de resaltado
NODE_HIGHLIGHT_COLORS = {
    "search": (HIGHLIGHT_SEARCH_FILL, HIGHLIGHT_SEARCH_BORDER),
    "play": (HIGHLIGHT_PLAY_FILL, HIGHLIGHT_PLAY_BORDER),
    "visit": (HIGHLIGHT_VISIT_FILL, HIGHLIGHT_VISIT_BORDER),
    "insert": (HIGHLIGHT_INSERT_FILL, HIGHLIGHT_INSERT_BORDER),
    "rotate": (HIGHLIGHT_ROTATE_FILL, HIGHLIGHT_ROTATE_BORDER),
}


def _ease_in_out_cubic(t: float) -> float:
    """Curva cúbica suave para desplazamientos y rotaciones."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - pow(-2.0 * t + 2.0, 3) / 2.0


def _ease_out_back(t: float) -> float:
    """Curva con ligero rebote para la aparición de nodos insertados."""
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * pow(t - 1.0, 3) + c1 * pow(t - 1.0, 2)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _node_fields(node):
    """Extrae (valor, izq, der, activo, altura) desde un objeto Node del AVL o un dict."""
    if isinstance(node, dict):
        return (
            node["value"],
            node.get("left"),
            node.get("right"),
            node.get("active", True),
            node.get("height", 1),
        )
    return node.value, node.left, node.right, node.active, node.height


def _collect_tree_info(root_node):
    """Recorre el árbol en in-orden para asignar columna, profundidad, aristas y metadatos."""
    nodes = []
    edges = []
    meta = {}

    def walk(node, depth: int):
        val, left, right, active, height = _node_fields(node)

        if left:
            left_val = _node_fields(left)[0]
            edges.append((val, left_val))
            walk(left, depth + 1)

        col = len(nodes)
        nodes.append((val, col, depth))
        meta[val] = {"active": active, "height": height}

        if right:
            right_val = _node_fields(right)[0]
            edges.append((val, right_val))
            walk(right, depth + 1)

    if root_node:
        walk(root_node, 0)
    return nodes, edges, meta


class TreeCanvas(QWidget):
    """Lienzo interactivo con animaciones suaves a 60 FPS para inserciones, balanceos y recorridos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(460, 420)

        self.structure: dict | None = None
        self.edges: list[tuple[int, int]] = []
        self.node_meta: dict[int, dict] = {}
        self.highlights: dict[int, str] = {}

        # Posiciones para interpolación suave entre estados
        self.prev_positions: dict[int, tuple[float, float]] = {}
        self.target_positions: dict[int, tuple[float, float]] = {}
        self.node_radius: float = 26.0

        # Estado de animación cuadro a cuadro (~60 FPS)
        self.anim_t: float = 1.0
        self.anim_duration_ms: int = 450
        self.anim_elapsed_ms: int = 0
        self.frame_interval_ms: int = 16

        # Elementos visuales especiales durante inserción/balanceo
        self.phase: str | None = None
        self.newly_inserted: int | None = None
        self.probe_value: int | None = None
        self.probe_from: tuple[float, float] | None = None
        self.probe_to: tuple[float, float] | None = None
        self.last_probe_pos: tuple[float, float] | None = None
        self.active_visit_edge: tuple[int, int] | None = None
        self.imbalance_info: tuple[int, int, str, str] | None = None

        self.frame_timer = QTimer(self)
        self.frame_timer.setInterval(self.frame_interval_ms)
        self.frame_timer.timeout.connect(self._on_frame_tick)

    def _compute_layout(self, structure: dict | None) -> tuple[dict[int, tuple[float, float]], list[tuple[int, int]], dict[int, dict], float]:
        nodes, edges, meta = _collect_tree_info(structure)
        if not nodes:
            return {}, [], {}, 26.0

        w = max(self.width(), 460)
        h = max(self.height(), 420)
        n = len(nodes)
        max_depth = max(d for _, _, d in nodes) + 1

        avail_w = max(w - 96.0, 200.0)
        avail_h = max(h - 110.0, 200.0)

        dx = min(96.0, avail_w / max(n - 1, 1)) if n > 1 else 0.0
        radius = max(17.0, min(27.0, (dx * 0.40) if n > 1 else 28.0))
        total_w = (n - 1) * dx
        start_x = (w - total_w) / 2.0

        level_h = min(98.0, avail_h / max(max_depth - 1, 1)) if max_depth > 1 else 0.0
        total_h = (max_depth - 1) * level_h
        start_y = max(62.0, (h - total_h) / 2.0)

        positions = {}
        for val, col, depth in nodes:
            x = start_x + col * dx
            y = start_y + depth * level_h
            positions[val] = (x, y)

        return positions, edges, meta, radius

    def _current_interpolated_positions(self) -> dict[int, tuple[float, float]]:
        eased = _ease_in_out_cubic(self.anim_t)
        result = {}
        for val, target in self.target_positions.items():
            if val in self.prev_positions:
                px, py = self.prev_positions[val]
                result[val] = (_lerp(px, target[0], eased), _lerp(py, target[1], eased))
            else:
                result[val] = target
        return result

    def clear_overlays(self):
        """Limpia indicadores temporales de sonda/desbalance."""
        self.probe_value = None
        self.probe_from = None
        self.probe_to = None
        self.last_probe_pos = None
        self.active_visit_edge = None
        self.imbalance_info = None
        self.newly_inserted = None

    def set_steady_tree(self, structure: dict | None, highlights: dict[int, str] | None = None, animate_layout: bool = False):
        """Muestra la estructura estable del árbol (opcionalmente animando recolocación de nodos)."""
        old_positions = self._current_interpolated_positions() if animate_layout and self.target_positions else {}
        self.clear_overlays()
        self.phase = None
        self.structure = structure
        self.highlights = dict(highlights) if highlights else {}

        new_positions, edges, meta, radius = self._compute_layout(structure)
        self.edges = edges
        self.node_meta = meta
        self.node_radius = radius
        self.target_positions = new_positions

        if animate_layout and old_positions and new_positions:
            self.prev_positions = {
                val: old_positions.get(val, new_positions[val])
                for val in new_positions
            }
            self._start_frame_anim(420)
        else:
            self.prev_positions = dict(new_positions)
            self.anim_t = 1.0
            self.frame_timer.stop()
            self.update()

    def play_trace_step(self, step: dict, duration_ms: int = 500):
        """Ejecuta una transición animada a 60 FPS correspondiente a un paso de inserción."""
        prev_snapshot = self._current_interpolated_positions() if self.target_positions else {}
        prev_highlights = dict(self.highlights)

        self.structure = step["structure"]
        self.highlights = dict(step.get("highlights", {}))
        self.phase = step.get("phase")

        new_positions, edges, meta, radius = self._compute_layout(self.structure)
        self.edges = edges
        self.node_meta = meta
        self.node_radius = radius
        self.target_positions = new_positions

        # Reiniciar sobreposiciones específicas del cuadro
        self.probe_value = None
        self.probe_from = None
        self.probe_to = None
        self.active_visit_edge = None
        self.imbalance_info = None
        self.newly_inserted = None

        if self.phase == "visit":
            self.prev_positions = dict(new_positions)
            self.probe_value = step.get("probe_value")
            target_val = step.get("probe_target")
            if target_val in new_positions:
                tx, ty = new_positions[target_val]
                target_pt = (tx, ty - radius - 22.0)
                if self.last_probe_pos is not None:
                    self.probe_from = self.last_probe_pos
                else:
                    self.probe_from = (tx, max(18.0, ty - radius - 70.0))
                self.probe_to = target_pt
                self.last_probe_pos = target_pt

                # Resaltar arista entrante si viene desde otro nodo visitado
                prev_visited = [k for k, v in prev_highlights.items() if v == "visit"]
                if prev_visited:
                    self.active_visit_edge = (prev_visited[0], target_val)

        elif self.phase == "duplicate":
            self.prev_positions = dict(new_positions)
            self.probe_value = step.get("probe_value")
            target_val = step.get("probe_target")
            if target_val in new_positions:
                tx, ty = new_positions[target_val]
                self.probe_from = self.last_probe_pos or (tx, ty - radius - 48.0)
                self.probe_to = (tx, ty - radius - 22.0)
                self.last_probe_pos = self.probe_to

        elif self.phase in ("insert_leaf", "insert_root"):
            inserted_val = step.get("inserted")
            parent_val = step.get("parent")
            self.newly_inserted = inserted_val

            origin_map = {}
            for val, target in new_positions.items():
                if val == inserted_val:
                    if self.last_probe_pos is not None:
                        origin_map[val] = self.last_probe_pos
                    elif parent_val in prev_snapshot:
                        origin_map[val] = prev_snapshot[parent_val]
                    else:
                        origin_map[val] = (target[0], max(24.0, target[1] - 60.0))
                else:
                    origin_map[val] = prev_snapshot.get(val, target)

            self.prev_positions = origin_map
            self.last_probe_pos = None

        elif self.phase == "imbalance":
            self.prev_positions = {
                val: prev_snapshot.get(val, new_positions[val])
                for val in new_positions
            }
            pivot = step.get("pivot")
            fb_node = step.get("fb_node", pivot)
            fb_str = step.get("fb", "")
            rot_dir = step.get("rotation_dir", "left")
            if pivot is not None:
                self.imbalance_info = (pivot, fb_node, fb_str, rot_dir)

        elif self.phase == "rotate":
            self.prev_positions = {
                val: prev_snapshot.get(val, new_positions[val])
                for val in new_positions
            }
            rot_dir = step.get("rotation_dir")
            pivot = step.get("pivot")
            if rot_dir and pivot is not None:
                self.imbalance_info = (pivot, pivot, "", rot_dir)

        else:
            self.prev_positions = {
                val: prev_snapshot.get(val, new_positions[val])
                for val in new_positions
            }

        self._start_frame_anim(max(180, duration_ms))

    def _start_frame_anim(self, duration_ms: int):
        self.anim_duration_ms = duration_ms
        self.anim_elapsed_ms = 0
        self.anim_t = 0.0
        if not self.frame_timer.isActive():
            self.frame_timer.start()
        self.update()

    def _on_frame_tick(self):
        self.anim_elapsed_ms += self.frame_interval_ms
        if self.anim_elapsed_ms >= self.anim_duration_ms:
            self.anim_t = 1.0
            self.frame_timer.stop()
        else:
            self.anim_t = self.anim_elapsed_ms / float(max(1, self.anim_duration_ms))
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.structure:
            new_positions, edges, meta, radius = self._compute_layout(self.structure)
            self.edges = edges
            self.node_meta = meta
            self.node_radius = radius
            self.target_positions = new_positions
            if self.anim_t >= 1.0:
                self.prev_positions = dict(new_positions)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect()
        # Fondo suave con cuadrícula de puntos sutil
        painter.fillRect(rect, QColor("#FAFCFF"))
        painter.setPen(QPen(QColor("#E2E8F0"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        step = 28
        for gx in range(20, rect.width() - 12, step):
            for gy in range(20, rect.height() - 12, step):
                painter.drawPoint(gx, gy)

        if not self.structure or not self.target_positions:
            self._paint_empty_state(painter, rect)
            return

        positions = self._current_interpolated_positions()
        self._paint_edges(painter, positions)
        self._paint_nodes(painter, positions)
        self._paint_imbalance_overlay(painter, positions)
        self._paint_probe(painter)

    def _paint_empty_state(self, painter: QPainter, rect):
        cx, cy = rect.width() / 2.0, rect.height() / 2.0
        pen = QPen(QColor("#CBD5E1"), 2.0, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QColor("#F1F5F9"))
        painter.drawEllipse(QPointF(cx, cy - 42), 30, 30)

        painter.setPen(QColor("#10B981"))
        painter.setFont(QFont("Segoe UI Emoji", 20))
        painter.drawText(QRectF(cx - 30, cy - 72, 60, 60), Qt.AlignmentFlag.AlignCenter, "🌱")

        painter.setPen(QColor("#334155"))
        painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        painter.drawText(QRectF(20, cy - 2, rect.width() - 40, 28), Qt.AlignmentFlag.AlignCenter, "El árbol AVL está vacío")

        painter.setPen(QColor("#64748B"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            QRectF(32, cy + 28, rect.width() - 64, 48),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            "Escribe un entero o una lista (ej. 10, 20, 30) y presiona Insertar para ver la animación de inserción y balanceo.",
        )

    def _paint_edges(self, painter: QPainter, positions: dict[int, tuple[float, float]]):
        r = self.node_radius
        for parent_val, child_val in self.edges:
            if parent_val not in positions or child_val not in positions:
                continue
            px, py = positions[parent_val]
            cx, cy = positions[child_val]

            dx = cx - px
            dy = cy - py
            dist = math.hypot(dx, dy)
            if dist < 1.0:
                continue
            ux, uy = dx / dist, dy / dist

            start_pad = r + 2.0 if self.node_meta.get(parent_val, {}).get("active", True) else 22.0
            end_pad = r + 3.0 if self.node_meta.get(child_val, {}).get("active", True) else 24.0

            sx, sy = px + ux * start_pad, py + uy * start_pad
            ex, ey = cx - ux * end_pad, cy - uy * end_pad

            is_visit_edge = self.active_visit_edge == (parent_val, child_val)
            edge_color = QColor(HIGHLIGHT_VISIT_BORDER) if is_visit_edge else QColor(EDGE_COLOR)
            edge_width = 2.8 if is_visit_edge else 1.9

            painter.setPen(QPen(edge_color, edge_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(sx, sy), QPointF(ex, ey))

            # Punta de flecha estilizada tipo vee
            arrow_len = 9.0
            angle = math.atan2(ey - sy, ex - sx)
            left_pt = QPointF(ex - arrow_len * math.cos(angle - 0.45), ey - arrow_len * math.sin(angle - 0.45))
            right_pt = QPointF(ex - arrow_len * math.cos(angle + 0.45), ey - arrow_len * math.sin(angle + 0.45))
            painter.setBrush(edge_color)
            painter.drawPolygon(QPolygonF([QPointF(ex, ey), left_pt, right_pt]))

    def _paint_nodes(self, painter: QPainter, positions: dict[int, tuple[float, float]]):
        r = self.node_radius
        pulse = math.sin(self.anim_t * math.pi) if self.anim_t < 1.0 else 0.0

        for val, (x, y) in positions.items():
            active = self.node_meta.get(val, {}).get("active", True)
            mode = self.highlights.get(val)

            scale = 1.0
            if val == self.newly_inserted and self.anim_t < 1.0:
                scale = max(0.3, _ease_out_back(self.anim_t))
            elif mode in ("visit", "rotate", "play", "search") and self.anim_t < 1.0:
                scale = 1.0 + 0.08 * pulse

            nr = r * scale

            if mode:
                fill_hex, border_hex = NODE_HIGHLIGHT_COLORS.get(mode, NODE_HIGHLIGHT_COLORS["search"])
                fill_col = QColor(fill_hex)
                border_col = QColor(border_hex)
                text_col = QColor(NODE_ACTIVE_TEXT)
                border_w = 3.2
            elif active:
                fill_col = QColor(NODE_ACTIVE_FILL)
                border_col = QColor(NODE_ACTIVE_BORDER)
                text_col = QColor(NODE_ACTIVE_TEXT)
                border_w = 2.4
            else:
                fill_col = QColor(NODE_INACTIVE_FILL)
                border_col = QColor(NODE_INACTIVE_BORDER)
                text_col = QColor(NODE_INACTIVE_TEXT)
                border_w = 2.0

            # Halo exterior para nodos resaltados
            if mode:
                halo = QColor(border_col)
                halo.setAlpha(45 + int(45 * pulse))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(halo)
                if active:
                    painter.drawEllipse(QPointF(x, y), nr + 6.5, nr + 6.5)
                else:
                    painter.drawRoundedRect(QRectF(x - 42, y - 27, 84, 54), 14, 14)

            # Sombra suave bajo el nodo
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(15, 23, 42, 24))
            if active:
                painter.drawEllipse(QPointF(x, y + 2.5), nr, nr)
            else:
                painter.drawRoundedRect(QRectF(x - 37, y - 20.5, 74, 44), 12, 12)

            # Cuerpo y borde del nodo
            pen_style = Qt.PenStyle.SolidLine if active else Qt.PenStyle.DashLine
            painter.setPen(QPen(border_col, border_w, pen_style))
            painter.setBrush(fill_col)

            if active:
                painter.drawEllipse(QPointF(x, y), nr, nr)
                font_size = max(9, int(nr * 0.46))
                painter.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
                painter.setPen(text_col)
                painter.drawText(QRectF(x - nr, y - nr, nr * 2, nr * 2), Qt.AlignmentFlag.AlignCenter, str(val))
            else:
                box = QRectF(x - 37, y - 22, 74, 44)
                painter.drawRoundedRect(box, 12, 12)
                painter.setPen(text_col)
                painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                painter.drawText(QRectF(x - 37, y - 20, 74, 22), Qt.AlignmentFlag.AlignCenter, str(val))
                painter.setFont(QFont("Segoe UI", 7))
                painter.drawText(QRectF(x - 37, y, 74, 18), Qt.AlignmentFlag.AlignCenter, "inactivo")

    def _paint_imbalance_overlay(self, painter: QPainter, positions: dict[int, tuple[float, float]]):
        if not self.imbalance_info:
            return
        pivot, fb_node, fb_str, rot_dir = self.imbalance_info
        if pivot not in positions:
            return

        px, py = positions[pivot]
        r = self.node_radius

        # Insignia FB = ±2 al lado del nodo desbalanceado
        if fb_str and fb_node in positions:
            fx, fy = positions[fb_node]
            badge_rect = QRectF(fx + r + 8, fy - 14, 64, 24)
            painter.setPen(QPen(QColor(HIGHLIGHT_ROTATE_BORDER), 1.5))
            painter.setBrush(QColor("#FFF7ED"))
            painter.drawRoundedRect(badge_rect, 8, 8)
            painter.setPen(QColor("#9A3412"))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"FB: {fb_str}")

        # Arco curvo indicando el sentido de rotación (izquierda o derecha)
        arc_rect = QRectF(px - r - 12, py - r - 12, (r + 12) * 2, (r + 12) * 2)
        pen = QPen(QColor(HIGHLIGHT_ROTATE_BORDER), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if rot_dir == "left":
            # Arco superior en sentido antihorario hacia la izquierda
            painter.drawArc(arc_rect, 35 * 16, 110 * 16)
            end_angle = math.radians(145)
            tip = QPointF(px + (r + 12) * math.cos(end_angle), py - (r + 12) * math.sin(end_angle))
            self._draw_small_arrow(painter, tip, math.radians(125), QColor(HIGHLIGHT_ROTATE_BORDER))
        else:
            # Arco superior en sentido horario hacia la derecha
            painter.drawArc(arc_rect, 145 * 16, -110 * 16)
            end_angle = math.radians(35)
            tip = QPointF(px + (r + 12) * math.cos(end_angle), py - (r + 12) * math.sin(end_angle))
            self._draw_small_arrow(painter, tip, math.radians(55), QColor(HIGHLIGHT_ROTATE_BORDER))

    def _draw_small_arrow(self, painter: QPainter, tip: QPointF, angle_rad: float, color: QColor):
        size = 7.5
        p1 = QPointF(tip.x() - size * math.cos(angle_rad - 0.5), tip.y() - size * math.sin(angle_rad - 0.5))
        p2 = QPointF(tip.x() - size * math.cos(angle_rad + 0.5), tip.y() - size * math.sin(angle_rad + 0.5))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(QPolygonF([tip, p1, p2]))

    def _paint_probe(self, painter: QPainter):
        if self.probe_value is None or self.probe_from is None or self.probe_to is None:
            return
        t = _ease_in_out_cubic(self.anim_t)
        px = _lerp(self.probe_from[0], self.probe_to[0], t)
        py = _lerp(self.probe_from[1], self.probe_to[1], t)

        # Ficha flotante que desciende buscando la posición del nuevo valor
        pill = QRectF(px - 22, py - 14, 44, 28)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(15, 23, 42, 30))
        painter.drawRoundedRect(pill.translated(0, 2), 14, 14)

        painter.setPen(QPen(QColor(HIGHLIGHT_INSERT_BORDER), 2.2))
        painter.setBrush(QColor(HIGHLIGHT_INSERT_FILL))
        painter.drawRoundedRect(pill, 14, 14)

        painter.setPen(QColor("#065F46"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, str(self.probe_value))
