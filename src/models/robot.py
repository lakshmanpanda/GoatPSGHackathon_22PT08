import time
from datetime import datetime

class Robot:
    def __init__(self, robot_id, start_node):
        self.id = robot_id
        self.current_node = start_node
        self.target_node = None
        self.path = []
        self.status = "IDLE"
        self.battery_level = 100
        self.wait_start_time = None
        self.charging_start_time = None
        self.log_entries = []
        self.movement_speed = 1
        self.last_move_time = time.time()
        self.battery_consumption_rate = 5
        self.charging_rate = 20

    def assign_task(self, target_node, path):
        self.target_node = target_node
        self.path = path
        self.status = "MOVING"
        self.log(f"Assigned task to move to {target_node}")
        self.wait_start_time = None

    def move_next(self, traffic_manager):
        current_time = time.time()
        if current_time - self.last_move_time < 1.0 / self.movement_speed:
            return

        if not self.path:
            self.status = "IDLE"
            self.target_node = None
            self.log("Task completed")
            return
        
        next_node = self.path[0]

        if not traffic_manager.can_robot_move_to(self, next_node):
            self.status = "WAITING"
            if not self.wait_start_time:
                self.wait_start_time = time.time()
                self.log(f"Waiting at {self.current_node} - Node {next_node} is occupied")
            return
            
        old_node = self.current_node
        old_battery = self.battery_level

        self.current_node = self.path.pop(0)
        self.last_move_time = current_time

        if old_node != self.current_node:
            self.battery_level = max(0, self.battery_level - self.battery_consumption_rate)
            self.log(f"Moved from {old_node} to {self.current_node} (Battery: {old_battery}% -> {self.battery_level}%)")

        if hasattr(self, 'nav_graph') and self.nav_graph.is_charging_station(self.current_node):
            remaining_path_length = len(self.path)
            battery_needed = remaining_path_length * self.battery_consumption_rate

            nearest_charger = self.nav_graph.get_nearest_charging_station(self.target_node)
            if nearest_charger:
                charger_path = self.nav_graph.find_path(self.target_node, nearest_charger)
                if charger_path:
                    charger_path_length = len(charger_path) - 1
                    battery_needed += charger_path_length * self.battery_consumption_rate

                    if self.battery_level - battery_needed <= 20:
                        if self.path and self.target_node:
                            self.original_path = self.path.copy()
                            self.original_target = self.target_node
                        self.start_charging(self.nav_graph)
                        self.log(f"Need to charge: Will need {battery_needed}%, will have {self.battery_level - battery_needed}% after destination")
                        return
        
        if not self.path:
            self.status = "IDLE"
            self.target_node = None
            self.log("Task completed")

    def start_charging(self, nav_graph):
        if nav_graph.is_charging_station(self.current_node):
            self.status = "CHARGING"
            self.charging_start_time = time.time()
            self.log("Started charging at charging station")
            return True
        else:
            self.log("Cannot charge here - not a charging station")
            return False

    def stop_charging(self):
        self.status = "IDLE"
        self.battery_level = 100
        self.charging_start_time = None
        self.log("Finished charging")
        
        if hasattr(self, 'original_path') and hasattr(self, 'original_target'):
            self.path = self.original_path
            self.target_node = self.original_target
            self.status = "MOVING"
            self.log("Resuming original task after charging")
            delattr(self, 'original_path')
            delattr(self, 'original_target')

    def update_charging(self):
        if self.status == "CHARGING":
            current_time = time.time()
            if current_time - self.charging_start_time >= 0.1:
                self.battery_level = min(100, self.battery_level + self.charging_rate)
                self.charging_start_time = current_time
                if self.battery_level >= 100:
                    self.stop_charging()

    def is_idle(self):
        return self.status == "IDLE"

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Robot {self.id}: {message}"
        self.log_entries.append(log_entry)
        return log_entry

    def __str__(self):
        return f"Robot {self.id} at {self.current_node}, Status: {self.status}, Battery: {self.battery_level}%"

if __name__ == "__main__":
    robot = Robot(1, "A")
    robot.assign_task("E", ["B", "E"])
    while not robot.is_idle():
        print(robot)
        robot.move_next()
