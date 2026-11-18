from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
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

from avl import AVLTree
from graph_render import cleanup_temp_files, render_to_pixmap, render_tree
from persistence import DEFAULT_DATA_PATH, save_tree


def _count_nodes(structure):
    """Cuenta recursivamente (nodos_activos, total_nodos) en la estructura del árbol."""
    if not structure:
        return 0, 0
    la, lt = _count_nodes(structure.get("left"))
    ra, rt = _count_nodes(structure.get("right"))
    active = (1 if structure.get("active", True) else 0) + la + ra
    total = 1 + lt + rt
    return active, total


class MainWindow(QMainWindow):
    """Ventana principal del Programa de Aprendizaje de Árboles (PAA)."""

    def __init__(self, tree: AVLTree | None = None, data_path: str = DEFAULT_DATA_PATH):
        super().__init__()
        cleanup_temp_files()
        self.tree = tree if tree is not None else AVLTree()
        self.data_path = data_path
        self.current_svg_path: str | None = None

        # Estado de la animación de recorridos
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(600)
        self.anim_timer.timeout.connect(self._on_animation_step)
        self.anim_sequence: list[int] = []
        self.anim_index: int = 0

        self.setWindowTitle("PAA - Programa de Aprendizaje de Árboles AVL")
        self.resize(1140, 720)

        self._build_ui()
        self.refresh_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Panel izquierdo (40%)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Grupo de controles
        controls_group = QGroupBox("Operaciones del Árbol AVL")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(10)

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Ingresa un valor entero (ej. 25)...")
        self.value_input.returnPressed.connect(self.on_insert)
        controls_layout.addWidget(self.value_input)

        btn_grid = QGridLayout()
        btn_grid.setSpacing(8)

        self.btn_insert = QPushButton("Insertar")
        self.btn_insert.setObjectName("btnSuccess")
        self.btn_insert.clicked.connect(self.on_insert)

        self.btn_delete = QPushButton("Eliminar")
        self.btn_delete.setObjectName("btnDanger")
        self.btn_delete.clicked.connect(self.on_delete)

        self.btn_search = QPushButton("Buscar")
        self.btn_search.clicked.connect(self.on_search)

        self.btn_deactivate = QPushButton("Desactivar")
        self.btn_deactivate.setObjectName("btnWarning")
        self.btn_deactivate.clicked.connect(self.on_deactivate)

        self.btn_modify = QPushButton("Modificar")
        self.btn_modify.setObjectName("btnSecondary")
        self.btn_modify.clicked.connect(self.on_modify)

        self.btn_clear = QPushButton("Limpiar árbol")
        self.btn_clear.setObjectName("btnDanger")
        self.btn_clear.clicked.connect(self.on_clear)

        btn_grid.addWidget(self.btn_insert, 0, 0)
        btn_grid.addWidget(self.btn_delete, 0, 1)
        btn_grid.addWidget(self.btn_search, 1, 0)
        btn_grid.addWidget(self.btn_deactivate, 1, 1)
        btn_grid.addWidget(self.btn_modify, 2, 0)
        btn_grid.addWidget(self.btn_clear, 2, 1)

        controls_layout.addLayout(btn_grid)
        left_layout.addWidget(controls_group)

        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #CBD5E1;")
        left_layout.addWidget(separator)

        # Grupo de recorridos siempre visibles + animación
        traversals_group = QGroupBox("Recorridos (Nodos Activos)")
        traversals_layout = QVBoxLayout(traversals_group)
        traversals_layout.setSpacing(8)

        self.lbl_preorder = self._create_traversal_row(traversals_layout, "Pre-orden:")
        self.lbl_inorder = self._create_traversal_row(traversals_layout, "In-orden:")
        self.lbl_postorder = self._create_traversal_row(traversals_layout, "Post-orden:")

        play_row = QHBoxLayout()
        play_row.setSpacing(8)

        self.combo_traversal = QComboBox()
        self.combo_traversal.addItems(["Pre-orden", "In-orden", "Post-orden"])

        self.btn_play = QPushButton("▶ Reproducir recorrido")
        self.btn_play.setObjectName("btnSuccess")
        self.btn_play.clicked.connect(self.on_play_traversal)

        play_row.addWidget(self.combo_traversal, 1)
        play_row.addWidget(self.btn_play, 1)
        traversals_layout.addLayout(play_row)

        self.lbl_current_step = QLabel("Paso actual: -")
        self.lbl_current_step.setStyleSheet("font-weight: 600; color: #16A34A; padding-top: 4px;")
        traversals_layout.addWidget(self.lbl_current_step)

        left_layout.addWidget(traversals_group)

        # Etiqueta de estado de nodos en el panel izquierdo
        self.lbl_node_counts = QLabel("Nodos activos: 0 / Total: 0")
        self.lbl_node_counts.setStyleSheet("font-weight: 600; color: #334155; padding: 4px;")
        left_layout.addWidget(self.lbl_node_counts)
        left_layout.addStretch()

        # Panel derecho (60%)
        right_group = QGroupBox("Visualización del Árbol AVL (Graphviz)")
        right_layout = QVBoxLayout(right_group)

        self.canvas_label = QLabel("Árbol vacío")
        self.canvas_label.setObjectName("canvasLabel")
        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas_label.setMinimumSize(420, 420)
        right_layout.addWidget(self.canvas_label)

        main_layout.addWidget(left_panel, 4)
        main_layout.addWidget(right_group, 6)

    def _create_traversal_row(self, parent_layout, title: str) -> QLabel:
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: 600; color: #475569;")
        value_lbl = QLabel("[]")
        value_lbl.setObjectName("traversalValue")
        value_lbl.setWordWrap(True)
        value_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        parent_layout.addWidget(title_lbl)
        parent_layout.addWidget(value_lbl)
        return value_lbl

    def stop_animation(self):
        """Detiene la animación en curso si está activa."""
        if self.anim_timer.isActive():
            self.anim_timer.stop()
        self.anim_sequence = []
        self.anim_index = 0
        self.lbl_current_step.setText("Paso actual: -")

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

        self.anim_sequence = sequence
        self.anim_index = 0
        self._on_animation_step()
        self.anim_timer.start()

    def _on_animation_step(self):
        """Ejecuta un paso de la animación resaltando el nodo actual."""
        total = len(self.anim_sequence)
        if self.anim_index < total:
            current_val = self.anim_sequence[self.anim_index]
            step_num = self.anim_index + 1
            step_text = f"Paso actual: {current_val} ({step_num}/{total})"
            self.lbl_current_step.setText(step_text)
            self.refresh_ui(
                status_msg=step_text,
                highlight_value=current_val,
                highlight_color="play",
                preserve_step_label=True,
            )
            self.anim_index += 1
        else:
            self.anim_timer.stop()
            self.anim_sequence = []
            self.anim_index = 0
            self.lbl_current_step.setText("Paso actual: Recorrido completado")
            self.refresh_ui(
                status_msg="Recorrido completado",
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

    def _persist_and_refresh(self, message: str = ""):
        save_tree(self.tree, self.data_path)
        self.value_input.clear()
        self.value_input.setFocus()
        self.refresh_ui(message)

    def on_insert(self):
        self.stop_animation()
        val = self._read_int_input()
        if val is None:
            return
        self.tree.insert(val)
        self._persist_and_refresh(f"Nodo {val} insertado.")

    def on_delete(self):
        self.stop_animation()
        val = self._read_int_input()
        if val is None:
            return
        self.tree.delete(val)
        self._persist_and_refresh(f"Operación eliminar ({val}) ejecutada.")

    def on_search(self):
        self.stop_animation()
        val = self._read_int_input()
        if val is None:
            return
        found = self.tree.search(val)
        if found:
            self.refresh_ui(
                status_msg=f"Valor {val} encontrado y resaltado.",
                highlight_value=val,
                highlight_color="search",
            )
        else:
            self.refresh_ui(status_msg=f"Valor {val} no encontrado.")
            QMessageBox.information(self, "Búsqueda", "Valor no encontrado")

    def on_deactivate(self):
        self.stop_animation()
        val = self._read_int_input()
        if val is None:
            return
        if self.tree.deactivate(val):
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
        self._persist_and_refresh(f"Valor {old_val} modificado por {new_val}.")

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
            self._persist_and_refresh("Árbol vaciado.")

    def _update_canvas_pixmap(self):
        if not self.current_svg_path or self.tree.is_empty():
            self.canvas_label.setPixmap(QPixmap())
            self.canvas_label.setText("Árbol vacío")
            return
        pixmap = render_to_pixmap(
            self.current_svg_path,
            self.canvas_label.width(),
            self.canvas_label.height(),
        )
        self.canvas_label.setText("")
        self.canvas_label.setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_svg_path and not self.tree.is_empty():
            self._update_canvas_pixmap()

    def refresh_ui(
        self,
        status_msg: str = "",
        highlight_value: int | None = None,
        highlight_color: str = "search",
        preserve_step_label: bool = False,
    ):
        if not preserve_step_label:
            self.lbl_current_step.setText("Paso actual: -")

        pre_list = self.tree.preorder()
        in_list = self.tree.inorder()
        post_list = self.tree.postorder()

        pre_str = ", ".join(map(str, pre_list)) or "(vacío)"
        in_str = ", ".join(map(str, in_list)) or "(vacío)"
        post_str = ", ".join(map(str, post_list)) or "(vacío)"

        self.lbl_preorder.setText(f"[{pre_str}]")
        self.lbl_inorder.setText(f"[{in_str}]")
        self.lbl_postorder.setText(f"[{post_str}]")

        structure = self.tree.get_tree_structure()
        active_count, total_count = _count_nodes(structure)
        counts_text = f"Nodos activos: {active_count} / Total: {total_count}"
        self.lbl_node_counts.setText(counts_text)

        self.btn_play.setEnabled(active_count > 0)

        if status_msg:
            self.statusBar().showMessage(f"{status_msg} | {counts_text}")
        else:
            self.statusBar().showMessage(counts_text)

        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.tree.is_empty():
            self.current_svg_path = None
            self.canvas_label.setPixmap(QPixmap())
            self.canvas_label.setText("Árbol vacío")
        else:
            self.current_svg_path = render_tree(
                self.tree,
                highlight_value=highlight_value,
                highlight_color=highlight_color,
            )
            self._update_canvas_pixmap()
