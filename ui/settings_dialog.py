import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import ttkbootstrap as ttk
from tkinter.ttk import Combobox
from .config import config

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, api_key: str, assistant_id: str):
        super().__init__(parent)
        self.title("Settings")
        self.resizable(False, False)
        self.result = None

        parent.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        w, h = int(pw*2/3), int(ph*2/3)
        self.geometry(f"{w}x{h}+{px+(pw-w)//2}+{py+(ph-h)//2}")
        self.transient(parent)

        form = ttk.Frame(self, padding=20)
        form.pack(fill=tk.BOTH, expand=True)

        # Default Download Directory
        ttk.Label(form, text="Default Download Directory:").pack(anchor="w")
        dir_var = tk.StringVar(value=config.default_download_dir)
        ttk.Entry(form, textvariable=dir_var).pack(fill=tk.X, pady=(0,5))
        def browse():
            sel = filedialog.askdirectory(initialdir=dir_var.get())
            if sel:
                dir_var.set(sel)
        ttk.Button(form, text="Browse", command=browse, bootstyle="outline-secondary")\
           .pack(anchor="w", pady=(0,10))

        # Assistant ID
        ttk.Label(form, text="Assistant ID:").pack(anchor="w")
        aid_var = tk.StringVar(value=assistant_id or config.assistant_id)
        ttk.Entry(form, textvariable=aid_var, width=50).pack(fill=tk.X, pady=(0,15))

        # Saved API Keys
        ttk.Label(form, text="Saved API Keys:").pack(anchor="w")
        keynames = list(config.saved_api_keys.keys())
        saved_cb = Combobox(form, values=keynames, state="readonly")
        saved_cb.pack(fill=tk.X, pady=(0,5))

        # Delete Key Button
        def delete_key():
            name = saved_cb.get()
            if not name:
                messagebox.showwarning("Warning", "Please select a key to delete.")
                return
            if not messagebox.askyesno("Confirm", f"Delete saved API Key '{name}'?"):
                return
            # Delete from config and save
            config.saved_api_keys.pop(name, None)
            config.save()
            # Update combobox values
            new_names = list(config.saved_api_keys.keys())
            saved_cb['values'] = new_names
            saved_cb.set('')
            messagebox.showinfo("Deleted", f"API Key '{name}' has been deleted.")
        ttk.Button(form, text="Delete Key", command=delete_key, bootstyle="danger")\
           .pack(anchor="e", pady=(0,15))

        # PIN input
        ttk.Label(form, text="PIN:").pack(anchor="w")
        pin_var = tk.StringVar()
        ttk.Entry(form, textvariable=pin_var, show="*", width=20).pack(fill=tk.X, pady=(0,10))

        # API Key input
        ttk.Label(form, text="API Key:").pack(anchor="w")
        key_var = tk.StringVar(value=config.api_key)
        ttk.Entry(form, textvariable=key_var, show="*", width=60).pack(fill=tk.X, pady=(0,5))

        # Unlock Button
        def unlock():
            name = saved_cb.get()
            pin = pin_var.get().strip()
            if not name or not pin:
                messagebox.showwarning("Warning", "Select a key and enter PIN.")
                return
            entry = config.saved_api_keys.get(name)
            if not entry:
                messagebox.showerror("Error", "Key not found.")
                return
            if hashlib.sha256(pin.encode()).hexdigest() != entry["pin_hash"]:
                messagebox.showerror("Error", "Incorrect PIN.")
                return
            try:
                clear_key = config.decrypt_api_key(entry["api_key_enc"], pin)
                key_var.set(clear_key)
                messagebox.showinfo("Unlocked", f"API Key for '{name}' loaded.")
            except Exception:
                messagebox.showerror("Error", "Failed to decrypt API Key.")
        ttk.Button(form, text="Unlock", command=unlock, bootstyle="secondary")\
           .pack(anchor="w", pady=(0,15))

        # Save this API Key?
        remember_key = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text="Save this API Key", variable=remember_key)\
           .pack(anchor="w", pady=(0,15))

        # Confirm
        def on_confirm():
            config.default_download_dir = dir_var.get().strip()
            config.assistant_id = aid_var.get().strip()

            final_key = key_var.get().strip()
            if remember_key.get() and final_key:
                name = simpledialog.askstring("Key Name", "Name for this API Key:", parent=self)
                pin = simpledialog.askstring("PIN", "4-digit PIN:", show="*", parent=self)
                if not name or not pin or len(pin)!=4 or not pin.isdigit():
                    messagebox.showerror("Error", "Valid name and 4-digit PIN required.")
                    return
                pin_hash = hashlib.sha256(pin.encode()).hexdigest()
                enc = config.encrypt_api_key(final_key, pin)
                config.saved_api_keys[name] = {"api_key_enc": enc, "pin_hash": pin_hash}

            config.api_key = final_key
            config.save()
            self.result = (config.api_key, config.assistant_id)
            self.destroy()

        ttk.Button(form, text="Confirm", command=on_confirm, bootstyle="secondary")\
           .pack()

        self.grab_set()
