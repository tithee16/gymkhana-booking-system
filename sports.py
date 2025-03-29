import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from pymongo import MongoClient
from datetime import date
import uuid

# MongoDB Connection
client = MongoClient("mongodb+srv://tithee:tithee@cluster0.elvlqwp.mongodb.net/")
db = client["sports_db"]
students_collection = db["students"]
booking_collection = db["booking"]

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
    
    if return_dt < issue_dt:
        messagebox.showerror("Error", "Return Date cannot be before Issue Date!")
        return
    
    student_data = {
        "name": name_entry.get(),
        "email": email_entry.get(),
        "mobile": mobile_entry.get(),
        "reg_no": reg_entry.get(),
        "branch": branch_var.get(),
        "year": year_var.get()
    }
    
    booking_data = {
        "booking_id": str(uuid.uuid4()),
        "name": name_entry.get(),
        "reg_no": reg_entry.get(),
        "sports": sports_var.get(),
        "issue_date": issue_dt.strftime("%Y-%m-%d"),
        "return_date": return_dt.strftime("%Y-%m-%d"),
        "returned": False
    }
    
    if "" in student_data.values() or booking_data["sports"] == "":
        messagebox.showerror("Error", "All fields are required!")
        return
    
    students_collection.update_one({"reg_no": student_data["reg_no"]}, {"$set": student_data}, upsert=True)
    booking_collection.insert_one(booking_data)
    
    messagebox.showinfo("Success", "Booking Registered Successfully!")
    reset_fields()  # Clear all fields after booking

# Function to open admin panel (Placeholder)
def open_admin_panel():
    messagebox.showinfo("Admin Panel", "Admin Panel Coming Soon!")

# Function to open records page (Placeholder)
def open_records():
    messagebox.showinfo("Records", "Records Page Coming Soon!")

# GUI Window
root = tk.Tk()
root.title("Sports Equipment Booking System")
root.geometry("450x650")

# Admin & Records Buttons
top_frame = tk.Frame(root)
top_frame.pack(pady=10)

admin_button = tk.Button(top_frame, text="Admin Panel", command=open_admin_panel, bg="blue", fg="white", font=("Arial", 12, "bold"))
admin_button.pack(side=tk.LEFT, padx=10)

records_button = tk.Button(top_frame, text="Records", command=open_records, bg="orange", fg="white", font=("Arial", 12, "bold"))
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
