import tkinter as tk
from tkinter import ttk
from pymongo import MongoClient

# MongoDB Connection
client = MongoClient("mongodb+srv://tithee:tithee@cluster0.elvlqwp.mongodb.net/")
db = client["sports_db"]
collection = db["booking"]

def show_records():
    # Create records window
    records_window = tk.Tk()
    records_window.title("All Booking Records")
    records_window.geometry("1200x600")

    # Main frame
    main_frame = tk.Frame(records_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Title
    tk.Label(main_frame, text="Complete Booking History", font=("Arial", 16, "bold")).pack(pady=10)

    # Table frame
    table_frame = tk.Frame(main_frame)
    table_frame.pack(fill=tk.BOTH, expand=True)

    # Scrollbars
    tree_scroll_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
    tree_scroll_y = tk.Scrollbar(table_frame, orient=tk.VERTICAL)

    # Table columns
    columns = (
        "Booking ID", "Name", "Email", "Mobile", "Reg No", 
        "Branch", "Year", "Sport", "Issue Date", 
        "Return Date", "Status"
    )

    # Create Treeview
    tree = ttk.Treeview(
        table_frame, 
        columns=columns, 
        show="headings",
        xscrollcommand=tree_scroll_x.set,
        yscrollcommand=tree_scroll_y.set,
        height=20
    )

    # Configure scrollbars
    tree_scroll_x.config(command=tree.xview)
    tree_scroll_y.config(command=tree.yview)

    # Pack everything
    tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    # Configure columns
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", minwidth=100, stretch=tk.YES)

    def fetch_records():
        for record in tree.get_children():
            tree.delete(record)
        records = collection.find().sort("_id", -1)  # Newest first
        for record in records:
            tree.insert("", "end", values=(
                record.get("booking_id", ""), 
                record.get("name", ""), 
                record.get("email", ""),
                record.get("mobile", ""), 
                record.get("reg_no", ""), 
                record.get("branch", ""),
                record.get("year", ""), 
                record.get("sports", ""), 
                record.get("issue_date", ""),
                record.get("return_date", ""), 
                record.get("status", "")
            ))

    # Button frame
    button_frame = tk.Frame(main_frame)
    button_frame.pack(pady=10)

    # Refresh button
    tk.Button(button_frame, text="Refresh Records", command=fetch_records,
             bg="blue", fg="white", font=("Arial", 12, "bold"),
             padx=15, pady=5).pack()

    # Load initial data
    fetch_records()

    records_window.mainloop()

if __name__ == "__main__":
    show_records()