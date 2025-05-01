import os
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk

class PDFListFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text="Uploaded PDFs")
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.pdf_files = []
        self.check_vars = {}

        container = self
        canvas = tk.Canvas(container)
        sb = ttk.Scrollbar(container, command=canvas.yview)
        self.cb_frame = ttk.Frame(canvas)
        self.cb_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0,0), window=self.cb_frame, anchor="nw")
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
        for widget in self.cb_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()
        for path in self.pdf_files:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(
                self.cb_frame,
                text=os.path.basename(path),
                variable=var
            )
            chk.pack(anchor="w", pady=2, padx=5)
            self.check_vars[path] = var

    def get_selected(self):
        return [p for p, var in self.check_vars.items() if var.get()]
