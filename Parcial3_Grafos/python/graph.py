"""
Module: graph.py
Description: Directed graph representation and shortest path routing algorithms (Dijkstra)
             for the PERA project (Planificador Eficiente de Rutas Automotrices).
"""

import collections
import heapq
import json
import os


class Graph:
    """Grafo dirigido ponderado con soporte para múltiples criterios y desactivación de nodos."""

    def __init__(self, directed=True):
        self.directed = directed
        self.cities = {}  # city_id -> {id, name, lat, lon, fuel_price_cop, active}
        self.adj = collections.defaultdict(dict)  # from_id -> {to_id -> edge_dict}

    def load_from_json(self, filepath: str) -> bool:
        """Carga ciudades y aristas desde un archivo JSON."""
        resolved_path = filepath
        if not os.path.isabs(resolved_path) and not os.path.exists(resolved_path):
            candidate = os.path.join(os.path.dirname(__file__), filepath)
            if os.path.exists(candidate):
                resolved_path = candidate

        if not os.path.exists(resolved_path):
            return False

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.cities.clear()
            self.adj.clear()

            for city in data.get("cities", []):
                self.add_city(
                    city_id=city["id"],
                    name=city["name"],
                    department=city.get("department", "N/A"),
                    lat=city["lat"],
                    lon=city["lon"],
                    fuel_price_cop=city["fuel_price_cop"],
                    active=city.get("active", True)
                )

            for edge in data.get("edges", []):
                from_id = edge.get("from") or edge.get("from_id")
                to_id = edge.get("to") or edge.get("to_id")
                self.add_edge(
                    from_id=from_id,
                    to_id=to_id,
                    distance_km=edge["distance_km"],
                    time_hours=edge["time_hours"],
                    toll_cost_cop=edge["toll_cost_cop"],
                    fuel_cost_cop=edge.get("fuel_cost_cop"),
                    active=edge.get("active", True),
                    category=edge.get("category", "Primaria"),
                    validated=edge.get("validated", True),
                    source=edge.get("source", "Google Maps"),
                    researcher=edge.get("researcher", "Grupo UPC")
                )
            return True
        except Exception:
            return False

    def add_city(self, city_id: str, name: str, lat: float, lon: float, fuel_price_cop: float,
                 active: bool = True, department: str = "N/A") -> bool:
        """Agrega o actualiza una ciudad en el grafo."""
        self.cities[city_id] = {
            "id": city_id,
            "name": name,
            "department": department,
            "lat": lat,
            "lon": lon,
            "fuel_price_cop": fuel_price_cop,
            "active": active
        }
        if city_id not in self.adj:
            self.adj[city_id] = {}
        return True

    def remove_city(self, city_id: str) -> bool:
        """Elimina una ciudad y todas sus aristas conectadas."""
        if city_id not in self.cities:
            return False
        del self.cities[city_id]
        if city_id in self.adj:
            del self.adj[city_id]
        for u in list(self.adj.keys()):
            if city_id in self.adj[u]:
                del self.adj[u][city_id]
        return True

    def save_to_json(self, filepath: str) -> bool:
        """Guarda el grafo en un archivo JSON."""
        return save_graph(self, filepath)

    def add_edge(self, from_id: str, to_id: str, distance_km: float, time_hours: float,
                 toll_cost_cop: float, fuel_cost_cop: float = None, active: bool = True,
                 category: str = "Primaria", validated: bool = True,
                 source: str = "Google Maps", researcher: str = "Grupo UPC") -> bool:
        """Agrega una arista dirigida entre dos ciudades con sus respectivos costos."""
        if from_id not in self.cities or to_id not in self.cities:
            return False

        if fuel_cost_cop is None:
            fuel_price = self.cities[from_id]["fuel_price_cop"]
            fuel_cost_cop = round((distance_km / 35.0) * fuel_price, 2)

        edge_data = {
            "from": from_id,
            "to": to_id,
            "from_id": from_id,
            "to_id": to_id,
            "distance_km": float(distance_km),
            "time_hours": float(time_hours),
            "toll_cost_cop": float(toll_cost_cop),
            "fuel_cost_cop": float(fuel_cost_cop)
            ,"active": bool(active), "category": category, "validated": bool(validated),
            "source": source, "researcher": researcher
        }
        self.adj[from_id][to_id] = edge_data

        if not self.directed:
            rev_fuel = round((distance_km / 35.0) * self.cities[to_id]["fuel_price_cop"], 2)
            rev_edge = {
                "from": to_id,
                "to": from_id,
                "from_id": to_id,
                "to_id": from_id,
                "distance_km": float(distance_km),
                "time_hours": float(time_hours),
                "toll_cost_cop": float(toll_cost_cop),
                "fuel_cost_cop": float(rev_fuel)
                ,"active": bool(active), "category": category, "validated": bool(validated),
                "source": source, "researcher": researcher
            }
            self.adj[to_id][from_id] = rev_edge

        return True

    def remove_edge(self, from_id: str, to_id: str) -> bool:
        """Elimina la arista entre from_id y to_id."""
        removed = False
        if from_id in self.adj and to_id in self.adj[from_id]:
            del self.adj[from_id][to_id]
            removed = True
        if not self.directed and to_id in self.adj and from_id in self.adj[to_id]:
            del self.adj[to_id][from_id]
            removed = True
        return removed

    def deactivate_city(self, city_id: str) -> bool:
        """Desactiva una ciudad para que sea ignorada en cálculos y recorridos."""
        if city_id in self.cities:
            self.cities[city_id]["active"] = False
            return True
        return False

    def set_edge_active(self, from_id: str, to_id: str, active: bool) -> bool:
        """Activa o desactiva una arista sin eliminarla."""
        edge = self.adj.get(from_id, {}).get(to_id)
        if edge is None:
            return False
        edge["active"] = bool(active)
        return True

    def modify_city(self, city_id: str, **kwargs) -> bool:
        """Modifica atributos permitidos de una ciudad."""
        city = self.cities.get(city_id)
        if city is None or any(key not in city for key in kwargs):
            return False
        city.update(kwargs)
        return True

    def activate_city(self, city_id: str) -> bool:
        """Activa una ciudad previamente desactivada."""
        if city_id in self.cities:
            self.cities[city_id]["active"] = True
            return True
        return False

    def modify_edge(self, from_id: str, to_id: str, **kwargs) -> bool:
        """Modifica atributos de una arista existente."""
        if from_id not in self.adj or to_id not in self.adj[from_id]:
            return False

        edge = self.adj[from_id][to_id]
        for key, value in kwargs.items():
            edge[key] = value

        if not self.directed and to_id in self.adj and from_id in self.adj[to_id]:
            rev_edge = self.adj[to_id][from_id]
            for key, value in kwargs.items():
                rev_edge[key] = value

        return True

    def get_cities(self) -> list[dict]:
        """Retorna la lista de todas las ciudades registradas."""
        return list(self.cities.values())

    def get_edges(self) -> list[dict]:
        """Retorna la lista de todas las aristas registradas."""
        edges = []
        for from_id in self.adj:
            for to_id, edge in self.adj[from_id].items():
                edges.append(dict(edge))
        return edges

    def get_neighbors(self, city_id: str) -> list[dict]:
        """Retorna los vecinos salientes de una ciudad."""
        if city_id not in self.adj:
            return []
        return list(self.adj[city_id].values())

    def is_connected(self) -> bool:
        """Verifica mediante BFS si todos los nodos activos están fuertemente conectados."""
        active_cities = [cid for cid, c in self.cities.items() if c.get("active", True)]
        if len(active_cities) <= 1:
            return True

        for start in active_cities:
            visited = {start}
            queue = collections.deque([start])
            while queue:
                curr = queue.popleft()
                for nxt in self.adj.get(curr, {}):
                    if self.cities.get(nxt, {}).get("active", True) and nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            if len(visited) != len(active_cities):
                return False

        return True

    def shortest_path(self, origin: str, destination: str, weight: str) -> dict | None:
        """
        Encuentra el camino más corto entre origin y destination minimizando el criterio weight
        utilizando el algoritmo de Dijkstra. Ignora ciudades inactivas.
        """
        if origin not in self.cities or destination not in self.cities:
            return None
        if not self.cities[origin].get("active", True) or not self.cities[destination].get("active", True):
            return None

        if origin == destination:
            return {
                "path": [origin],
                "total_distance_km": 0.0,
                "total_time_hours": 0.0,
                "total_toll_cop": 0.0,
                "total_fuel_cop": 0.0,
                "weight_used": weight,
                "total_weight": 0.0
            }

        pq = [(0.0, origin, [origin])]
        visited = {}

        while pq:
            cost, curr, path = heapq.heappop(pq)

            if curr in visited and visited[curr] <= cost:
                continue
            visited[curr] = cost

            if curr == destination:
                total_distance = 0.0
                total_time = 0.0
                total_toll = 0.0
                total_fuel = 0.0

                for i in range(len(path) - 1):
                    edge = self.adj[path[i]][path[i + 1]]
                    total_distance += edge["distance_km"]
                    total_time += edge["time_hours"]
                    total_toll += edge["toll_cost_cop"]
                    total_fuel += edge["fuel_cost_cop"]

                return {
                    "path": path,
                    "total_distance_km": round(total_distance, 2),
                    "total_time_hours": round(total_time, 2),
                    "total_toll_cop": round(total_toll, 2),
                    "total_fuel_cop": round(total_fuel, 2),
                    "weight_used": weight,
                    "total_weight": round(cost, 2)
                }

            for nxt, edge in self.adj.get(curr, {}).items():
                if not edge.get("active", True):
                    continue
                if not self.cities.get(nxt, {}).get("active", True):
                    continue

                step_cost = edge.get(weight, 0.0)
                new_cost = cost + step_cost

                if nxt not in visited or new_cost < visited[nxt]:
                    heapq.heappush(pq, (new_cost, nxt, path + [nxt]))

        return None

    def shortest_path_combined(self, origin: str, destination: str, weights: dict = None) -> dict | None:
        """
        Calcula la ruta óptima ponderando múltiples criterios normalizados con min-max:
        weights = {"distance_km": 0.25, "time_hours": 0.25, "toll_cost_cop": 0.25, "fuel_cost_cop": 0.25}
        """
        if origin not in self.cities or destination not in self.cities:
            return None
        if not self.cities[origin].get("active", True) or not self.cities[destination].get("active", True):
            return None

        if weights is None:
            weights = {
                "distance_km": 0.25,
                "time_hours": 0.25,
                "toll_cost_cop": 0.25,
                "fuel_cost_cop": 0.25
            }

        all_edges = self.get_edges()
        if not all_edges:
            return None

        min_max = {}
        for criterion in weights:
            values = [e[criterion] for e in all_edges if criterion in e]
            if values:
                min_max[criterion] = (min(values), max(values))
            else:
                min_max[criterion] = (0.0, 1.0)

        def get_edge_combined_cost(edge_dict):
            cost = 0.0
            for crit, weight_factor in weights.items():
                val = edge_dict.get(crit, 0.0)
                c_min, c_max = min_max.get(crit, (0.0, 1.0))
                denom = c_max - c_min if c_max > c_min else 1.0
                norm_val = (val - c_min) / denom
                cost += weight_factor * norm_val
            return cost

        if origin == destination:
            return {
                "path": [origin],
                "total_distance_km": 0.0,
                "total_time_hours": 0.0,
                "total_toll_cop": 0.0,
                "total_fuel_cop": 0.0,
                "weight_used": "combined",
                "total_weight": 0.0,
                "total_combined_cost": 0.0
            }

        pq = [(0.0, origin, [origin])]
        visited = {}

        while pq:
            cost, curr, path = heapq.heappop(pq)

            if curr in visited and visited[curr] <= cost:
                continue
            visited[curr] = cost

            if curr == destination:
                total_distance = 0.0
                total_time = 0.0
                total_toll = 0.0
                total_fuel = 0.0

                for i in range(len(path) - 1):
                    edge = self.adj[path[i]][path[i + 1]]
                    total_distance += edge["distance_km"]
                    total_time += edge["time_hours"]
                    total_toll += edge["toll_cost_cop"]
                    total_fuel += edge["fuel_cost_cop"]

                combined_cost = round(cost, 4)
                return {
                    "path": path,
                    "total_distance_km": round(total_distance, 2),
                    "total_time_hours": round(total_time, 2),
                    "total_toll_cop": round(total_toll, 2),
                    "total_fuel_cop": round(total_fuel, 2),
                    "weight_used": "combined",
                    "total_weight": combined_cost,
                    "total_combined_cost": combined_cost
                }

            for nxt, edge in self.adj.get(curr, {}).items():
                if not edge.get("active", True):
                    continue
                if not self.cities.get(nxt, {}).get("active", True):
                    continue

                step_cost = get_edge_combined_cost(edge)
                new_cost = cost + step_cost

                if nxt not in visited or new_cost < visited[nxt]:
                    heapq.heappush(pq, (new_cost, nxt, path + [nxt]))

        return None


def save_graph(graph: Graph, filepath: str) -> bool:
    """
    Serializa el grafo a formato JSON con la misma estructura requerida,
    incluyendo metadatos, precio de combustible y respaldo .bak previo.
    """
    import datetime
    import shutil

    resolved_path = filepath
    if not os.path.isabs(resolved_path) and not os.path.exists(resolved_path):
        candidate = os.path.join(os.path.dirname(__file__), filepath)
        if os.path.exists(os.path.dirname(candidate)):
            resolved_path = candidate

    try:
        if os.path.exists(resolved_path):
            backup_path = resolved_path + ".bak"
            shutil.copyfile(resolved_path, backup_path)

        cities_data = []
        for city in graph.get_cities():
            cities_data.append({
                "id": city["id"],
                "name": city["name"],
                "lat": city["lat"],
                "lon": city["lon"],
                "department": city.get("department", "N/A"),
                "fuel_price_cop": city["fuel_price_cop"],
                "active": city.get("active", True)
            })

        edges_data = []
        for edge in graph.get_edges():
            edges_data.append({
                "from": edge["from"],
                "to": edge["to"],
                "distance_km": edge["distance_km"],
                "time_hours": edge["time_hours"],
                "toll_cost_cop": edge["toll_cost_cop"],
                "fuel_cost_cop": edge["fuel_cost_cop"]
                ,"active": edge.get("active", True), "category": edge.get("category", "Primaria"),
                "validated": edge.get("validated", True), "source": edge.get("source", "Google Maps"),
                "researcher": edge.get("researcher", "Grupo UPC")
            })

        payload = {
            "_meta": {
                "description": "Rutas terrestres entre 12 capitales de Colombia - PERA Parcial 3",
                "saved_at": datetime.datetime.now().isoformat(),
                "directed": graph.directed,
                "graphs": ["distance", "toll", "fuel"],
                "assumptions": {
                    "km_per_gallon": 35,
                    "fuel_price_source": "CREG nov 2026, gasolina corriente por ciudad"
                }
            },
            "cities": cities_data,
            "edges": edges_data
        }

        with open(resolved_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return True
    except Exception:
        return False


if __name__ == "__main__":
    g = Graph(directed=True)
    assert g.load_from_json("graph_data.json") is True
    print("Ciudades:", len(g.get_cities()))  # 12
    print("Aristas:", len(g.get_edges()))    # 38
    assert len(g.get_cities()) == 12
    assert len(g.get_edges()) == 38
    assert g.is_connected() is True

    r = g.shortest_path("BOG", "CTG", "distance_km")
    print("Distancia BOG->CTG:", r)

    r = g.shortest_path("BOG", "CTG", "toll_cost_cop")
    print("Peaje BOG->CTG:", r)

    r = g.shortest_path("BOG", "CTG", "fuel_cost_cop")
    print("Combustible BOG->CTG:", r)

    r = g.shortest_path_combined("BOG", "CTG")
    print("Combinada BOG->CTG:", r)

    g.deactivate_city("MDE")
    r2 = g.shortest_path("BOG", "CTG", "distance_km")
    print("Sin MDE:", r2)
    assert "MDE" not in r2["path"]

    print("OK graph.py")
