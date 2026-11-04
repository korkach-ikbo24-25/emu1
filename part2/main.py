import os
import sys
import socket
import argparse
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


def run_start_script(shell, gui, path):
    """Проигрывает стартовый скрипт как диалог: prompt + ввод + вывод.
    Ошибочные строки не останавливают выполнение."""
    if not os.path.isfile(path):
        gui._append(f"[start-script] файл не найден: {path}\n")
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except OSError as e:
        gui._append(f"[start-script] ошибка чтения: {e}\n")
        return

    for raw in lines:
        line = raw.rstrip('\n')
        if not line.strip() or line.strip().startswith('#'):
            continue
        gui._append(gui.prompt)
        gui._append(line + '\n')
        out = shell.execute(line)
        if out:
            gui._append(out + '\n')
        if shell.exit_requested:
            gui.root.after(50, gui.root.destroy)
            return
        gui.prompt = gui._make_prompt()
        gui._append(gui.prompt)
        gui.text.mark_set('input_start', 'end-1c')


def parse_args():
    p = argparse.ArgumentParser(description="Эмулятор shell — этап 2")
    p.add_argument('--vfs',
                   help="Путь к физическому расположению VFS (ZIP). "
                        "На этом этапе сохраняется, реально используется на этапе 3.")
    p.add_argument('--start-script',
                   help="Путь к стартовому скрипту для выполнения команд эмулятора")
    p.add_argument('--debug', action='store_true',
                   help="Отладочный вывод всех заданных параметров при запуске")
    return p.parse_args()


def main():
    args = parse_args()

    if args.debug:
        print(f"[DEBUG] vfs          = {args.vfs!r}")
        print(f"[DEBUG] start-script = {args.start_script!r}")
        print(f"[DEBUG] title        = {build_title()}")

    shell = Shell()
    root = tk.Tk()
    gui = ShellGUI(root, shell)

    if args.start_script:
        run_start_script(shell, gui, args.start_script)

    root.mainloop()


if __name__ == '__main__':
    main()
