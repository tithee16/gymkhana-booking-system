import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from pymongo import MongoClient
from datetime import datetime, date, timedelta
import subprocess
import re

# MongoDB Connection
client = MongoClient("mongodb+srv://tithee:tithee@cluster0.elvlqwp.mongodb.net/")
db = client["sports_db"]
collection = db["booking"]
counter_collection = db["counters"]
students_collection = db["students"]  # Collection for student records

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

def extract_branch_from_email(email):
    """Extract branch from email in format username@branch.vjti.ac.in"""
    if not email or '@' not in email or '.vjti.ac.in' not in email:
        return None
    
    domain_part = email.split('@')[1]
    branch_code = domain_part.split('.')[0].lower()
    
    branch_mapping = {
        'ce': 'CS',
        'it': 'IT',
        'et': 'ExTC',
        'el': 'Electronics',
        'ee': 'Electrical',
        'me': 'Mechanical',
        'ci': 'Civil',
        'pe': 'Production',
        'tx': 'Textile',
        'cc': 'Chemical',
        'mc': 'MCA',
        'ms': 'Masters'
    }
    
    return branch_mapping.get(branch_code)

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
    """Set the maximum return date to 15 days from issue date"""
    issue_dt = issue_date.get_date()
    max_return_date = issue_dt + timedelta(days=15)
    return_date.config(mindate=issue_dt, maxdate=max_return_date)
    if return_date.get_date() > max_return_date:
        return_date.set_date(max_return_date)

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

def is_valid_email():
    email = email_entry.get()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.vjti\.ac\.in$'
    return re.match(pattern, email) is not None

def fetch_student_data(reg_no):
    """Fetch student data from database based on registration number"""
    student = students_collection.find_one({"reg_no": reg_no})
    if student:
        return student
    return None

def autofill_student_data(event=None):
    """Autofill form fields when registration number matches existing student"""
    reg_no = reg_entry.get()
    
    if len(reg_no) == 9 and reg_no.isdigit():
        student = fetch_student_data(reg_no)
        if student:
            name_entry.delete(0, tk.END)
            name_entry.insert(0, student.get('name', ''))
            
            email_entry.delete(0, tk.END)
            email_entry.insert(0, student.get('email', ''))
            
            mobile_entry.delete(0, tk.END)
            mobile_entry.insert(0, student.get('mobile', ''))
            
            branch_var.set(student.get('branch', ''))
            year_var.set(student.get('year', ''))
            
            if student.get('email', ''):
                email_event = type('Event', (), {'widget': email_entry})()
                on_email_focus_out(email_event)

def book_equipment():
    issue_dt = issue_date.get_date()
    return_dt = return_date.get_date()

    if return_dt < issue_dt:
        messagebox.showerror("Error", "Return Date cannot be before Issue Date!")
        return
    
    reg_no = reg_entry.get()
    sport_name = sports_var.get()

    if not check_inventory_availability(sport_name):
        messagebox.showerror("Error", "This equipment is currently out of stock!")
        return

    existing_booking = collection.find_one({"reg_no": reg_no, "status": "Pending"})
    if existing_booking:
        messagebox.showerror("Error", "You already have a pending booking!")
        return

    if not is_valid_mobile():
        messagebox.showerror("Error", "Mobile number must be exactly 10 digits")
        mobile_entry.focus_set()
        return
        
    if not is_valid_email():
        messagebox.showerror("Error", "Email must be a valid VJTI email (username@branch.vjti.ac.in)")
        email_entry.focus_set()
        return
    
    if not is_valid_registration():
        messagebox.showerror("Error", "Registration number must be exactly 9 digits")
        reg_entry.focus_set()
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
    
    if not students_collection.find_one({"reg_no": reg_no}):
        students_collection.insert_one({
            "reg_no": reg_no,
            "name": student_data["name"],
            "email": student_data["email"],
            "mobile": student_data["mobile"],
            "branch": student_data["branch"],
            "year": student_data["year"]
        })
    
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

def validate_numeric_input(new_value, max_length):
    if new_value == "":
        return True
    if not new_value.isdigit():
        return False
    if len(new_value) > max_length:
        return False
    return True

def validate_mobile(new_value):
    return validate_numeric_input(new_value, 10)

def validate_registration(new_value):
    return validate_numeric_input(new_value, 9)

def is_valid_mobile():
    mobile = mobile_entry.get()
    return len(mobile) == 10 and mobile.isdigit()

def is_valid_registration():
    reg_no = reg_entry.get()
    return len(reg_no) == 9 and reg_no.isdigit()

def on_email_focus_out(event):
    """Auto-fill branch when email is entered"""
    email = email_entry.get()
    if email:
        branch = extract_branch_from_email(email)
        if branch:
            branch_var.set(branch)
            branch_dropdown.config(background='#e6ffe6')
            branch_dropdown.after(1000, lambda: branch_dropdown.config(background='white'))

# Main Window Setup
root = tk.Tk()
root.title("Sports Equipment Booking System")
root.geometry("600x750")
root.resizable(True, True)

validate_mobile_cmd = root.register(validate_mobile)
validate_reg_cmd = root.register(validate_registration)

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

root.configure(bg=BG_COLOR)

# Header Frame
header_frame = tk.Frame(root, bg=HEADER_COLOR, height=80)
header_frame.pack(fill=tk.X)

tk.Label(header_frame, text="SPORTS EQUIPMENT BOOKING", font=("Segoe UI", 18, "bold"), 
         bg=HEADER_COLOR, fg="white").pack(side=tk.LEFT, padx=20)

# Main Container
main_container = tk.Frame(root, padx=20, pady=20, bg=BG_COLOR)
main_container.pack(expand=True, fill=tk.BOTH)

# Form Container
form_card = tk.Frame(main_container, bg="white", bd=2, relief=tk.RAISED, 
                    highlightbackground="#dfe6e9", highlightthickness=1)
form_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

# Form Section
form_frame = tk.Frame(form_card, padx=15, pady=15, bg="white")
form_frame.pack(fill=tk.BOTH, expand=True)

tk.Label(form_frame, text="Student Information", font=HEADING_FONT, 
         bg="white", fg=TEXT_COLOR).pack(anchor='w', pady=(0, 15))

fields_frame = tk.Frame(form_frame, bg="white")
fields_frame.pack(fill=tk.X)

# Create form fields
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
    
    if var_name == "mobile_entry":
        entry = tk.Entry(row_frame, font=SMALL_FONT, width=30, 
                        bg=ENTRY_BG, fg=TEXT_COLOR, relief=tk.SOLID, borderwidth=1,
                        validate="key", validatecommand=(validate_mobile_cmd, '%P'))
    elif var_name == "reg_entry":
        entry = tk.Entry(row_frame, font=SMALL_FONT, width=30, 
                        bg=ENTRY_BG, fg=TEXT_COLOR, relief=tk.SOLID, borderwidth=1,
                        validate="key", validatecommand=(validate_reg_cmd, '%P'))
    else:
        entry = tk.Entry(row_frame, font=SMALL_FONT, width=30, 
                        bg=ENTRY_BG, fg=TEXT_COLOR, relief=tk.SOLID, borderwidth=1)
    
    entry.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
    globals()[var_name] = entry

reg_entry.bind('<KeyRelease>', autofill_student_data)

# Dropdown Fields
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
    if var_name == "branch_var":
        branch_dropdown = combobox

email_entry.bind('<FocusOut>', on_email_focus_out)

# Date Selection
dates_frame = tk.Frame(form_frame, bg="white")
dates_frame.pack(fill=tk.X, pady=(15, 0))

tk.Label(dates_frame, text="Booking Dates", font=HEADING_FONT, 
         bg="white", fg=TEXT_COLOR).pack(anchor='w', pady=(0, 15))

date_selection_frame = tk.Frame(dates_frame, bg="white")
date_selection_frame.pack(fill=tk.X)

today = date.today()

# Create both frames first
issue_date_frame = tk.Frame(date_selection_frame, bg="white")
issue_date_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

return_date_frame = tk.Frame(date_selection_frame, bg="white")
return_date_frame.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.X, expand=True)

# Populate issue date frame
tk.Label(issue_date_frame, text="Issue Date:", font=MEDIUM_FONT, 
         bg="white", fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)

issue_date = DateEntry(
    issue_date_frame,
    width=12,
    background=ACCENT_COLOR,
    foreground="white",
    borderwidth=2,
    mindate=today,
    font=SMALL_FONT,
    date_pattern='yyyy-mm-dd'
)
issue_date.set_date(today)
issue_date.pack(side=tk.LEFT, padx=5)
issue_date.bind("<<DateEntrySelected>>", update_return_date)

# Populate return date frame
tk.Label(return_date_frame, text="Return Date:", font=MEDIUM_FONT, 
         bg="white", fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)

return_date = DateEntry(
    return_date_frame,
    width=12,
    background=ACCENT_COLOR,
    foreground="white",
    borderwidth=2,
    mindate=today,
    font=SMALL_FONT,
    date_pattern='yyyy-mm-dd'
)
return_date.set_date(today)
return_date.pack(side=tk.LEFT, padx=5)

# Initialize the return date limits
update_return_date()

# Buttons
button_container = tk.Frame(main_container, bg=BG_COLOR, pady=10)
button_container.pack(fill=tk.X)

book_button = tk.Button(button_container, text="BOOK EQUIPMENT", command=book_equipment, 
                       bg=SUCCESS_COLOR, fg="white", font=BUTTON_FONT,
                       width=20, pady=8, relief=tk.FLAT, bd=0,
                       activebackground="#2ecc71", activeforeground="white")
book_button.pack(pady=10)

action_buttons_frame = tk.Frame(main_container, bg=BG_COLOR, pady=5)
action_buttons_frame.pack(fill=tk.X)

admin_button = tk.Button(action_buttons_frame, text="ADMIN PANEL", command=open_admin_panel, 
                        bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT,
                        width=18, pady=10, relief=tk.FLAT, bd=0,
                        activebackground="#3498db", activeforeground="white")
admin_button.pack(side=tk.LEFT, padx=10, expand=True)

records_button = tk.Button(action_buttons_frame, text="VIEW RECORDS", command=open_records_page, 
                          bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT,
                          width=18, pady=10, relief=tk.FLAT, bd=0,
                          activebackground="#3498db", activeforeground="white")
records_button.pack(side=tk.RIGHT, padx=10, expand=True)

# Footer
footer_frame = tk.Frame(root, bg=HEADER_COLOR, height=40)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
tk.Label(footer_frame, text="Sports Equipment Booking System © 2023", 
         bg=HEADER_COLOR, fg="white", font=("Segoe UI", 9)).pack(pady=10)

root.mainloop()