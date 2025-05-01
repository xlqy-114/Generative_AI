import tkinter as tk
import ttkbootstrap as ttk

class ChatFrame(ttk.Labelframe):
    def __init__(self, parent, on_send):
        super().__init__(parent, text="Chat Input")
        self.pack(fill=tk.X, padx=20, pady=(0,10))

        self.on_send = on_send
        self.chat_input = tk.Text(self, height=3)
        self.chat_input.pack(fill=tk.X, padx=5, pady=(0,5))
        self.chat_input.bind("<Return>", self._on_enter)

        ttk.Button(self, text="Send", command=self._trigger_send, bootstyle="success")\
           .pack(anchor="e", padx=5)

    def _on_enter(self, event):
        self._trigger_send()
        return "break"

    def _trigger_send(self):
        msg = self.chat_input.get("1.0", tk.END).strip()
        if not msg:
            return
        self.chat_input.delete("1.0", tk.END)
        self.on_send(msg)
