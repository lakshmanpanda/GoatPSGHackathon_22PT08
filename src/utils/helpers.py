import heapq

def dijkstra(graph, start, target):
    """Finds the shortest path using Dijkstra's Algorithm."""
    if start not in graph or target not in graph:
        return []
        
    queue = [(0, start)]
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous_nodes = {node: None for node in graph}
    visited = set()

    while queue:
        current_distance, current_node = heapq.heappop(queue)
        
        if current_node in visited:
            continue
            
        visited.add(current_node)

        if current_node == target:
            path = []
            while current_node:
                path.insert(0, current_node)
                current_node = previous_nodes[current_node]
            return path

        for neighbor in graph[current_node]:
            if neighbor in visited:
                continue
                
            distance = current_distance + 1
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(queue, (distance, neighbor))

    return []

if __name__ == "__main__":
    sample_graph = {
        "A": ["B", "C"],
        "B": ["A", "D", "E"],
        "C": ["A", "D"],
        "D": ["B", "C", "E"],
        "E": ["B", "D"]
    }

    print(dijkstra(sample_graph, "A", "E"))
