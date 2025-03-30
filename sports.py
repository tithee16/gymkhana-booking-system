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
root.geometry("500x750")  # Adjusted window size

# Configure font sizes
LARGE_FONT = ("Arial", 12)
HEADING_FONT = ("Arial", 16, "bold")
BUTTON_FONT = ("Arial", 14, "bold")

# Main container with equal padding
main_container = tk.Frame(root, padx=40)
main_container.pack(expand=True, fill=tk.BOTH, pady=20)

# ========= LEFT SIDE: FORM FIELDS =========
left_frame = tk.Frame(main_container)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# ========= STUDENT INFORMATION SECTION =========
student_info_frame = tk.Frame(left_frame)
student_info_frame.pack(fill=tk.X, pady=(0, 20))

# Student Information Heading with increased spacing
tk.Label(student_info_frame, text="Student Information", font=HEADING_FONT).pack(anchor='w', pady=(0, 20))

# Form Fields (2-column layout)
form_frame = tk.Frame(student_info_frame)
form_frame.pack(fill=tk.X)

# Left Column - Labels
label_frame = tk.Frame(form_frame)
label_frame.pack(side=tk.LEFT)

# Right Column - Entry Fields
entry_frame = tk.Frame(form_frame)
entry_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)

# Create label-entry pairs with increased spacing
fields = [
    ("Name:", "name_entry"),
    ("Email ID:", "email_entry"),
    ("Mobile No:", "mobile_entry"),
    ("Registration No:", "reg_entry")
]

for text, var_name in fields:
    tk.Label(label_frame, text=text, anchor='e', width=15, font=LARGE_FONT).pack(pady=10, anchor='e')
    entry = tk.Entry(entry_frame, width=30, font=LARGE_FONT)
    entry.pack(pady=10, anchor='w')
    globals()[var_name] = entry

# Dropdown Fields with increased spacing
dropdowns = [
    ("Branch:", "branch_var", ["CS", "IT", "ExTC", "Electronics", "Electrical", 
     "Mechanical", "Civil", "Production", "Textile", "Chemical", "MCA", "Masters"]),
    ("Year:", "year_var", ["1st", "2nd", "3rd", "4th"]),
    ("Select Sport:", "sports_var", ["Football", "Basketball", "Volleyball", "Throwball", 
     "Cricket Bat", "Tennis Ball", "Season Ball", "Badminton Racket", "Shuttle Cock",
     "Table Tennis Racket", "Table Tennis Ball", "Carrom Striker", "Chess"])
]

for text, var_name, values in dropdowns:
    tk.Label(label_frame, text=text, anchor='e', width=15, font=LARGE_FONT).pack(pady=10, anchor='e')
    var = tk.StringVar()
    combobox = ttk.Combobox(entry_frame, textvariable=var, values=values, width=27, font=LARGE_FONT)
    combobox.pack(pady=10, anchor='w')
    globals()[var_name] = var

# ========= DATE SELECTION SECTION =========
dates_frame = tk.Frame(left_frame)
dates_frame.pack(fill=tk.X, pady=20)

# Date Fields Heading with increased spacing
tk.Label(dates_frame, text="Booking Dates", font=HEADING_FONT).pack(anchor='w', pady=(0, 20))

# Date selection fields
date_selection_frame = tk.Frame(dates_frame)
date_selection_frame.pack(fill=tk.X)

today = date.today()

tk.Label(date_selection_frame, text="Issue Date:", width=15, anchor='e', font=LARGE_FONT).pack(side=tk.LEFT, padx=5)
issue_date = DateEntry(date_selection_frame, width=12, background="darkblue", foreground="white", 
                      borderwidth=2, mindate=today, font=LARGE_FONT)
issue_date.pack(side=tk.LEFT, padx=5)

tk.Label(date_selection_frame, text="Return Date:", width=15, anchor='e', font=LARGE_FONT).pack(side=tk.LEFT, padx=5)
return_date = DateEntry(date_selection_frame, width=12, background="darkblue", foreground="white", 
                       borderwidth=2, mindate=today, font=LARGE_FONT)
return_date.pack(side=tk.LEFT, padx=5)

issue_date.bind("<<DateEntrySelected>>", update_return_date)

# BOOK Button aligned just below date fields
book_button_frame = tk.Frame(left_frame)
book_button_frame.pack(fill=tk.X, pady=(10, 20))

book_button = tk.Button(book_button_frame, text="BOOK", command=book_equipment, 
                       bg="green", fg="white", font=BUTTON_FONT,
                       width=15, pady=8)
book_button.pack()

# ========= RIGHT SIDE: ACTION BUTTONS =========
right_frame = tk.Frame(main_container)
right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20)

# Vertical buttons container
buttons_frame = tk.Frame(right_frame)
buttons_frame.pack(pady=20)

# Admin Button (stacked vertically)
admin_button = tk.Button(buttons_frame, text="Admin Panel", command=open_admin_panel, 
                        bg="blue", fg="white", font=BUTTON_FONT,
                        width=15, pady=8)
admin_button.pack(pady=10)

# Records Button (stacked vertically)
records_button = tk.Button(buttons_frame, text="Records", command=open_records_page, 
                          bg="orange", fg="white", font=BUTTON_FONT,
                          width=15, pady=8)
records_button.pack(pady=10)

root.mainloop()