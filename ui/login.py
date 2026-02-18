

import customtkinter as ctk
from config import ADMIN_USER, ADMIN_PASS
from tkinter import messagebox
from logic.auth_manager import AuthManager
from logic.session_manager import SessionManager
from PIL import Image
import os

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Load Icons
        image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        self.eye_icon = ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "eye.png")),
                                     dark_image=Image.open(os.path.join(image_path, "eye-white.png")),
                                     size=(20, 20))
        self.eye_off_icon = ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "eye-off.png")),
                                         dark_image=Image.open(os.path.join(image_path, "eye-off-white.png")),
                                         size=(20, 20))

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
        self.entry_admin_user = ctk.CTkEntry(self.form_frame, placeholder_text="Admin Username", 
                                             placeholder_text_color="#808080", text_color=("black", "white"), 
                                             fg_color=("white", "#343638"), width=280, height=40)
        self.entry_admin_pass = ctk.CTkEntry(self.form_frame, placeholder_text="Password", 
                                             placeholder_text_color="#808080", text_color=("black", "white"), 
                                             fg_color=("white", "#343638"), show="*", width=280, height=40)
        
        # Admin Eye Button
        self.btn_eye_admin = ctk.CTkButton(self.form_frame, text="", image=self.eye_icon, width=30, height=30,
                                           fg_color="transparent", hover_color=("#dbdbdb", "#3b3b3b"),
                                           command=lambda: self.toggle_password_visibility(self.entry_admin_pass, self.btn_eye_admin))
        
        self.entry_admin_user.bind("<Return>", self.login_event)
        self.entry_admin_pass.bind("<Return>", self.login_event)
        self.admin_widgets.extend([self.entry_admin_user, self.entry_admin_pass])

        # Admin Labels
        self.lbl_admin_user = ctk.CTkLabel(self.form_frame, text="Admin Username", font=("Roboto", 12))
        self.lbl_admin_pass = ctk.CTkLabel(self.form_frame, text="Password", font=("Roboto", 12))

        # -- Lecturer Widgets --
        self.lecturer_widgets = []
        self.entry_lec_id = ctk.CTkEntry(self.form_frame, placeholder_text="Lecturer ID (e.g. LEC001)", 
                                         placeholder_text_color="#808080", text_color=("black", "white"), 
                                         fg_color=("white", "#343638"), width=280, height=40)
        self.entry_lec_pass = ctk.CTkEntry(self.form_frame, placeholder_text="Password", 
                                           placeholder_text_color="#808080", text_color=("black", "white"), 
                                           fg_color=("white", "#343638"), show="*", width=280, height=40)
        
        # Lecturer Eye Button
        self.btn_eye_lec = ctk.CTkButton(self.form_frame, text="", image=self.eye_icon, width=30, height=30,
                                         fg_color="transparent", hover_color=("#dbdbdb", "#3b3b3b"),
                                         command=lambda: self.toggle_password_visibility(self.entry_lec_pass, self.btn_eye_lec))

        self.entry_lec_id.bind("<Return>", self.login_event)
        self.entry_lec_pass.bind("<Return>", self.login_event)
        self.lecturer_widgets.extend([self.entry_lec_id, self.entry_lec_pass])

        # Lecturer Labels
        self.lbl_lec_id = ctk.CTkLabel(self.form_frame, text="Lecturer ID", font=("Roboto", 12))
        self.lbl_lec_pass = ctk.CTkLabel(self.form_frame, text="Password", font=("Roboto", 12))

        # Shared Widgets
        self.options_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.options_frame.grid(row=4, column=0, pady=(10, 20), padx=20, sticky="ew")
        self.options_frame.grid_columnconfigure(0, weight=1)
        self.options_frame.grid_columnconfigure(1, weight=1)

        self.remember_me = ctk.CTkCheckBox(self.options_frame, text="Remember Me", checkbox_width=20, checkbox_height=20)
        self.remember_me.grid(row=0, column=0, sticky="w", padx=10)
        
        # Removed old switch
        # self.cb_show_pass = ctk.CTkSwitch(...) 

        self.btn_login = ctk.CTkButton(self.card, text="Login", command=self.login_event, width=280, height=40, font=("Roboto Medium", 14))
        self.btn_login.grid(row=5, column=0, pady=(0, 40), padx=20)

        # Initial State
        self.switch_tab("Admin")

    def switch_tab(self, value):
        # Clear previous widgets
        for widget in self.form_frame.winfo_children():
            widget.grid_forget()
            widget.place_forget() # Also clear placed widgets
        
        if value == "Admin":
            self.lbl_admin_user.grid(row=0, column=0, sticky="w", pady=(10, 0))
            self.entry_admin_user.grid(row=1, column=0, pady=(0, 10))
            
            self.lbl_admin_pass.grid(row=2, column=0, sticky="w", pady=(10, 0))
            self.entry_admin_pass.grid(row=3, column=0, pady=(0, 10))
            
            # Place the eye button relative to the password entry
            self.btn_eye_admin.place(in_=self.entry_admin_pass, relx=1.0, rely=0.5, x=-5, anchor="e")
            
        else:
            self.lbl_lec_id.grid(row=0, column=0, sticky="w", pady=(10, 0))
            self.entry_lec_id.grid(row=1, column=0, pady=(0, 10))
            
            self.lbl_lec_pass.grid(row=2, column=0, sticky="w", pady=(10, 0))
            self.entry_lec_pass.grid(row=3, column=0, pady=(0, 10))
            
            # Place the eye button relative to the password entry
            self.btn_eye_lec.place(in_=self.entry_lec_pass, relx=1.0, rely=0.5, x=-5, anchor="e")

    def toggle_password_visibility(self, entry, button):
        if entry.cget("show") == "*":
            entry.configure(show="")
            button.configure(image=self.eye_off_icon)
        else:
            entry.configure(show="*")
            button.configure(image=self.eye_icon)

    def login_event(self, event=None):
        role_selected = self.tab_var.get()
        auth = AuthManager()

        if role_selected == "Admin":
            username = self.entry_admin_user.get()
            password = self.entry_admin_pass.get()

            # Re-using unified login for simplicity, assuming Admin user won't clash with Lecturer ID
            success, role, user_data = auth.login(username, password)
            
            # Enforce role match
            if success and role != "admin": # Found lecturer with admin credentials, safe check
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
        
        # Reset visibility for both fields
        self.entry_admin_pass.configure(show="*")
        self.btn_eye_admin.configure(image=self.eye_icon)
        self.entry_lec_pass.configure(show="*")
        self.btn_eye_lec.configure(image=self.eye_icon)

    def on_show(self):
        self.cleanup()


