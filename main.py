import tkinter as tk
import ttkbootstrap as ttk
from ui.main_app import MainApp

if __name__ == "__main__":
    app = ttk.Window(themename="superhero")
    MainApp(app)
    app.mainloop()
