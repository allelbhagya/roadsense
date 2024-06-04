import csv
import random

def load_pems_data(file_path, sample_size=100):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        data = [(int(row['from']), int(row['to']), float(row['cost'])) for row in reader]
    sampled_edges = random.sample(data, sample_size)
    nodes = {node for edge in sampled_edges for node in edge[:2]}
    node_positions = {node: (random.randint(50, 350), random.randint(50, 350)) for node in nodes}

    return node_positions, sampled_edges

node_positions, edges = load_pems_data('./data/PEMS08/PEMS08.csv', sample_size=100)

import tkinter as tk
import random
import math

class CarMovementApp(tk.Tk):
    def __init__(self, node_positions, edges):
        super().__init__()
        self.title("Car Movement")
        self.geometry("600x600") 
        self.node_positions = self.scale_positions(node_positions, 600, 600)
        self.edges = edges
        self.current_node = random.choice(list(self.node_positions.keys()))
        self.total_cost = 0
        self.current_cost = 0
        self.current_position = self.node_positions[self.current_node]
        self.target_node = None
        self.car = None
        self.timer = None
        self.create_widgets()
        self.bind("<KeyPress>", self.on_key_press)
        self.anomaly_threshold = 5 
        self.edge_costs = {edge: 0 for edge in self.edges} 
        self.anomaly_message = tk.Label(self, text="Status: Normal")
        self.anomaly_message.pack()

    def scale_positions(self, positions, width, height):
        """Scale node positions to fit within the given width and height."""
        max_x = max(pos[0] for pos in positions.values())
        max_y = max(pos[1] for pos in positions.values())
        scale_x = (width - 50) / max_x
        scale_y = (height - 50) / max_y
        scaled_positions = {node: (x * scale_x + 25, y * scale_y + 25) for node, (x, y) in positions.items()}
        return scaled_positions

    def create_widgets(self):
        self.canvas = tk.Canvas(self, width=600, height=600) 
        self.canvas.pack()

        self.current_cost_label = tk.Label(self, text=f"Current Cost: {self.current_cost:.3f}")
        self.current_cost_label.pack()

        self.draw_graph()

    def draw_graph(self):
        self.canvas.delete("all")
        for (node, (x, y)) in self.node_positions.items():
            self.canvas.create_oval(x-15, y-15, x+15, y+15, fill="lightblue")
            self.canvas.create_text(x, y-25, text=str(node))

        for (from_node, to_node, _) in self.edges:
            x1, y1 = self.node_positions[from_node]
            x2, y2 = self.node_positions[to_node]
            self.canvas.create_line(x1, y1, x2, y2)

        if self.car is None:
            x, y = self.current_position
            self.car = self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red")

    def on_key_press(self, event):
        direction = {'Up': (0, -1), 'Down': (0, 1), 'Left': (-1, 0), 'Right': (1, 0)}
        if event.keysym in direction:
            dx, dy = direction[event.keysym]
            self.move_car(dx, dy)
            if self.current_node != self.target_node:  
                self.start_timer()

    def start_timer(self):
        if self.timer is None:
            self.timer = self.after(100, self.update_current_cost)

    def update_current_cost(self):
        if self.current_node != self.target_node:
            if not self.is_inside_node(self.current_position):
                self.current_cost += 0.1
                self.total_cost += 0.1
                self.current_cost_label.config(text=f"Current Cost: {self.current_cost:.3f}")

                edge = self.get_edge_from_nodes(self.current_node, self.target_node)
                if edge and self.current_cost >= self.anomaly_threshold:
                    self.edge_costs[edge] += 1 
                    self.check_anomaly(edge)
        else:
            if self.is_inside_node(self.current_position): 
                self.current_cost = 0 
                self.current_cost_label.config(text=f"Current Cost: {self.current_cost:.3f}")
            else:
                self.current_cost = 0 
                self.current_cost_label.config(text=f"Current Cost: {self.current_cost:.3f}")
                
        if self.current_cost >= self.anomaly_threshold: 
            self.after_cancel(self.timer) 
            self.timer = None
            self.anomaly_message.config(text="Status: Anomaly Detected!")
        else:
            self.timer = self.after(100, self.update_current_cost)

    def move_car(self, dx, dy):
        step_size = 5
        prev_x, prev_y = self.current_position
        new_x = prev_x + dx * step_size
        new_y = prev_y + dy * step_size
        if self.is_valid_move(new_x, new_y) and self.is_on_path(new_x, new_y):
            self.current_position = (new_x, new_y)
            self.canvas.coords(self.car, new_x - 5, new_y - 5, new_x + 5, new_y + 5)
            for node, (nx, ny) in self.node_positions.items():
                if math.isclose(new_x, nx, abs_tol=10) and math.isclose(new_y, ny, abs_tol=10):
                    self.current_node = node
                    if node in self.node_positions.keys(): 
                        self.current_cost = 0 
                        self.current_cost_label.config(text=f"Current Cost: {self.current_cost:.3f}")
                        self.anomaly_message.config(text="Status: Normal")
                    break

    def is_valid_move(self, x, y):
        return 0 <= x <= 800 and 0 <= y <= 800

    def is_inside_node(self, position):
        x, y = position
        for (node, (nx, ny)) in self.node_positions.items():
            if nx - 15 <= x <= nx + 15 and ny - 15 <= y <= ny + 15:
                return True
        return False

    def is_on_path(self, x, y):
        for (from_node, to_node, _) in self.edges:
            x1, y1 = self.node_positions[from_node]
            x2, y2 = self.node_positions[to_node]
            if self.is_point_on_line(x, y, x1, y1, x2, y2):
                return True
        return False

    def is_point_on_line(self, px, py, x1, y1, x2, y2):
        tolerance = 10 
        dist = abs((y2-y1)*px - (x2-x1)*py + x2*y1 - y2*x1) / math.sqrt((y2-y1)**2 + (x2-x1)**2)
        return dist <= tolerance and min(x1, x2) <= px <= max(x1, x2) and min(y1, y2) <= py <= max(y1, y2)

    def get_edges(self):
        return self.edges

    def get_edge_from_nodes(self, node1, node2):
        for (from_node, to_node, cost) in self.edges:
            if (node1 == from_node and node2 == to_node) or (node1 == to_node and node2 == from_node):
                return (from_node, to_node)
        return None

    def check_anomaly(self, edge):
        if self.edge_costs[edge] > self.anomaly_threshold:
            self.anomaly_message.config(text="Status: Anomaly Detected!")
        else:
            self.anomaly_message.config(text="Status: Normal")

def load_pems_data(file_path, sample_size):
    node_positions = {
        i: (random.randint(0, 100), random.randint(0, 100))
        for i in range(sample_size)
    }
    edges = [
        (random.randint(0, sample_size - 1), random.randint(0, sample_size - 1), random.uniform(1, 10))
        for _ in range(sample_size * 2)
    ]
    return node_positions, edges

node_positions, edges = load_pems_data('./data/PEMS08/PEMS08.csv', sample_size=40)

app = CarMovementApp(node_positions, edges)
app.mainloop()
