# Programa de Aprendizaje de Árboles (PAA) — Árboles AVL

Aplicación de escritorio en **Python + PyQt6** diseñada para enseñar e implementar la estructura de datos **Árbol AVL** de forma visual e interactiva (inserciones animadas, detección de desbalance, rotaciones simples/dobles en movimiento a 60 FPS, eliminación física, desactivación lógica, modificación, búsqueda, recorridos animados y persistencia en JSON).

---

## 1. Requisitos

1. **Python 3.10+**
2. **PyQt6** (dentro del entorno virtual `.venv`):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r Taller3_AVL/python/requirements.txt
   ```

---

## 2. Cómo ejecutar

Desde la raíz del repositorio (con el entorno virtual activo):

```powershell
python Taller3_AVL/python/main.py
```

Al iniciar, la aplicación pregunta si deseas cargar los datos guardados previamente en `data.json` o iniciar con un árbol vacío. Toda modificación posterior se guarda automáticamente en `Taller3_AVL/python/data.json` (creando copia de respaldo `data.json.bak`).

---

## 3. Arquitectura del Módulo Python

- `avl.py`: Implementación real de la estructura de datos **Árbol AVL** (`Node`, `AVLTree`), rotaciones simples (LL, RR) y dobles (LR, RL), borrado lógico (`deactivate`), recorridos (`preorder`, `inorder`, `postorder`), traza paso a paso (`insert_with_trace`) y serialización/deserialización exacta (`get_tree_structure`, `from_structure`).
- `persistence.py`: Persistencia en formato JSON (`save_tree`, `load_tree`, `tree_exists`, `backup_tree`) con metadatos de fecha y conteo de nodos.
- `tree_canvas.py`: Lienzo interactivo con `QPainter` a 60 FPS que lee directamente la estructura `AVLTree`/`Node` y anima las inserciones, factores de balance, rotaciones y recorridos.
- `styles.py`: Paleta de colores y hoja de estilos QSS (`APP_QSS`) para la interfaz PyQt6.
- `gui.py`: Ventana principal (`MainWindow`), panel de operaciones, métricas del árbol, recorridos siempre visibles y control de animaciones.
- `main.py`: Punto de entrada de la aplicación y diálogo inicial de carga de datos.

---

## 4. Capturas de Pantalla

*(Espacio reservado para agregar las capturas de pantalla del proyecto)*

- `docs/captura_arbol_balanceado.png` — Árbol AVL balanceado tras insertar `10, 20, 30, 40, 50, 25` (raíz `30`).
- `docs/captura_animacion_rotacion.png` — Detección de factor de balance y animación de rotación AVL.
- `docs/captura_nodo_inactivo.png` — Visualización de nodo desactivado en gris con borde punteado.
- `docs/captura_recorrido_animado.png` — Animación paso a paso de recorridos Pre-orden, In-orden y Post-orden.
