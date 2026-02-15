import hashlib
import sys

# --- MANDATORY FIX FOR REPORTLAB 'usedforsecurity' ERROR ---
try:
    hashlib.md5(b'test', usedforsecurity=False)
except TypeError:
    real_md5 = hashlib.md5
    def md5_patched(data=b'', **kwargs):
        kwargs.pop('usedforsecurity', None) # Remove the broken argument
        return real_md5(data, **kwargs)
    hashlib.md5 = md5_patched
# ---------------------------------------------------------

import customtkinter as ctk
from .login import LoginFrame
from .dashboard import DashboardFrame
from .lecturer_dashboard import LecturerDashboardFrame

class App(ctk.CTk):
    def __init__(self):
        super().__init__(className="FaceDetention Attendance System")

        self.title("FaceDetention Attendance System")
        self.geometry("1200x800")
        
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.active_frame_name = None # Track active frame by name or instance

        self.frames = {}
        self.current_user = None # Store logged in user info
        
        # Initialize frames
        for F in (LoginFrame, DashboardFrame, LecturerDashboardFrame):
            frame_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.check_session()

    def check_session(self):
        from logic.session_manager import SessionManager
        session = SessionManager.load_session()
        if session:
             role = session.get("role")
             self.current_user = session.get("user_data")
             
             if role == "admin":
                  self.show_frame("DashboardFrame")
             elif role == "lecturer":
                  self.show_frame("LecturerDashboardFrame")
             else:
                  self.show_frame("LoginFrame")
        else:
             self.show_frame("LoginFrame")

    def show_frame(self, frame_name):
        print(f"DEBUG: App.show_frame({frame_name}) called")
        # Cleanup previous frame
        if self.active_frame_name and self.active_frame_name in self.frames:
            old_frame = self.frames[self.active_frame_name]
            if hasattr(old_frame, "cleanup"):
                old_frame.cleanup()

        self.active_frame_name = frame_name
        if frame_name not in self.frames:
             print(f"ERROR: Frame {frame_name} not found in frames: {list(self.frames.keys())}")
             return
             
        frame = self.frames[frame_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()
