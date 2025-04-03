import tkinter as tk
from tkinter import ttk
from pymongo import MongoClient
from datetime import datetime

class BookingRecordsViewer:
    def __init__(self):
        # MongoDB Connection
        self.client = MongoClient("mongodb+srv://tithee:tithee@cluster0.elvlqwp.mongodb.net/")
        self.db = self.client["sports_db"]
        self.collection = self.db["booking"]
        
        # Create main window
        self.records_window = tk.Tk()
        self.records_window.title("Sports Equipment Booking System")
        self.records_window.geometry("1300x700")
        self.records_window.configure(bg="#f0f0f0")
        
        # Apply modern theme
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_container = tk.Frame(self.records_window, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#2c3e50")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            header_frame, 
            text="SPORTS EQUIPMENT BOOKING RECORDS", 
            font=("Segoe UI", 18, "bold"), 
            fg="white", 
            bg="#2c3e50",
            padx=20,
            pady=15
        ).pack()
        
        # Filter controls
        filter_frame = tk.Frame(main_container, bg="#f0f0f0")
        filter_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            filter_frame, 
            text="Filter by:", 
            font=("Segoe UI", 10), 
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.filter_var = tk.StringVar()
        filter_options = ["All", "Active (Pending)", "Returned"]
        for option in filter_options:
            tk.Radiobutton(
                filter_frame, 
                text=option, 
                variable=self.filter_var, 
                value=option,
                bg="#f0f0f0",
                font=("Segoe UI", 9),
                command=self.fetch_records
            ).pack(side=tk.LEFT, padx=5)
        
        self.filter_var.set("All")
        
        # Search box
        search_frame = tk.Frame(main_container, bg="#f0f0f0")
        search_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            search_frame, 
            text="Search:", 
            font=("Segoe UI", 10), 
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_entry = tk.Entry(
            search_frame, 
            font=("Segoe UI", 10), 
            width=40,
            relief=tk.GROOVE,
            borderwidth=1
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            search_frame, 
            text="Search", 
            command=self.fetch_records,
            bg="#3498db",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            search_frame, 
            text="Clear", 
            command=self.clear_search,
            bg="#95a5a6",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=15
        ).pack(side=tk.LEFT)
        
        # Table frame
        table_frame = tk.Frame(main_container)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        tree_scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        tree_scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        
        # Table columns
        columns = (
            "Booking ID", "Name", "Email", "Mobile", "Reg No", 
            "Branch", "Year", "Sport", "Issue Date", 
            "Return Date", "Status", "Days Left"
        )
        
        # Create Treeview with custom style
        self.style.configure("Treeview", 
                            font=("Segoe UI", 10), 
                            rowheight=25,
                            borderwidth=0,
                            highlightthickness=0)
        self.style.configure("Treeview.Heading", 
                            font=("Segoe UI", 10, "bold"),
                            background="#34495e",
                            foreground="white",
                            relief=tk.FLAT)
        self.style.map("Treeview.Heading",
                      background=[('active', '#2c3e50')])
        
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            xscrollcommand=tree_scroll_x.set,
            yscrollcommand=tree_scroll_y.set,
            height=15,
            selectmode="extended",
            style="Treeview"
        )
        
        # Configure scrollbars
        tree_scroll_x.config(command=self.tree.xview)
        tree_scroll_y.config(command=self.tree.yview)
        
        # Pack everything
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure columns
        col_widths = {
            "Booking ID": 100,
            "Name": 150,
            "Email": 180,
            "Mobile": 100,
            "Reg No": 100,
            "Branch": 120,
            "Year": 70,
            "Sport": 120,
            "Issue Date": 100,
            "Return Date": 100,
            "Status": 80,
            "Days Left": 80
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor="center")
        
        # Add tag configurations for row coloring
        self.tree.tag_configure('pending', background='#e8f4f8')
        self.tree.tag_configure('overdue', background='#ffdddd')
        self.tree.tag_configure('returned', background='#e8f8e8')
        
        # Button frame
        button_frame = tk.Frame(main_container, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Buttons
        tk.Button(
            button_frame, 
            text="Refresh", 
            command=self.fetch_records,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Export to CSV", 
            command=self.export_to_csv,
            bg="#2980b9",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Close", 
            command=self.records_window.destroy,
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=5
        ).pack(side=tk.RIGHT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(
            main_container, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Segoe UI", 9),
            bg="#dfe6e9",
            fg="#2d3436"
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Load initial data
        self.fetch_records()
        
    def fetch_records(self):
        self.status_var.set("Loading records...")
        self.records_window.update()
        
        try:
            # Clear existing data
            for record in self.tree.get_children():
                self.tree.delete(record)
            
            # Build query based on filters
            query = {}
            search_term = self.search_entry.get().strip()
            if search_term:
                query["$or"] = [
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"email": {"$regex": search_term, "$options": "i"}},
                    {"reg_no": {"$regex": search_term, "$options": "i"}},
                    {"booking_id": {"$regex": search_term, "$options": "i"}}
                ]
            
            filter_value = self.filter_var.get()
            if filter_value == "Active (Pending)":
                query["status"] = {"$in": ["Active", "Pending"]}  # Show both Active and Pending statuses
            elif filter_value == "Returned":
                query["status"] = "Returned"

            
            records = self.collection.find(query).sort("_id", -1)  # Newest first
            
            today = datetime.now().date()
            
            for record in records:
                # Calculate days left/overdue
                return_date_str = record.get("return_date", "")
                days_left = ""
                
                try:
                    return_date = datetime.strptime(return_date_str, "%Y-%m-%d").date()
                    delta = (return_date - today).days
                    if delta >= 0:
                        days_left = f"{delta} days"
                    else:
                        days_left = f"Overdue {-delta} days"
                except (ValueError, AttributeError):
                    pass
                
                # Determine row tag based on status
                status = record.get("status", "")
                tag = ""
                if status in ["Active", "Pending"]:
                    if days_left.startswith("Overdue"):
                        tag = "overdue"
                    else:
                        tag = "pending"
                elif status == "Returned":
                    tag = "returned"
                
                self.tree.insert("", "end", values=(
                    record.get("booking_id", ""), 
                    record.get("name", ""), 
                    record.get("email", ""),
                    record.get("mobile", ""), 
                    record.get("reg_no", ""), 
                    record.get("branch", ""),
                    record.get("year", ""), 
                    record.get("sports", ""), 
                    record.get("issue_date", ""),
                    return_date_str, 
                    status,
                    days_left
                ), tags=(tag,))
            
            self.status_var.set(f"Loaded {self.tree.get_children().__len__()} records | Filter: {filter_value}")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
    
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.fetch_records()
    
    def export_to_csv(self):
        # Placeholder for export functionality
        self.status_var.set("Export to CSV functionality would be implemented here")
    
    def run(self):
        self.records_window.mainloop()

if __name__ == "__main__":
    app = BookingRecordsViewer()
    app.run()