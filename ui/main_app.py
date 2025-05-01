import tkinter as tk
import ttkbootstrap as ttk
from .analysis_frame import AnalysisFrame
from .fetch_frame import FetchFrame
from .settings_dialog import SettingsDialog
from .config import config

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Auto Analysis")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = int(sw*2/3), int(sh*2/3)
        x, y = (sw-w)//2, (sh-h)//2
        root.geometry(f"{w}x{h}+{x}+{y}")

        container = ttk.Frame(root)
        container.pack(fill=tk.BOTH, expand=True)


        self.main_menu = ttk.Frame(container)
        self.main_menu.pack(fill=tk.BOTH, expand=True)


        ttk.Label(
            self.main_menu,
            text="Financial Auto\n\nAnalysis Tool",
            font=(None, 64, 'bold'),
            justify="left"
        ).place(relx=0.18, rely=0.5, anchor='w')

        btn_fetch = ttk.Button(
            self.main_menu,
            text="Fetch PDFs",
            command=self.show_fetch,
            bootstyle="outline-info"
        )
        btn_analysis = ttk.Button(
            self.main_menu,
            text="Analysis",
            command=self.show_analysis,
            bootstyle="outline-primary"
        )
        btn_settings = ttk.Button(
            self.main_menu,
            text="Settings",
            command=self.open_settings,
            bootstyle="dark"
        )


        for i, btn in enumerate((btn_fetch, btn_analysis, btn_settings)):
            btn.place(
                relx=0.75,
                rely=0.3 + i*0.2,
                relwidth=0.2,
                relheight=1/6,
                anchor='center'
            )

        self.feature_container = ttk.Frame(container)
        self.fetch = FetchFrame(self.feature_container, self.show_main_menu)
        self.analysis = AnalysisFrame(self.feature_container, self.show_main_menu)

    def show_main_menu(self):
        self.feature_container.pack_forget()
        self.main_menu.pack(fill=tk.BOTH, expand=True)

    def show_fetch(self):
        self.main_menu.pack_forget()
        self.feature_container.pack(fill=tk.BOTH, expand=True)
        self.analysis.frame.pack_forget()
        self.fetch.frame.pack(fill=tk.BOTH, expand=True)

    def show_analysis(self):
        self.main_menu.pack_forget()
        self.feature_container.pack(fill=tk.BOTH, expand=True)
        self.fetch.frame.pack_forget()
        self.analysis.frame.pack(fill=tk.BOTH, expand=True)

    def open_settings(self):
        dlg = SettingsDialog(
            self.root,
            api_key=config.api_key,
            assistant_id=config.assistant_id
        )

        self.root.wait_window(dlg)
        if getattr(dlg, "result", None):
            api_key, assistant_id = dlg.result

            config.api_key = api_key
            config.assistant_id = assistant_id
            config.save()

            self.analysis.api_key = api_key
            self.analysis.assistant_id = assistant_id
