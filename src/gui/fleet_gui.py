import tkinter as tk
from tkinter import ttk, messagebox
import math
from ..controllers.fleet_manager import FleetManager
from ..models.nav_graph import NavGraph

class FleetManagementGUI:
    def __init__(self, root, nav_graph_path):
        self.root = root
        self.root.title("Fleet Management System")

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.main_frame, width=800, height=600, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.clear_button = ttk.Button(control_frame, text="Clear Selection", command=self.clear_selection)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(control_frame, text="Delete Selected Robot", command=self.delete_selected_robot)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        scrollbar = ttk.Scrollbar(status_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_text = tk.Text(status_frame, width=40, height=30, yscrollcommand=scrollbar.set)
        self.status_text.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.config(command=self.status_text.yview)

        self.nav_graph = NavGraph(nav_graph_path)
        self.fleet_manager = FleetManager(self.nav_graph)
        self.selected_robot = None

        self.canvas.bind("<Button-1>", self.handle_click)
        self.draw_graph()
        self.start_simulation()

    def draw_graph(self):
        self.canvas.delete("all")
        for node, neighbors in self.nav_graph.edges.items():
            x1, y1 = self.nav_graph.get_vertex_coordinates(node).values()
            for neighbor in neighbors:
                x2, y2 = self.nav_graph.get_vertex_coordinates(neighbor).values()
                self.canvas.create_line(x1, y1, x2, y2, fill="gray", width=2)

        for node, coords in self.nav_graph.vertices.items():
            x, y = coords['x'], coords['y']
            color = "green" if self.nav_graph.is_charging_station(node) else "blue"
            self.canvas.create_oval(x-10, y-10, x+10, y+10, fill=color)
            label = coords.get('name', node)
            self.canvas.create_text(x, y-15, text=label, font=("Arial", 10, "bold"))

        self.draw_robots()

    def draw_robots(self):
        self.canvas.delete("robot")
        for robot in self.fleet_manager.robots.values():
            x, y = self.nav_graph.get_vertex_coordinates(robot.current_node).values()
            color = "red" if robot.id == self.selected_robot else "orange"
            self.canvas.create_oval(x-8, y-8, x+8, y+8, fill=color, tags="robot")
            self.canvas.create_rectangle(x-12, y-20, x+12, y-12, fill="white", tags="robot")
            self.canvas.create_text(x, y-16, text=str(robot.id), font=("Arial", 8, "bold"), tags="robot")

            status_color = {"IDLE": "green", "MOVING": "blue", "WAITING": "orange", "CHARGING": "purple"}.get(robot.status, "black")
            self.canvas.create_text(x, y+15, text=robot.status, font=("Arial", 8), fill=status_color, tags="robot")

            if robot.id == self.selected_robot:
                self.canvas.create_oval(x-12, y-12, x+12, y+12, outline="red", width=2, tags="robot")

    def handle_click(self, event):
        clicked_robot = None
        for robot in self.fleet_manager.robots.values():
            x, y = self.nav_graph.get_vertex_coordinates(robot.current_node).values()
            if math.dist((x, y), (event.x, event.y)) < 8:
                clicked_robot = robot
                break

        if clicked_robot:
            self.selected_robot = clicked_robot.id
        else:
            clicked_vertex = None
            for vertex_id, coords in self.nav_graph.vertices.items():
                x, y = coords['x'], coords['y']
                if math.dist((x, y), (event.x, event.y)) < 20:
                    clicked_vertex = vertex_id
                    break

            if clicked_vertex:
                if self.selected_robot is None:
                    if any(robot.current_node == clicked_vertex for robot in self.fleet_manager.robots.values()):
                        messagebox.showerror("Error", "Cannot spawn robot at an occupied node!")
                        return
                    self.selected_robot = self.fleet_manager.add_robot(clicked_vertex)
                else:
                    if self.fleet_manager.assign_task(self.selected_robot, clicked_vertex):
                        self.selected_robot = None
                    else:
                        messagebox.showerror("Error", "Cannot assign task to robot!")

        self.draw_robots()
        self.update_status()

    def clear_selection(self):
        self.selected_robot = None
        self.draw_robots()
        self.update_status()

    def delete_selected_robot(self):
        if self.selected_robot is None:
            messagebox.showwarning("Warning", "No robot selected!")
            return

        if messagebox.askyesno("Confirm", f"Delete Robot {self.selected_robot}?"):
            if self.selected_robot in self.fleet_manager.robots:
                del self.fleet_manager.robots[self.selected_robot]
                self.selected_robot = None
                self.draw_robots()
                self.update_status()
                messagebox.showinfo("Success", "Robot deleted successfully!")
            else:
                messagebox.showerror("Error", "Robot not found!")

    def update_status(self):
        self.status_text.delete(1.0, tk.END)
        for robot in self.fleet_manager.robots.values():
            self.status_text.insert(tk.END, f"{robot}\n")
        self.status_text.see(tk.END)

    def start_simulation(self):
        def update():
            self.fleet_manager.update_fleet()
            self.draw_robots()
            self.update_status()
            self.root.after(50, update)
        update()

if __name__ == "__main__":
    root = tk.Tk()
    app = FleetManagementGUI(root, "data/nav_graph.json")
    root.mainloop()
