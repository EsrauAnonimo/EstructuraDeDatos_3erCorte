import json


class Node:
    """Nodo del árbol AVL."""

    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.height = 1
        self.active = True


class AVLTree:
    """Árbol AVL con soporte para borrado lógico (desactivación) y serialización."""

    def __init__(self):
        self.root = None

    def is_empty(self):
        return self.root is None

    def clear(self):
        self.root = None

    def _height(self, node):
        return node.height if node else 0

    def _update_height(self, node):
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance_factor(self, node):
        return self._height(node.left) - self._height(node.right) if node else 0

    def _rotate_right(self, y):
        # Rotación simple a la derecha
        x = y.left
        t2 = x.right
        x.right = y
        y.left = t2
        self._update_height(y)
        self._update_height(x)
        return x

    def _rotate_left(self, x):
        # Rotación simple a la izquierda
        y = x.right
        t2 = y.left
        y.left = x
        x.right = t2
        self._update_height(x)
        self._update_height(y)
        return y

    def _rebalance(self, node):
        # Actualiza la altura y aplica las rotaciones necesarias según el factor de balance
        self._update_height(node)
        balance = self._balance_factor(node)

        # Caso Izquierda-Izquierda (rotación simple derecha)
        if balance > 1 and self._balance_factor(node.left) >= 0:
            return self._rotate_right(node)

        # Caso Izquierda-Derecha (rotación doble izquierda-derecha)
        if balance > 1 and self._balance_factor(node.left) < 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        # Caso Derecha-Derecha (rotación simple izquierda)
        if balance < -1 and self._balance_factor(node.right) <= 0:
            return self._rotate_left(node)

        # Caso Derecha-Izquierda (rotación doble derecha-izquierda)
        if balance < -1 and self._balance_factor(node.right) > 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def insert(self, value):
        self.root = self._insert(self.root, value)

    def insert_with_trace(self, value):
        """Inserta un valor y devuelve los pasos visuales del recorrido, inserción y rotaciones."""
        steps = []

        if not self.root:
            self.root = Node(value)
            steps.append({
                "structure": self.get_tree_structure(),
                "highlights": {value: "insert"},
                "message": f"Nodo {value} insertado como raíz del árbol.",
            })
            return steps

        path = []
        current = self.root
        while current:
            if value < current.value:
                steps.append({
                    "structure": self.get_tree_structure(),
                    "highlights": {current.value: "visit"},
                    "message": f"Comparando {value} < {current.value} → bajar a la izquierda.",
                })
                path.append((current, "left"))
                current = current.left
            elif value > current.value:
                steps.append({
                    "structure": self.get_tree_structure(),
                    "highlights": {current.value: "visit"},
                    "message": f"Comparando {value} > {current.value} → bajar a la derecha.",
                })
                path.append((current, "right"))
                current = current.right
            else:
                estado = "activo" if current.active else "inactivo"
                steps.append({
                    "structure": self.get_tree_structure(),
                    "highlights": {current.value: "search"},
                    "message": f"El valor {value} ya existe ({estado}); no se permiten duplicados.",
                })
                return steps

        parent, direction = path[-1]
        setattr(parent, direction, Node(value))
        steps.append({
            "structure": self.get_tree_structure(),
            "highlights": {value: "insert"},
            "message": f"Nodo {value} insertado como hijo {'izquierdo' if direction == 'left' else 'derecho'} de {parent.value}.",
        })

        for idx in range(len(path) - 1, -1, -1):
            self._rebalance_with_trace(path, idx, value, steps)

        return steps

    def _rebalance_with_trace(self, path, idx, inserted_value, steps):
        """Actualiza altura del nodo en path[idx] y registra pasos si ocurre rotación."""
        node, _ = path[idx]
        self._update_height(node)
        balance = self._balance_factor(node)
        if -1 <= balance <= 1:
            return

        fb_str = f"+{balance}" if balance > 0 else str(balance)
        if balance > 1:
            child_attr = "left"
            is_simple = self._balance_factor(node.left) >= 0
            simple_fn, simple_name = self._rotate_right, "Rotación Simple Derecha (LL)"
            first_fn, second_fn = self._rotate_left, self._rotate_right
            dbl_name, short_name, dir1, dir2 = "Izquierda-Derecha (LR)", "I-D", "izquierda", "derecha"
        else:
            child_attr = "right"
            is_simple = self._balance_factor(node.right) <= 0
            simple_fn, simple_name = self._rotate_left, "Rotación Simple Izquierda (RR)"
            first_fn, second_fn = self._rotate_right, self._rotate_left
            dbl_name, short_name, dir1, dir2 = "Derecha-Izquierda (RL)", "D-I", "derecha", "izquierda"

        if is_simple:
            steps.append({
                "structure": self.get_tree_structure(),
                "highlights": {node.value: "rotate", inserted_value: "insert"},
                "message": f"Desbalance en {node.value} (FB = {fb_str}) → {simple_name}.",
            })
            new_sub = simple_fn(node)
            self._attach_subtree(path, idx, new_sub)
            steps.append({
                "structure": self.get_tree_structure(),
                "highlights": {new_sub.value: "rotate", inserted_value: "insert"},
                "message": f"{simple_name} completada: {new_sub.value} sube como raíz del subárbol.",
            })
        else:
            child = getattr(node, child_attr)
            pivot_child = child.value
            steps.append({
                "structure": self.get_tree_structure(),
                "highlights": {node.value: "rotate", pivot_child: "rotate", inserted_value: "insert"},
                "message": f"Desbalance en {node.value} (FB = {fb_str}) → Rotación Doble {dbl_name}.",
            })
            rotated_child = first_fn(child)
            setattr(node, child_attr, rotated_child)
            steps.append({
                "structure": self.get_tree_structure(),
                "highlights": {rotated_child.value: "rotate", pivot_child: "rotate"},
                "message": f"Rotación Doble {short_name} (1/2): rotación {dir1} en {pivot_child}.",
            })
            new_sub = second_fn(node)
            self._attach_subtree(path, idx, new_sub)
            steps.append({
                "structure": self.get_tree_structure(),
                "highlights": {new_sub.value: "rotate", inserted_value: "insert"},
                "message": f"Rotación Doble {short_name} (2/2): rotación {dir2} en {node.value}.",
            })

    def _attach_subtree(self, path, idx, new_subtree):
        """Reconecta un subárbol rotado en la raíz o en su nodo padre."""
        if idx == 0:
            self.root = new_subtree
        else:
            parent, parent_dir = path[idx - 1]
            setattr(parent, parent_dir, new_subtree)

    def _insert(self, node, value):
        if not node:
            return Node(value)

        if value < node.value:
            node.left = self._insert(node.left, value)
        elif value > node.value:
            node.right = self._insert(node.right, value)
        else:
            # Decisión de diseño: no se permiten valores duplicados en el árbol AVL;
            # si el valor ya existe, se ignora la inserción y se retorna el nodo actual.
            return node

        return self._rebalance(node)

    def delete(self, value):
        self.root = self._delete(self.root, value)

    def _delete(self, node, value):
        if not node:
            return None

        if value < node.value:
            node.left = self._delete(node.left, value)
        elif value > node.value:
            node.right = self._delete(node.right, value)
        else:
            # Nodo con 0 o 1 hijo
            if not node.left:
                return node.right
            if not node.right:
                return node.left

            # Nodo con 2 hijos: reemplazar por el sucesor in-orden (mínimo del subárbol derecho)
            successor = self._min_node(node.right)
            node.value = successor.value
            node.active = successor.active
            node.right = self._delete(node.right, successor.value)

        return self._rebalance(node)

    def _min_node(self, node):
        current = node
        while current.left:
            current = current.left
        return current

    def search(self, value):
        # Búsqueda binaria que solo considera válidos los nodos activos
        current = self.root
        while current:
            if value < current.value:
                current = current.left
            elif value > current.value:
                current = current.right
            else:
                return current.active
        return False

    def deactivate(self, value):
        # Borrado lógico: marca el nodo como inactivo conservando su posición y el balance
        current = self.root
        while current:
            if value < current.value:
                current = current.left
            elif value > current.value:
                current = current.right
            else:
                current.active = False
                return True
        return False

    def modify(self, old_value, new_value):
        self.delete(old_value)
        self.insert(new_value)

    def preorder(self):
        result = []
        self._preorder(self.root, result)
        return result

    def _preorder(self, node, result):
        if not node:
            return
        if node.active:
            result.append(node.value)
        self._preorder(node.left, result)
        self._preorder(node.right, result)

    def inorder(self):
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if not node:
            return
        self._inorder(node.left, result)
        if node.active:
            result.append(node.value)
        self._inorder(node.right, result)

    def postorder(self):
        result = []
        self._postorder(self.root, result)
        return result

    def _postorder(self, node, result):
        if not node:
            return
        self._postorder(node.left, result)
        self._postorder(node.right, result)
        if node.active:
            result.append(node.value)

    def get_tree_structure(self):
        # Incluye todos los nodos (activos e inactivos) para visualización y serialización JSON
        return self._serialize(self.root)

    def _serialize(self, node):
        if not node:
            return None
        return {
            "value": node.value,
            "active": node.active,
            "height": node.height,
            "left": self._serialize(node.left),
            "right": self._serialize(node.right),
        }

    @classmethod
    def from_structure(cls, structure):
        # Reconstruye un AVLTree respetando exactamente la estructura, alturas y estados
        tree = cls()
        tree.root = cls._deserialize(structure)
        return tree

    @classmethod
    def _deserialize(cls, data):
        if not data:
            return None
        node = Node(data["value"])
        node.active = data["active"]
        node.height = data["height"]
        node.left = cls._deserialize(data["left"])
        node.right = cls._deserialize(data["right"])
        return node


if __name__ == "__main__":
    tree = AVLTree()

    print("=== 1. Inserción secuencial (1 al 7) ===")
    for v in [1, 2, 3, 4, 5, 6, 7]:
        tree.insert(v)
    print("Inorder:  ", tree.inorder())
    print("Preorder: ", tree.preorder())
    print("Postorder:", tree.postorder())

    print("\n=== 2. Inserción con rotaciones (10, 20, 30, 40, 50, 25) ===")
    tree.clear()
    for v in [10, 20, 30, 40, 50, 25]:
        tree.insert(v)
    print(json.dumps(tree.get_tree_structure(), indent=2))

    print("\n=== 3. Búsqueda de valores ===")
    print("Buscar 25 (existente):", tree.search(25))
    print("Buscar 99 (inexistente):", tree.search(99))

    print("\n=== 4. Desactivar nodo (20) y mostrar recorridos ===")
    tree.deactivate(20)
    print("Buscar 20 (desactivado):", tree.search(20))
    print("Inorder:  ", tree.inorder())
    print("Preorder: ", tree.preorder())
    print("Postorder:", tree.postorder())

    print("\n=== 5. Modificar valor (25 -> 27) y mostrar recorridos ===")
    tree.modify(25, 27)
    print("Inorder:  ", tree.inorder())
    print("Preorder: ", tree.preorder())
    print("Postorder:", tree.postorder())

    print("\n=== 6. Eliminar nodo con 2 hijos (30) y mostrar estructura ===")
    tree.delete(30)
    print("Inorder:  ", tree.inorder())
    print(json.dumps(tree.get_tree_structure(), indent=2))
