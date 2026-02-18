
import customtkinter as ctk
import cv2
import PIL.Image, PIL.ImageTk
from tkinter import messagebox, filedialog, ttk
import os
from config import COL_SESSIONS, COL_STUDENTS, COL_ATTENDANCE
from database.db_handler import DatabaseHandler
from logic.face_handler import FaceHandler
import numpy as np
from datetime import datetime
import csv
import threading
from logic.pdf_generator import PDFGenerator
from logic.path_handler import PathHandler

class AttendanceFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseHandler()
        self.cap = None
        self.is_running = False
        self.known_encodings = {} # {id: encoding}
        self.students_cache = {} # {id: dept}
        self.current_session = None
        self.lock = threading.Lock()


        self.grid_columnconfigure(0, weight=3) # Video
        self.grid_columnconfigure(1, weight=1) # Sidebar
        self.grid_rowconfigure(2, weight=1) # Video Row
        self.grid_rowconfigure(3, weight=0) # Details Row

        # Header with Session Selection
        self.top_bar = ctk.CTkFrame(self)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.top_bar, text="Select Session:").pack(side="left", padx=10)
        
        self.combo_session = ctk.CTkComboBox(self.top_bar, values=["Loading..."], command=self.on_session_change)
        self.combo_session.pack(side="left", padx=10)
        
        # Helper to refresh sessions on click/show
        self.combo_session.bind("<Button-1>", lambda e: self.refresh_sessions_async())

        self.btn_start = ctk.CTkButton(self.top_bar, text="Start Attendance", command=self.start_attendance)
        self.btn_start.pack(side="left", padx=10)
        
        self.btn_stop = ctk.CTkButton(self.top_bar, text="Stop", command=self.stop_attendance, state="disabled", fg_color="red", hover_color="darkred")
        self.btn_stop.pack(side="left", padx=10)

        self.btn_view = ctk.CTkButton(self.top_bar, text="View Records", command=self.show_records, fg_color="blue", hover_color="darkblue")
        self.btn_view.pack(side="right", padx=10)

        self.btn_download_pdf = ctk.CTkButton(self.top_bar, text="Download PDF", command=self.download_pdf, fg_color="#E67E22", hover_color="#D35400")
        self.btn_download_pdf.pack(side="right", padx=10)

        # Status Label
        self.lbl_status = ctk.CTkLabel(self, text="Ready", font=("Roboto", 14))
        self.lbl_status.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.progress = ctk.CTkProgressBar(self, height=5, corner_radius=0)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(25,0)) # Overlay or just below status
        self.progress.grid_remove()

        # Video Feed (Left)
        self.video_frame = ctk.CTkFrame(self)
        self.video_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.video_frame.grid_columnconfigure(0, weight=1)
        self.video_frame.grid_rowconfigure(0, weight=1)
        
        self._create_video_label()
        
        # Sidebar (Right)
        self.sidebar = ctk.CTkFrame(self, width=300)
        self.sidebar.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.sidebar, text="Marked Students", font=("Roboto", 16, "bold")).grid(row=0, column=0, pady=10)

        # Live List
        # Live List Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", rowheight=30, font=("Roboto", 12))
        style.map("Treeview", 
            background=[("selected", "#1f6aa5")],
            foreground=[("selected", "white"), ("!selected", "white")]
        )
        style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Roboto", 13, "bold"))

        self.live_list = ttk.Treeview(self.sidebar, columns=("ID", "Name", "Time"), show="headings")
        self.live_list.heading("ID", text="Student ID")
        self.live_list.heading("Name", text="Name")
        self.live_list.heading("Time", text="Time")
        self.live_list.column("ID", width=80, anchor="center")
        self.live_list.column("Name", width=200, anchor="center")
        self.live_list.column("Time", width=100, anchor="center")
        self.live_list.grid(row=1, column=0, sticky="nsew", padx=5)
        self.live_list.bind("<<TreeviewSelect>>", self.on_live_select)

        # Details Panel (Bottom of Main Frame)
        self.details_frame = ctk.CTkFrame(self, fg_color="#333333", height=120)
        self.details_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.details_frame.grid_columnconfigure(1, weight=1)
        
        self._create_detail_image_label()
        
        # Text Info Container
        self.info_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)
        
        self.lbl_det_name = ctk.CTkLabel(self.info_frame, text="Name: -", font=("Roboto", 18, "bold"))
        self.lbl_det_name.pack(anchor="w")
        
        self.lbl_det_id = ctk.CTkLabel(self.info_frame, text="ID: -", font=("Roboto", 14))
        self.lbl_det_id.pack(anchor="w")
        
        self.lbl_det_dept = ctk.CTkLabel(self.info_frame, text="Dept: -", font=("Roboto", 14))
        self.lbl_det_dept.pack(anchor="w")
        
        self.marked_users = set()

        # Create blank image for camera off state
        self.blank_image = ctk.CTkImage(
            light_image=PIL.Image.new("RGB", (640, 480), "black"),
            dark_image=PIL.Image.new("RGB", (640, 480), "black"),
            size=(640, 480)
        )

        # Initial Load handled by on_show


    def cleanup(self):
        """Releases resources when frame is destroyed"""
        self.stop_attendance()
        self.is_running = False # Force stop threads
        if self.cap:
             self.cap.release()
             self.cap = None

    def on_show(self):
        self.refresh_sessions_async()

    def _create_video_label(self):
        self.lbl_video = ctk.CTkLabel(self.video_frame, text="Camera Feed Off")
        self.lbl_video.grid(row=0, column=0)

    def _create_detail_image_label(self):
        self.lbl_det_image = ctk.CTkLabel(self.details_frame, text="[No Photo]", width=100, height=100)
        self.lbl_det_image.grid(row=0, column=0, padx=10, pady=10)

    def refresh_sessions_async(self):
        self.show_loading(True)
        threading.Thread(target=self._load_sessions, daemon=True).start()

    def _load_sessions(self):
        try:
            sessions = self.db.find_all_documents(COL_SESSIONS)
            session_values = [f"{s['lecId']} - {s['lecTitle']}" for s in sessions]
            
            def update_ui():
                self.show_loading(False)
                self.combo_session.configure(values=session_values if session_values else ["No Sessions"])
                if session_values:
                    self.combo_session.set(session_values[0])
                    self.on_session_change(session_values[0])
                else:
                    self.combo_session.set("No Sessions")

            self.after(0, update_ui)
        except Exception as e:
            print(f"Error loading sessions: {e}")
            self.after(0, lambda: self.show_loading(False))

    def on_session_change(self, selection):
        if not selection or selection == "No Sessions" or selection == "Loading...":
            return
        
        session_id = selection.split(" - ")[0]
        # Fetch session in BG
        threading.Thread(target=self._update_session_and_load, args=(session_id,), daemon=True).start()

    def _update_session_and_load(self, session_id):
        try:
            self.current_session = self.db.find_document(COL_SESSIONS, {"lecId": session_id})
            if self.current_session:
                self.after(0, self.load_marked_students)
        except Exception as e:
            print(f"Error fetching session: {e}")

    def load_students_async(self):
        self.lbl_status.configure(text="Loading Student Data...")
        self.show_loading(True)
        threading.Thread(target=self._load_students, daemon=True).start()

    def _load_students(self):
        """Pre-load student encodings and depts"""
        try:
            students = self.db.find_all_documents(COL_STUDENTS)
            self.known_encodings = {}
            self.students_cache = {}
            for s in students:
                 if "face_encoding" in s and s["face_encoding"]:
                     self.known_encodings[s["userId"]] = FaceHandler.convert_list_to_encoding(s["face_encoding"])
                     self.students_cache[s["userId"]] = {
                         "dept": s.get("UserDept", ""),
                         "name": s.get("userName", "Unknown")
                     }
            self.after(0, lambda: self.lbl_status.configure(text="Ready to Start"))
            self.after(0, self.start_camera)
        except Exception as e:
            print(f"Error loading students: {e}")
            self.after(0, lambda: messagebox.showerror("Error", "Failed to load student data."))
        finally:
             self.after(0, lambda: self.show_loading(False))
             
    def show_loading(self, show):
        if show:
            self.progress.grid()
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.grid_remove()

    def start_attendance(self):
        selection = self.combo_session.get()
        if not selection or selection == "No Sessions" or selection == "Loading...":
            messagebox.showwarning("Warning", "Please select a valid session.")
            return

        session_id = selection.split(" - ")[0]
        # If current_session is missing (e.g. didn't wait for load), fetch it
        if not self.current_session or self.current_session["lecId"] != session_id:
             self.current_session = self.db.find_document(COL_SESSIONS, {"lecId": session_id})
        
        if not self.current_session:
             messagebox.showerror("Error", "Session not found!")
             return

        self.btn_start.configure(state="disabled")
        self.load_students_async()
        
    def start_camera(self):
        # We can refresh marked list here too just in case
        self.load_marked_students()

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
             messagebox.showerror("Error", "Could not open camera.")
             self.btn_start.configure(state="normal")
             return

        self.is_running = True
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text=f"Tracking Attendance for: {self.current_session['lecTitle']}")
        self.update_video()

    def stop_attendance(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None # Explicitly set to None
        
        try:
            # Force clear the image
            if self.lbl_video.winfo_exists():
                self.lbl_video.configure(image=self.blank_image, text="") 
                self.lbl_video.image = self.blank_image
            
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self.lbl_status.configure(text="Ready")
            
            # Clear details panel
            self.lbl_det_name.configure(text="Name: -")
            self.lbl_det_id.configure(text="ID: -")
            self.lbl_det_dept.configure(text="Dept: -")
            if self.lbl_det_image.winfo_exists():
                self.lbl_det_image.configure(image=None, text="[No Photo]")
                self.lbl_det_image.image = None
        except Exception as e:
            print(f"Error in stop_attendance UI cleanup: {e}")

    def update_video(self):
        if not self.is_running or not self.winfo_exists():
            return

        ret, frame = self.cap.read()
        if ret:
            # Resize for better performance
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small_frame = small_frame[:, :, ::-1] # BGR to RGB
            rgb_small_frame = np.ascontiguousarray(rgb_small_frame)

            # Face Recognition
            # Ensure face_recognition is imported. It is at the end of file, which is accessible.
            import face_recognition 

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Scale back up
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2

                user_id = FaceHandler.match_face(face_encoding, self.known_encodings)
                
                color = (0, 0, 255) # Red by default
                label = "Unknown"

                if user_id:
                    student_info = self.students_cache.get(user_id)
                    if student_info:
                        student_dept = student_info["dept"]
                        student_name = student_info["name"]
                        
                        # Validation Logic
                        if  student_dept.lower() == self.current_session["lecDept"].lower():
                            color = (0, 255, 0) # Green
                            label = f"{student_name} (Marked)"
                            threading.Thread(target=self.log_attendance, args=(user_id,), daemon=True).start()
                        else:
                            color = (0, 165, 255) # Orange
                            label = f"{student_name} (Wrong Dept)"

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, label, (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 0.6, color, 1)

            # Convert to Tkinter Image (CTkImage)
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(img)
            
            try:
                # Using CTkImage to fix HighDPI warning
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
                
                if self.winfo_exists():
                    self.lbl_video.configure(image=ctk_img, text="")
                    self.lbl_video.imgtk = ctk_img # Keep reference
            except Exception as e:
                print(f"Frame update error: {e}. Recreating label.")
                if self.lbl_video.winfo_exists():
                    self.lbl_video.destroy()
                self._create_video_label()
        
        self.after(20, self.update_video)

    def load_marked_students(self):
        # Clear current list
        for item in self.live_list.get_children():
            self.live_list.delete(item)
        self.marked_users = set()
        
        # Don't show global loading here as it might be frequent, 
        # but maybe a small status?
        threading.Thread(target=self._fetch_marked_thread, daemon=True).start()

    def _fetch_marked_thread(self):
        try:
            if not self.current_session:
                return

            records = self.db.find_all_documents(COL_ATTENDANCE, {"lecId": self.current_session["lecId"]})
            for r in records:
                self.marked_users.add(r["userId"])
                
                # Prepare UI data
                timestamp = r.get("timestamp", "")
                if isinstance(timestamp, datetime):
                    time_str = timestamp.strftime("%H:%M:%S")
                else:
                    time_str = "" 
                
                user_id = r["userId"]
                name = "Unknown" 
                
                if user_id in self.students_cache:
                    name = self.students_cache[user_id]["name"]
                else:
                    # Fallback fetch name if cache not ready
                    s = self.db.find_document(COL_STUDENTS, {"userId": user_id})
                    if s: name = s.get("userName", "Unknown")

                self.after(0, lambda n=name, t=time_str, u=user_id: self._add_to_live_list_safe(n, t, u))
        except Exception as e:
            print(f"Error loading marked: {e}")

    # Optimized log_attendance
    def log_attendance(self, user_id):
        with self.lock:
            if user_id in self.marked_users:
                return

            # Background thread safe logging
            try:
                query = {
                    "lecId": self.current_session["lecId"],
                    "userId": user_id,
                    "lecDate": self.current_session["lecDate"]
                }
                
                existing = self.db.find_document(COL_ATTENDANCE, query)
                if not existing:
                    timestamp = datetime.now()
                    attendance_record = {
                        "lecId": self.current_session["lecId"],
                        "userId": user_id,
                        "lecDate": self.current_session["lecDate"],
                        "timestamp": timestamp
                    }
                    self.db.insert_document(COL_ATTENDANCE, attendance_record)
                    print(f"Attendance marked for {user_id}")
                    
                    self.marked_users.add(user_id)
                    self.after(0, lambda: self._add_to_live_list_safe("Unknown", timestamp.strftime("%H:%M:%S"), user_id))
                    
                    # Live update details panel
                    self.after(0, lambda: self._fetch_student_details(user_id))
                else:
                     self.marked_users.add(user_id) # Cache it
            except Exception as e:
                print(f"Error logging attendance: {e}")

    def _add_to_live_list_safe(self, name, time_str, user_id):
        if not self.winfo_exists():
            return

        # Allow checking cache for name if "Unknown" passed
        if name == "Unknown" and user_id in self.students_cache:
            name = self.students_cache[user_id]["name"]
            
        # Check duplicates
        for child in self.live_list.get_children():
            # Check ID (Now 1st val, index 0)
            if self.live_list.item(child)["values"][0] == user_id:
                return

        self.live_list.insert("", 0, values=(user_id, name, time_str))

    def on_live_select(self, event):
        selected = self.live_list.selection()
        if not selected:
            return
        
        # Values: ID, Name, Time
        values = self.live_list.item(selected)["values"]
        if not values:
            return 
            
        user_id = str(values[0]) # ID is 1st
        
        # Fetch details (from cache or DB)
        # We have basic details in cache
        info = self.students_cache.get(user_id)
        if info:
            self.lbl_det_name.configure(text=f"Name: {info['name']}")
            self.lbl_det_dept.configure(text=f"Dept: {info['dept']}")
        
        self.lbl_det_id.configure(text=f"ID: {user_id}")
        
        # Fetch detailed info (Image + Name/Dept if missing) from DB
        threading.Thread(target=self._fetch_student_details, args=(user_id,), daemon=True).start()

    def _update_detail_image_ui(self, ctk_img, text=""):
        try:
             self.lbl_det_image.configure(image=ctk_img, text=text)
             self.lbl_det_image.image = ctk_img
        except Exception as e:
             print(f"Detail image update error: {e}. Recreating.")
             if self.lbl_det_image.winfo_exists():
                 self.lbl_det_image.destroy()
             self._create_detail_image_label()
             try:
                 self.lbl_det_image.configure(image=ctk_img, text=text)
                 self.lbl_det_image.image = ctk_img
             except: pass

    def _fetch_student_details(self, user_id):
        try:
            student = self.db.find_document(COL_STUDENTS, {"userId": user_id})
            
            # Update Text Fields (Safe update via after)
            name = student.get("userName", "-") if student else "-"
            dept = student.get("UserDept", "-") if student else "-"
            
            self.after(0, lambda: self.lbl_det_name.configure(text=f"Name: {name}"))
            self.after(0, lambda: self.lbl_det_id.configure(text=f"ID: {user_id}"))
            self.after(0, lambda: self.lbl_det_dept.configure(text=f"Dept: {dept}"))
            
            # Update Image
            if student and "image_path" in student:
                img_path = PathHandler.resolve_path(student["image_path"])
                if img_path and os.path.exists(img_path):
                    img = PIL.Image.open(img_path)
                    # Use CTkImage for HighDPI support
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(150, 150))
                    
                    self.after(0, lambda: self._update_detail_image_ui(ctk_img, ""))
                else:
                    self.after(0, lambda: self._update_detail_image_ui(None, "[Image Not Found]"))
            else:
                self.after(0, lambda: self._update_detail_image_ui(None, "[No Image]"))
        except Exception as e:
            print(f"Error loading details: {e}")

    def show_records(self):
        selection = self.combo_session.get()
        if not selection or selection == "No Sessions" or selection == "Loading...":
            messagebox.showwarning("Warning", "Please select a session.")
            return

        session_id = selection.split(" - ")[0]
        
        # Create Popup
        top = ctk.CTkToplevel(self)
        top.title(f"Attendance Records: {selection}")
        top.geometry("700x500")
        
        # Treeview
        from tkinter import ttk
        tree = ttk.Treeview(top, columns=("ID", "Name", "Time"), show="headings")
        tree.heading("ID", text="Student ID")
        tree.heading("Name", text="Name")
        tree.heading("Time", text="Timestamp")
        tree.column("ID", width=80, anchor="center")
        tree.column("Name", width=200, anchor="center")
        tree.column("Time", width=150, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Fetch Data in BG
        self.show_loading(True)
        
        def fetch():
            try:
                records = self.db.find_all_documents(COL_ATTENDANCE, {"lecId": session_id})
                for r in records:
                    timestamp = r.get("timestamp", "")
                    if isinstance(timestamp, datetime):
                        timestamp = timestamp.strftime("%H:%M:%S")
                    
                    user_id = r.get("userId")
                    name = "Unknown"
                    # Try cache first
                    if user_id in self.students_cache:
                        name = self.students_cache[user_id]["name"]
                    else:
                        # Fallback DB
                        s = self.db.find_document(COL_STUDENTS, {"userId": user_id})
                        if s: name = s.get("userName", "Unknown")

                    tree.insert("", "end", values=(user_id, name, timestamp))
            except Exception as e:
                print(e)
            finally:
                self.after(0, lambda: self.show_loading(False))
                
        threading.Thread(target=fetch, daemon=True).start()

    def download_pdf(self):
        selection = self.combo_session.get()
        if not selection or selection == "No Sessions": 
            messagebox.showwarning("Warning", "Please select a session to download.")
            return

        session_id = selection.split(" - ")[0]
        session_title = selection.split(" - ")[1] if " - " in selection else "Session"
        
        # Default filename
        default_file = f"Attendance_{session_id}_{session_title.replace(' ', '_')}.pdf"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_file
        )
        if not file_path:
            return

        self.btn_download_pdf.configure(state="disabled")
        self.show_loading(True)
        threading.Thread(target=self._generate_pdf_thread, args=(session_id, file_path), daemon=True).start()

    def _generate_pdf_thread(self, session_id, file_path):
        try:
            # 1. Get Session Data (Ensure we have it fresh)
            session = self.db.find_document(COL_SESSIONS, {"lecId": str(session_id)})
            if not session:
                 self.after(0, lambda: messagebox.showerror("Error", "Session not found."))
                 return

            # 2. Get Attendance Records
            records = self.db.find_all_documents(COL_ATTENDANCE, {"lecId": str(session_id)})
            
            # 3. Get Student Names
            student_ids = list(set([r['userId'] for r in records]))
            student_map = {}
            if student_ids:
                for uid in student_ids:
                    s = self.db.find_document(COL_STUDENTS, {"userId": uid})
                    if s:
                        student_map[uid] = s.get("userName", "Unknown")
            
            # 4. Generate
            success = PDFGenerator.generate_attendance_pdf(session, records, student_map, file_path)
            
            if success:
                self.after(0, lambda: messagebox.showinfo("Success", "Attendance PDF downloaded successfully."))
            else:
                self.after(0, lambda: messagebox.showerror("Error", "Failed to generate PDF."))
                
        except Exception as e:
             print(f"PDF Gen Error: {e}")
             self.after(0, lambda: messagebox.showerror("Error", f"Export failed: {e}"))
        finally:
             self.after(0, lambda: self.show_loading(False))
             self.after(0, lambda: self.btn_download_pdf.configure(state="normal"))

import face_recognition # Imported here to avoid lag on startup if possible, though usually top level is fine.
