from ..models.robot import Robot
from ..utils.helpers import dijkstra
from .traffic_manager import TrafficManager
import time

class FleetManager:
    def __init__(self, nav_graph):
        self.robots = {}
        self.nav_graph = nav_graph
        self.traffic_manager = TrafficManager(self)
        self.next_robot_id = 1

    def add_robot(self, start_node):
        robot_id = self.next_robot_id
        self.next_robot_id += 1
        robot = Robot(robot_id, start_node)
        robot.nav_graph = self.nav_graph  
        self.robots[robot_id] = robot
        print(f"Robot {robot_id} added at {start_node}")
        return robot_id

    def assign_task(self, robot_id: str, target_node: str) -> bool:
        if robot_id not in self.robots:
            return False

        robot = self.robots[robot_id]
        is_feasible, reason = self.nav_graph.is_path_feasible(robot.current_node, target_node, robot.battery_level)

        if not is_feasible:
            charger = self.nav_graph.get_nearest_charging_station(robot.current_node)
            if charger:
                path = self.nav_graph.find_path(robot.current_node, charger)
                if path:
                    robot.original_target = target_node
                    robot.original_path = self.nav_graph.find_path(charger, target_node)
                    robot.assign_task(charger, path)
                    robot.log(f"Cannot complete task: {reason}. Heading to charging station first.")
                    return True
            else:
                robot.log(f"Cannot complete task: {reason}. No charging station available.")
                return False

        path = self.nav_graph.find_path(robot.current_node, target_node)
        if path:
            path_length = len(path) - 1
            expected_battery = robot.battery_level
            robot.assign_task(target_node, path)
            robot.log(f"Task assigned. Current battery: {robot.battery_level}%, Path length: {path_length}, Battery needed: {path_length * 5}%")
            return True

        return False

    def update_fleet(self):
        self.traffic_manager.update_traffic()

        for robot in self.robots.values():
            robot.update_charging()

            if robot.status == "CHARGING":
                if robot.battery_level >= 100:
                    robot.stop_charging()
                    if hasattr(robot, 'original_target') and robot.original_target:
                        robot.assign_task(robot.original_target, robot.original_path)
                        robot.log("Resuming original task after charging")
                        delattr(robot, 'original_target')
                        delattr(robot, 'original_path')
                continue

            if robot.status == "MOVING" or robot.status == "WAITING":
                robot.move_next(self.traffic_manager)

if __name__ == "__main__":
    from ..models.nav_graph import NavGraph

    nav_graph = NavGraph("data/nav_graph.json")
    fleet_manager = FleetManager(nav_graph)

    fleet_manager.add_robot("A")
    fleet_manager.assign_task(1, "E")

    while any(not robot.is_idle() for robot in fleet_manager.robots.values()):
        fleet_manager.update_fleet()
