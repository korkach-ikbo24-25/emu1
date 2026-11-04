import os
import socket
import tkinter as tk
from tkinter import scrolledtext
from commands import Shell

def build_title():
    user = os.environ.get('USER') or os.environ.get('USERNAME') or 'user'
    return f"Эмулятор - [{user}@{socket.gethostname()}]"

class ShellGUI:
    def __init__(self, root, shell):
        self.root = root
        self.shell = shell
        root.title(build_title())
        root.geometry("800x500")

        self.text = scrolledtext.ScrolledText(
            root, bg='black', fg='#d0d0d0',
            insertbackground='white', font=('Consolas', 11)
        )
        self.text.pack(fill='both', expand=True)
        self.text.bind('<Return>', self.on_enter)
        self.text.bind('<Key>', self.on_key)

        self.prompt = self._make_prompt()
        self._append(self.prompt)
        self.text.mark_set('input_start', 'end-1c')

    def _make_prompt(self):
        user = os.environ.get('USER', 'user')
        return f"{user}@{socket.gethostname()}:$ "

    def _append(self, s):
        self.text.insert('end', s)
        self.text.see('end')

    def on_key(self, event):
        if event.keysym in ('Left', 'Up', 'Home'):
            if self.text.compare('insert', '<=', 'input_start'):
                return 'break'
        return None

    def on_enter(self, event):
        line = self.text.get('input_start', 'end-1c')
        self._append('\n')
        out = self.shell.execute(line)
        if out:
            self._append(out + '\n')
        if self.shell.exit_requested:
            self.root.after(50, self.root.destroy)
            return 'break'
        self.prompt = self._make_prompt()
        self._append(self.prompt)
        self.text.mark_set('input_start', 'end-1c')
        return 'break'

def main():
    root = tk.Tk()
    ShellGUI(root, Shell())
    root.mainloop()

if __name__ == '__main__':
    main()
