import os
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk

class PDFListFrame(ttk.Labelframe):
    """Frame for displaying and managing uploaded PDFs."""
    def __init__(self, parent):
        super().__init__(parent, text="Uploaded PDFs")

        self.pdf_files = []
        self.check_vars = {}

        # Scrollable container
        canvas = tk.Canvas(self)
        sb = ttk.Scrollbar(self, command=canvas.yview)
        self.inner = ttk.Frame(canvas)
        self.inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def upload(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        for p in paths:
            if p not in self.pdf_files:
                self.pdf_files.append(p)
        self._rebuild()

    def delete(self):
        to_delete = [p for p, var in self.check_vars.items() if var.get()]
        if not to_delete:
            messagebox.showwarning("Warning", "No PDF selected.")
            return
        for p in to_delete:
            self.pdf_files.remove(p)
        self._rebuild()

    def clear_all(self):
        if not self.pdf_files or not messagebox.askyesno("Confirm", "Clear all PDFs?"):
            return
        self.pdf_files.clear()
        self._rebuild()

    def _rebuild(self):
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.check_vars.clear()
        for path in self.pdf_files:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.inner, text=os.path.basename(path), variable=var)
            chk.pack(anchor="w", padx=5, pady=2)
            self.check_vars[path] = var

    def get_selected(self):
        return [p for p, var in self.check_vars.items() if var.get()]