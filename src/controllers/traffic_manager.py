from datetime import datetime
import os
import time

class TrafficManager:
    def __init__(self, fleet_manager):
        self.fleet_manager = fleet_manager
        self.occupied_nodes = {}
        self.occupied_lanes = {}
        self.log_file = "src/logs/fleet_logs.txt"
        self.last_warning_time = {}
        self.last_step_time = {}
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def can_robot_move_to(self, robot, next_node):
        current_node = robot.current_node
        if next_node in self.occupied_nodes and self.occupied_nodes[next_node] != robot.id:
            return False
        lane = tuple(sorted([current_node, next_node]))
        if lane in self.occupied_lanes and self.occupied_lanes[lane] != robot.id:
            return False
        return True

    def update_traffic(self):
        current_time = time.time()
        self.occupied_nodes = {}
        self.occupied_lanes = {}

        for robot in self.fleet_manager.robots.values():
            self.log_robot_step(robot, current_time)
            if robot.current_node in self.occupied_nodes:
                warning_key = (robot.current_node, robot.id)
                last_warning = self.last_warning_time.get(warning_key, 0)
                if current_time - last_warning >= 1.0:
                    self.log_robot_state(robot)
                    self.log_robot_state(self.fleet_manager.robots[self.occupied_nodes[robot.current_node]])
                    print(f"WARNING: Multiple robots at node {robot.current_node}")
                    self.last_warning_time[warning_key] = current_time
            self.occupied_nodes[robot.current_node] = robot.id

            if robot.status == "MOVING" and robot.path:
                next_node = robot.path[0]
                lane = tuple(sorted([robot.current_node, next_node]))
                if lane in self.occupied_lanes and self.occupied_lanes[lane] != robot.id:
                    warning_key = (lane, robot.id)
                    last_warning = self.last_warning_time.get(warning_key, 0)
                    if current_time - last_warning >= 1.0:
                        self.log_robot_state(robot)
                        self.log_robot_state(self.fleet_manager.robots[self.occupied_lanes[lane]])
                        print(f"WARNING: Multiple robots on lane {lane}")
                        self.last_warning_time[warning_key] = current_time
                self.occupied_lanes[lane] = robot.id

    def log_robot_step(self, robot, current_time):
        last_step = self.last_step_time.get(robot.id, 0)
        if current_time - last_step < 1.0:
            return

        self.last_step_time[robot.id] = current_time
        state_key = f"{robot.current_node}_{robot.status}"
        if hasattr(self, 'last_state') and state_key == self.last_state.get(robot.id):
            return

        if not hasattr(self, 'last_state'):
            self.last_state = {}
        self.last_state[robot.id] = state_key

        step_info = f"\n[Robot {robot.id}]\n  Location: {robot.current_node}\n  Status: {robot.status}\n  Battery: {robot.battery_level}%"
        
        if robot.status == "MOVING" and robot.path:
            step_info += f"\n  Next Node: {robot.path[0]}\n  Path: {robot.current_node} -> {' -> '.join(robot.path)}"
            battery_needed = len(robot.path) * robot.battery_consumption_rate
            step_info += f"\n  Battery needed for path: {battery_needed}%"
        elif robot.status == "CHARGING":
            step_info += f"\n  Charging at: {robot.current_node}"
        elif robot.status == "WAITING":
            step_info += f"\n  Waiting at: {robot.current_node}"
        elif robot.status == "IDLE":
            step_info += f"\n  Idle at: {robot.current_node}"

        if hasattr(robot, 'target_node') and robot.target_node:
            step_info += f"\n  Final Target: {robot.target_node}"

        print(step_info)
        with open(self.log_file, 'a') as f:
            f.write(step_info + '\n')

    def log_robot_state(self, robot):
        with open(self.log_file, 'a') as f:
            for entry in robot.log_entries:
                f.write(entry + '\n')
            robot.log_entries.clear()

    def get_robot_at_node(self, node):
        return self.occupied_nodes.get(node)

    def get_robot_on_lane(self, node1, node2):
        lane = tuple(sorted([node1, node2]))
        return self.occupied_lanes.get(lane)

if __name__ == "__main__":
    from src.models.nav_graph import NavGraph
    from src.controllers.fleet_manager import FleetManager

    nav_graph = NavGraph("data/nav_graph.json")
    fleet_manager = FleetManager(nav_graph)
    traffic_manager = TrafficManager(fleet_manager)

    fleet_manager.add_robot(1, "A")
    fleet_manager.add_robot(2, "B")
    fleet_manager.assign_task(1, "E")
    fleet_manager.assign_task(2, "D")

    while any(not robot.is_idle() for robot in fleet_manager.robots.values()):
        traffic_manager.update_traffic()
        fleet_manager.update_fleet()
