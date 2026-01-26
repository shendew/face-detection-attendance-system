
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from database.db_handler import DatabaseHandler
from config import COL_SESSIONS, COL_ATTENDANCE, COL_STUDENTS
from logic.pdf_generator import PDFGenerator
from logic.session_manager import SessionManager
import threading
import os

class LecturerDashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseHandler()
        self.lecturer_data = None
        
        # Grid Config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # header
        self.header = ctk.CTkFrame(self, height=50)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.lbl_welcome = ctk.CTkLabel(self.header, text="Welcome, Lecturer", font=("Roboto Medium", 20))
        self.lbl_welcome.pack(side="left", padx=20)
        
        self.btn_logout = ctk.CTkButton(self.header, text="Logout", fg_color="red", command=self.logout, width=80)
        self.btn_logout.pack(side="right", padx=20)

        # Content - Session List
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        
        # Treeview
        columns = ("ID", "Title", "Date", "Dept", "Action")
        self.tree = ttk.Treeview(self.content, columns=columns, show="headings")
        self.tree.heading("ID", text="Session ID")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Dept", text="Dept")
        self.tree.heading("Action", text="Status") # Just visual for now
        
        self.tree.column("ID", width=100)
        self.tree.column("Title", width=200)
        self.tree.column("Date", width=100)
        self.tree.column("Dept", width=100)
        self.tree.column("Action", width=100)

        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        sb = ttk.Scrollbar(self.content, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        # Actions Panel
        self.actions = ctk.CTkFrame(self)
        self.actions.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        self.btn_download = ctk.CTkButton(self.actions, text="Download Attendance PDF", command=self.download_pdf)
        self.btn_download.pack(pady=10)
        
        self.progress = ctk.CTkProgressBar(self.actions, orientation="horizontal", mode="indeterminate")
        # self.progress.pack(pady=5) # Show when downloading

    def on_show(self):
        # Load user info
        # Try from controller , then session
        user_data = getattr(self.controller, "current_user", None)
        if not user_data:
            session = SessionManager.load_session()
            if session and session.get("role") == "lecturer":
                 user_data = session.get("user_data")
        
        if user_data:
            self.lecturer_data = user_data
            self.lbl_welcome.configure(text=f"Welcome, {user_data.get('lecturerName', 'Lecturer')}")
            self.load_sessions(user_data.get("lecturerId"))
        else:
            # Fallback or error
            self.lbl_welcome.configure(text="Welcome, Lecturer")

    def load_sessions(self, lecturer_id):
        # Clear tree
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        threading.Thread(target=self._fetch_sessions, args=(lecturer_id,), daemon=True).start()

    def _fetch_sessions(self, lecturer_id):
        try:
            # Find sessions where lecturerId matches
            sessions = self.db.find_all_documents(COL_SESSIONS, {"lecturerId": lecturer_id})
            
            def update():
                if sessions:
                    for s in sessions:
                        self.tree.insert("", "end", values=(
                            s.get("lecId"), 
                            s.get("lecTitle"), 
                            s.get("lecDate"), 
                            s.get("lecDept"), 
                            "Active" 
                        ))
                else:
                    self.tree.insert("", "end", values=("No Sessions Found", "", "", "", ""))
                    
            self.after(0, update)
        except Exception as e:
            print(f"Error fetching sessions: {e}")

    def download_pdf(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Session", "Please select a session to download attendance.")
            return
        
        item = self.tree.item(selected[0])
        session_id = item['values'][0]
        session_title = item['values'][1]
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Attendance_{session_id}_{session_title}.pdf"
        )
        
        if not file_path:
            return

        self.btn_download.configure(state="disabled")
        self.progress.pack(pady=5)
        self.progress.start()
        
        threading.Thread(target=self._generate_pdf_thread, args=(session_id, file_path), daemon=True).start()

    def _generate_pdf_thread(self, session_id, file_path):
        try:
            # 1. Get Session Data
            session = self.db.find_document(COL_SESSIONS, {"lecId": str(session_id)})
            
            # 2. Get Attendance Records
            records = self.db.find_all_documents(COL_ATTENDANCE, {"lecId": str(session_id)})
            
            # 3. Get Student Names for these records
            student_ids = list(set([r['userId'] for r in records]))
            student_map = {}
            if student_ids:
                # Optimized: in real app use $in query, here loop is fine for small scale
                for uid in student_ids:
                    s = self.db.find_document(COL_STUDENTS, {"userId": uid})
                    if s:
                        student_map[uid] = s.get("userName", "Unknown")
            
            # 4. Generate
            success = PDFGenerator.generate_attendance_pdf(session, records, student_map, file_path)
            
            self.after(0, lambda: self._post_download(success))
            
        except Exception as e:
            print(f"PDF Gen Error: {e}")
            self.after(0, lambda: self._post_download(False))

    def _post_download(self, success):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_download.configure(state="normal")
        if success:
            messagebox.showinfo("Success", "Attendance PDF downloaded successfully.")
        else:
            messagebox.showerror("Error", "Failed to generate PDF.")

    def logout(self):
        if not messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            return

        SessionManager.clear_session()
        self.controller.current_user = None
        self.controller.show_frame("LoginFrame")
