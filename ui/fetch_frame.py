import os
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
import requests
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from .config import config

class FetchFrame:
    def __init__(self, parent, go_back):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        ttk.Button(self.frame, text="← Back", command=go_back)\
           .pack(anchor="nw", padx=10, pady=10)

        self.pdf_urls = {}
        self.check_vars = {}
        self.ask_location = tk.BooleanVar(value=False)

        top = ttk.Frame(self.frame)
        top.pack(fill=tk.X, padx=20, pady=10)
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Page URL:").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(top)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=(5,10))

        ttk.Button(top, text="Load PDFs", command=self.load_pdfs, bootstyle="primary")\
            .grid(row=0, column=2, padx=5)
        ttk.Button(top, text="Download Selected", command=self.download_selected, bootstyle="info")\
            .grid(row=0, column=3, padx=5)
        ttk.Checkbutton(top, text="Ask location", variable=self.ask_location)\
            .grid(row=0, column=4, sticky="e", padx=(10,0))

        container = ttk.Labelframe(self.frame, text="PDF Files")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(container)
        sb = ttk.Scrollbar(container, command=canvas.yview)
        self.list_frame = ttk.Frame(canvas)
        self.list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        spacer_height = 30
        ttk.Frame(self.frame, height=spacer_height).pack(fill=tk.X)

    def load_pdfs(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Enter a URL.")
            return
        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except Exception as e:
            messagebox.showerror("Error", f"Fetch failed: {e}")
            return

        soup = BeautifulSoup(resp.text, 'html.parser')
        self.pdf_urls.clear()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if not href.lower().endswith('.pdf'):
                continue
            full = href if href.startswith('http') else requests.compat.urljoin(url, href)
            parsed = urlparse(full)
            raw = os.path.basename(parsed.path)
            name = unquote(raw).replace('+',' ')
            tag = a.find_previous(['h2','h3'])
            section = tag.get_text(strip=True) if tag else 'Uncategorized'
            self.pdf_urls.setdefault(section, {})[name] = full

        self._rebuild()

    def _rebuild(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()
        for section, files in self.pdf_urls.items():
            ttk.Label(self.list_frame, text=section, bootstyle="secondary")\
                .pack(anchor="w", pady=(5,0))
            for filename, url in files.items():
                var = tk.BooleanVar()
                ttk.Checkbutton(self.list_frame, text=filename, variable=var)\
                    .pack(anchor="w", padx=10)
                self.check_vars[(section, filename)] = var

    def download_selected(self):
        if not self.check_vars:
            messagebox.showwarning("Warning", "Nothing to download.")
            return
        if self.ask_location.get():
            directory = filedialog.askdirectory()
            if not directory:
                return
            base_dir = directory
        else:
            base_dir = config.default_download_dir

        for (section, filename), var in self.check_vars.items():
            if var.get():
                file_url = self.pdf_urls[section][filename]
                folder = os.path.join(base_dir, section)
                os.makedirs(folder, exist_ok=True)
                try:
                    response = requests.get(file_url)
                    response.raise_for_status()
                    with open(os.path.join(folder, filename), 'wb') as f:
                        f.write(response.content)
                except Exception as e:
                    messagebox.showerror("Error", f"{filename}: {e}")
        messagebox.showinfo("Done", "Downloads complete.")
