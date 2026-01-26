
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
        self.entry_admin_user.bind("<Return>", self.login_event)
        self.entry_admin_pass.bind("<Return>", self.login_event)
        self.admin_widgets.extend([self.entry_admin_user, self.entry_admin_pass])

        # -- Lecturer Widgets --
        self.lecturer_widgets = []
        self.entry_lec_id = ctk.CTkEntry(self.form_frame, placeholder_text="Lecturer ID (e.g. LEC001)", width=280, height=40)
        self.entry_lec_pass = ctk.CTkEntry(self.form_frame, placeholder_text="Password", show="*", width=280, height=40)
        self.entry_lec_id.bind("<Return>", self.login_event)
        self.entry_lec_pass.bind("<Return>", self.login_event)
        self.lecturer_widgets.extend([self.entry_lec_id, self.entry_lec_pass])

        # Shared Widgets
        # Shared Widgets
        self.options_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.options_frame.grid(row=4, column=0, pady=(10, 20), padx=20, sticky="ew")
        self.options_frame.grid_columnconfigure(0, weight=1)
        self.options_frame.grid_columnconfigure(1, weight=1)

        self.remember_me = ctk.CTkCheckBox(self.options_frame, text="Remember Me", checkbox_width=20, checkbox_height=20)
        self.remember_me.grid(row=0, column=0, sticky="w", padx=10)
        
        self.cb_show_pass = ctk.CTkSwitch(self.options_frame, text="Show Password", command=self.toggle_password_visibility, switch_width=30, switch_height=15)
        self.cb_show_pass.grid(row=0, column=1, sticky="e", padx=10)

        self.btn_login = ctk.CTkButton(self.card, text="Login", command=self.login_event, width=280, height=40, font=("Roboto Medium", 14))
        self.btn_login.grid(row=5, column=0, pady=(0, 40), padx=20)

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

    def toggle_password_visibility(self):
        is_checked = self.cb_show_pass.get()
        show_char = "" if is_checked else "*"
        self.entry_admin_pass.configure(show=show_char)
        self.entry_lec_pass.configure(show=show_char)

    def login_event(self, event=None):
        role_selected = self.tab_var.get()
        auth = AuthManager()

        if role_selected == "Admin":
            username = self.entry_admin_user.get()
            password = self.entry_admin_pass.get()

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

    def cleanup(self):
        # Clear fields on navigating away
        self.entry_admin_user.delete(0, 'end')
        self.entry_admin_pass.delete(0, 'end')
        self.entry_lec_id.delete(0, 'end')
        self.entry_lec_pass.delete(0, 'end')
        self.cb_show_pass.deselect()
        self.toggle_password_visibility() # Reset visibility state
