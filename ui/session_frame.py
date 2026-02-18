
import customtkinter as ctk
from tkinter import messagebox, ttk
from config import COL_SESSIONS, COL_LECTURERS, COL_DEPARTMENTS, COL_ATTENDANCE
from database.db_handler import DatabaseHandler
import threading
from datetime import datetime

class SessionFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseHandler()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Manage Sessions", font=("Roboto Medium", 20)).grid(row=0, column=0, pady=10, sticky="w", padx=20)

        # --- LEFT: FORM ---
        self.form_frame = ctk.CTkScrollableFrame(self, label_text="Create New Session", width=400)
        self.form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.form_frame.grid_columnconfigure(1, weight=1)

        self.entries = {}
        self.create_entry("Session ID", 0, state="readonly")
        self.create_entry("Title", 1)
        self.create_entry("Department", 2, is_combo=True, state="readonly")
        
        # Date defaults to today
        ctk.CTkLabel(self.form_frame, text="Date (YYYY-MM-DD)").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.entry_date = ctk.CTkEntry(self.form_frame)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Lecturer Dropdown
        ctk.CTkLabel(self.form_frame, text="Lecturer").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        
        self.combo_lecturer = ctk.CTkComboBox(self.form_frame, values=["Loading..."])
        self.combo_lecturer.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        # Load Lecturers Async (Handled in on_show)
        # threading.Thread(target=self._load_lecturers_thread, daemon=True).start()

        # Buttons Container
        self.button_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.button_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=20)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        self.btn_save = ctk.CTkButton(self.button_frame, text="Save", command=self.save_session)
        self.btn_save.grid(row=0, column=0, columnspan=2, padx=10, sticky="ew")

        self.btn_update = ctk.CTkButton(self.button_frame, text="Update", command=self.update_session, fg_color="orange", hover_color="darkorange")
        self.btn_update.grid(row=0, column=0, padx=(10, 5), sticky="ew")
        self.btn_update.grid_remove() # Hide initially

        self.btn_delete = ctk.CTkButton(self.button_frame, text="Delete", command=self.delete_session, fg_color="red", hover_color="darkred")
        self.btn_delete.grid(row=0, column=1, padx=(5, 10), sticky="ew")
        self.btn_delete.grid_remove() # Hide initially
        
        self.btn_clear = ctk.CTkButton(self.button_frame, text="Clear Form", command=self.clear_form, fg_color="gray", hover_color="darkgray")
        self.btn_clear.grid(row=1, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="ew")

        # --- RIGHT: LIST ---
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=10)
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.list_frame.grid_rowconfigure(0, weight=1)

        # Treeview Styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", rowheight=40, font=("Roboto", 12))
        style.map("Treeview", 
            background=[("selected", "#1f6aa5")],
            foreground=[("selected", "white"), ("!selected", "white")]
        )
        style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Roboto", 13, "bold"))

        # Treeview
        self.tree = ttk.Treeview(self.list_frame, columns=("ID", "Title", "Dept", "Date"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Dept", text="Dept")
        self.tree.heading("Date", text="Date")
        self.tree.column("ID", width=60)
        self.tree.column("Title", width=250)
        self.tree.column("Dept", width=80)
        self.tree.column("Date", width=100)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.progress = ctk.CTkProgressBar(self.list_frame, height=10, corner_radius=0)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.progress.grid_remove()

        # self.load_sessions() # MOVED TO ON_SHOW

    def on_show(self):
        self.clear_form() # Populate ID
        self.load_sessions()
        # Refresh lecturers dropdown as well
        threading.Thread(target=self._load_lecturers_thread, daemon=True).start()
        # Refresh Depts
        threading.Thread(target=self._load_depts_thread, daemon=True).start()

    def create_entry(self, label_text, row, is_combo=False, state="normal"):
        ctk.CTkLabel(self.form_frame, text=label_text).grid(row=row, column=0, padx=10, pady=5, sticky="e")
        
        if is_combo:
            widget = ctk.CTkComboBox(self.form_frame, values=["Loading..."], state=state)
        else:
            widget = ctk.CTkEntry(self.form_frame, state=state)

        widget.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        key = label_text.lower().replace(" ", "_")
        self.entries[key] = widget

    def _load_depts_thread(self):
        try:
             depts = self.db.find_all_documents(COL_DEPARTMENTS)
             dept_names = [d["name"] for d in depts]
             self.after(0, lambda: self.entries["department"].configure(values=dept_names if dept_names else ["No Depts"]))
        except Exception as e:
             print(f"Error loading depts: {e}")

    def _load_lecturers_thread(self):
        try:
            lecturers = self.db.find_all_documents(COL_LECTURERS)
            lecturer_names = [f"{l['lecturerId']} - {l['lecturerName']}" for l in lecturers]
            self.after(0, lambda: self._update_lecturer_combo(lecturer_names))
        except Exception as e:
            print(f"Error loading lecturers: {e}")
            self.after(0, lambda: self._update_lecturer_combo(None))

    def _update_lecturer_combo(self, values):
        if not self.winfo_exists():
            return

        if values:
            self.combo_lecturer.configure(values=values)
            self.combo_lecturer.set(values[0])
        else:
            self.combo_lecturer.configure(values=["No Lecturers Found"])
            self.combo_lecturer.set("No Lecturers Found")

    def load_sessions(self):
        self.progress.grid()
        self.progress.start()
        threading.Thread(target=self._fetch_sessions_thread, daemon=True).start()

    def _fetch_sessions_thread(self):
        try:
             sessions = self.db.find_all_documents(COL_SESSIONS)
             self.after(0, lambda: self._update_session_list(sessions))
        except Exception as e:
             print(e)
             self.after(0, lambda: self._update_session_list(None))
             
    def _update_session_list(self, sessions):
        if not self.winfo_exists():
            return

        self.progress.stop()
        self.progress.grid_remove()
        
        if sessions is None:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for s in sessions:
            self.tree.insert("", "end", values=(s.get("lecId", ""), s.get("lecTitle", ""), s.get("lecDept", ""), s.get("lecDate", "")))

    def on_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        item = self.tree.item(selected_item)
        sess_id = item['values'][0]
        
        session = self.db.find_document(COL_SESSIONS, {"lecId": str(sess_id)})
        if session:
            self.entries["session_id"].configure(state="normal")
            self.entries["session_id"].delete(0, 'end')
            self.entries["session_id"].insert(0, session.get("lecId", ""))
            self.entries["session_id"].configure(state="readonly")
            
            self.entries["title"].delete(0, 'end')
            self.entries["title"].insert(0, session.get("lecTitle", ""))
            
            self.entries["department"].configure(state="normal")
            self.entries["department"].set(session.get("lecDept", ""))
            self.entries["department"].configure(state="readonly")
            
            self.entry_date.delete(0, 'end')
            self.entry_date.insert(0, session.get("lecDate", ""))


            # Try to select lecturer in combo
            lec_id = session.get("lecturerId", "")
            # Find matching value in combo options
            found_lec = False
            current_values = self.combo_lecturer.cget("values")
            if current_values:
                for val in current_values:
                    if val.startswith(lec_id):
                        self.combo_lecturer.set(val)
                        found_lec = True
                        break
            
            if not found_lec:
                 # Set raw ID if not found in list (better than empty)
                 self.combo_lecturer.set(lec_id if lec_id else "")

            # Toggle buttons
            self.btn_save.grid_remove()
            self.btn_update.grid(row=0, column=0, padx=(10, 5), sticky="ew")
            self.btn_delete.grid(row=0, column=1, padx=(5, 10), sticky="ew")

    def update_session(self):
        sess_id = self.entries["session_id"].get()
        if not sess_id:
            messagebox.showwarning("Warning", "Session ID is required.")
            return

        data = {key: entry.get() for key, entry in self.entries.items()}
        lec_selection = self.combo_lecturer.get()
        date_str = self.entry_date.get()
        
        # Validation
        # Validation
        missing_fields = []
        if not data["title"]: missing_fields.append("Title")
        if not data["department"]: missing_fields.append("Department")
        if not date_str: missing_fields.append("Date")
        if not lec_selection or lec_selection == "No Lecturers Found": missing_fields.append("Lecturer")

        if missing_fields:
             messagebox.showwarning("Validation Error", f"Missing fields: {', '.join(missing_fields)}")
             return

        lecturer_id = lec_selection.split(" - ")[0] if lec_selection and lec_selection != "No Lecturers Found" else ""

        update_data = {
            "lecTitle": data["title"],
            "lecDept": data["department"],
            "lecDate": date_str,
            "lecturerId": lecturer_id
        }

        if self.db.update_document(COL_SESSIONS, {"lecId": sess_id}, update_data):
            messagebox.showinfo("Success", "Session updated successfully!")
            self.load_sessions()
            self.clear_form()
        else:
            messagebox.showerror("Error", "Failed to update session.")

    def delete_session(self):
        sess_id = self.entries["session_id"].get()
        if not sess_id:
            messagebox.showwarning("Warning", "Session ID is required.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this session?"):
            # Cascading delete: Remove attendance records first
            self.db.delete_many_documents(COL_ATTENDANCE, {"lecId": sess_id})
            
            if self.db.delete_document(COL_SESSIONS, {"lecId": sess_id}):
                messagebox.showinfo("Success", "Session deleted.")
                self.load_sessions()
                self.clear_form()
            else:
                messagebox.showerror("Error", "Failed to delete session.")

    def save_session(self):
        data = {key: entry.get() for key, entry in self.entries.items()}
        lec_selection = self.combo_lecturer.get()
        date_str = self.entry_date.get()

        if not all(data.values()) or not lec_selection or lec_selection == "No Lecturers Found":
             missing_fields = []
             if not data["title"]: missing_fields.append("Title")
             if not data["department"]: missing_fields.append("Department")
             if not date_str: missing_fields.append("Date")
             if not lec_selection or lec_selection == "No Lecturers Found": missing_fields.append("Lecturer")
             
             messagebox.showwarning("Validation Error", f"Missing fields: {', '.join(missing_fields)}")
             return

        lecturer_id = lec_selection.split(" - ")[0]

        session_doc = {
            "lecId": data["session_id"],
            "lecTitle": data["title"],
            "lecDept": data["department"],
            "lecDate": date_str,
            "lecturerId": lecturer_id
        }

        if self.db.insert_document(COL_SESSIONS, session_doc):
            messagebox.showinfo("Success", "Session created successfully!")
            self.load_sessions()
            self.clear_form()
        else:
            messagebox.showerror("Database Error", "Failed to save session.")

    def clear_form(self):
        for entry in self.entries.values():
            if isinstance(entry, ctk.CTkEntry):
                current_state = entry.cget("state")
                entry.configure(state="normal")
                entry.delete(0, 'end')
                if current_state == "readonly" and entry == self.entries.get("session_id"):
                     entry.configure(state="readonly")
            elif isinstance(entry, ctk.CTkComboBox):
                entry.set("")
        
        # Auto-fill Next ID
        try:
            next_id = self.db.get_next_id(COL_SESSIONS, "lecId", "SES")
            if "session_id" in self.entries:
                entry = self.entries["session_id"]
                entry.configure(state="normal")
                entry.delete(0, 'end')
                entry.insert(0, next_id)
                entry.configure(state="readonly")
        except Exception as e:
            print(f"Error fetching next ID: {e}")
        # Reset date
        self.entry_date.delete(0, 'end')
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Show Save button again, hide others
        self.btn_save.grid()
        self.btn_update.grid_remove()
        self.btn_delete.grid_remove()

    def cleanup(self):
        self.clear_form()
