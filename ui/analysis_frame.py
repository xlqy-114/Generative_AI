import os
import re
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk

from .config import config
from .analyzer import analyze_pdf_with_openai, analyze_multiple_pdfs, chat_with_openai
from .pdf_list_frame import PDFListFrame
from .chat_frame import ChatFrame
from .settings_dialog import SettingsDialog

class AnalysisFrame:
    """Frame for uploading PDFs, running analysis, and chatting with the assistant."""
    def __init__(self, parent, go_back):
        self.frame = ttk.Frame(parent)

        # ← Back button
        ttk.Button(self.frame, text="← Back", command=go_back)\
           .pack(anchor="nw", padx=10, pady=10)

        # Load persisted API key & assistant ID
        self.api_key = config.api_key
        self.assistant_id = config.assistant_id

        # Top toolbar
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

        # PDF list
        self.pdf_list = PDFListFrame(self.frame)

        # Progress bar (hidden until analysis/chat starts)
        self.progress = ttk.Progressbar(self.frame, mode="indeterminate")

        # Model Output (with word wrap)
        out = ttk.Labelframe(self.frame, text="Model Output")
        out.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,10))
        self.output_text = tk.Text(out, wrap="word", state="disabled")
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Chat input (only text)
        self.chat = ChatFrame(self.frame, on_send=self._on_chat_send)

        # Analyze PDFs button (batch)
        bottom = ttk.Frame(self.frame)
        bottom.pack(fill=tk.X, padx=20, pady=(0,10))
        ttk.Button(bottom, text="Analyze PDFs", command=self.batch_analyze, bootstyle="info")\
           .pack()

    def upload(self):
        self.pdf_list.upload()

    def delete(self):
        self.pdf_list.delete()

    def clear_all(self):
        self.pdf_list.clear_all()

    def batch_analyze(self):
        files = self.pdf_list.get_selected()
        if not files:
            messagebox.showwarning("Warning", "Select a PDF.")
            return
        if not (self.api_key and self.assistant_id):
            messagebox.showwarning(
                "Warning",
                "Please set both API Key and Assistant ID in Settings."
            )
            return

        self._clear_output()
        # show and start progress
        self.progress.pack(fill=tk.X, padx=20, pady=(0,10))
        self.progress.start()

        threading.Thread(
            target=self._run_batch_analysis,
            args=(files,),
            daemon=True
        ).start()

    def _run_batch_analysis(self, files):
        try:
            result = analyze_multiple_pdfs(files, self.api_key, self.assistant_id)
            self.frame.after(0, lambda: self._append(result + "\n"))
        except Exception as e:
            self.frame.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.frame.after(0, self._finish)

    def _on_chat_send(self, message: str):
        if not (self.api_key and self.assistant_id):
            messagebox.showwarning(
                "Warning",
                "Please set both API Key and Assistant ID in Settings."
            )
            return

        self._append(f"[User]: {message}\n")
        self.progress.pack(fill=tk.X, padx=20, pady=(0,10))
        self.progress.start()

        threading.Thread(
            target=self._run_chat,
            args=(message,),
            daemon=True
        ).start()

    def _run_chat(self, user_message: str):
        try:
            response = chat_with_openai(self.api_key, self.assistant_id, user_message)
            self.frame.after(0, lambda: self._append(f"[Assistant]: {response}\n\n"))
        except Exception as e:
            self.frame.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.frame.after(0, self._finish)

    def open_settings(self):
        dlg = SettingsDialog(self.frame, api_key=self.api_key, assistant_id=self.assistant_id)
        self.frame.wait_window(dlg)
        if getattr(dlg, "result", None):
            self.api_key, self.assistant_id = dlg.result
            config.api_key = self.api_key
            config.assistant_id = self.assistant_id
            config.save()

    # === Output helpers ===

    def _finish(self):
        self.progress.stop()
        self.progress.pack_forget()

    def _clear_output(self):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state="disabled")

    def _append(self, text: str):
        """Insert text into output, aligning any Markdown tables."""
        formatted = self._format_code_blocks(text)
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, formatted)
        self.output_text.config(state="disabled")

    def _format_code_blocks(self, text: str) -> str:
        """Detect and align tables inside Markdown code blocks."""
        parts = re.split(r'(```[\s\S]*?```)', text)
        for i, part in enumerate(parts):
            if part.startswith("```") and part.endswith("```"):
                inner = part[3:-3].strip("\n")
                aligned = self._align_markdown_table(inner)
                parts[i] = "```" + aligned + "```"
        return "".join(parts)

    def _align_markdown_table(self, content: str) -> str:
        """Align columns of a Markdown table by padding to max widths."""
        lines = content.splitlines()
        # Identify table rows
        table = [ln for ln in lines if ln.strip().startswith("|") and ln.strip().endswith("|")]
        if not table:
            return content

        # Parse cells
        rows = [ [cell.strip() for cell in ln.strip().strip("|").split("|")] for ln in table ]
        cols = max(len(r) for r in rows)
        widths = [0]*cols
        for r in rows:
            for idx, cell in enumerate(r):
                widths[idx] = max(widths[idx], len(cell))

        # Rebuild aligned rows
        aligned = []
        for r in rows:
            cells = []
            for idx, cell in enumerate(r):
                if set(cell) <= {"-"}:
                    cells.append("-"*widths[idx])
                else:
                    cells.append(cell.ljust(widths[idx]))
            aligned.append("| " + " | ".join(cells) + " |")

        # Replace original table in content
        out_lines = []
        ti = 0
        for ln in lines:
            if ti < len(table) and ln == table[ti]:
                out_lines.append(aligned[ti])
                ti += 1
            else:
                out_lines.append(ln)
        return "\n".join(out_lines)
