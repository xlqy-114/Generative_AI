import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from .config import config
from .analyzer import analyze_pdf_with_openai, chat_with_openai

class AnalysisFrame:
    """Frame for uploading PDFs, running analysis, and chatting with the assistant."""
    def __init__(self, parent, go_back):
        """Initialize the UI components and state variables."""
        self.frame = ttk.Frame(parent)
        # Back button to return to main menu
        ttk.Button(self.frame, text="← Back", command=go_back)\
           .pack(anchor="nw", padx=10, pady=10)

        # State: list of PDF file paths and their checkbox variables
        self.pdf_files = []
        self.check_vars = {}
        # API key and Assistant ID, set in Settings
        self.api_key = ""
        self.assistant_id = config.assistant_id

        # Top toolbar with action buttons
        top = ttk.Frame(self.frame)
        top.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(top, text="📁 Upload PDF", command=self.upload, bootstyle="primary")\
           .pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="🗑️ Delete Selected", command=self.delete, bootstyle="danger")\
           .pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="🧹 Clear All", command=self.clear_all, bootstyle="warning")\
           .pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="⚙️ Settings", command=self.open_settings, bootstyle="secondary")\
           .pack(side=tk.RIGHT, padx=5)

        # Container for showing uploaded PDF list
        container = ttk.Labelframe(self.frame, text="Uploaded PDFs")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
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

        # Progress bar displayed during analysis or chat
        self.progress = ttk.Progressbar(self.frame, mode="indeterminate")

        # Text area for displaying model output
        out = ttk.Labelframe(self.frame, text="Model Output")
        out.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,10))
        self.output_text = tk.Text(out, wrap="none", state="disabled")
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Chat input area
        chatf = ttk.Labelframe(self.frame, text="Chat Input")
        chatf.pack(fill=tk.X, padx=20, pady=(0,10))
        self.chat_input = tk.Text(chatf, height=3)
        self.chat_input.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Button(chatf, text="Send", command=self.send_chat, bootstyle="success")\
           .pack(anchor="e", padx=5)

        # Button to start PDF analysis
        bottom = ttk.Frame(self.frame)
        bottom.pack(fill=tk.X, padx=20, pady=(0,10))
        ttk.Button(bottom, text="Analyze PDFs", command=self.analyze, bootstyle="info")\
           .pack()

    def upload(self):
        """Open file dialog to select PDF(s) and add them to the list."""
        paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        for p in paths:
            if p not in self.pdf_files:
                self.pdf_files.append(p)
        self._rebuild()

    def delete(self):
        """Remove selected PDFs from the list."""
        to_delete = [p for p, var in self.check_vars.items() if var.get()]
        if not to_delete:
            messagebox.showwarning("Warning", "No PDF selected.")
            return
        for p in to_delete:
            self.pdf_files.remove(p)
        self._rebuild()

    def clear_all(self):
        """Clear all uploaded PDFs after user confirmation."""
        if not self.pdf_files or not messagebox.askyesno("Confirm", "Clear all PDFs?"):
            return
        self.pdf_files.clear()
        self._rebuild()

    def _rebuild(self):
        """Rebuild the checkbox list to reflect current pdf_files."""
        for widget in self.cb_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()
        for path in self.pdf_files:
            var = tk.BooleanVar()
            ttk.Checkbutton(
                self.cb_frame,
                text=os.path.basename(path),
                variable=var
            ).pack(anchor="w", pady=2, padx=5)
            self.check_vars[path] = var

    def analyze(self):
        """
        Start analysis of selected PDFs:
        validate inputs, clear output, show progress, and spawn a worker thread.
        """
        selected = [p for p, var in self.check_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("Warning", "Select a PDF.")
            return
        if not self.api_key or not self.assistant_id:
            messagebox.showwarning(
                "Warning",
                "Please set both API Key and Assistant ID in Settings."
            )
            return
        self._clear_output()
        self.progress.pack(fill=tk.X, padx=20, pady=(0,10))
        self.progress.start()
        threading.Thread(
            target=self._run_analysis,
            args=(selected,),
            daemon=True
        ).start()

    def _run_analysis(self, files):
        """Worker thread: upload each PDF, run analysis, and append results."""
        for pdf in files:
            try:
                result = analyze_pdf_with_openai(
                    pdf,
                    self.api_key,
                    self.assistant_id
                )
                self.frame.after(
                    0,
                    lambda pdf=pdf, result=result:
                    self._append(f"===== {os.path.basename(pdf)} =====\n{result}\n\n")
                )
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", str(e)))
                break
        self.frame.after(0, self._finish)

    def _append(self, text):
        """Append text to the output area, preserving scroll position."""
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.config(state="disabled")

    def _clear_output(self):
        """Clear all text from the output area."""
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state="disabled")

    def send_chat(self):
        """
        Send a chat message:
        validate inputs, show progress, and start worker thread.
        """
        message = self.chat_input.get("1.0", tk.END).strip()
        if not message or not self.api_key or not self.assistant_id:
            messagebox.showwarning(
                "Warning",
                "Enter message, API Key, and Assistant ID."
            )
            return
        self._append(f"[User]: {message}\n")
        self.chat_input.delete("1.0", tk.END)
        self.progress.pack(fill=tk.X, padx=20, pady=(0,10))
        self.progress.start()
        threading.Thread(
            target=self._run_chat,
            args=(message,),
            daemon=True
        ).start()

    def _run_chat(self, user_message):
        """Worker thread: send user_message to chat API and append assistant response."""
        try:
            response = chat_with_openai(
                self.api_key,
                self.assistant_id,
                user_message
            )
            self.frame.after(
                0,
                lambda: self._append(f"[Assistant]: {response}\n\n")
            )
        except Exception as e:
            self.frame.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.frame.after(0, self._finish)

    def _finish(self):
        """Stop and hide the progress bar."""
        self.progress.stop()
        self.progress.pack_forget()

    def open_settings(self):
        """Open the settings dialog to set API key, Assistant ID, and download dir."""
        root = self.frame.winfo_toplevel()
        settings_window = tk.Toplevel(root)
        settings_window.title("Settings")
        settings_window.resizable(False, False)

        pw, ph = root.winfo_width(), root.winfo_height()
        px, py = root.winfo_x(), root.winfo_y()
        w, h = int(pw * 2/3), int(ph * 2/3)
        settings_window.geometry(
            f"{w}x{h}+{px+(pw-w)//2}+{py+(ph-h)//2}"
        )
        settings_window.transient(root)

        form = ttk.Frame(settings_window)
        form.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Default Download Directory
        ttk.Label(form, text="Default Download Directory:").pack(anchor="w")
        dir_var = tk.StringVar(value=config.default_download_dir)
        dir_entry = ttk.Entry(form, textvariable=dir_var)
        dir_entry.pack(fill=tk.X, pady=(0,5))
        def browse_directory():
            selected = filedialog.askdirectory()
            if selected:
                dir_var.set(selected)
                config.default_download_dir = selected
        ttk.Button(
            form,
            text="Browse",
            command=browse_directory,
            bootstyle="outline-secondary"
        ).pack(anchor="w", pady=(0,10))

        # API Key
        ttk.Label(form, text="API Key:").pack(anchor="w")
        key_var = tk.StringVar(value=self.api_key)
        api_entry = ttk.Entry(form, textvariable=key_var, show="*", width=50)
        api_entry.pack(fill=tk.X, pady=(0,10))

        # Assistant ID
        ttk.Label(form, text="Assistant ID:").pack(anchor="w")
        aid_var = tk.StringVar(value=self.assistant_id)
        aid_entry = ttk.Entry(form, textvariable=aid_var, width=50)
        aid_entry.pack(fill=tk.X, pady=(0,15))

        def save_settings():
            """Save API key and Assistant ID back to the frame and config."""
            self.api_key = key_var.get().strip()
            self.assistant_id = aid_var.get().strip()
            config.assistant_id = self.assistant_id
            settings_window.destroy()

        ttk.Button(
            form,
            text="Confirm",
            command=save_settings,
            bootstyle="secondary"
        ).pack()
        settings_window.grab_set()
