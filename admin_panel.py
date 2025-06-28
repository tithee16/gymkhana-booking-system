import tkinter as tk
import os
import pandas as pd
from datetime import datetime
from tkinter import ttk, messagebox
from pymongo import MongoClient
from tkinter.font import Font

BG_COLOR = "#f0f2f5"
HEADER_COLOR = "#2c3e50"
BUTTON_COLOR = "#3498db"
BUTTON_HOVER = "#2980b9"
SUCCESS_COLOR = "#27ae60"
WARNING_COLOR = "#e67e22"
DANGER_COLOR = "#e74c3c"
TEXT_COLOR = "#2c3e50"
LIGHT_TEXT = "#ecf0f1"
TABLE_HEADER_COLOR = "#34495e"

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
                bookings_tree.tag_configure('overdue', background='#ffdddd', foreground='#cc0000')  # light red
                bookings_tree.item(item_id, tags=('overdue',))
            # Highlight items due today with yellow background
            elif is_due_today:
                bookings_tree.tag_configure('due_today', background='#ffffcc', foreground='#997300')  # light yellow
                bookings_tree.item(item_id, tags=('due_today',))
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load bookings: {str(e)}")

def search_bookings():
    """Search bookings by any parameter"""
    search_term = search_entry.get().strip().lower()
    if not search_term:
        load_bookings()  # Reload all if search is empty
        return
    
    try:
        # Clear existing rows
        for row in bookings_tree.get_children():
            bookings_tree.delete(row)
        
        # Get current date for comparison
        current_date = datetime.now().date()
        
        # Search across multiple fields (case insensitive)
        regex_pattern = f".*{search_term}.*"
        pending_bookings = bookings.find({
            "status": "Pending",
            "$or": [
                {"booking_id": {"$regex": regex_pattern, "$options": "i"}},
                {"name": {"$regex": regex_pattern, "$options": "i"}},
                {"reg_no": {"$regex": regex_pattern, "$options": "i"}},
                {"sports": {"$regex": regex_pattern, "$options": "i"}},
                {"issue_date": {"$regex": regex_pattern, "$options": "i"}},
                {"return_date": {"$regex": regex_pattern, "$options": "i"}}
            ]
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
                bookings_tree.tag_configure('overdue', background='#ffdddd', foreground='#cc0000')
                bookings_tree.item(item_id, tags=('overdue',))
            elif is_due_today:
                bookings_tree.tag_configure('due_today', background='#ffffcc', foreground='#997300')
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

def close_panel():
    """Close the admin panel"""
    admin_root.destroy()

# Main GUI Setup
admin_root = tk.Tk()
admin_root.title("Admin Panel - Sports Equipment Management")
admin_root.geometry("1100x750")
admin_root.configure(bg=BG_COLOR)

# Set custom font
title_font = Font(family="Helvetica", size=16, weight="bold")
header_font = Font(family="Helvetica", size=12, weight="bold")
button_font = Font(family="Helvetica", size=10, weight="bold")
table_font = Font(family="Helvetica", size=10)

# Configure style for ttk widgets
style = ttk.Style()
style.theme_use('clam')

# Configure Treeview colors
style.configure("Treeview",
                background="#ffffff",
                foreground=TEXT_COLOR,
                rowheight=25,
                fieldbackground="#ffffff",
                font=table_font)
style.map('Treeview', background=[('selected', BUTTON_COLOR)])

# Configure Treeview Heading
style.configure("Treeview.Heading",
                background=TABLE_HEADER_COLOR,
                foreground=LIGHT_TEXT,
                font=header_font,
                padding=5)

# Main container frame
main_frame = tk.Frame(admin_root, bg=BG_COLOR)
main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

# Header
header_frame = tk.Frame(main_frame, bg=HEADER_COLOR)
header_frame.pack(fill=tk.X, pady=(0, 15))

header_label = tk.Label(header_frame, 
                       text="Sports Equipment Management System - Admin Panel", 
                       font=title_font, 
                       bg=HEADER_COLOR, 
                       fg=LIGHT_TEXT,
                       padx=10,
                       pady=10)
header_label.pack()

# Content Frame
content_frame = tk.Frame(main_frame, bg=BG_COLOR)
content_frame.pack(fill=tk.BOTH, expand=True)

# Inventory Section
inventory_frame = tk.LabelFrame(content_frame, 
                              text=" Equipment Inventory ",
                              font=header_font,
                              bg=BG_COLOR,
                              fg=TEXT_COLOR,
                              padx=10,
                              pady=10)
inventory_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

# Inventory Treeview with scrollbars
inventory_scroll_y = ttk.Scrollbar(inventory_frame)
inventory_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

inventory_scroll_x = ttk.Scrollbar(inventory_frame, orient=tk.HORIZONTAL)
inventory_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

inventory_tree = ttk.Treeview(inventory_frame, 
                             columns=("ID", "Equipment Name", "Count"), 
                             show="headings",
                             yscrollcommand=inventory_scroll_y.set,
                             xscrollcommand=inventory_scroll_x.set,
                             height=6)
inventory_tree.pack(fill=tk.BOTH, expand=True)

inventory_scroll_y.config(command=inventory_tree.yview)
inventory_scroll_x.config(command=inventory_tree.xview)

# Configure columns
inventory_tree.heading("ID", text="Equipment ID", anchor=tk.CENTER)
inventory_tree.heading("Equipment Name", text="Equipment Name", anchor=tk.CENTER)
inventory_tree.heading("Count", text="Available Count", anchor=tk.CENTER)

inventory_tree.column("ID", width=120, anchor=tk.CENTER)
inventory_tree.column("Equipment Name", width=250, anchor=tk.CENTER)
inventory_tree.column("Count", width=120, anchor=tk.CENTER)

# Bookings Section
bookings_frame = tk.LabelFrame(content_frame, 
                             text=" Current Bookings (Pending Only) ",
                             font=header_font,
                             bg=BG_COLOR,
                             fg=TEXT_COLOR,
                             padx=10,
                             pady=10)
bookings_frame.pack(fill=tk.BOTH, expand=True)

# Search Frame
search_frame = tk.Frame(bookings_frame, bg=BG_COLOR)
search_frame.pack(fill=tk.X, pady=(0, 10))

search_label = tk.Label(search_frame, 
                       text="Search:", 
                       font=button_font, 
                       bg=BG_COLOR,
                       fg=TEXT_COLOR)
search_label.pack(side=tk.LEFT, padx=(0, 5))

search_entry = tk.Entry(search_frame, 
                       font=table_font, 
                       width=30,
                       relief=tk.SOLID,
                       borderwidth=1)
search_entry.pack(side=tk.LEFT, padx=5)
search_entry.bind("<Return>", lambda e: search_bookings())

search_button = tk.Button(search_frame, 
                         text="Search", 
                         command=search_bookings,
                         bg=BUTTON_COLOR, 
                         fg=LIGHT_TEXT, 
                         font=button_font,
                         padx=15, 
                         pady=2,
                         relief=tk.RAISED,
                         borderwidth=2,
                         activebackground=BUTTON_HOVER)
search_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(search_frame, 
                        text="Clear", 
                        command=clear_search,
                        bg=WARNING_COLOR, 
                        fg=LIGHT_TEXT, 
                        font=button_font,
                        padx=15, 
                        pady=2,
                        relief=tk.RAISED,
                        borderwidth=2,
                        activebackground="#d35400")
clear_button.pack(side=tk.LEFT, padx=5)

# Bookings Treeview with scrollbars
bookings_scroll_y = ttk.Scrollbar(bookings_frame)
bookings_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

bookings_scroll_x = ttk.Scrollbar(bookings_frame, orient=tk.HORIZONTAL)
bookings_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

bookings_tree = ttk.Treeview(bookings_frame, 
                           columns=("Booking ID", "Name", "Reg No", "Equipment", "Issue Date", "Return Date"), 
                           show="headings",
                           selectmode="browse",
                           yscrollcommand=bookings_scroll_y.set,
                           xscrollcommand=bookings_scroll_x.set,
                           height=6)
bookings_tree.pack(fill=tk.BOTH, expand=True)

bookings_scroll_y.config(command=bookings_tree.yview)
bookings_scroll_x.config(command=bookings_tree.xview)

# Configure columns
bookings_tree.heading("Booking ID", text="Booking ID", anchor=tk.CENTER)
bookings_tree.heading("Name", text="Student Name", anchor=tk.CENTER)
bookings_tree.heading("Reg No", text="Registration No", anchor=tk.CENTER)
bookings_tree.heading("Equipment", text="Equipment", anchor=tk.CENTER)
bookings_tree.heading("Issue Date", text="Issue Date", anchor=tk.CENTER)
bookings_tree.heading("Return Date", text="Return Date", anchor=tk.CENTER)

bookings_tree.column("Booking ID", width=100, anchor=tk.CENTER)
bookings_tree.column("Name", width=150, anchor=tk.CENTER)
bookings_tree.column("Reg No", width=120, anchor=tk.CENTER)
bookings_tree.column("Equipment", width=150, anchor=tk.CENTER)
bookings_tree.column("Issue Date", width=120, anchor=tk.CENTER)
bookings_tree.column("Return Date", width=120, anchor=tk.CENTER)

# Buttons Frame
button_frame = tk.Frame(main_frame, bg=BG_COLOR)
button_frame.pack(fill=tk.X, pady=(15, 0))

return_button = tk.Button(button_frame, 
                        text="Return Equipment", 
                        command=return_equipment, 
                        bg=DANGER_COLOR, 
                        fg=LIGHT_TEXT, 
                        font=button_font,
                        padx=20, 
                        pady=8,
                        relief=tk.RAISED,
                        borderwidth=2,
                        activebackground="#c0392b")
return_button.pack(side=tk.LEFT, padx=10, expand=True)

reload_button = tk.Button(button_frame, 
                         text="Refresh Data", 
                         command=lambda: [load_bookings(), load_inventory()], 
                         bg=BUTTON_COLOR, 
                         fg=LIGHT_TEXT, 
                         font=button_font,
                         padx=20, 
                         pady=8,
                         relief=tk.RAISED,
                         borderwidth=2,
                         activebackground=BUTTON_HOVER)
reload_button.pack(side=tk.LEFT, padx=10, expand=True)

export_button = tk.Button(button_frame, 
                         text="Export to Power BI", 
                         command=export_to_powerbi, 
                         bg=SUCCESS_COLOR, 
                         fg=LIGHT_TEXT, 
                         font=button_font,
                         padx=20, 
                         pady=8,
                         relief=tk.RAISED,
                         borderwidth=2,
                         activebackground="#219653")
export_button.pack(side=tk.LEFT, padx=10, expand=True)

close_button = tk.Button(button_frame, 
                        text="Close Panel", 
                        command=close_panel, 
                        bg=HEADER_COLOR, 
                        fg=LIGHT_TEXT, 
                        font=button_font,
                        padx=20, 
                        pady=8,
                        relief=tk.RAISED,
                        borderwidth=2,
                        activebackground="#1a252f")
close_button.pack(side=tk.LEFT, padx=10, expand=True)


# Initialize and load data
initialize_inventory()
remove_duplicates()
load_inventory()
load_bookings()

# Center the window on screen
window_width = admin_root.winfo_reqwidth()
window_height = admin_root.winfo_reqheight()
position_right = int(admin_root.winfo_screenwidth()/2 - window_width/2)
position_down = int(admin_root.winfo_screenheight()/2 - window_height/2)
admin_root.geometry(f"+{position_right}+{position_down}")

admin_root.mainloop()