
import customtkinter as ctk
from tkinter import messagebox, ttk
from config import COL_BATCHES, COL_DEPARTMENTS
from database.db_handler import DatabaseHandler
import threading

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseHandler()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Batch Section (Left)
        self.batch_frame = ctk.CTkFrame(self)
        self.batch_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.setup_crud_section(self.batch_frame, "Manage Batches", COL_BATCHES, "Batch Name")

        # Department Section (Right)
        self.dept_frame = ctk.CTkFrame(self)
        self.dept_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.setup_crud_section(self.dept_frame, "Manage Departments", COL_DEPARTMENTS, "Department Name")

    def setup_crud_section(self, parent_frame, title, collection, field_label):
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(parent_frame, text=title, font=("Roboto Medium", 18)).grid(row=0, column=0, pady=10)

        # Entry
        entry = ctk.CTkEntry(parent_frame, placeholder_text=f"New {field_label}")
        entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # List (Treeview)
        tree = ttk.Treeview(parent_frame, columns=("Name",), show="headings", height=10)
        tree.heading("Name", text=field_label)
        tree.column("Name", width=200)
        tree.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        
        # Add Button
        def add_item():
            val = entry.get().strip()
            if not val:
                 messagebox.showwarning("Warning", "Input cannot be empty.")
                 return
            if self.db.find_document(collection, {"name": val}):
                 messagebox.showerror("Error", "Item already exists.")
                 return
            
            if self.db.insert_document(collection, {"name": val}):
                entry.delete(0, 'end')
                load_items()
            else:
                messagebox.showerror("Error", "Failed to add item.")

        def delete_item():
            selected = tree.selection()
            if not selected:
                return
            val = tree.item(selected)['values'][0]
            if messagebox.askyesno("Confirm", f"Delete '{val}'?"):
                if self.db.delete_document(collection, {"name": val}):
                    load_items()
                else:
                    messagebox.showerror("Error", "Failed to delete item.")

        btn_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=5)
        
        ctk.CTkButton(btn_frame, text="Add", command=add_item, width=80).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Delete", command=delete_item, fg_color="red", hover_color="darkred", width=80).pack(side="left", padx=5)

        def load_items():
            def fetch_data():
                # Fetch data in background thread
                items = self.db.find_all_documents(collection)
                
                # Schedule UI update on main thread
                def update_ui():
                    for item in tree.get_children():
                        tree.delete(item)
                    for i in items:
                        tree.insert("", "end", values=(i.get("name"),))
                
                self.after(0, update_ui)

            threading.Thread(target=fetch_data, daemon=True).start()
        
        # Initial Load
        load_items()
        
        # Store refresh function to be called on show if needed
        # Just simple load for now, assuming local updates

    def cleanup(self):
        pass

    def on_show(self):
        # Refresh lists in case of external changes? 
        # For now, we rebuild the frame or we can trigger refresh.
        # Since setup_crud_section logic is closures, it's hard to trigger from outside. 
        # Rebuilding via dashboard caching system is fine as long as we don't cache SettingsFrame or provide refresh mechanism.
        # Check Dashboard: it caches. 
        # So we should make load_items accessible or just rebuild UI? 
        # Rebuilding UI is expensive.
        # Let's verify if on_show re-runs setup? No.
        # Let's make setup return the load function and store it.
        pass
