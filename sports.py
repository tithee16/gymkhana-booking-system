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
counter_collection = db["counters"]  # For maintaining unique IDs

# Function to get next booking ID
def get_next_booking_id():
    counter = counter_collection.find_one_and_update(
        {"_id": "booking_id"},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return f"B{counter['sequence_value']}"

# Function to update inventory count when equipment is booked
def update_inventory_on_booking(sport_name, change=-1):
    inventory = db["Inventory"]
    result = inventory.update_one(
        {"name": sport_name},
        {"$inc": {"count": change}}
    )
    return result.modified_count > 0

def check_inventory_availability(sport_name):
    item = db["Inventory"].find_one({"name": sport_name})
    return item and item.get("count", 0) > 0

def update_return_date(*args):
    return_date.config(mindate=issue_date.get_date())

def reset_fields():
    name_entry.delete(0, tk.END)
    email_entry.delete(0, tk.END)
    mobile_entry.delete(0, tk.END)
    reg_entry.delete(0, tk.END)
    branch_var.set("")
    year_var.set("")
    sports_var.set("")
    issue_date.set_date(today)
    return_date.set_date(today)

def book_equipment():
    issue_dt = issue_date.get_date()
    return_dt = return_date.get_date()
    reg_no = reg_entry.get()
    sport_name = sports_var.get()

    if return_dt < issue_dt:
        messagebox.showerror("Error", "Return Date cannot be before Issue Date!")
        return

    if not check_inventory_availability(sport_name):
        messagebox.showerror("Error", "This equipment is currently out of stock!")
        return

    existing_booking = collection.find_one({"reg_no": reg_no, "status": "Pending"})
    if existing_booking:
        messagebox.showerror("Error", "You already have a pending booking!")
        return

    existing_student = db["students"].find_one({"reg_no": reg_no})
    if existing_student:
        messagebox.showerror("Error", "This registration number is already in use!")
        return

    # Generate unique booking ID
    booking_id = get_next_booking_id()
    
    student_data = {
        "booking_id": booking_id,
        "name": name_entry.get(),
        "email": email_entry.get(),
        "mobile": mobile_entry.get(),
        "reg_no": reg_no,
        "branch": branch_var.get(),
        "year": year_var.get(),
        "sports": sport_name,
        "issue_date": issue_dt.strftime("%Y-%m-%d"),
        "return_date": return_dt.strftime("%Y-%m-%d"),
        "status": "Pending"
    }
    
    if "" in student_data.values():
        messagebox.showerror("Error", "All fields are required!")
        return
    
    collection.insert_one(student_data)
    
    if not update_inventory_on_booking(sport_name):
        messagebox.showerror("Error", "Failed to update inventory count!")
        return
    
    messagebox.showinfo("Success", f"Booking Registered Successfully! Your Booking ID: {booking_id}")
    reset_fields()

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

# Initialize counter if not exists
if not counter_collection.find_one({"_id": "booking_id"}):
    counter_collection.insert_one({"_id": "booking_id", "sequence_value": 0})

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

today = date.today()

tk.Label(root, text="Issue Date:").pack()
issue_date = DateEntry(root, width=12, background="darkblue", foreground="white", borderwidth=2, mindate=today)
issue_date.pack()
 
tk.Label(root, text="Return Date:").pack()
return_date = DateEntry(root, width=12, background="darkblue", foreground="white", borderwidth=2, mindate=today)
return_date.pack()

issue_date.bind("<<DateEntrySelected>>", update_return_date)

book_button = tk.Button(root, text="BOOK", command=book_equipment, bg="green", fg="white", font=("Arial", 12, "bold"))
book_button.pack(pady=20)

root.mainloop()