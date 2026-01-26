
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from config import COL_STUDENTS, COL_BATCHES, COL_DEPARTMENTS
from database.db_handler import DatabaseHandler
from logic.face_handler import FaceHandler
from logic.validators import validate_email, validate_non_empty
import os
import shutil
import threading
import PIL.Image

class StudentFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseHandler()
        self.selected_image_path = None
        self.entries = {}

        self.grid_columnconfigure(1, weight=1) # Give weight to list entry
        self.grid_rowconfigure(1, weight=1)

        # Header
        ctk.CTkLabel(self, text="Manage Students", font=("Roboto Medium", 20)).grid(row=0, column=0, pady=10, sticky="w", padx=20)

        # Content Split: Left (Form), Right (List)
        
        # --- LEFT: FORM ---
        self.form_frame = ctk.CTkScrollableFrame(self, label_text="Add New Student", width=400)
        self.form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.form_frame.grid_columnconfigure(1, weight=1)

        self.entries = {}

        # Fields
        self.create_entry("User ID", 0, state="readonly")
        self.create_entry("Full Name", 1)
        self.create_entry("Email", 2)
        self.create_entry("Batch", 3, is_combo=True)
        self.create_entry("Department", 4, is_combo=True)
        self.create_entry("Contact", 5)

        # Image Selection Section
        ctk.CTkLabel(self.form_frame, text="Photo").grid(row=6, column=0, padx=10, pady=5, sticky="ne")
        
        self.photo_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.photo_frame.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        
        self.btn_image = ctk.CTkButton(self.photo_frame, text="Select Photo", command=self.select_image, width=100)
        self.btn_image.grid(row=0, column=0, padx=(0, 5), pady=5)
        
        self.btn_camera = ctk.CTkButton(self.photo_frame, text="Capture", command=self.open_camera, width=100, fg_color="#E91E63", hover_color="#C2185B")
        self.btn_camera.grid(row=0, column=1, padx=5, pady=5)
        
        self.lbl_image_path = ctk.CTkLabel(self.photo_frame, text="No file selected", font=("Roboto", 12))
        self.lbl_image_path.grid(row=1, column=0, columnspan=2, sticky="w", padx=5)

        # Preview
        self.lbl_preview = ctk.CTkLabel(self.form_frame, text="[No Image]", width=100, height=100)
        self.lbl_preview.grid(row=7, column=0, columnspan=2, pady=5)

        # Buttons Row
        self.btn_save = ctk.CTkButton(self.form_frame, text="Save", command=self.save_student)
        self.btn_save.grid(row=8, column=0, padx=5, pady=20)
        
        self.btn_update = ctk.CTkButton(self.form_frame, text="Update", command=self.update_student, fg_color="orange", hover_color="darkorange")
        self.btn_update.grid(row=8, column=1, padx=5, pady=20)

        self.btn_delete = ctk.CTkButton(self.form_frame, text="Delete", command=self.delete_student, fg_color="red", hover_color="darkred")
        self.btn_delete.grid(row=9, column=0, columnspan=2, pady=5)
        
        self.btn_clear = ctk.CTkButton(self.form_frame, text="Clear Form", command=self.clear_form, fg_color="gray", hover_color="darkgray")
        self.btn_clear.grid(row=10, column=0, columnspan=2, pady=5)

        # --- RIGHT: LIST ---
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=10)
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.list_frame.grid_rowconfigure(0, weight=1)

        # Treeview Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", rowheight=30)
        style.map("Treeview", background=[("selected", "#1f6aa5")])
        style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Roboto", 10, "bold"))

        self.tree = ttk.Treeview(self.list_frame, columns=("ID", "Name", "Dept"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Dept", text="Dept")
        self.tree.column("ID", width=100)
        self.tree.column("Name", width=200)
        self.tree.column("Dept", width=100)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Progress Bar (Hidden by default)
        self.progress = ctk.CTkProgressBar(self.list_frame, height=10, corner_radius=0)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.progress.grid_remove()



    def on_show(self):
        self.load_students()
        threading.Thread(target=self._load_dropdowns, daemon=True).start()

    def _load_dropdowns(self):
        try:
            batches = self.db.find_all_documents(COL_BATCHES)
            depts = self.db.find_all_documents(COL_DEPARTMENTS)
            
            batch_vals = [b["name"] for b in batches] if batches else ["No Batches"]
            dept_vals = [d["name"] for d in depts] if depts else ["No Departments"]
            
            self.after(0, lambda v=batch_vals: self.entries["batch"].configure(values=v))
            self.after(0, lambda v=dept_vals: self.entries["department"].configure(values=v))
            
            # Default selection if needed? CTkComboBox usually selects first.
        except Exception as e:
            print(f"Error loading dropdowns: {e}")

    def create_entry(self, label_text, row, is_combo=False, state="normal"):
        label = ctk.CTkLabel(self.form_frame, text=label_text)
        label.grid(row=row, column=0, padx=10, pady=5, sticky="e")
        
        if is_combo:
            widget = ctk.CTkComboBox(self.form_frame, values=["Loading..."], state="readonly")
        else:
            widget = ctk.CTkEntry(self.form_frame, state=state)
            
        widget.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        # Store reference using label text as key (simplified)
        key = label_text.lower().replace(" ", "_")
        self.entries[key] = widget

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
        if file_path:
            self.set_image(file_path)

    def open_camera(self):
        from .camera_capture import CameraCaptureDialog
        CameraCaptureDialog(self, self.set_image)

    def set_image(self, file_path):
        if file_path:
            self.selected_image_path = file_path
            self.lbl_image_path.configure(text=os.path.basename(file_path))
            self._update_preview(file_path)

    def _update_preview(self, file_path):
        try:
            if file_path and os.path.exists(file_path):
                 img = PIL.Image.open(file_path)
                 ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                 self.lbl_preview.configure(image=ctk_img, text="")
            else:
                 self.lbl_preview.configure(image=None, text="[No Image]")
        except Exception as e:
            print(f"Preview Error: {e}")
            self.lbl_preview.configure(image=None, text="[Error]")

    def load_students(self):
        # Show Progress
        self.progress.grid()
        self.progress.start()
        
        # Disable buttons to prevent conflict
        self.btn_save.configure(state="disabled")
        
        threading.Thread(target=self._fetch_students_thread, daemon=True).start()

    def _fetch_students_thread(self):
        try:
            students = self.db.find_all_documents(COL_STUDENTS)
            self.after(0, lambda: self._update_student_list(students))
        except Exception as e:
            print(f"Error loading students: {e}")
            self.after(0, lambda: self._update_student_list(None))

    def _update_student_list(self, students):
        if not self.winfo_exists():
            return

        self.progress.stop()
        self.progress.grid_remove()
        self.btn_save.configure(state="normal")
        
        if students is None:
             messagebox.showerror("Error", "Failed to load students.")
             return

        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for s in students:
            self.tree.insert("", "end", values=(s.get("userId", ""), s.get("userName", ""), s.get("UserDept", "")))

    def on_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        item = self.tree.item(selected_item)
        user_id = item['values'][0]
        
        # Fetch full details
        student = self.db.find_document(COL_STUDENTS, {"userId": str(user_id)})
        if student:
            self.entries["user_id"].configure(state="normal")
            self.entries["user_id"].delete(0, 'end')
            self.entries["user_id"].insert(0, student.get("userId", ""))
            self.entries["user_id"].configure(state="readonly")
            
            self.entries["full_name"].delete(0, 'end')
            self.entries["full_name"].insert(0, student.get("userName", ""))
            
            self.entries["email"].delete(0, 'end')
            self.entries["email"].insert(0, student.get("userEmail", ""))
            
            self.entries["batch"].set(student.get("UserBatch", ""))
            self.entries["department"].set(student.get("UserDept", ""))
            
            self.entries["contact"].delete(0, 'end')
            self.entries["contact"].insert(0, student.get("userContact", ""))
            
            self.selected_image_path = student.get("image_path", None)
            if self.selected_image_path:
                 self.lbl_image_path.configure(text=os.path.basename(self.selected_image_path))
                 self._update_preview(self.selected_image_path)
            else:
                 self.lbl_image_path.configure(text="No file selected")
                 self._update_preview(None)
                 
            # Disable ID edit to prevent primary key change issues (optional, but good practice)
            # self.entries["user_id"].configure(state="disabled") 

    def update_student(self):
        user_id = self.entries["user_id"].get()
        if not user_id:
            messagebox.showwarning("Warning", "User ID is required for update.")
            return

        data = {key: entry.get() for key, entry in self.entries.items()}
        
        # Validation
        if not validate_email(data["email"]):
             messagebox.showwarning("Validation Error", "Invalid Email Address!")
             return
        
        update_data = {
            "userName": data["full_name"],
            "userEmail": data["email"],
            "UserBatch": data["batch"],
            "UserDept": data["department"],
            "userContact": data["contact"],
            "image_path": self.selected_image_path
        }
        
        # Re-encode if image changed (or just always re-encode if path exists)
        if self.selected_image_path:
             try:
                 encoding = FaceHandler.encode_face(self.selected_image_path)
                 if encoding is not None:
                     update_data["face_encoding"] = FaceHandler.convert_encoding_to_list(encoding)
             except:
                 pass

        if self.db.update_document(COL_STUDENTS, {"userId": user_id}, update_data):
            messagebox.showinfo("Success", "Student updated successfully!")
            self.load_students()
            self.clear_form()
        else:
            messagebox.showerror("Error", "Failed to update student.")

    def delete_student(self):
        user_id = self.entries["user_id"].get()
        if not user_id:
            messagebox.showwarning("Warning", "User ID is required.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this student?"):
            if self.db.delete_document(COL_STUDENTS, {"userId": user_id}):
                messagebox.showinfo("Success", "Student deleted.")
                self.load_students()
                self.clear_form()
            else:
                messagebox.showerror("Error", "Failed to delete student.")

    def save_student(self):
        data = {key: entry.get() for key, entry in self.entries.items()}
        
        # Validation
        # Check all required fields (Exclude ID as it is auto-generated)
        required_fields = {k: v for k, v in data.items() if k != "user_id"}
        if not all(required_fields.values()) or not self.selected_image_path:
            messagebox.showwarning("Validation Error", "All fields and photo are required!")
            return

        if not validate_email(data["email"]):
             messagebox.showwarning("Validation Error", "Invalid Email Address!")
             return

        # Encode Face
        try:
            encoding = FaceHandler.encode_face(self.selected_image_path)
            if encoding is None:
                messagebox.showerror("Face Error", "No face detected in the selected photo!")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error processing image: {e}")
            return
            
        # Auto-generate ID if empty
        user_id = data["user_id"]
        if not user_id:
            user_id = self.db.get_next_id(COL_STUDENTS, "userId", "STU")

        # Prepare Data
        student_doc = {
            "userId": user_id,
            "userName": data["full_name"],
            "userEmail": data["email"],
            "UserBatch": data["batch"],
            "UserDept": data["department"],
            "userContact": data["contact"],
            "face_encoding": FaceHandler.convert_encoding_to_list(encoding),
            # Ideally store image path or bytes
            "image_path": self.selected_image_path 
        }

        # Insert to DB
        if self.db.insert_document(COL_STUDENTS, student_doc):
            messagebox.showinfo("Success", f"Student registered successfully! ID: {user_id}")
            self.load_students() # Refresh List
            self.clear_form()
        else:
            messagebox.showerror("Database Error", "Failed to save student.")

    def clear_form(self):
        for entry in self.entries.values():
            if isinstance(entry, ctk.CTkEntry):
                current_state = entry.cget("state")
                entry.configure(state="normal")
                entry.delete(0, 'end')
                if current_state == "readonly" and entry == self.entries.get("user_id"):
                     entry.configure(state="readonly")
                # For others, keep normal. The loop sets all normal then delete. 
                # only ID is readonly.
                
                # Re-apply readonly to user_id specifically
                if entry == self.entries.get("user_id"):
                    entry.configure(state="readonly")
                
            elif isinstance(entry, ctk.CTkComboBox):
                entry.set("")
        self.selected_image_path = None
        self.lbl_image_path.configure(text="No file selected")
        self._update_preview(None)

    def cleanup(self):
        self.clear_form()
