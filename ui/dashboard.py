
import customtkinter as ctk
from tkinter import messagebox
from .student_frame import StudentFrame
from .lecturer_frame import LecturerFrame
from .session_frame import SessionFrame
from .student_frame import StudentFrame
from .lecturer_frame import LecturerFrame
from .session_frame import SessionFrame
from .attendance_frame import AttendanceFrame
from .settings_frame import SettingsFrame

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="Attendance System", font=("Roboto Medium", 20))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_students = ctk.CTkButton(self.sidebar, text="Students", command=self.show_students)
        self.btn_students.grid(row=1, column=0, padx=20, pady=10)

        self.btn_lecturers = ctk.CTkButton(self.sidebar, text="Lecturers", command=self.show_lecturers)
        self.btn_lecturers.grid(row=2, column=0, padx=20, pady=10)

        self.btn_sessions = ctk.CTkButton(self.sidebar, text="Sessions", command=self.show_sessions)
        self.btn_sessions.grid(row=3, column=0, padx=20, pady=10)
        
        self.btn_live = ctk.CTkButton(self.sidebar, text="Live Attendance", fg_color="green", hover_color="darkgreen", command=self.show_live)
        self.btn_live.grid(row=4, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(self.sidebar, text="Data Settings", command=self.show_settings)
        self.btn_settings.grid(row=5, column=0, padx=20, pady=10)

        self.btn_logout = ctk.CTkButton(self.sidebar, text="Logout", fg_color="red", hover_color="darkred", command=self.logout)
        self.btn_logout.grid(row=6, column=0, padx=20, pady=20)

        # Content Area
        self.content_area = ctk.CTkFrame(self)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.current_frame = None
        self.show_students() # Default view

    def switch_frame(self, frame_class):
        # Cleanup previous frame
        if self.current_frame:
            if hasattr(self.current_frame, "cleanup"):
                self.current_frame.cleanup()
        
        # Get or Create frame instance
        if frame_class not in self.frames:
            self.frames[frame_class] = frame_class(self.content_area, self.controller)
            self.frames[frame_class].grid(row=0, column=0, sticky="nsew")
        
        # Switch
        self.current_frame = self.frames[frame_class]
        self.current_frame.tkraise()
        
        # Refresh/Initialize new frame data
        if hasattr(self.current_frame, "on_show"):
            self.current_frame.on_show()

    def show_students(self):
        self.switch_frame(StudentFrame)

    def show_lecturers(self):
        self.switch_frame(LecturerFrame)

    def show_sessions(self):
        self.switch_frame(SessionFrame)
    
    def show_live(self):
        self.switch_frame(AttendanceFrame)

    def show_settings(self):
        self.switch_frame(SettingsFrame)

    def logout(self):
        if not messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            return
        
        self.cleanup()
        from logic.session_manager import SessionManager
        SessionManager.clear_session()
        self.controller.show_frame("LoginFrame")

    def cleanup(self):
        for frame in self.frames.values():
            if hasattr(frame, "cleanup"):
                frame.cleanup()
