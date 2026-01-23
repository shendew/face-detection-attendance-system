
import customtkinter as ctk
from config import ADMIN_USER, ADMIN_PASS
from tkinter import messagebox
from logic.auth_manager import AuthManager
from logic.session_manager import SessionManager

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Grid system for centering
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main Card Container
        self.card = ctk.CTkFrame(self, width=400, corner_radius=15, fg_color=("white", "#2b2b2b"))
        self.card.grid(row=0, column=0, padx=20, pady=20)
        self.card.grid_columnconfigure(0, weight=1)

        # Title / Header
        self.lbl_header = ctk.CTkLabel(self.card, text="Welcome Back", font=("Roboto Medium", 24))
        self.lbl_header.grid(row=0, column=0, pady=(30, 20), padx=20)

        # Segmented Control (Tabs)
        self.tab_var = ctk.StringVar(value="Admin")
        self.tabs = ctk.CTkSegmentedButton(self.card, values=["Admin", "Lecturer"], 
                                           command=self.switch_tab, variable=self.tab_var,
                                           width=300)
        self.tabs.grid(row=1, column=0, pady=(0, 20), padx=20)

        # Form Container
        self.form_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.form_frame.grid(row=2, column=0, sticky="nsew", padx=20)
        self.form_frame.grid_columnconfigure(0, weight=1)

        # -- Admin Widgets --
        self.admin_widgets = []
        self.entry_admin_user = ctk.CTkEntry(self.form_frame, placeholder_text="Admin Username", width=280, height=40)
        self.entry_admin_pass = ctk.CTkEntry(self.form_frame, placeholder_text="Password", show="*", width=280, height=40)
        self.admin_widgets.extend([self.entry_admin_user, self.entry_admin_pass])

        # -- Lecturer Widgets --
        self.lecturer_widgets = []
        self.entry_lec_id = ctk.CTkEntry(self.form_frame, placeholder_text="Lecturer ID (e.g. LEC001)", width=280, height=40)
        self.entry_lec_pass = ctk.CTkEntry(self.form_frame, placeholder_text="Password", show="*", width=280, height=40)
        self.lecturer_widgets.extend([self.entry_lec_id, self.entry_lec_pass])

        # Shared Widgets
        self.remember_me = ctk.CTkCheckBox(self.card, text="Remember Me", checkbox_width=20, checkbox_height=20)
        self.remember_me.grid(row=3, column=0, pady=(10, 20), padx=50, sticky="w")

        self.btn_login = ctk.CTkButton(self.card, text="Login", command=self.login_event, width=280, height=40, font=("Roboto Medium", 14))
        self.btn_login.grid(row=4, column=0, pady=(0, 40), padx=20)

        # Initial State
        self.switch_tab("Admin")

    def switch_tab(self, value):
        # Clear previous widgets
        for widget in self.form_frame.winfo_children():
            widget.grid_forget()

        if value == "Admin":
            self.entry_admin_user.grid(row=0, column=0, pady=10)
            self.entry_admin_pass.grid(row=1, column=0, pady=10)
        else:
            self.entry_lec_id.grid(row=0, column=0, pady=10)
            self.entry_lec_pass.grid(row=1, column=0, pady=10)

    def login_event(self):
        role_selected = self.tab_var.get()
        auth = AuthManager()

        if role_selected == "Admin":
            username = self.entry_admin_user.get()
            password = self.entry_admin_pass.get()
            # For admin, auth manager checks config, but let's pass to generic or specific?
            # Creating a unified login in AuthManager handles checking both if implemented that way,
            # but here we know the intent.
            # Let's force check based on selection to avoid ambiguity.
            
            # Re-using unified login for simplicity, assuming Admin user won't clash with Lecturer ID
            success, role, user_data = auth.login(username, password)
            
            # Enforce role match
            if success and role != "admin": # Found lecturer with admin credentials? Unlikely but safe check
                 success = False

        else: # Lecturer
            username = self.entry_lec_id.get()
            password = self.entry_lec_pass.get()
            success, role, user_data = auth.login(username, password)
            
            # Enforce role match
            if success and role != "lecturer":
                success = False

        if success:
            if self.remember_me.get() == 1:
                SessionManager.save_session(username, role, user_data)
            
            # Clear fields
            self.entry_admin_pass.delete(0, 'end')
            self.entry_lec_pass.delete(0, 'end')

            if role == "admin":
                 self.controller.show_frame("DashboardFrame")
            elif role == "lecturer":
                 self.controller.current_user = user_data
                 self.controller.show_frame("LecturerDashboardFrame")
        else:
            messagebox.showerror("Login Failed", f"Invalid {role_selected} Credentials")
