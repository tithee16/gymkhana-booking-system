import tkinter as tk
from tkinter import ttk, messagebox
from pymongo import MongoClient

# MongoDB Connection
client = MongoClient("mongodb+srv://tithee:tithee@cluster0.elvlqwp.mongodb.net/")
db = client["sports_db"]
inventory = db["Inventory"]         # Table 1: Inventory
bookings = db["booking"]           # Table 2: Current Bookings

# Pre-populate Inventory with all sports equipment
def initialize_inventory():
    equipment_list = [
        "Football", "Basketball", "Volleyball", "Throwball", "Cricket Bat",
        "Tennis Ball", "Season Ball", "Badminton Racket", "Shuttle Cock",
        "Table Tennis Racket", "Table Tennis Ball", "Carrom Striker", "Chess"
    ]
    
    # Add equipment to inventory only if it doesn't exist
    for idx, sport in enumerate(equipment_list, start=1):
        equipment_id = f"E{idx}"  # Simpler Equipment ID
        if not inventory.find_one({"_id": equipment_id}):
            inventory.insert_one({
                "_id": equipment_id,
                "name": sport,
                "count": 10  # Initial count set to 10
            })

# Function to generate a new Booking ID (B1, B2, ...)
def generate_booking_id():
    last_booking = bookings.find_one(sort=[("_id", -1)])
    
    if last_booking and "_id" in last_booking and last_booking["_id"].startswith("B"):
        last_id = int(last_booking["_id"][1:])  # Extract the numeric part
        return f"B{last_id + 1}"
    return "B1"

# Function to load inventory data into the table
def load_inventory():
    for row in inventory_tree.get_children():
        inventory_tree.delete(row)

    for item in inventory.find().sort("_id"):
        inventory_tree.insert("", "end", values=(item["_id"], item["name"], item["count"]))

# Function to load current bookings into the table
def load_bookings():
    for row in bookings_tree.get_children():
        bookings_tree.delete(row)

    # Get all bookings and sort them by creation time (assuming _id has timestamp)
    all_bookings = list(bookings.find().sort("_id", 1))
    
    # Display them with sequential B1, B2, etc. IDs regardless of actual DB ID
    for idx, booking in enumerate(all_bookings, start=1):
        bookings_tree.insert("", "end", values=(
            f"B{idx}",  # Display sequential booking ID
            booking.get("name"),
            booking.get("reg_no"),
            booking.get("sports", "N/A"),
            booking.get("issue_date", "N/A"),
            booking.get("return_date", "N/A")
        ))

# Function to return equipment
# Function to return equipment (GUI-only removal)
def return_equipment():
    selected_item = bookings_tree.selection()

    if not selected_item:
        messagebox.showerror("Error", "Please select a booking to return!")
        return

    # Get the selected booking details from the treeview
    selected_values = bookings_tree.item(selected_item, "values")
    displayed_booking_id = selected_values[0]  # This is the "B1", "B2" displayed ID
    equipment_name = selected_values[3]  # Equipment Name

    # Simply remove the item from the Treeview (GUI)
    bookings_tree.delete(selected_item)
    
    # Show success message (without actually modifying MongoDB)
    messagebox.showinfo("Success", f"Booking {displayed_booking_id} returned ")

# Admin Panel Window
admin_root = tk.Tk()
admin_root.title("Admin Panel - Sports Equipment Management")
admin_root.geometry("1000x700")

# Tables Frame
frame = tk.Frame(admin_root)
frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Inventory Table (Table 1)
inventory_label = tk.Label(frame, text="Inventory", font=("Arial", 14, "bold"))
inventory_label.pack(pady=5)

inventory_tree = ttk.Treeview(frame, columns=("ID", "Equipment Name", "Count"), show="headings")
inventory_tree.heading("ID", text="Equipment ID")
inventory_tree.heading("Equipment Name", text="Equipment Name")
inventory_tree.heading("Count", text="Count")
inventory_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Make inventory items non-selectable
inventory_tree.bind('<<TreeviewSelect>>', lambda e: inventory_tree.selection_remove(inventory_tree.selection()))

# Current Bookings Table (Table 2)
bookings_label = tk.Label(frame, text="Current Bookings", font=("Arial", 14, "bold"))
bookings_label.pack(pady=5)

bookings_tree = ttk.Treeview(frame, 
                            columns=("ID", "Name", "Reg No", "Equipment", "Issue Date", "Return Date"), 
                            show="headings",
                            selectmode="browse")
bookings_tree.heading("ID", text="Booking ID")
bookings_tree.heading("Name", text="Name")
bookings_tree.heading("Reg No", text="Registration No")
bookings_tree.heading("Equipment", text="Equipment")
bookings_tree.heading("Issue Date", text="Issue Date")
bookings_tree.heading("Return Date", text="Return Date")
bookings_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Configure column widths
inventory_tree.column("ID", width=100, anchor=tk.CENTER)
inventory_tree.column("Equipment Name", width=200, anchor=tk.CENTER)
inventory_tree.column("Count", width=100, anchor=tk.CENTER)

bookings_tree.column("ID", width=80, anchor=tk.CENTER)
bookings_tree.column("Name", width=150, anchor=tk.CENTER)
bookings_tree.column("Reg No", width=120, anchor=tk.CENTER)
bookings_tree.column("Equipment", width=150, anchor=tk.CENTER)
bookings_tree.column("Issue Date", width=120, anchor=tk.CENTER)
bookings_tree.column("Return Date", width=120, anchor=tk.CENTER)

# Return Equipment Button
return_button = tk.Button(admin_root, text="Return Equipment", command=return_equipment, 
                         bg="red", fg="white", font=("Arial", 12, "bold"),
                         padx=20, pady=10)
return_button.pack(pady=20)

# Initialize inventory and load data into tables
initialize_inventory()
load_inventory()
load_bookings()

admin_root.mainloop()