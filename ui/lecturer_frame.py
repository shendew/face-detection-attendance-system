
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from config import COL_LECTURERS, COL_SESSIONS, COL_ATTENDANCE
from database.db_handler import DatabaseHandler
import os
import threading
import PIL.Image

class LecturerFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseHandler()
        self.selected_image_path = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Manage Lecturers", font=("Roboto Medium", 20)).grid(row=0, column=0, pady=10, sticky="w", padx=20)

        # --- LEFT: FORM ---
        self.form_frame = ctk.CTkScrollableFrame(self, label_text="Add New Lecturer", width=400)
        self.form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.form_frame.grid_columnconfigure(1, weight=1)

        self.entries = {}
        self.create_entry("Lecturer ID", 0, state="readonly")
        self.create_entry("Lecturer Name", 1)
        self.create_entry("Email", 2)
        self.create_entry("Password", 3)

        self.btn_image = ctk.CTkButton(self.form_frame, text="Select Photo", command=self.select_image)
        self.btn_image.grid(row=4, column=0, padx=10, pady=10)
        self.lbl_image_path = ctk.CTkLabel(self.form_frame, text="No file selected")
        self.lbl_image_path.grid(row=4, column=1, sticky="w", padx=10)

        # Preview
        # Preview
        self._create_preview_label()

        # Buttons Container
        self.button_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.button_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=20)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        self.btn_save = ctk.CTkButton(self.button_frame, text="Save", command=self.save_lecturer)
        self.btn_save.grid(row=0, column=0, columnspan=2, padx=10, sticky="ew")

        self.btn_update = ctk.CTkButton(self.button_frame, text="Update", command=self.update_lecturer, fg_color="orange", hover_color="darkorange")
        self.btn_update.grid(row=0, column=0, padx=(10, 5), sticky="ew")
        self.btn_update.grid_remove()

        self.btn_delete = ctk.CTkButton(self.button_frame, text="Delete", command=self.delete_lecturer, fg_color="red", hover_color="darkred")
        self.btn_delete.grid(row=0, column=1, padx=(5, 10), sticky="ew")
        self.btn_delete.grid_remove()
        
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

        self.tree = ttk.Treeview(self.list_frame, columns=("ID", "Name", "Email"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Email", text="Email")
        self.tree.column("ID", width=80)
        self.tree.column("Name", width=220)
        self.tree.column("Email", width=230)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Progress
        self.progress = ctk.CTkProgressBar(self.list_frame, height=10, corner_radius=0)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.progress.grid_remove()
    
    def on_show(self):
        self.clear_form()
        self.load_lecturers()

    def _create_preview_label(self):
        self.lbl_preview = ctk.CTkLabel(self.form_frame, text="[No Image]", width=100, height=100)
        self.lbl_preview.grid(row=5, column=0, columnspan=2, pady=5)

    def create_entry(self, label_text, row, state="normal"):
        ctk.CTkLabel(self.form_frame, text=label_text).grid(row=row, column=0, padx=10, pady=5, sticky="e")
        entry = ctk.CTkEntry(self.form_frame, state=state)
        entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        key = label_text.lower().replace(" ", "_")
        self.entries[key] = entry

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
        if file_path:
            self.selected_image_path = file_path
            self.lbl_image_path.configure(text=os.path.basename(file_path))
            self._update_preview(file_path)

    def _update_preview(self, file_path):
        if not self.winfo_exists():
            return
            
        try:
            if file_path and os.path.exists(file_path):
                 img = PIL.Image.open(file_path)
                 self.current_image_ref = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                 self.lbl_preview.configure(image=self.current_image_ref, text="")
            else:
                 self.lbl_preview.configure(image=None, text="[No Image]")
                 self.current_image_ref = None
        except Exception as e:
            print(f"Preview Error: {e}. Recreating label.")
            if self.lbl_preview.winfo_exists():
                self.lbl_preview.destroy()
            self._create_preview_label()
            
            # Retry
            if self.current_image_ref:
                try:
                    self.lbl_preview.configure(image=self.current_image_ref, text="")
                except:
                    pass

    def load_lecturers(self):
        self.progress.grid()
        self.progress.start()
        threading.Thread(target=self._fetch_lecturers_thread, daemon=True).start()

    def _fetch_lecturers_thread(self):
        try:
            lecturers = self.db.find_all_documents(COL_LECTURERS)
            self.after(0, lambda: self._update_lecturer_list(lecturers))
        except Exception as e:
            print(e)
            self.after(0, lambda: self._update_lecturer_list(None))

    def _update_lecturer_list(self, lecturers):
        if not self.winfo_exists():
            return

        self.progress.stop()
        self.progress.grid_remove()
        
        if lecturers is None:
             # messagebox.showerror("Error", "Failed to load lecturers.") # Optional, might annoy on startup
             return

        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for l in lecturers:
            self.tree.insert("", "end", values=(l.get("lecturerId", ""), l.get("lecturerName", ""), l.get("lecturerEmail", "")))

    def on_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        item = self.tree.item(selected_item)
        lec_id = item['values'][0]
        
        lecturer = self.db.find_document(COL_LECTURERS, {"lecturerId": str(lec_id)})
        if lecturer:
            self.entries["lecturer_id"].configure(state="normal")
            self.entries["lecturer_id"].delete(0, 'end')
            self.entries["lecturer_id"].insert(0, lecturer.get("lecturerId", ""))
            self.entries["lecturer_id"].configure(state="readonly")
            
            self.entries["lecturer_name"].delete(0, 'end')
            self.entries["lecturer_name"].insert(0, lecturer.get("lecturerName", ""))
            
            self.entries["email"].delete(0, 'end')
            self.entries["email"].insert(0, lecturer.get("lecturerEmail", ""))
            
            self.entries["password"].delete(0, 'end')
            self.entries["password"].insert(0, lecturer.get("password", ""))

            self.selected_image_path = lecturer.get("lecturerPhoto", None)
            if self.selected_image_path:
                 self.lbl_image_path.configure(text=os.path.basename(self.selected_image_path))
                 self._update_preview(self.selected_image_path)
            else:
                 self.lbl_image_path.configure(text="No file selected")
                 self._update_preview(None)

            # Toggle Buttons
            self.btn_save.grid_remove()
            self.btn_update.grid(row=0, column=0, padx=(10, 5), sticky="ew")
            self.btn_delete.grid(row=0, column=1, padx=(5, 10), sticky="ew")

    def update_lecturer(self):
        lec_id = self.entries["lecturer_id"].get()
        if not lec_id:
            messagebox.showwarning("Warning", "Lecturer ID is required.")
            return

        data = {key: entry.get() for key, entry in self.entries.items()}
        
        # Validation
        if not data["lecturer_name"] or not data["email"] or not data["password"]:
             missing_fields = []
             if not data["lecturer_name"]: missing_fields.append("Name")
             if not data["email"]: missing_fields.append("Email")
             if not data["password"]: missing_fields.append("Password")
             messagebox.showwarning("Validation Error", f"Missing fields: {', '.join(missing_fields)}")
             return
        
        update_data = {
            "lecturerName": data["lecturer_name"],
            "lecturerEmail": data["email"],
            "password": data["password"],
            "lecturerPhoto": self.selected_image_path
        }

        if self.db.update_document(COL_LECTURERS, {"lecturerId": lec_id}, update_data):
            messagebox.showinfo("Success", "Lecturer updated successfully!")
            self.load_lecturers()
            self.clear_form()
        else:
            messagebox.showerror("Error", "Failed to update lecturer.")

    def delete_lecturer(self):
        lec_id = self.entries["lecturer_id"].get()
        if not lec_id:
            messagebox.showwarning("Warning", "Lecturer ID is required.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this lecturer?"):
            # Cascade: Delete all sessions and their attendance
            sessions = self.db.find_all_documents(COL_SESSIONS, {"lecturerId": lec_id})
            for s in sessions:
                self.db.delete_many_documents(COL_ATTENDANCE, {"lecId": s["lecId"]})
                self.db.delete_document(COL_SESSIONS, {"lecId": s["lecId"]})

            if self.db.delete_document(COL_LECTURERS, {"lecturerId": lec_id}):
                messagebox.showinfo("Success", "Lecturer deleted.")
                self.load_lecturers()
                self.clear_form()
            else:
                messagebox.showerror("Error", "Failed to delete lecturer.")

    def save_lecturer(self):
        data = {key: entry.get() for key, entry in self.entries.items()}
        
        # Validation (Exclude ID)
        required_fields = {k: v for k, v in data.items() if k != "lecturer_id"}
        if not all(required_fields.values()) or not self.selected_image_path:
            missing_fields = []
            if not data["lecturer_name"]: missing_fields.append("Name")
            if not data["email"]: missing_fields.append("Email")
            if not data["password"]: missing_fields.append("Password")
            if not self.selected_image_path: missing_fields.append("Photo")
            
            messagebox.showwarning("Validation Error", f"Missing fields: {', '.join(missing_fields)}")
            return

        lec_id = data["lecturer_id"]
        if not lec_id:
            lec_id = self.db.get_next_id(COL_LECTURERS, "lecturerId", "LEC")

        lecturer_doc = {
            "lecturerId": lec_id,
            "lecturerName": data["lecturer_name"],
            "lecturerEmail": data["email"],
            "password": data["password"],
            "lecturerPhoto": self.selected_image_path # Storing path for simplicity
        }

        if self.db.insert_document(COL_LECTURERS, lecturer_doc):
            messagebox.showinfo("Success", "Lecturer registered successfully!")
            self.load_lecturers()
            self.clear_form()
        else:
            messagebox.showerror("Database Error", "Failed to save lecturer.")

    def clear_form(self):
        for entry in self.entries.values():
            entry.configure(state="normal")
            entry.delete(0, 'end')
        
        # Reset ID to readonly
        if "lecturer_id" in self.entries:
            self.entries["lecturer_id"].configure(state="readonly")
            
        self.selected_image_path = None
        self.lbl_image_path.configure(text="No file selected")
        self._update_preview(None)
        
        # Auto-fill Next ID
        try:
            next_id = self.db.get_next_id(COL_LECTURERS, "lecturerId", "LEC")
            if "lecturer_id" in self.entries:
                entry = self.entries["lecturer_id"]
                entry.configure(state="normal")
                entry.delete(0, 'end')
                entry.insert(0, next_id)
                entry.configure(state="readonly")
        except Exception as e:
            print(f"Error fetching next ID: {e}")
        
        # Show Save button again, hide others
        self.btn_save.grid()
        self.btn_update.grid_remove()
        self.btn_delete.grid_remove()

    def cleanup(self):
        self.clear_form()
