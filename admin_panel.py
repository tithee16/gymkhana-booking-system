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
    """Load only Pending bookings into the table and highlight overdue items and items due today"""
    try:
        # Clear existing rows
        for row in bookings_tree.get_children():
            bookings_tree.delete(row)

        # Get current date for comparison
        current_date = datetime.now().date()
        
        # Fetch only pending bookings sorted by booking_id
        pending_bookings = bookings.find({"status": "Pending"}).sort("booking_id", 1)
        
        # Insert into treeview
        for booking in pending_bookings:
            return_date_str = booking.get("return_date", "")
            try:
                # Try to parse the return date
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d").date()
                is_overdue = return_date < current_date
                is_due_today = return_date == current_date
            except (ValueError, TypeError):
                # If date parsing fails, don't mark as overdue or due today
                is_overdue = False
                is_due_today = False
            
            item_id = bookings_tree.insert("", "end", values=(
                booking.get("booking_id", "N/A"),
                booking.get("name", "N/A"),
                booking.get("reg_no", "N/A"),
                booking.get("sports", "N/A"),
                booking.get("issue_date", "N/A"),
                return_date_str
            ))
            
            # Highlight overdue items with red background
            if is_overdue:
                bookings_tree.tag_configure('overdue', background='#ffcccc')  # light red
                bookings_tree.item(item_id, tags=('overdue',))
            # Highlight items due today with yellow background
            elif is_due_today:
                bookings_tree.tag_configure('due_today', background='#ffff99')  # light yellow
                bookings_tree.item(item_id, tags=('due_today',))
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load bookings: {str(e)}")

def search_bookings():
    """Search bookings by registration number"""
    search_term = search_entry.get().strip()
    if not search_term:
        load_bookings()  # Reload all if search is empty
        return
    
    try:
        # Clear existing rows
        for row in bookings_tree.get_children():
            bookings_tree.delete(row)
        
        # Get current date for comparison
        current_date = datetime.now().date()
        
        # Search for registration numbers containing the search term (case insensitive)
        regex_pattern = f".*{search_term}.*"
        pending_bookings = bookings.find({
            "status": "Pending",
            "reg_no": {"$regex": regex_pattern, "$options": "i"}
        }).sort("booking_id", 1)
        
        # Insert matching records into treeview
        for booking in pending_bookings:
            return_date_str = booking.get("return_date", "")
            try:
                return_date = datetime.strptime(return_date_str, "%Y-%m-%d").date()
                is_overdue = return_date < current_date
                is_due_today = return_date == current_date
            except (ValueError, TypeError):
                is_overdue = False
                is_due_today = False
            
            item_id = bookings_tree.insert("", "end", values=(
                booking.get("booking_id", "N/A"),
                booking.get("name", "N/A"),
                booking.get("reg_no", "N/A"),
                booking.get("sports", "N/A"),
                booking.get("issue_date", "N/A"),
                return_date_str
            ))
            
            if is_overdue:
                bookings_tree.tag_configure('overdue', background='#ffcccc')
                bookings_tree.item(item_id, tags=('overdue',))
            elif is_due_today:
                bookings_tree.tag_configure('due_today', background='#ffff99')
                bookings_tree.item(item_id, tags=('due_today',))
                
    except Exception as e:
        messagebox.showerror("Search Error", f"Failed to search bookings: {str(e)}")

def clear_search():
    """Clear search entry and reload all bookings"""
    search_entry.delete(0, tk.END)
    load_bookings()

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
admin_root.geometry("1000x700")  # Slightly increased window height

# Main container frame
main_frame = tk.Frame(admin_root)
main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Inventory Section
inventory_frame = tk.Frame(main_frame)
inventory_frame.pack(fill=tk.BOTH, expand=True)

inventory_label = tk.Label(inventory_frame, text="Inventory", font=("Arial", 14, "bold"))
inventory_label.pack(pady=5)

inventory_tree = ttk.Treeview(inventory_frame, columns=("ID", "Equipment Name", "Count"), 
                             show="headings", height=10)  # Previous height
inventory_tree.heading("ID", text="Equipment ID")
inventory_tree.heading("Equipment Name", text="Equipment Name")
inventory_tree.heading("Count", text="Count")
inventory_tree.pack(padx=10, pady=(0, 20), fill=tk.BOTH)  # Added space between tables
inventory_tree.bind('<<TreeviewSelect>>', lambda e: inventory_tree.selection_remove(inventory_tree.selection()))

# Bookings Section
bookings_frame = tk.Frame(main_frame)
bookings_frame.pack(fill=tk.BOTH, expand=True)

bookings_label = tk.Label(bookings_frame, text="Current Bookings (Pending Only)", font=("Arial", 14, "bold"))
bookings_label.pack(pady=5)

# Search Frame
search_frame = tk.Frame(bookings_frame)
search_frame.pack(pady=(0, 5), fill=tk.X)

search_label = tk.Label(search_frame, text="Search by Reg No:", font=("Arial", 12))
search_label.pack(side=tk.LEFT, padx=5)

search_entry = tk.Entry(search_frame, font=("Arial", 12), width=30)
search_entry.pack(side=tk.LEFT, padx=5)
search_entry.bind("<Return>", lambda e: search_bookings())

search_button = tk.Button(search_frame, text="Search", command=search_bookings,
                         bg="#4CAF50", fg="white", font=("Arial", 12),
                         padx=15, pady=2)
search_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(search_frame, text="Clear", command=clear_search,
                        bg="#f44336", fg="white", font=("Arial", 12),
                        padx=15, pady=2)
clear_button.pack(side=tk.LEFT, padx=5)

bookings_tree = ttk.Treeview(bookings_frame, 
                           columns=("Booking ID", "Name", "Reg No", "Equipment", "Issue Date", "Return Date"), 
                           show="headings",
                           selectmode="browse",
                           height=10)  # Previous height
bookings_tree.heading("Booking ID", text="Booking ID")
bookings_tree.heading("Name", text="Name")
bookings_tree.heading("Reg No", text="Registration No")
bookings_tree.heading("Equipment", text="Equipment")
bookings_tree.heading("Issue Date", text="Issue Date")
bookings_tree.heading("Return Date", text="Return Date")
bookings_tree.pack(padx=10, pady=(0, 15), fill=tk.BOTH)  # Space above buttons

# Buttons Frame (positioned closer to tables)
button_frame = tk.Frame(main_frame)
button_frame.pack(pady=(6, 4))  # Reduced padding to move buttons up

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


# Initialize and load data
initialize_inventory()
remove_duplicates()
load_inventory()
load_bookings()

admin_root.mainloop()