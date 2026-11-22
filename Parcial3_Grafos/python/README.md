# PERA - Planificador Eficiente de Rutas Automotrices (Parcial 3)

Módulo en Python para la planificación y optimización multicriterio de rutas terrestres entre las principales 12 capitales de Colombia.

## Descripción

El sistema modela una red vial como un grafo dirigido ponderado donde cada arista cuenta con atributos reales y actualizados a noviembre de 2026:
- **Distancia** (`distance_km`): Kilómetros de ruta (Google Maps).
- **Tiempo** (`time_hours`): Horas de viaje estimadas en hora valle.
- **Peaje** (`toll_cost_cop`): Costo total de peajes en pesos colombianos.
- **Combustible** (`fuel_cost_cop`): Costo calculado según el precio oficial de gasolina corriente por ciudad de origen (Circular CREG 339 de 2026) y un rendimiento estimado de 35 km/galón.

Permite encontrar rutas mínimas mediante el algoritmo de **Dijkstra** para criterios individuales o mediante un **criterio combinado** con normalización min-max, además de soportar la activación y desactivación de ciudades (para simular cierres viales o bloqueos).

## Instalación de dependencias

Asegúrese de contar con el entorno virtual activo:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r Parcial3_Grafos/python/requirements.txt
```

## Ejecución de pruebas

Para verificar el correcto funcionamiento del modelo de grafos y Dijkstra:

```powershell
python Parcial3_Grafos/python/graph.py
```

o desde la carpeta `Parcial3_Grafos/python`:

```powershell
cd Parcial3_Grafos/python
python graph.py
```

## Próximos pasos

La interfaz gráfica interactiva en PyQt6, el visualizador con Folium / QWebEngineView y el dashboard de comparación de rutas serán integrados en la siguiente entrega.
