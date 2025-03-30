import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from pymongo import MongoClient
from datetime import date
import subprocess

# MongoDB Connection
client = MongoClient("mongodb+srv://tithee:tithee@cluster0.elvlqwp.mongodb.net/")
db = client["sports_db"]
collection = db["booking"]

# Function to update inventory count when equipment is booked
def update_inventory_on_booking(sport_name, change=-1):
    """Update inventory count when equipment is booked (decrease by 1)"""
    inventory = db["Inventory"]
    result = inventory.update_one(
        {"name": sport_name},
        {"$inc": {"count": change}}
    )
    return result.modified_count > 0

# Function to check inventory availability
def check_inventory_availability(sport_name):
    """Check if equipment is available in inventory"""
    item = db["Inventory"].find_one({"name": sport_name})
    return item and item.get("count", 0) > 0

# Function to update return date min limit
def update_return_date(*args):
    return_date.config(mindate=issue_date.get_date())

# Function to reset form fields after booking
def reset_fields():
    name_entry.delete(0, tk.END)
    email_entry.delete(0, tk.END)
    mobile_entry.delete(0, tk.END)
    reg_entry.delete(0, tk.END)
    branch_var.set("")
    year_var.set("")
    sports_var.set("")
    issue_date.set_date(today)  # Reset to today's date
    return_date.set_date(today)  # Reset to today's date

# Function to submit data
def book_equipment():
    issue_dt = issue_date.get_date()
    return_dt = return_date.get_date()
    
    reg_no = reg_entry.get()  # Student Registration Number
    sport_name = sports_var.get()

    if return_dt < issue_dt:
        messagebox.showerror("Error", "Return Date cannot be before Issue Date!")
        return

    # Check inventory availability
    if not check_inventory_availability(sport_name):
        messagebox.showerror("Error", "This equipment is currently out of stock!")
        return

    # Check if student already has a pending booking
    existing_booking = collection.find_one({"reg_no": reg_no, "status": "Pending"})
    if existing_booking:
        messagebox.showerror("Error", "You already have a pending booking. Please return the previous equipment first.")
        return

    # Check if registration number already exists in the database
    existing_student = db["students"].find_one({"reg_no": reg_no})
    if existing_student:
        messagebox.showerror("Error", "This registration number is already in use. Please check again.")
        return

    student_data = {
        "name": name_entry.get(),
        "email": email_entry.get(),
        "mobile": mobile_entry.get(),
        "reg_no": reg_no,
        "branch": branch_var.get(),
        "year": year_var.get(),
        "sports": sport_name,
        "issue_date": issue_dt.strftime("%Y-%m-%d"),
        "return_date": return_dt.strftime("%Y-%m-%d"),
        "status": "Pending"  # Default return status
    }
    
    if "" in student_data.values():
        messagebox.showerror("Error", "All fields are required!")
        return
    
    collection.insert_one(student_data)
    
    # Update inventory count
    if not update_inventory_on_booking(sport_name):
        messagebox.showerror("Error", "Failed to update inventory count!")
        return
    
    messagebox.showinfo("Success", "Booking Registered Successfully!")
    reset_fields()

# Function to open admin panel
def open_admin_panel():
    try:
        subprocess.Popen(['python', 'admin_panel.py'])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open admin panel: {str(e)}")

def open_records_page():
    try:
        subprocess.Popen(['python', 'records_page.py'])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open records: {str(e)}")

# GUI Window
root = tk.Tk()
root.title("Sports Equipment Booking System")
root.geometry("450x650")

# Admin & Records Buttons
top_frame = tk.Frame(root)
top_frame.pack(pady=10)

admin_button = tk.Button(top_frame, text="Admin Panel", command=open_admin_panel, bg="blue", fg="white", font=("Arial", 12, "bold"))
admin_button.pack(side=tk.LEFT, padx=10)

records_button = tk.Button(top_frame, text="Records", command=open_records_page, bg="orange", fg="white", font=("Arial", 12, "bold"))
records_button.pack(side=tk.RIGHT, padx=10)

# Labels and Entry Fields
tk.Label(root, text="Student Information", font=("Arial", 14, "bold")).pack(pady=10)

tk.Label(root, text="Name:").pack()
name_entry = tk.Entry(root)
name_entry.pack()

tk.Label(root, text="Email ID:").pack()
email_entry = tk.Entry(root)
email_entry.pack()

tk.Label(root, text="Mobile No:").pack()
mobile_entry = tk.Entry(root)
mobile_entry.pack()

tk.Label(root, text="Registration No:").pack()
reg_entry = tk.Entry(root)
reg_entry.pack()

tk.Label(root, text="Branch:").pack()
branch_var = tk.StringVar()
branch_dropdown = ttk.Combobox(root, textvariable=branch_var, values=[
    "CS", "IT", "ExTC", "Electronics", "Electrical", "Mechanical", 
    "Civil", "Production", "Textile", "Chemical", "MCA", "Masters"
])
branch_dropdown.pack()

tk.Label(root, text="Year:").pack()
year_var = tk.StringVar()
year_dropdown = ttk.Combobox(root, textvariable=year_var, values=["1st", "2nd", "3rd", "4th"])
year_dropdown.pack()

tk.Label(root, text="Select Sport:").pack()
sports_var = tk.StringVar()
sports_dropdown = ttk.Combobox(root, textvariable=sports_var, values=[
    "Football", "Basketball", "Volleyball", "Throwball", "Cricket Bat",
    "Tennis Ball", "Season Ball", "Badminton Racket", "Shuttle Cock",
    "Table Tennis Racket", "Table Tennis Ball", "Carrom Striker", "Chess"
])
sports_dropdown.pack()

# Disable past dates in calendar
today = date.today()

tk.Label(root, text="Issue Date:").pack()
issue_date = DateEntry(root, width=12, background="darkblue", foreground="white", borderwidth=2, mindate=today)
issue_date.pack()

tk.Label(root, text="Return Date:").pack()
return_date = DateEntry(root, width=12, background="darkblue", foreground="white", borderwidth=2, mindate=today)
return_date.pack()

# Update return date when issue date changes
issue_date.bind("<<DateEntrySelected>>", update_return_date)

# BOOK Button
book_button = tk.Button(root, text="BOOK", command=book_equipment, bg="green", fg="white", font=("Arial", 12, "bold"))
book_button.pack(pady=20)

root.mainloop()