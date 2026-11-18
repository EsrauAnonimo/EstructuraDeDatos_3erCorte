# Programa de Aprendizaje de Árboles (PAA) — Árboles AVL

Aplicación de escritorio en **Python + PyQt6 + Graphviz** diseñada para visualizar y aprender el funcionamiento de un **Árbol AVL** (inserciones, rotaciones automáticas, eliminación física, desactivación lógica, modificación, búsqueda resaltada, recorridos animados y persistencia en JSON).

---

## 1. Requisitos

1. **Python 3.10+**
2. **Graphviz (binario del sistema)** instalado y disponible en el `PATH` (`dot -V`):
   - En Windows (PowerShell):
     ```powershell
     winget install --id Graphviz.Graphviz -e
     ```
3. **Librerías de Python** (dentro del entorno virtual `.venv`):
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

- `avl.py`: Lógica pura del árbol AVL (`Node`, `AVLTree`), rotaciones simples y dobles, borrado lógico (`deactivate`), recorridos (`preorder`, `inorder`, `postorder`) y serialización/deserialización exacta (`get_tree_structure`, `from_structure`).
- `persistence.py`: Persistencia en formato JSON (`save_tree`, `load_tree`, `tree_exists`, `backup_tree`) con metadatos de fecha y conteo de nodos.
- `graph_render.py`: Generación del grafo en formato DOT y renderizado vectorial a SVG/QPixmap mediante Graphviz y `QSvgRenderer`, diferenciando nodos activos, inactivos y resaltados (búsqueda o animación).
- `styles.py`: Paleta de colores y hoja de estilos QSS (`APP_QSS`) para la interfaz PyQt6.
- `gui.py`: Ventana principal (`MainWindow`), panel de controles, panel de recorridos siempre visibles, animación paso a paso con `QTimer` y lienzo visual del árbol.
- `main.py`: Punto de entrada de la aplicación y diálogo inicial de carga de datos.

---

## 4. Capturas de Pantalla

*(Espacio reservado para agregar las capturas de pantalla del proyecto)*

- `docs/captura_arbol_balanceado.png` — Árbol AVL balanceado tras insertar `10, 20, 30, 40, 50, 25` (raíz `30`).
- `docs/captura_nodo_inactivo.png` — Visualización de nodo desactivado en gris con borde punteado.
- `docs/captura_busqueda_resaltada.png` — Búsqueda de un nodo activo resaltado en amarillo/rojo.
- `docs/captura_recorrido_animado.png` — Animación paso a paso de recorridos Pre-orden, In-orden y Post-orden.
