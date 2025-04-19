
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict
import itertools

app = FastAPI()

# Assumptions
PRODUCTS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
WAREHOUSES = ["C1", "C2", "C3"]

# Warehouse product availability
WAREHOUSE_STOCK = {
    "C1": {"A", "B", "D", "E"},
    "C2": {"C", "F", "G"},
    "C3": {"H", "I"}
}

# Cost matrix (per trip)
COST_MATRIX = {
    ("C1", "L1"): 20, ("L1", "C1"): 20,
    ("C2", "L1"): 30, ("L1", "C2"): 30,
    ("C3", "L1"): 40, ("L1", "C3"): 40,
    ("C1", "C2"): 15, ("C2", "C1"): 15,
    ("C1", "C3"): 25, ("C3", "C1"): 25,
    ("C2", "C3"): 35, ("C3", "C2"): 35,
}

WEIGHT_PER_ITEM_KG = 0.5
COST_PER_KM = 2  # Assume fixed for now

class OrderRequest(BaseModel):
    __root__: Dict[str, int]  # e.g. {"A": 1, "B": 2}

# Helper to find which warehouses can fulfill which items
def get_product_sources(order):
    product_sources = {}
    for product in order:
        sources = [w for w, items in WAREHOUSE_STOCK.items() if product in items]
        product_sources[product] = sources
    return product_sources

# Generate all possible warehouse pickup combinations
def generate_paths(start_center, order):
    needed_warehouses = set()
    for p in order:
        for w, items in WAREHOUSE_STOCK.items():
            if p in items:
                needed_warehouses.add(w)
    needed_warehouses = list(needed_warehouses)

    # Start from start_center and create permutations
    routes = []
    for perm in itertools.permutations(needed_warehouses):
        if perm[0] != start_center:
            continue
        path = []
        current = start_center
        for wh in perm:
            if current != wh:
                path.append((current, wh))
                current = wh
        path.append((current, "L1"))  # Final delivery
        routes.append(path)
    return routes

# Cost calculator
def calculate_cost(path, total_weight):
    total_cost = 0
    for (src, dst) in path:
        dist_cost = COST_MATRIX.get((src, dst), 999)
        total_cost += dist_cost * total_weight
    return total_cost

@app.post("/calculate-cost")
async def calculate_delivery_cost(order: OrderRequest):
    order_data = order.__root__
    total_weight = sum(order_data.values()) * WEIGHT_PER_ITEM_KG
    min_cost = float('inf')
    best_path = None

    for start_center in WAREHOUSES:
        paths = generate_paths(start_center, order_data)
        for path in paths:
            cost = calculate_cost(path, total_weight)
            if cost < min_cost:
                min_cost = cost
                best_path = path

    return {"minimum_cost": min_cost, "best_path": best_path}
