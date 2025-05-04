import os
import re
import threading
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from PIL import Image, ImageTk, ImageSequence

from .config import config
from .analyzer import analyze_multiple_pdfs, chat_with_openai
from .pdf_list_frame import PDFListFrame
from .chat_frame import ChatFrame
from .settings_dialog import SettingsDialog

# Loading Animation Helper Class
class LoadingAnimation:
    def __init__(self, parent, gif_path, delay=100, width=None, height=None):
        img = Image.open(gif_path)
        orig_w, orig_h = img.size
        tw, th = width or orig_w, height or orig_h
        self.frames = []
        for f in ImageSequence.Iterator(img):
            frame = f.copy()
            if width or height:
                frame = frame.resize((tw, th), Image.Resampling.LANCZOS)
            self.frames.append(ImageTk.PhotoImage(frame))
        self.index = 0
        self.label = tk.Label(parent)
        self.delay = delay
        self._job = None

    def start(self, **grid_opts):
        self.label.grid(**grid_opts)
        self._animate()

    def _animate(self):
        self.label.config(image=self.frames[self.index])
        self.index = (self.index + 1) % len(self.frames)
        self._job = self.label.after(self.delay, self._animate)

    def stop(self):
        if self._job:
            self.label.after_cancel(self._job)
            self._job = None
        self.label.grid_forget()

# Main AnalysisFrame Class
class AnalysisFrame:
    def __init__(self, parent, go_back):
        self.frame = ttk.Frame(parent)
        self.current_thread_id = None
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(4, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        ttk.Button(self.frame, text="← Back", command=go_back).grid(
            row=0, column=0, sticky="nw", padx=10, pady=10
        )
        here = os.path.dirname(__file__)
        root_dir = os.path.abspath(os.path.join(here, os.pardir))
        assets = os.path.join(root_dir, "assets")
        agif = os.path.join(assets, "analysis.gif")
        sgif = os.path.join(assets, "send.gif")
        try:
            w, h = Image.open(sgif).size
            sw, sh = w // 2, h // 2
        except:
            sw = sh = None

        # Toolbar Buttons
        tb = ttk.Frame(self.frame)
        tb.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        tb.grid_columnconfigure(2, weight=1)
        ttk.Button(tb, text="📁 Upload PDF", command=self.upload, bootstyle="primary").grid(
            row=0, column=0, padx=5
        )
        ttk.Button(tb, text="🔎 Analyze PDFs", command=self.batch_analyze, bootstyle="info").grid(
            row=0, column=1, padx=5
        )
        ttk.Button(tb, text="🪣 Clear Output", command=self._clear_output, bootstyle="dark").grid(
            row=0, column=3, padx=5
        )
        ttk.Button(tb, text="❌ Delete Selected", command=self.delete, bootstyle="danger").grid(
            row=0, column=4, padx=5
        )
        ttk.Button(tb, text="🧹 Clear All PDFs", command=self.clear_all, bootstyle="warning").grid(
            row=0, column=5, padx=5
        )
        ttk.Button(tb, text="⚙️ Settings", command=self.open_settings, bootstyle="secondary").grid(
            row=0, column=6, padx=5
        )

        # PDF List
        self.pdf_list = PDFListFrame(self.frame)
        self.pdf_list.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        # Progress Bar and Animations
        self.progress_container = ttk.Frame(self.frame)
        self.analysis_anim = LoadingAnimation(self.progress_container, agif, delay=200)
        self.send_anim = LoadingAnimation(self.progress_container, sgif, delay=200, width=sw, height=sh)
        self.progress = ttk.Progressbar(self.progress_container, mode="indeterminate")

        # Output Text
        self.output_container = ttk.Labelframe(self.frame, text="Model Output")
        self.output_container.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0,10))
        self.output_text = tk.Text(self.output_container, wrap="word", state="disabled")
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Chat Input
        self.chat = ChatFrame(self.frame, on_send=self._on_chat_send)
        self.chat.grid(row=5, column=0, sticky="ew", padx=20, pady=(0,10))

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
        if not (config.api_key and config.assistant_id):
            messagebox.showwarning("Warning", "Set API Key and Assistant ID.")
            return

        self.progress_container.grid(row=3, column=0, sticky="ew", padx=20, pady=(0,10))
        self.progress_container.grid_columnconfigure(1, weight=1)
        self.analysis_anim.start(row=0, column=0, sticky="w", padx=(0,5))
        self.progress.grid(row=0, column=1, sticky="ew")
        self.progress.start()
        self.output_text.after(20, lambda: self.output_text.see(tk.END))

        threading.Thread(target=self._run_batch_analysis, args=(files,), daemon=True).start()

    def _on_chat_send(self, message: str):
        if not (config.api_key and config.assistant_id):
            messagebox.showwarning("Warning", "Set API Key and Assistant ID.")
            return
        self._append(f"[User]: {message}\n")
        self.progress_container.grid(row=3, column=0, sticky="ew", padx=20, pady=(0,10))
        self.progress_container.grid_columnconfigure(1, weight=1)
        self.send_anim.start(row=0, column=0, sticky="w", padx=(0,5))
        self.progress.grid(row=0, column=1, sticky="ew")
        self.progress.start()
        self.output_text.after(20, lambda: self.output_text.see(tk.END))

        threading.Thread(target=self._run_chat, args=(message,), daemon=True).start()

    def _run_batch_analysis(self, files):
        try:
            res, tid = analyze_multiple_pdfs(files, config.api_key, config.assistant_id)
            self.current_thread_id = tid
            self.frame.after(0, lambda: self._append(res + "\n"))
        except Exception as e:
            self.frame.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.frame.after(0, self._finish)

    def _run_chat(self, user_message: str):
        try:
            resp, tid = chat_with_openai(
                config.api_key,
                config.assistant_id,
                user_message,
                thread_id=self.current_thread_id
            )
            self.current_thread_id = tid
            self.frame.after(0, lambda: self._append(f"[Assistant]: {resp}\n\n"))
        except Exception as e:
            self.frame.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.frame.after(0, self._finish)

    def open_settings(self):
        dlg = SettingsDialog(self.frame, api_key=config.api_key, assistant_id=config.assistant_id)
        self.frame.wait_window(dlg)
        if getattr(dlg, "result", None):
            config.api_key, config.assistant_id = dlg.result
            config.save()

    def _finish(self):
        self.progress.stop()
        self.analysis_anim.stop()
        self.send_anim.stop()
        self.progress_container.grid_forget()

    def _clear_output(self):
        if not messagebox.askyesno(
            "Confirm Clear",
            "Clear the output?"
        ):
            return
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state="disabled")
        self.current_thread_id = None
        
    def _append(self, txt: str):
        fmt = self._format_code_blocks(txt)
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, fmt)
        self.output_text.config(state="disabled")
        self.output_text.after_idle(lambda: self.output_text.see(tk.END))

    def _format_code_blocks(self, txt: str) -> str:
        lines = txt.split("\n")
        table = []
        collecting = False
        for ln in lines:
            if ln.startswith("|") and '---' in ln:
                collecting = True
                table.append(ln)
            elif collecting and ln.startswith("|"):
                table.append(ln)
            else:
                collecting = False
        if not table:
            return txt
        rows = [row.strip('| ').split('|') for row in table]
        cols = len(rows[0])
        widths = [0] * cols
        for r in rows:
            for idx, c in enumerate(r):
                widths[idx] = max(widths[idx], len(c))
        out, ti = [], 0
        for ln in lines:
            if ti < len(table) and ln == table[ti]:
                cells = [
                    rows[ti][idx].ljust(widths[idx]) if set(rows[ti][idx]) != {"-"} else "-" * widths[idx]
                    for idx in range(len(rows[ti]))
                ]
                out.append("| " + " | ".join(cells) + " |")
                ti += 1
            else:
                out.append(ln)
        return "\n".join(out)
