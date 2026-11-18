from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from avl import AVLTree, Node
from persistence import DEFAULT_DATA_PATH, save_tree
from tree_canvas import TreeCanvas


def _count_nodes(node: Node | None) -> tuple[int, int]:
    """Cuenta recursivamente (nodos_activos, total_nodos) recorriendo los nodos del árbol AVL."""
    if not node:
        return 0, 0
    la, lt = _count_nodes(node.left)
    ra, rt = _count_nodes(node.right)
    active = (1 if node.active else 0) + la + ra
    total = 1 + lt + rt
    return active, total


def _apply_shadow(widget: QWidget, blur: int = 18, y_offset: int = 3, alpha: int = 18):
    """Agrega una sombra suave a las tarjetas para dar profundidad visual."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(shadow)


# Paleta semántica para el banner superior del lienzo según la fase de animación
BANNER_STYLES = {
    "idle": ("#F8FAFC", "#E2E8F0", "#475569"),
    "visit": ("#EEF2FF", "#C7D2FE", "#3730A3"),
    "insert": ("#ECFDF5", "#A7F3D0", "#065F46"),
    "rotate": ("#FFF7ED", "#FED7AA", "#9A3412"),
    "play": ("#F0FDF4", "#BBF7D0", "#166534"),
    "search": ("#FEFCE8", "#FDE047", "#854D0E"),
}

SPEED_OPTIONS = [
    ("Velocidad: Normal", 650),
    ("Velocidad: Rápida", 350),
    ("Velocidad: Lenta", 1050),
]


class MainWindow(QMainWindow):
    """Ventana principal del Programa de Aprendizaje de Árboles (PAA)."""

    def __init__(self, tree: AVLTree | None = None, data_path: str = DEFAULT_DATA_PATH):
        super().__init__()
        self.tree = tree if tree is not None else AVLTree()
        self.data_path = data_path

        # Estado unificado de animación (para recorridos e inserciones)
        self.base_step_ms: int = 650
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(self.base_step_ms)
        self.anim_timer.timeout.connect(self._on_animation_step)
        self.anim_mode: str | None = None  # "traversal" | "insert" | None
        self.anim_sequence: list[int] = []
        self.insert_steps: list[dict] = []
        self.anim_index: int = 0

        self.setWindowTitle("PAA · Programa de Aprendizaje de Árboles AVL")
        self.resize(1220, 780)
        self.setMinimumSize(1020, 680)

        self._build_ui()
        self.refresh_ui()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 16, 18, 14)
        root_layout.setSpacing(14)

        # Barra superior con título y métricas en tiempo real del árbol AVL
        root_layout.addWidget(self._build_header())

        # Contenido principal en dos columnas (40% controles / 60% lienzo)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)

        left_layout.addWidget(self._build_controls_card())
        left_layout.addWidget(self._build_traversals_card(), 1)

        body_layout.addWidget(left_panel, 4)
        body_layout.addWidget(self._build_canvas_card(), 6)

        root_layout.addLayout(body_layout, 1)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("headerBar")
        _apply_shadow(header, blur=20, y_offset=4, alpha=28)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("🌳  Programa de Aprendizaje de Árboles AVL")
        lbl_title.setObjectName("headerTitle")
        lbl_sub = QLabel("Estructura de datos Árbol AVL · Inserción animada, rotaciones y recorridos")
        lbl_sub.setObjectName("headerSubtitle")
        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)

        layout.addLayout(title_col, 1)

        self.lbl_badge_active = QLabel("Activos: 0")
        self.lbl_badge_active.setObjectName("statBadge")
        self.lbl_badge_total = QLabel("Total: 0")
        self.lbl_badge_total.setObjectName("statBadge")
        self.lbl_badge_height = QLabel("Altura: 0")
        self.lbl_badge_height.setObjectName("statBadge")

        layout.addWidget(self.lbl_badge_active)
        layout.addWidget(self.lbl_badge_total)
        layout.addWidget(self.lbl_badge_height)
        return header

    def _create_card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("card")
        _apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("cardTitle")
        layout.addWidget(lbl_title)

        divider = QFrame()
        divider.setObjectName("softDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        return card, layout

    def _build_controls_card(self) -> QFrame:
        card, layout = self._create_card("Operaciones del Árbol")

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Ingresa un entero o lista (ej. 25 ó 10, 20, 30)...")
        self.value_input.returnPressed.connect(self.on_insert)
        layout.addWidget(self.value_input)

        btn_grid = QGridLayout()
        btn_grid.setSpacing(8)

        self.btn_insert = self._make_btn("＋ Insertar", "btnSuccess", self.on_insert)
        self.btn_delete = self._make_btn("✕ Eliminar", "btnDanger", self.on_delete)
        self.btn_search = self._make_btn("⌕ Buscar", "", self.on_search)
        self.btn_deactivate = self._make_btn("⊘ Desactivar", "btnWarning", self.on_deactivate)
        self.btn_modify = self._make_btn("✎ Modificar", "btnIndigo", self.on_modify)
        self.btn_clear = self._make_btn("↺ Limpiar árbol", "btnSoftDanger", self.on_clear)

        btn_grid.addWidget(self.btn_insert, 0, 0)
        btn_grid.addWidget(self.btn_delete, 0, 1)
        btn_grid.addWidget(self.btn_search, 1, 0)
        btn_grid.addWidget(self.btn_deactivate, 1, 1)
        btn_grid.addWidget(self.btn_modify, 2, 0)
        btn_grid.addWidget(self.btn_clear, 2, 1)
        layout.addLayout(btn_grid)

        anim_row = QHBoxLayout()
        anim_row.setSpacing(8)

        self.chk_animate_insert = QCheckBox("Animar inserción")
        self.chk_animate_insert.setChecked(True)
        self.chk_animate_insert.setCursor(Qt.CursorShape.PointingHandCursor)

        self.combo_speed = QComboBox()
        for label, _ in SPEED_OPTIONS:
            self.combo_speed.addItem(label)
        self.combo_speed.currentIndexChanged.connect(self._on_speed_changed)

        anim_row.addWidget(self.chk_animate_insert)
        anim_row.addWidget(self.combo_speed, 1)
        layout.addLayout(anim_row)

        return card

    def _build_traversals_card(self) -> QFrame:
        card, layout = self._create_card("Recorridos (Nodos Activos)")

        self.lbl_preorder = self._create_traversal_row(layout, "Pre-orden")
        self.lbl_inorder = self._create_traversal_row(layout, "In-orden")
        self.lbl_postorder = self._create_traversal_row(layout, "Post-orden")

        play_row = QHBoxLayout()
        play_row.setSpacing(8)

        self.combo_traversal = QComboBox()
        self.combo_traversal.addItems(["Pre-orden", "In-orden", "Post-orden"])

        self.btn_play = self._make_btn("▶ Reproducir", "btnPlay", self.on_play_traversal)
        self.btn_stop_anim = self._make_btn("■ Detener", "btnSecondary", self.stop_animation)
        self.btn_stop_anim.setEnabled(False)

        play_row.addWidget(self.combo_traversal, 2)
        play_row.addWidget(self.btn_play, 2)
        play_row.addWidget(self.btn_stop_anim, 1)
        layout.addLayout(play_row)

        self.lbl_current_step = QLabel("Paso actual: -")
        self.lbl_current_step.setStyleSheet("font-weight: 600; color: #059669; padding: 4px 0px;")
        layout.addWidget(self.lbl_current_step)
        layout.addStretch(1)

        footer_divider = QFrame()
        footer_divider.setObjectName("softDivider")
        footer_divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(footer_divider)

        self.lbl_node_counts = QLabel("Nodos activos: 0 / Total: 0")
        self.lbl_node_counts.setStyleSheet("font-weight: 600; color: #64748B; font-size: 9.2pt;")
        layout.addWidget(self.lbl_node_counts)

        return card

    def _build_canvas_card(self) -> QFrame:
        card, layout = self._create_card("Visualización del Árbol AVL")

        # Leyenda compacta de estados de nodos
        legend_row = QHBoxLayout()
        legend_row.setSpacing(6)
        legend_items = [
            ("● Activo", "#2563EB"),
            ("◌ Inactivo", "#6B7280"),
            ("● Visitando", "#4F46E5"),
            ("● Nuevo", "#059669"),
            ("● Rotación", "#EA580C"),
            ("● Búsqueda", "#CA8A04"),
        ]
        for text, color in legend_items:
            chip = QLabel(text)
            chip.setObjectName("legendChip")
            chip.setStyleSheet(f"color: {color};")
            legend_row.addWidget(chip)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        # Banner de narración educativa en vivo
        self.lbl_anim_banner = QLabel("Listo · Ingresa un valor entero para visualizar su inserción y balanceo.")
        self.lbl_anim_banner.setObjectName("animBanner")
        self.lbl_anim_banner.setWordWrap(True)
        self._set_banner_style("idle")
        layout.addWidget(self.lbl_anim_banner)

        # Lienzo interactivo animado (60 FPS)
        tree_container = QFrame()
        tree_container.setObjectName("treeFrame")
        tree_container_layout = QVBoxLayout(tree_container)
        tree_container_layout.setContentsMargins(6, 6, 6, 6)
        self.tree_canvas = TreeCanvas()
        tree_container_layout.addWidget(self.tree_canvas)

        layout.addWidget(tree_container, 1)
        return card

    def _make_btn(self, text: str, obj_name: str, handler) -> QPushButton:
        btn = QPushButton(text)
        if obj_name:
            btn.setObjectName(obj_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(handler)
        return btn

    def _create_traversal_row(self, parent_layout, title: str) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(10)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("fieldLabel")
        title_lbl.setFixedWidth(76)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        value_lbl = QLabel("[]")
        value_lbl.setObjectName("traversalValue")
        value_lbl.setWordWrap(True)
        value_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        value_lbl.setMinimumHeight(32)
        value_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        row.addWidget(title_lbl)
        row.addWidget(value_lbl, 1)
        parent_layout.addLayout(row)
        return value_lbl

    def _set_banner_style(self, mode: str):
        bg, border, text = BANNER_STYLES.get(mode, BANNER_STYLES["idle"])
        self.lbl_anim_banner.setStyleSheet(
            f"background-color: {bg}; border: 1px solid {border}; "
            f"border-radius: 9px; padding: 8px 12px; color: {text}; font-weight: 600;"
        )

    def _on_speed_changed(self, index: int):
        if 0 <= index < len(SPEED_OPTIONS):
            self.base_step_ms = SPEED_OPTIONS[index][1]
            if not self.anim_timer.isActive():
                self.anim_timer.setInterval(self.base_step_ms)

    def stop_animation(self):
        """Detiene la animación en curso y deja visible el estado real del árbol."""
        was_running = self.anim_timer.isActive() or self.anim_mode is not None
        if self.anim_timer.isActive():
            self.anim_timer.stop()
        self.anim_timer.setInterval(self.base_step_ms)
        self.anim_mode = None
        self.anim_sequence = []
        self.insert_steps = []
        self.anim_index = 0
        self.btn_stop_anim.setEnabled(False)
        self.lbl_current_step.setText("Paso actual: -")
        self.tree_canvas.clear_overlays()
        if was_running:
            self._set_banner_style("idle")
            self.lbl_anim_banner.setText("Listo · Visualizando estado actual del árbol.")
            self.refresh_ui()

    def on_play_traversal(self):
        """Inicia la animación paso a paso del recorrido seleccionado."""
        self.stop_animation()

        mode = self.combo_traversal.currentText()
        if mode == "Pre-orden":
            sequence = self.tree.preorder()
        elif mode == "In-orden":
            sequence = self.tree.inorder()
        else:
            sequence = self.tree.postorder()

        if not sequence:
            self.statusBar().showMessage("No hay nodos activos para recorrer.")
            return

        self.anim_mode = "traversal"
        self.anim_sequence = sequence
        self.anim_index = 0
        self.anim_timer.setInterval(self.base_step_ms)
        self.btn_stop_anim.setEnabled(True)
        self._on_animation_step()
        self.anim_timer.start()

    def _on_animation_step(self):
        """Avanza un cuadro en la animación activa (inserción o recorrido)."""
        if self.anim_mode == "insert":
            self._step_insert_animation()
        else:
            self._step_traversal_animation()

    def _step_traversal_animation(self):
        total = len(self.anim_sequence)
        if self.anim_index < total:
            current_val = self.anim_sequence[self.anim_index]
            step_num = self.anim_index + 1
            step_text = f"Paso actual: {current_val} ({step_num}/{total})"
            self.lbl_current_step.setText(step_text)
            self._set_banner_style("play")
            self.lbl_anim_banner.setText(
                f"Recorrido {self.combo_traversal.currentText()} · Visitando nodo {current_val} ({step_num}/{total})"
            )
            self.refresh_ui(
                status_msg=step_text,
                highlight_value=current_val,
                highlight_color="play",
                preserve_step_label=True,
            )
            self.anim_index += 1
        else:
            self.anim_timer.stop()
            self.anim_timer.setInterval(self.base_step_ms)
            self.anim_mode = None
            self.anim_sequence = []
            self.anim_index = 0
            self.btn_stop_anim.setEnabled(False)
            self.lbl_current_step.setText("Paso actual: Recorrido completado")
            self._set_banner_style("play")
            self.lbl_anim_banner.setText("Recorrido completado correctamente.")
            self.refresh_ui(
                status_msg="Recorrido completado",
                preserve_step_label=True,
            )

    def _step_insert_animation(self):
        total = len(self.insert_steps)
        if self.anim_index < total:
            step = self.insert_steps[self.anim_index]
            step_num = self.anim_index + 1
            highlights = step["highlights"]
            message = step["message"]
            phase = step.get("phase")

            if phase in ("imbalance", "rotate") or "rotate" in highlights.values():
                banner_mode = "rotate"
            elif phase in ("insert_leaf", "insert_root") or "insert" in highlights.values():
                banner_mode = "insert"
            elif phase == "duplicate" or "search" in highlights.values():
                banner_mode = "search"
            else:
                banner_mode = "visit"

            if phase == "imbalance":
                step_ms = int(self.base_step_ms * 1.25)
                motion_ms = int(self.base_step_ms * 0.55)
            elif phase == "rotate":
                step_ms = int(self.base_step_ms * 1.35)
                motion_ms = int(self.base_step_ms * 1.05)
            else:
                step_ms = self.base_step_ms
                motion_ms = int(self.base_step_ms * 0.72)

            self._set_banner_style(banner_mode)
            self.lbl_anim_banner.setText(f"Paso {step_num}/{total} · {message}")
            self.lbl_current_step.setText(f"Inserción: paso {step_num}/{total}")
            self.statusBar().showMessage(message)

            self.anim_timer.setInterval(step_ms)
            self.tree_canvas.play_trace_step(step, duration_ms=motion_ms)
            self.anim_index += 1
        else:
            self.anim_timer.stop()
            self.anim_timer.setInterval(self.base_step_ms)
            self.anim_mode = None
            self.insert_steps = []
            self.anim_index = 0
            self.btn_stop_anim.setEnabled(False)
            self.lbl_current_step.setText("Paso actual: Inserción completada")
            self._set_banner_style("insert")
            self.lbl_anim_banner.setText("Inserción completada · Árbol AVL balanceado.")
            self.refresh_ui(
                status_msg="Inserción completada y guardada.",
                preserve_step_label=True,
            )

    def _read_int_input(self) -> int | None:
        text = self.value_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Dato requerido", "Por favor ingresa un número entero.")
            return None
        try:
            return int(text)
        except ValueError:
            QMessageBox.warning(self, "Valor inválido", f"'{text}' no es un número entero válido.")
            return None

    def _read_insert_values(self) -> list[int] | None:
        """Permite ingresar un único entero o una lista separada por comas/espacios."""
        raw = self.value_input.text().strip()
        if not raw:
            QMessageBox.warning(self, "Dato requerido", "Por favor ingresa uno o más números enteros.")
            return None
        tokens = [t for t in raw.replace(",", " ").split() if t]
        values = []
        for token in tokens:
            try:
                values.append(int(token))
            except ValueError:
                QMessageBox.warning(self, "Valor inválido", f"'{token}' no es un número entero válido.")
                return None
        return values

    def _persist_and_refresh(self, message: str = "", animate_layout: bool = False):
        save_tree(self.tree, self.data_path)
        self.value_input.clear()
        self.value_input.setFocus()
        self.refresh_ui(message, animate_layout=animate_layout)

    def on_insert(self):
        self.stop_animation()
        values = self._read_insert_values()
        if values is None:
            return

        all_steps = []
        for val in values:
            all_steps.extend(self.tree.insert_with_trace(val))

        save_tree(self.tree, self.data_path)
        self.value_input.clear()
        self.value_input.setFocus()

        # Actualiza recorridos y métricas directamente desde AVLTree
        self._update_metadata_ui()

        if self.chk_animate_insert.isChecked() and all_steps:
            self.anim_mode = "insert"
            self.insert_steps = all_steps
            self.anim_index = 0
            self.btn_stop_anim.setEnabled(True)
            self._on_animation_step()
            self.anim_timer.start()
        else:
            label = ", ".join(map(str, values))
            self._set_banner_style("insert")
            self.lbl_anim_banner.setText(f"Valor(es) {label} insertado(s) y balanceado(s).")
            self.refresh_ui(
                f"Nodo(s) {label} insertado(s).",
                highlight_value=values[-1],
                highlight_color="insert",
                animate_layout=True,
            )

    def on_delete(self):
        self.stop_animation()
        val = self._read_int_input()
        if val is None:
            return
        self.tree.delete(val)
        self._set_banner_style("idle")
        self.lbl_anim_banner.setText(f"Operación eliminar ({val}) aplicada.")
        self._persist_and_refresh(f"Operación eliminar ({val}) ejecutada.", animate_layout=True)

    def on_search(self):
        self.stop_animation()
        val = self._read_int_input()
        if val is None:
            return
        found = self.tree.search(val)
        if found:
            self._set_banner_style("search")
            self.lbl_anim_banner.setText(f"Valor {val} encontrado activo en el árbol.")
            self.refresh_ui(
                status_msg=f"Valor {val} encontrado y resaltado.",
                highlight_value=val,
                highlight_color="search",
            )
        else:
            self._set_banner_style("idle")
            self.lbl_anim_banner.setText(f"El valor {val} no se encontró activo en el árbol.")
            self.refresh_ui(status_msg=f"Valor {val} no encontrado.")
            QMessageBox.information(self, "Búsqueda", "Valor no encontrado")

    def on_deactivate(self):
        self.stop_animation()
        val = self._read_int_input()
        if val is None:
            return
        if self.tree.deactivate(val):
            self._set_banner_style("idle")
            self.lbl_anim_banner.setText(f"Nodo {val} marcado como inactivo (borrado lógico).")
            self._persist_and_refresh(f"Nodo {val} desactivado.")
        else:
            QMessageBox.information(self, "Desactivar", f"No se encontró el nodo {val} en el árbol.")

    def on_modify(self):
        self.stop_animation()
        old_val = self._read_int_input()
        if old_val is None:
            return
        new_val, ok = QInputDialog.getInt(
            self,
            "Modificar valor",
            f"Nuevo valor entero para reemplazar a {old_val}:",
            value=old_val,
        )
        if not ok:
            return
        self.tree.modify(old_val, new_val)
        self._set_banner_style("insert")
        self.lbl_anim_banner.setText(f"Valor {old_val} reemplazado por {new_val} y rebalanceado.")
        self._persist_and_refresh(f"Valor {old_val} modificado por {new_val}.", animate_layout=True)

    def on_clear(self):
        self.stop_animation()
        if self.tree.is_empty():
            return
        reply = QMessageBox.question(
            self,
            "Confirmar limpieza",
            "¿Estás seguro de que deseas vaciar todo el árbol?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.tree.clear()
            self._set_banner_style("idle")
            self.lbl_anim_banner.setText("Árbol vaciado · Ingresa un valor para comenzar.")
            self._persist_and_refresh("Árbol vaciado.")

    def _update_metadata_ui(self) -> str:
        pre_list = self.tree.preorder()
        in_list = self.tree.inorder()
        post_list = self.tree.postorder()

        pre_str = ", ".join(map(str, pre_list)) or "(vacío)"
        in_str = ", ".join(map(str, in_list)) or "(vacío)"
        post_str = ", ".join(map(str, post_list)) or "(vacío)"

        self.lbl_preorder.setText(f"[{pre_str}]")
        self.lbl_inorder.setText(f"[{in_str}]")
        self.lbl_postorder.setText(f"[{post_str}]")

        active_count, total_count = _count_nodes(self.tree.root)
        height = self.tree.root.height if self.tree.root else 0

        counts_text = f"Nodos activos: {active_count} / Total: {total_count}"
        self.lbl_node_counts.setText(counts_text)
        self.lbl_badge_active.setText(f"Activos: {active_count}")
        self.lbl_badge_total.setText(f"Total: {total_count}")
        self.lbl_badge_height.setText(f"Altura: {height}")

        self.btn_play.setEnabled(active_count > 0)
        return counts_text

    def refresh_ui(
        self,
        status_msg: str = "",
        highlight_value: int | None = None,
        highlight_color: str = "search",
        preserve_step_label: bool = False,
        animate_layout: bool = False,
    ):
        if not preserve_step_label:
            self.lbl_current_step.setText("Paso actual: -")

        counts_text = self._update_metadata_ui()

        if status_msg:
            self.statusBar().showMessage(f"{status_msg} | {counts_text}")
        else:
            self.statusBar().showMessage(counts_text)

        highlights = {highlight_value: highlight_color} if highlight_value is not None else {}
        self.tree_canvas.set_steady_tree(self.tree.root, highlights=highlights, animate_layout=animate_layout)
