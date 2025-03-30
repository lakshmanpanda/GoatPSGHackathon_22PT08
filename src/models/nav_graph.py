import json
from typing import Dict, List, Tuple, Optional
from ..utils.helpers import dijkstra

class NavGraph:
    def __init__(self, file_path: str):
        self.vertices: Dict[str, Dict] = {}
        self.edges: Dict[str, List[str]] = {}
        self.charging_stations: List[str] = []
        self.load_graph(file_path)

    def load_graph(self, file_path: str):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            level_data = next(iter(data['levels'].values()))

            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')

            for vertex in level_data['vertices']:
                x, y, _ = vertex
                min_x = min(min_x, float(x))
                max_x = max(max_x, float(x))
                min_y = min(min_y, float(y))
                max_y = max(max_y, float(y))

            scale_x = 700 / (max_x - min_x)
            scale_y = 500 / (max_y - min_y)
            scale = min(scale_x, scale_y)

            offset_x = (800 - (max_x - min_x) * scale) / 2
            offset_y = (600 - (max_y - min_y) * scale) / 2

            for i, vertex in enumerate(level_data['vertices']):
                x, y, info = vertex
                vertex_id = str(i)
                scaled_x = (float(x) - min_x) * scale + offset_x
                scaled_y = (float(y) - min_y) * scale + offset_y

                self.vertices[vertex_id] = {
                    'x': scaled_x,
                    'y': scaled_y,
                    'name': info.get('name', ''),
                    'is_charger': info.get('is_charger', False)
                }

                if info.get('is_charger', False):
                    self.charging_stations.append(vertex_id)

            for lane in level_data['lanes']:
                from_id, to_id, _ = lane
                from_id, to_id = str(from_id), str(to_id)

                if from_id not in self.edges:
                    self.edges[from_id] = []
                if to_id not in self.edges:
                    self.edges[to_id] = []

                self.edges[from_id].append(to_id)
                self.edges[to_id].append(from_id)

        except Exception as e:
            print(f"Error loading navigation graph: {e}")
            raise

    def get_vertex_coordinates(self, vertex_id: str) -> Dict[str, float]:
        if vertex_id not in self.vertices:
            raise ValueError(f"Vertex {vertex_id} not found in graph")
        return {'x': self.vertices[vertex_id]['x'], 'y': self.vertices[vertex_id]['y']}

    def get_vertex_name(self, vertex_id: str) -> str:
        if vertex_id not in self.vertices:
            raise ValueError(f"Vertex {vertex_id} not found in graph")
        return self.vertices[vertex_id]['name']

    def get_adjacent_vertices(self, vertex_id: str) -> List[str]:
        return self.edges.get(vertex_id, [])

    def find_path(self, start: str, target: str) -> List[str]:
        return dijkstra(self.edges, start, target)

    def is_charging_station(self, vertex_id: str) -> bool:
        return vertex_id in self.charging_stations

    def get_charging_stations(self) -> List[str]:
        return self.charging_stations

    def get_nearest_charging_station(self, vertex_id: str) -> Optional[str]:
        if not self.charging_stations:
            return None

        min_distance = float('inf')
        nearest = None

        for station in self.charging_stations:
            path = self.find_path(vertex_id, station)
            if path and len(path) < min_distance:
                min_distance = len(path)
                nearest = station

        return nearest

    def draw_graph(self, canvas):
        for vertex_id, adjacents in self.edges.items():
            start_coords = self.get_vertex_coordinates(vertex_id)
            for adj_id in adjacents:
                end_coords = self.get_vertex_coordinates(adj_id)
                canvas.create_line(
                    start_coords['x'], start_coords['y'],
                    end_coords['x'], end_coords['y'],
                    fill='gray', width=1
                )

        for vertex_id, info in self.vertices.items():
            x, y = info['x'], info['y']
            color = 'green' if self.is_charging_station(vertex_id) else 'blue'
            canvas.create_oval(x-5, y-5, x+5, y+5, fill=color)

            if info['name']:
                canvas.create_text(x, y-10, text=info['name'], font=('Arial', 8))

    def get_path_length(self, path: List[str]) -> int:
        return len(path) - 1 if path else 0

    def is_path_feasible(self, start: str, target: str, current_battery: int) -> Tuple[bool, str]:
        path = self.find_path(start, target)
        if not path:
            return False, "No path found to destination"

        path_length = self.get_path_length(path)
        if path_length * 5 > current_battery:
            return False, f"Not enough battery to reach destination (needs {path_length * 5}%, has {current_battery}%)"

        remaining_battery = current_battery - (path_length * 5)
        nearest_charger = self.get_nearest_charging_station(target)
        if not nearest_charger:
            return False, "No charging station available"

        charger_path = self.find_path(target, nearest_charger)
        if not charger_path:
            return False, "No path found to charging station"

        charger_path_length = self.get_path_length(charger_path)
        if charger_path_length * 5 > remaining_battery:
            return False, f"Not enough battery to reach charging station after destination (needs {charger_path_length * 5}%, will have {remaining_battery}%)"

        return True, "Path is feasible"

if __name__ == "__main__":
    nav_graph = NavGraph("data/nav_graph_1.json")
    print(nav_graph.get_adjacent_vertices("0"))
