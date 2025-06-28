# Footer
footer_frame = tk.Frame(root, bg=HEADER_COLOR, height=40)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
tk.Label(footer_frame, text="Sports Equipment Booking System © 2023", 
         bg=HEADER_COLOR, fg="white", font=("Segoe UI", 9)).pack(pady=10)