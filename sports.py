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
counter_collection = db["counters"]

# Initialize counter if not exists
if not counter_collection.find_one({"_id": "booking_id"}):
    counter_collection.insert_one({"_id": "booking_id", "sequence_value": 0})

def get_next_booking_id():
    counter = counter_collection.find_one_and_update(
        {"_id": "booking_id"},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return f"B{counter['sequence_value']}"

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

# Main Window Setup
root = tk.Tk()
root.title("Sports Equipment Booking System")
root.geometry("600x750")  # Adjusted window size
root.resizable(True, True)  # Disable resizing

# Color Scheme
BG_COLOR = "#f0f2f5"
HEADER_COLOR = "#2c3e50"
ACCENT_COLOR = "#3498db"
BUTTON_COLOR = "#2980b9"
SUCCESS_COLOR = "#27ae60"
ERROR_COLOR = "#e74c3c"
TEXT_COLOR = "#2c3e50"
ENTRY_BG = "#ffffff"

# Font Configuration
SMALL_FONT = ("Segoe UI", 10)
MEDIUM_FONT = ("Segoe UI", 11, "bold")
HEADING_FONT = ("Segoe UI", 16, "bold")
BUTTON_FONT = ("Segoe UI", 12, "bold")

# Configure root background
root.configure(bg=BG_COLOR)

# Header Frame
header_frame = tk.Frame(root, bg=HEADER_COLOR, height=80)
header_frame.pack(fill=tk.X)

tk.Label(header_frame, text="SPORTS EQUIPMENT BOOKING", font=("Segoe UI", 18, "bold"), 
         bg=HEADER_COLOR, fg="white").pack(side=tk.LEFT, padx=20)

# Main Container
main_container = tk.Frame(root, padx=20, pady=20, bg=BG_COLOR)
main_container.pack(expand=True, fill=tk.BOTH)

# Form Container with card-like appearance
form_card = tk.Frame(main_container, bg="white", bd=2, relief=tk.RAISED, 
                    highlightbackground="#dfe6e9", highlightthickness=1)
form_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

# ========= FORM SECTION =========
form_frame = tk.Frame(form_card, padx=15, pady=15, bg="white")
form_frame.pack(fill=tk.BOTH, expand=True)

# Student Information Heading
tk.Label(form_frame, text="Student Information", font=HEADING_FONT, 
         bg="white", fg=TEXT_COLOR).pack(anchor='w', pady=(0, 15))

# Form Fields Grid
fields_frame = tk.Frame(form_frame, bg="white")
fields_frame.pack(fill=tk.X)

# Create form fields with consistent styling
fields = [
    ("Name:", "name_entry"),
    ("Email ID:", "email_entry"),
    ("Mobile No:", "mobile_entry"),
    ("Registration No:", "reg_entry")
]

for i, (text, var_name) in enumerate(fields):
    row_frame = tk.Frame(fields_frame, bg="white")
    row_frame.grid(row=i, column=0, sticky='ew', pady=5)
    
    tk.Label(row_frame, text=text, anchor='w', font=MEDIUM_FONT, 
             bg="white", fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
    
    entry = tk.Entry(row_frame, font=SMALL_FONT, width=30, 
                    bg=ENTRY_BG, fg=TEXT_COLOR, relief=tk.SOLID, borderwidth=1)
    entry.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
    globals()[var_name] = entry

# Dropdown Fields with consistent styling
dropdowns = [
    ("Branch:", "branch_var", ["CS", "IT", "ExTC", "Electronics", "Electrical", 
     "Mechanical", "Civil", "Production", "Textile", "Chemical", "MCA", "Masters"]),
    ("Year:", "year_var", ["1st", "2nd", "3rd", "4th"]),
    ("Select Sport:", "sports_var", ["Football", "Basketball", "Volleyball", "Throwball", 
     "Cricket Bat", "Tennis Ball", "Season Ball", "Badminton Racket", "Shuttle Cock",
     "Table Tennis Racket", "Table Tennis Ball", "Carrom Striker", "Chess"])
]

for i, (text, var_name, values) in enumerate(dropdowns, start=len(fields)):
    row_frame = tk.Frame(fields_frame, bg="white")
    row_frame.grid(row=i, column=0, sticky='ew', pady=5)
    
    tk.Label(row_frame, text=text, anchor='w', font=MEDIUM_FONT, 
             bg="white", fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
    
    var = tk.StringVar()
    combobox = ttk.Combobox(row_frame, textvariable=var, values=values, 
                           font=SMALL_FONT, width=27, state="readonly")
    combobox.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TCombobox', fieldbackground=ENTRY_BG, background=ENTRY_BG)
    globals()[var_name] = var

# Date Selection with improved styling
dates_frame = tk.Frame(form_frame, bg="white")
dates_frame.pack(fill=tk.X, pady=(15, 0))

tk.Label(dates_frame, text="Booking Dates", font=HEADING_FONT, 
         bg="white", fg=TEXT_COLOR).pack(anchor='w', pady=(0, 15))

date_selection_frame = tk.Frame(dates_frame, bg="white")
date_selection_frame.pack(fill=tk.X)

today = date.today()

# Issue Date
issue_date_frame = tk.Frame(date_selection_frame, bg="white")
issue_date_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

tk.Label(issue_date_frame, text="Issue Date:", font=MEDIUM_FONT, 
         bg="white", fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)

issue_date = DateEntry(issue_date_frame, width=12, background=ACCENT_COLOR, 
                      foreground="white", borderwidth=2, mindate=today, 
                      font=SMALL_FONT, date_pattern='yyyy-mm-dd')
issue_date.pack(side=tk.LEFT, padx=5)  # Changed to LEFT to bring it closer

# Return Date
return_date_frame = tk.Frame(date_selection_frame, bg="white")
return_date_frame.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.X, expand=True)

tk.Label(return_date_frame, text="Return Date:", font=MEDIUM_FONT, 
         bg="white", fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)

return_date = DateEntry(return_date_frame, width=12, background=ACCENT_COLOR, 
                       foreground="white", borderwidth=2, mindate=today, 
                       font=SMALL_FONT, date_pattern='yyyy-mm-dd')
return_date.pack(side=tk.LEFT, padx=5)  # Changed to LEFT to bring it closer

issue_date.bind("<<DateEntrySelected>>", update_return_date)

# Button Container (moved upwards)
button_container = tk.Frame(main_container, bg=BG_COLOR, pady=10)  # Reduced pady to bring it up
button_container.pack(fill=tk.X)

# BOOK Button
book_button = tk.Button(button_container, text="BOOK EQUIPMENT", command=book_equipment, 
                       bg=SUCCESS_COLOR, fg="white", font=BUTTON_FONT,
                       width=20, pady=8, relief=tk.FLAT, bd=0,
                       activebackground="#2ecc71", activeforeground="white")
book_button.pack(pady=10)

# ========= ACTION BUTTONS ========= (enlarged and moved upwards)
action_buttons_frame = tk.Frame(main_container, bg=BG_COLOR, pady=5)  # Reduced pady to bring it up
action_buttons_frame.pack(fill=tk.X)

# Admin Button (enlarged)
admin_button = tk.Button(action_buttons_frame, text="ADMIN PANEL", command=open_admin_panel, 
                        bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT,
                        width=18, pady=10, relief=tk.FLAT, bd=0,  # Increased width and pady
                        activebackground="#3498db", activeforeground="white")
admin_button.pack(side=tk.LEFT, padx=10, expand=True)

# Records Button (enlarged)
records_button = tk.Button(action_buttons_frame, text="VIEW RECORDS", command=open_records_page, 
                          bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT,
                          width=18, pady=10, relief=tk.FLAT, bd=0,  # Increased width and pady
                          activebackground="#3498db", activeforeground="white")
records_button.pack(side=tk.RIGHT, padx=10, expand=True)

# Footer
footer_frame = tk.Frame(root, bg=HEADER_COLOR, height=40)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
tk.Label(footer_frame, text="Sports Equipment Booking System © 2023", 
         bg=HEADER_COLOR, fg="white", font=("Segoe UI", 9)).pack(pady=10)

root.mainloop()