import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import time
import os
import threading

class CameraCaptureDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_capture):
        super().__init__(parent)
        self.on_capture = on_capture
        self.title("Capture Photo")
        self.geometry("660x520")
        
        # Make modal
        self.transient(parent)
        self.after(200, lambda: self.grab_set()) # Wait for window to be viewable
        self.focus_force()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Video Frame
        self.label_video = ctk.CTkLabel(self, text="")
        self.label_video.grid(row=0, column=0, padx=10, pady=10)

        # Buttons
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.grid(row=1, column=0, pady=10)

        # Capture / Cancel Group
        self.btn_capture = ctk.CTkButton(self.btn_frame, text="Capture", command=self.capture)
        self.btn_capture.pack(side="left", padx=10)

        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Cancel", fg_color="red", hover_color="darkred", command=self.close)
        self.btn_cancel.pack(side="left", padx=10)

        # Retake / Confirm Group (Hidden initially)
        self.btn_retake = ctk.CTkButton(self.btn_frame, text="Retake", command=self.retake, fg_color="orange", hover_color="darkorange")
        self.btn_confirm = ctk.CTkButton(self.btn_frame, text="Confirm", command=self.confirm_capture, fg_color="green", hover_color="darkgreen")

        # Camera Setup
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.frozen = False
        self.current_frame = None
        
        # Start update loop
        self.update_video()

        self.protocol("WM_DELETE_WINDOW", self.close)

    def update_video(self):
        if not self.winfo_exists():
            return
            
        if self.running and not self.frozen:
            ret, frame = self.cap.read()
            if ret:
                # Convert color space BGR to RGB
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
                
                self.label_video.configure(image=ctk_img, text="")
                self.label_video.image = ctk_img
            
            # Schedule next update
            self.after(20, self.update_video)

    def capture(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            self.frozen = True
            
            # Show static frame one last time to ensure it looks frozen
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
            self.label_video.configure(image=ctk_img)
            self.label_video.image = ctk_img

            # Toggle Buttons
            self.btn_capture.pack_forget()
            self.btn_cancel.pack_forget()
            
            self.btn_retake.pack(side="left", padx=10)
            self.btn_confirm.pack(side="left", padx=10)

    def retake(self):
        self.frozen = False
        self.current_frame = None
        
        # Toggle Buttons
        self.btn_retake.pack_forget()
        self.btn_confirm.pack_forget()
        
        self.btn_capture.pack(side="left", padx=10)
        self.btn_cancel.pack(side="left", padx=10)
        
        # Resume loop
        self.update_video()

    def confirm_capture(self):
        if self.current_frame is not None:
            timestamp = int(time.time())
            filename = f"captured_{timestamp}.jpg"
            # Ensure folder exists
            if not os.path.exists("temp_captures"):
                os.makedirs("temp_captures")
            
            filepath = os.path.join("temp_captures", filename)
            cv2.imwrite(filepath, self.current_frame)
            
            self.on_capture(os.path.abspath(filepath))
            self.close()

    def close(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()
