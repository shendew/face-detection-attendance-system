
import customtkinter as ctk
from config import ADMIN_USER, ADMIN_PASS
from tkinter import messagebox

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Center content
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.login_box = ctk.CTkFrame(self)
        self.login_box.grid(row=1, column=0, pady=20, padx=20)

        self.label_title = ctk.CTkLabel(self.login_box, text="Admin Login", font=("Roboto Medium", 24))
        self.label_title.pack(pady=20, padx=40)

        self.entry_user = ctk.CTkEntry(self.login_box, placeholder_text="Username")
        self.entry_user.pack(pady=10, padx=20)

        self.entry_pass = ctk.CTkEntry(self.login_box, placeholder_text="Password", show="*")
        self.entry_pass.pack(pady=10, padx=20)

        self.btn_login = ctk.CTkButton(self.login_box, text="Login", command=self.login_event)
        self.btn_login.pack(pady=20, padx=20)

    def login_event(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()

        if username == ADMIN_USER and password == ADMIN_PASS:
            self.controller.show_frame("DashboardFrame")
            self.entry_pass.delete(0, 'end') # Clear password
        else:
            messagebox.showerror("Login Failed", "Invalid Credentials")
