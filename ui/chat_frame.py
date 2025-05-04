import tkinter as tk
import ttkbootstrap as ttk

class ChatFrame(ttk.Labelframe):
    def __init__(self, parent, on_send):
        super().__init__(parent, text="Chat Input")

        container = ttk.Frame(self)
        container.pack(fill=tk.X, padx=5, pady=5)

        self.on_send = on_send
        self.chat_input = tk.Text(container, height=3)
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        self.chat_input.bind("<Return>", self._on_enter)
        self.chat_input.bind("<KeyRelease>", lambda e: self.chat_input.see(tk.INSERT))

        ttk.Button(container, text="Send", command=self._trigger_send, bootstyle="success")\
           .pack(side=tk.RIGHT)

    def _on_enter(self, event):
        self._trigger_send()
        return "break"

    def _trigger_send(self):
        msg = self.chat_input.get("1.0", tk.END).strip()
        if not msg:
            return
        self.chat_input.see(tk.END)
        self.chat_input.delete("1.0", tk.END)
        self.chat_input.see(tk.END)
        self.on_send(msg)