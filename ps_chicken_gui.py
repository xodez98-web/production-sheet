import tkinter as tk
from tkinter import ttk
import csv, os, sys
from datetime import datetime

# ---------------- CONFIG ----------------
PARTS = [
    ("Thigh", "10089831"),
    ("Drumstick", "10089827"),
    ("Breast", "10089836"),
    ("Wings", "10089825"),
    ("Neck", "10089830"),
]

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COST_FILE = os.path.join(BASE_DIR, "part_costs.csv")

# ---------------- COST STORAGE ----------------
def load_latest_costs():
    if not os.path.exists(COST_FILE):
        return {}
    with open(COST_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
        if not rows:
            return {}
    latest_ts = max(r["timestamp"] for r in rows)
    return {r["part"]: float(r["cost"]) for r in rows if r["timestamp"] == latest_ts}

def save_costs(costs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    if os.path.exists(COST_FILE):
        with open(COST_FILE, newline="") as f:
            rows = list(csv.DictReader(f))
    for part, cost in costs.items():
        rows.append({"timestamp": timestamp, "part": part, "cost": cost})
    timestamps = sorted(set(r["timestamp"] for r in rows))[-5:]
    rows = [r for r in rows if r["timestamp"] in timestamps]
    with open(COST_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "part", "cost"])
        writer.writeheader()
        writer.writerows(rows)

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Chicken Production Sheet v0.09 by Shaiishyr")

cost_entries = {}

# -------- Part Cost Section --------
tk.Label(root, text="Part Cost Setup (KG)", font=("Arial", 19, "bold")).grid(
    row=0, column=0, columnspan=3, pady=(10,5)
)

saved_costs = load_latest_costs()
cost_locked = bool(saved_costs)

for i, (name, mid) in enumerate(PARTS):
    tk.Label(root, text=f"{name} ({mid})").grid(row=1+i, column=0, sticky="w", padx=5, pady=2)
    e = tk.Entry(root, width=10)
    e.grid(row=1+i, column=1, sticky="w", padx=5)
    if name in saved_costs:
        e.insert(0, saved_costs[name])
    cost_entries[name] = e
    if cost_locked:
        e.config(state="readonly")

def save_costs_btn():
    try:
        costs = {}
        for k, v in cost_entries.items():
            val = float(v.get())  # convert to float
            if val < 0:
                raise ValueError(f"{k} cannot be negative")  # negative check
            costs[k] = val
        save_costs(costs)
        lock_costs()
        message_lbl.config(text="Costs saved and locked", fg="green")
    except ValueError:
        message_lbl.config(text="Invalid cost input!", fg="red")

def edit_costs_btn():
    unlock_costs()
    message_lbl.config(text="Editing costs enabled", fg="blue")

def lock_costs():
    for e in cost_entries.values():
        e.config(state="readonly")

def unlock_costs():
    for e in cost_entries.values():
        e.config(state="normal")

tk.Button(root, text="Save Costs", width=12, command=save_costs_btn).grid(row=1, column=2, rowspan=2, padx=5)
tk.Button(root, text="Edit Costs", width=12, command=edit_costs_btn).grid(row=3, column=2, rowspan=2, padx=5)

# Message label
message_lbl = tk.Label(root, text="", font=("Arial", 16, "bold"))
message_lbl.grid(row=6, column=0, columnspan=3, pady=(5,5))

# -------- Raw Material --------
tk.Label(root, text="Raw Material (10089824)", font=("Arial", 19, "bold")).grid(row=7, column=0, columnspan=3, pady=(10,5))

tk.Label(root, text="Whole Chicken Qty (KG)").grid(row=8, column=0, sticky="w", padx=5, pady=2)
raw_qty_e = tk.Entry(root, width=10)
raw_qty_e.grid(row=8, column=1, sticky="w", padx=5)

tk.Label(root, text="Whole Chicken Total Cost (RM)").grid(row=9, column=0, sticky="w", padx=5, pady=2)
raw_cost_e = tk.Entry(root, width=10)
raw_cost_e.grid(row=9, column=1, sticky="w", padx=5)

# -------- Part Quantity --------
tk.Label(root, text="Parts Quantity (KG)", font=("Arial", 19, "bold")).grid(row=10, column=0, columnspan=3, pady=(10,5))

qty_entries = {}
for i, (name, mid) in enumerate(PARTS):
    tk.Label(root, text=f"{name} ({mid})").grid(row=11+i, column=0, sticky="w", padx=5, pady=2)
    e = tk.Entry(root, width=10)
    e.grid(row=11+i, column=1, sticky="w", padx=5)
    qty_entries[name] = e

# -------- Difference display --------
diff_lbl = tk.Label(root, text="", fg="red", font=("Arial", 12))
diff_lbl.grid(row=16, column=0, columnspan=3, pady=(5,5))

# -------- Result Table --------
cols = ("Part", "Mat ID", "Quantity (KG)", "Adj Cost/kg", "Adj Total")
tree = ttk.Treeview(root, columns=cols, show="headings", height=6)
for c in cols:
    tree.heading(c, text=c)
    tree.column(c, width=120, anchor="center")
tree.grid(row=17, column=0, columnspan=3, pady=(5,10))

# -------- Calculation --------
def calculate():
    try:
        raw_qty = float(raw_qty_e.get())
        raw_cost = float(raw_cost_e.get())
        costs = {k: float(v.get()) for k,v in cost_entries.items()}

        parts = []
        total_qty = 0
        out_total = 0
        for name, mid in PARTS:
            qty = float(qty_entries[name].get())
            total_qty += qty
            base_total = qty * costs[name]
            out_total += base_total
            parts.append({"name": name, "mid": mid, "qty": qty, "base": base_total})

        # Show quantity and cost difference inline
        qty_diff = round(raw_qty - total_qty,2)
        cost_diff = round(raw_cost - out_total,2)
        diff_lbl.config(text=f"Quantity Difference: {qty_diff} kg | Cost Difference: RM {cost_diff}")

        # Adjust costs proportionally
        ratio = raw_cost / out_total
        for p in parts[:-1]:
            p["adj_total"] = round(p["base"]*ratio,2)
            p["adj_cost"] = round(p["adj_total"]/p["qty"],2)
        last = parts[-1]
        last["adj_total"] = round(raw_cost - sum(p["adj_total"] for p in parts[:-1]),2)
        last["adj_cost"] = round(last["adj_total"]/last["qty"],2)

        # Update cost entries to new adjusted cost
        for p in parts:
            e = cost_entries[p["name"]]
            e.config(state="normal")
            e.delete(0, tk.END)
            e.insert(0, p["adj_cost"])
            e.config(state="readonly")

        save_costs({p["name"]: p["adj_cost"] for p in parts})

        tree.delete(*tree.get_children())
        for p in parts:
            tree.insert("", "end", values=(p["name"], p["mid"], p["qty"], p["adj_cost"], p["adj_total"]))

        message_lbl.config(text="Calculation complete, costs updated", fg="green")
    except ValueError:
        message_lbl.config(text="Invalid numeric input!", fg="red")

tk.Button(root, text="Calculate & Adjust", width=20, command=calculate).grid(row=18, column=0, columnspan=3, pady=(10,15))

root.mainloop()
