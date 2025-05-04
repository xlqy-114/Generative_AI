import os
import tkinter as tk
import ttkbootstrap as ttk
from ui.main_app import MainApp

if __name__ == "__main__":
    app = ttk.Window(themename="superhero")
    app.option_add("*Font", "Arial 12")
    app.title("Financial Auto Analysis Tool")
    ico_path = os.path.join(os.path.dirname(__file__), "assets", "my_app.ico")
    app.iconbitmap(ico_path)

    MainApp(app)
    app.mainloop()
