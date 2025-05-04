import tkinter as tk
import ttkbootstrap as ttk

class OutputFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text="Model Output")
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,10))

        self.output_text = tk.Text(self, wrap="none", state="disabled")
        self.output_text.pack(fill=tk.BOTH, expand=True)

        self.progress = ttk.Progressbar(self, mode="indeterminate")

    def append(self, text: str):
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.config(state="disabled")
        self.output_text.see(tk.END)

    def clear(self):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state="disabled")

    def start_progress(self):
        self.progress.pack(fill=tk.X, padx=20, pady=(0,10))
        self.progress.start()

    def stop_progress(self):
        self.progress.stop()
        self.progress.pack_forget()
