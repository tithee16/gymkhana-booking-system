import tkinter as tk
import os
import pandas as pd
from datetime import datetime
from tkinter import ttk, messagebox
from pymongo import MongoClient

def export_to_powerbi():
    """Export current data to CSV for Power BI consumption"""
    try:
        # Create powerbi_data directory if it doesn't exist
        os.makedirs("powerbi_data", exist_ok=True)
        
        # Get current data
        booking_data = list(bookings.find())
        inventory_data = list(inventory.find())
        
        # Convert to DataFrames
        bookings_df = pd.DataFrame(booking_data)
        inventory_df = pd.DataFrame(inventory_data)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to CSV
        bookings_df.to_csv(f"powerbi_data/bookings_{timestamp}.csv", index=False)
        inventory_df.to_csv(f"powerbi_data/inventory_{timestamp}.csv", index=False)
        
        messagebox.showinfo("Success", "Data exported successfully for Power BI!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export data: {str(e)}")


# MongoDB Connection
client = MongoClient("mongodb+srv://tithee:tithee@cluster0.elvlqwp.mongodb.net/")
db = client["sports_db"]
inventory = db["Inventory"]
bookings = db["booking"]

def update_inventory_on_return(equipment_name, change=1):
    """Update inventory count when equipment is returned"""
    try:
        result = inventory.update_one(
            {"name": equipment_name},
            {"$inc": {"count": change}}
        )
        return result.modified_count > 0
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to update inventory: {str(e)}")
        return False

def remove_duplicates():
    """Remove duplicate equipment entries from inventory"""
    try:
        seen = set()
        duplicates = []
        for item in inventory.find():
            name = item.get("name")
            if name in seen:
                duplicates.append(item["_id"])
            else:
                seen.add(name)
        if duplicates:
            inventory.delete_many({"_id": {"$in": duplicates}})
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to remove duplicates: {str(e)}")

def initialize_inventory():
    """Initialize inventory with default equipment if empty"""
    try:
        equipment_list = [
            "Football", "Basketball", "Volleyball", "Throwball", "Cricket Bat",
            "Tennis Ball", "Season Ball", "Badminton Racket", "Shuttle Cock",
            "Table Tennis Racket", "Table Tennis Ball", "Carrom Striker", "Chess"
        ]
        
        for sport in equipment_list:
            if not inventory.find_one({"name": sport}):
                equipment_id = f"E{equipment_list.index(sport) + 1}"
                inventory.insert_one({
                    "_id": equipment_id,
                    "name": sport,
                    "count": 10
                })
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to initialize inventory: {str(e)}")

def load_inventory():
    """Load inventory data into the table"""
    try:
        for row in inventory_tree.get_children():
            inventory_tree.delete(row)

        for item in inventory.find().sort("_id"):
            inventory_tree.insert("", "end", values=(
                item["_id"], 
                item["name"], 
                item["count"]
            ))
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load inventory: {str(e)}")

def load_bookings():
    """Load only Pending bookings into the table"""
    try:
        # Clear existing rows
        for row in bookings_tree.get_children():
            bookings_tree.delete(row)

        # Fetch only pending bookings sorted by booking_id
        pending_bookings = bookings.find({"status": "Pending"}).sort("booking_id", 1)
        
        # Insert into treeview
        for booking in pending_bookings:
            bookings_tree.insert("", "end", values=(
                booking.get("booking_id", "N/A"),
                booking.get("name", "N/A"),
                booking.get("reg_no", "N/A"),
                booking.get("sports", "N/A"),
                booking.get("issue_date", "N/A"),
                booking.get("return_date", "N/A")
            ))
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load bookings: {str(e)}")

def return_equipment():
    """Mark selected booking as returned and update inventory"""
    selected_item = bookings_tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a booking to return!")
        return

    try:
        selected_values = bookings_tree.item(selected_item, "values")
        booking_id = selected_values[0]
        equipment_name = selected_values[3]

        # Update inventory first
        if not update_inventory_on_return(equipment_name):
            return
        
        # Update booking status to "Returned"
        result = bookings.update_one(
            {"booking_id": booking_id, "status": "Pending"},
            {"$set": {"status": "Returned"}}
        )
        
        if result.modified_count == 1:
            # Refresh the bookings table (will now exclude this returned item)
            load_bookings()
            load_inventory()
            messagebox.showinfo("Success", f"Booking {booking_id} marked as returned!")
        else:
            messagebox.showerror("Error", "Failed to update booking status!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process return: {str(e)}")

# Main GUI Setup
admin_root = tk.Tk()
admin_root.title("Admin Panel - Sports Equipment Management")
admin_root.geometry("1000x700")

# Tables Frame
frame = tk.Frame(admin_root)
frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Inventory Table
inventory_label = tk.Label(frame, text="Inventory", font=("Arial", 14, "bold"))
inventory_label.pack(pady=5)

inventory_tree = ttk.Treeview(frame, columns=("ID", "Equipment Name", "Count"), show="headings")
inventory_tree.heading("ID", text="Equipment ID")
inventory_tree.heading("Equipment Name", text="Equipment Name")
inventory_tree.heading("Count", text="Count")
inventory_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
inventory_tree.bind('<<TreeviewSelect>>', lambda e: inventory_tree.selection_remove(inventory_tree.selection()))

# Current Bookings Table (Only Pending Status)
bookings_label = tk.Label(frame, text="Current Bookings (Pending Only)", font=("Arial", 14, "bold"))
bookings_label.pack(pady=5)

bookings_tree = ttk.Treeview(frame, 
                           columns=("Booking ID", "Name", "Reg No", "Equipment", "Issue Date", "Return Date"), 
                           show="headings",
                           selectmode="browse")
bookings_tree.heading("Booking ID", text="Booking ID")
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

bookings_tree.column("Booking ID", width=100, anchor=tk.CENTER)
bookings_tree.column("Name", width=150, anchor=tk.CENTER)
bookings_tree.column("Reg No", width=120, anchor=tk.CENTER)
bookings_tree.column("Equipment", width=150, anchor=tk.CENTER)
bookings_tree.column("Issue Date", width=120, anchor=tk.CENTER)
bookings_tree.column("Return Date", width=120, anchor=tk.CENTER)

# Buttons
button_frame = tk.Frame(admin_root)
button_frame.pack(pady=10)

return_button = tk.Button(button_frame, text="Return Equipment", command=return_equipment, 
                         bg="red", fg="white", font=("Arial", 12, "bold"),
                         padx=20, pady=5)
return_button.pack(side=tk.LEFT, padx=10)

reload_button = tk.Button(button_frame, text="Reload Bookings", command=load_bookings, 
                          bg="blue", fg="white", font=("Arial", 12, "bold"),
                          padx=20, pady=5)
reload_button.pack(side=tk.LEFT, padx=10)

export_button = tk.Button(button_frame, text="Export to Power BI", command=export_to_powerbi, 
                         bg="green", fg="white", font=("Arial", 12, "bold"),
                         padx=20, pady=5)
export_button.pack(side=tk.LEFT, padx=10)

# Initialize and load data
initialize_inventory()
remove_duplicates()
load_inventory()
load_bookings()

admin_root.mainloop()