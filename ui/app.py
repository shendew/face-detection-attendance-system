
import customtkinter as ctk
from .login import LoginFrame
from .dashboard import DashboardFrame

class App(ctk.CTk):
    def __init__(self):
        super().__init__(className="FaceDetention Attendance System")

        self.title("FaceDetention Attendance System")
        self.geometry("1200x800")
        
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        # Initialize frames
        for F in (LoginFrame, DashboardFrame):
            frame_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()
