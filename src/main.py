import tkinter as tk
import sys
from src.gui.fleet_gui import FleetManagementGUI

def main():
    if len(sys.argv) > 1:
        graph_file = sys.argv[1]
        if graph_file not in ["nav_graph_1.json", "nav_graph_2.json", "nav_graph_3.json"]:
            print("Invalid graph file. Using nav_graph_1.json")
            graph_file = "nav_graph_1.json"
    else:
        graph_file = "nav_graph_1.json"
    
    print(f"Using navigation graph: {graph_file}")
    root = tk.Tk()
    app = FleetManagementGUI(root, f"data/{graph_file}")
    app.start_simulation()
    root.mainloop()

if __name__ == "__main__":
    main()
