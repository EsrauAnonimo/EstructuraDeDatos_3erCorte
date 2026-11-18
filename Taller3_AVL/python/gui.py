import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
    QVBoxLayout,
    QWidget,
)

from avl import AVLTree
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
        self.tree = tree if tree is not None else AVLTree()
        self.data_path = data_path

        self.setWindowTitle("PAA - Programa de Aprendizaje de Árboles AVL")
        self.resize(1100, 680)

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

        # Grupo de recorridos siempre visibles
        traversals_group = QGroupBox("Recorridos (Nodos Activos)")
        traversals_layout = QVBoxLayout(traversals_group)
        traversals_layout.setSpacing(8)

        self.lbl_preorder = self._create_traversal_row(traversals_layout, "Pre-orden:")
        self.lbl_inorder = self._create_traversal_row(traversals_layout, "In-orden:")
        self.lbl_postorder = self._create_traversal_row(traversals_layout, "Post-orden:")

        left_layout.addWidget(traversals_group)

        # Etiqueta de estado de nodos en el panel izquierdo
        self.lbl_node_counts = QLabel("Nodos activos: 0 / Total: 0")
        self.lbl_node_counts.setStyleSheet("font-weight: 600; color: #334155; padding: 4px;")
        left_layout.addWidget(self.lbl_node_counts)
        left_layout.addStretch()

        # Panel derecho (60%)
        right_group = QGroupBox("Visualización del Árbol AVL")
        right_layout = QVBoxLayout(right_group)

        self.canvas_label = QLabel("Árbol vacío")
        self.canvas_label.setObjectName("canvasLabel")
        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_label.setWordWrap(True)
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
        val = self._read_int_input()
        if val is None:
            return
        self.tree.insert(val)
        self._persist_and_refresh(f"Nodo {val} insertado.")

    def on_delete(self):
        val = self._read_int_input()
        if val is None:
            return
        self.tree.delete(val)
        self._persist_and_refresh(f"Operación eliminar ({val}) ejecutada.")

    def on_search(self):
        val = self._read_int_input()
        if val is None:
            return
        found = self.tree.search(val)
        if found:
            self.statusBar().showMessage(f"Valor {val} encontrado (activo).")
            QMessageBox.information(self, "Búsqueda", f"El valor {val} SÍ se encuentra activo en el árbol.")
        else:
            self.statusBar().showMessage(f"Valor {val} no encontrado.")
            QMessageBox.information(self, "Búsqueda", f"Valor {val} no encontrado en el árbol activo.")

    def on_deactivate(self):
        val = self._read_int_input()
        if val is None:
            return
        if self.tree.deactivate(val):
            self._persist_and_refresh(f"Nodo {val} desactivado.")
        else:
            QMessageBox.information(self, "Desactivar", f"No se encontró el nodo {val} en el árbol.")

    def on_modify(self):
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

    def refresh_ui(self, status_msg: str = ""):
        pre_str = ", ".join(map(str, self.tree.preorder())) or "(vacío)"
        in_str = ", ".join(map(str, self.tree.inorder())) or "(vacío)"
        post_str = ", ".join(map(str, self.tree.postorder())) or "(vacío)"

        self.lbl_preorder.setText(f"[{pre_str}]")
        self.lbl_inorder.setText(f"[{in_str}]")
        self.lbl_postorder.setText(f"[{post_str}]")

        structure = self.tree.get_tree_structure()
        active_count, total_count = _count_nodes(structure)
        counts_text = f"Nodos activos: {active_count} / Total: {total_count}"
        self.lbl_node_counts.setText(counts_text)

        if status_msg:
            self.statusBar().showMessage(f"{status_msg} | {counts_text}")
        else:
            self.statusBar().showMessage(counts_text)

        if self.tree.is_empty():
            self.canvas_label.setText("Árbol vacío")
            self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            formatted = json.dumps(structure, indent=2)
            self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            self.canvas_label.setText(formatted)
