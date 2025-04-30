import os
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
import requests
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from .config import config

class FetchFrame:
    """Scrape and download PDFs."""
    def __init__(self, parent, go_back):
        self.frame = ttk.Frame(parent)
        ttk.Button(self.frame, text="← Back", command=go_back).pack(anchor="nw", padx=10, pady=10)

        self.pdf_urls     = {}
        self.check_vars   = {}
        self.ask_location = tk.BooleanVar(value=False)

        top = ttk.Frame(self.frame)
        top.pack(fill=tk.X, padx=20, pady=10)
        ttk.Label(top, text="Page URL:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(top, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=(5,10))
        ttk.Button(top, text="Load PDFs", command=self.load_pdfs, bootstyle="primary").pack(side=tk.LEFT)
        ttk.Checkbutton(top, text="Ask location", variable=self.ask_location).pack(side=tk.LEFT, padx=10)

        container = ttk.Labelframe(self.frame, text="PDF Files")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        canvas = tk.Canvas(container)
        sb = ttk.Scrollbar(container, command=canvas.yview)
        self.list_frame = ttk.Frame(canvas)
        self.list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.list_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        bottom = ttk.Frame(self.frame)
        bottom.pack(fill=tk.X, padx=20, pady=(0,10))
        ttk.Button(bottom, text="Download Selected", command=self.download_selected, bootstyle="info").pack()

    def load_pdfs(self):
        """Scrape and group by nearest heading."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning","Enter a URL.")
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
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.check_vars.clear()
        for sec, files in self.pdf_urls.items():
            ttk.Label(self.list_frame, text=sec, font=(None,10,'bold')).pack(anchor='w', pady=(5,0))
            for fname, link in files.items():
                var = tk.BooleanVar()
                ttk.Checkbutton(self.list_frame, text=fname, variable=var).pack(anchor='w', padx=20)
                self.check_vars[(sec,fname)] = var

    def download_selected(self):
        """Download PDFs to chosen or default dir."""
        if not self.check_vars:
            messagebox.showwarning("Warning","Nothing to download.")
            return
        if self.ask_location.get():
            d = filedialog.askdirectory()
            if not d:
                return
            base = d
        else:
            base = config.default_download_dir

        for (sec,fname), var in self.check_vars.items():
            if var.get():
                url = self.pdf_urls[sec][fname]
                folder = os.path.join(base, sec)
                os.makedirs(folder, exist_ok=True)
                try:
                    r = requests.get(url)
                    r.raise_for_status()
                    with open(os.path.join(folder, fname), 'wb') as f:
                        f.write(r.content)
                except Exception as e:
                    messagebox.showerror("Error", f"{fname}: {e}")
        messagebox.showinfo("Done","Downloads complete.")
