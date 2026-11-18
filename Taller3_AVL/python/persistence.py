from datetime import datetime
import json
import os

from avl import AVLTree

# Ruta por defecto para el archivo de persistencia JSON
DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__) or ".", "data.json")


def _count_nodes(structure):
    """Cuenta recursivamente (total_nodos, nodos_activos) desde el diccionario del árbol."""
    if not structure:
        return 0, 0
    left_total, left_active = _count_nodes(structure.get("left"))
    right_total, right_active = _count_nodes(structure.get("right"))
    total = 1 + left_total + right_total
    active = (1 if structure.get("active", True) else 0) + left_active + right_active
    return total, active


def backup_tree(filepath: str = DEFAULT_DATA_PATH) -> bool:
    """Crea una copia de respaldo (filepath + '.bak') antes de sobrescribir."""
    if not os.path.isfile(filepath):
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as src:
            content = src.read()
        with open(filepath + ".bak", "w", encoding="utf-8") as dst:
            dst.write(content)
        return True
    except Exception as exc:
        print(f"Error al crear respaldo de '{filepath}': {exc}")
        return False


def save_tree(tree: AVLTree, filepath: str = DEFAULT_DATA_PATH) -> bool:
    """Guarda la estructura del árbol AVL y sus metadatos en un archivo JSON."""
    try:
        if os.path.isfile(filepath):
            backup_tree(filepath)

        structure = tree.get_tree_structure()
        total_nodes, active_nodes = _count_nodes(structure)
        payload = {
            "tree": structure,
            "meta": {
                "saved_at": datetime.now().isoformat(timespec="seconds"),
                "total_nodes": total_nodes,
                "active_nodes": active_nodes,
            },
        }

        parent_dir = os.path.dirname(filepath)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except Exception as exc:
        print(f"Error al guardar el árbol en '{filepath}': {exc}")
        return False


def load_tree(filepath: str = DEFAULT_DATA_PATH) -> AVLTree | None:
    """Carga y reconstruye exactamente el árbol AVL desde un archivo JSON."""
    if not os.path.isfile(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "tree" not in data:
            return None
        return AVLTree.from_structure(data["tree"])
    except Exception:
        return None


def tree_exists(filepath: str = DEFAULT_DATA_PATH) -> bool:
    """Verifica si el archivo existe y contiene un JSON válido con la clave 'tree'."""
    if not os.path.isfile(filepath):
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return isinstance(data, dict) and "tree" in data
    except Exception:
        return False


if __name__ == "__main__":
    test_path = DEFAULT_DATA_PATH

    # 1. Crear AVLTree e insertar 10 valores
    original_tree = AVLTree()
    for val in [50, 25, 75, 10, 30, 60, 80, 5, 15, 27]:
        original_tree.insert(val)
    original_tree.deactivate(30)

    # Verificar que get_tree_structure() y from_structure() son inversos perfectos
    reconstructed = AVLTree.from_structure(original_tree.get_tree_structure())
    assert reconstructed.get_tree_structure() == original_tree.get_tree_structure()

    # 2. Guardar en data.json
    assert save_tree(original_tree, test_path) is True
    assert tree_exists(test_path) is True

    # Probar respaldo al sobrescribir
    assert save_tree(original_tree, test_path) is True
    assert os.path.isfile(test_path + ".bak") is True

    # 3. Cargar con load_tree
    loaded_tree = load_tree(test_path)
    assert loaded_tree is not None

    # 4. Verificar que inorder(), preorder(), postorder() coinciden con el original
    assert loaded_tree.inorder() == original_tree.inorder()
    assert loaded_tree.preorder() == original_tree.preorder()
    assert loaded_tree.postorder() == original_tree.postorder()

    # 5. Verificar que get_tree_structure() del cargado es idéntico al original
    assert loaded_tree.get_tree_structure() == original_tree.get_tree_structure()

    # 6. Probar tree_exists() antes y después de borrar el archivo
    print("tree_exists antes de borrar:", tree_exists(test_path))
    os.remove(test_path)
    if os.path.isfile(test_path + ".bak"):
        os.remove(test_path + ".bak")
    print("tree_exists después de borrar:", tree_exists(test_path))
    assert tree_exists(test_path) is False

    print("OK persistencia")
