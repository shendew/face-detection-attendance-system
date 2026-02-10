
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

        # Store sections for refreshing
        self.sections = [] # List of tuples: (tree, collection)
        
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
        
        self.sections.append((tree, collection)) # Store for refresh
        
        # Styles
        style = ttk.Style()
        style.configure("Treeview", font=("Roboto", 12), rowheight=30)
        style.map("Treeview", 
            background=[("selected", "#1f6aa5")],
            foreground=[("selected", "white"), ("!selected", "white")]
        )
        style.configure("Treeview.Heading", font=("Roboto", 12, "bold"))

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
                self.load_data(tree, collection)
            else:
                messagebox.showerror("Error", "Failed to add item.")

        def delete_item():
            selected = tree.selection()
            if not selected:
                return
            val = str(tree.item(selected)['values'][0])
            if messagebox.askyesno("Confirm", f"Delete '{val}'?"):
                if self.db.delete_document(collection, {"name": val}):
                    self.load_data(tree, collection)
                else:
                    messagebox.showerror("Error", "Failed to delete item.")

        btn_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=5)
        
        ctk.CTkButton(btn_frame, text="Add", command=add_item, width=80).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Delete", command=delete_item, fg_color="red", hover_color="darkred", width=80).pack(side="left", padx=5)

        # Initial Load
        self.load_data(tree, collection)

    def load_data(self, tree, collection):
        def fetch_data():
            try:
                # Fetch data in background thread
                items = self.db.find_all_documents(collection)
                
                # Schedule UI update on main thread
                self.after(0, lambda: self._update_tree(tree, items))
            except Exception as e:
                print(f"Error loading {collection}: {e}")

        threading.Thread(target=fetch_data, daemon=True).start()

    def _update_tree(self, tree, items):
        if not self.winfo_exists():
            return
        
        for item in tree.get_children():
            tree.delete(item)
            
        if items:
            for i in items:
                tree.insert("", "end", values=(i.get("name"),))

    def cleanup(self):
        pass

    def on_show(self):
        # Refresh all sections
        for tree, collection in self.sections:
            self.load_data(tree, collection)
