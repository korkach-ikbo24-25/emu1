import os
import sys
import socket
import argparse
import zipfile
import tkinter as tk
from tkinter import scrolledtext
from vfs import VFS, VFSError
from commands import Shell

def ensure_vfs():
    # создает zip-архивы при первом запуске
    base = os.path.join(os.path.dirname(__file__), 'vfs')
    os.makedirs(base, exist_ok=True)

    def build(filename, files):
        path = os.path.join(base, filename)
        if not os.path.exists(path):
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for name, data in files.items():
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                    zf.writestr(name, data)
            print(f"[VFS] Создан архив: {filename}")

    build('minimal.zip', {
        'hello.txt': 'Привет из VFS\n',
    })
    build('several.zip', {
        'readme.md':    'readme из VFS\n',
        'data/a.txt':   'содержимое a.txt\n',
        'data/b.txt':   'содержимое b.txt\n',
        'data/bin.dat': bytes(range(256)),
    })
    build('deep.zip', {
        'level1/level2/level3/deep.txt':     'глубокий файл\n',
        'level1/level2/level3/level4/1.txt': 'текст 1\n',
        'level1/level2/level3/level4/2.txt': 'текст 2\n',
    })

def build_title():
    # формируем заголовок окна из реальных данных ос
    user = os.environ.get('USER') or os.environ.get('USERNAME') or 'user'
    return f"Эмулятор - [{user}@{socket.gethostname()}]"

class ShellGUI:
    def __init__(self, root, shell):
        self.root = root
        self.shell = shell
        root.title(build_title())
        root.geometry("900x600")

        # создаем черное окно консоли
        self.text = scrolledtext.ScrolledText(
            root, bg='black', fg='#d0d0d0',
            insertbackground='white', font=('Consolas', 11)
        )
        self.text.pack(fill='both', expand=True)

        # кнопка на случай, если enter не срабатывает
        self.btn = tk.Button(root, text="Выполнить (Enter)", command=self.on_btn_click, bg="gray")
        self.btn.pack(side='bottom', fill='x')

        # привязка клавиши enter
        self.text.bind('<Return>', self.on_enter)
        root.bind('<Return>', self.on_enter)

        self.text.focus_set()
        self.prompt = self._make_prompt()
        self._append(self.prompt)
        # метка, чтобы нельзя было редактировать вывод выше
        self.text.mark_set('input_start', 'end-1c')

    def _make_prompt(self):
        # приглашение командной строки (например, user@host:/data$)
        user = os.environ.get('USER', 'user')
        return f"{user}@{socket.gethostname()}:{self.shell.vfs.getcwd()}$ "

    def _append(self, s):
        # добавляет текст в конец и прокручивает вниз
        self.text.insert('end', s)
        self.text.see('end')

    def on_btn_click(self):
        # обработка нажатия на кнопку
        self.on_enter(None)

    def on_enter(self, event):
        # обработка нажатия enter
        try:
            # берем текст только из строки ввода
            line = self.text.get('input_start', 'end-1c')
            self._append('\n')
            # выполняем команду
            out = self.shell.execute(line)
            if out:
                self._append(out + '\n')
            
            # если была команда exit, закрываем окно
            if self.shell.exit_requested:
                self.root.after(50, self.root.destroy)
                return 'break'
                
            # печатаем новое приглашение
            self.prompt = self._make_prompt()
            self._append(self.prompt)
            self.text.mark_set('input_start', 'end-1c')
            self.text.focus_set()
        except Exception as e:
            self._append(f"\nОШИБКА GUI: {e}\n")
        return 'break'

def run_start_script(shell, gui, path):
    # выполняет стартовый скрипт (имитация ввода пользователя)
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
        # пропускаем пустые строки и комментарии
        if not line.strip() or line.strip().startswith('#'):
            continue
            
        # печатаем приглашение и саму команду
        gui._append(gui.prompt)
        gui._append(line + '\n')
        
        # выполняем
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
    # парсим аргументы командной строки
    p = argparse.ArgumentParser(description="Эмулятор shell")
    p.add_argument('--vfs', help="Путь к ZIP-архиву VFS")
    p.add_argument('--start-script', help="Путь к стартовому скрипту")
    p.add_argument('--debug', action='store_true', help="Отладочный вывод")
    return p.parse_args()

def main():
    args = parse_args()
    
    # создает архивы, если их нет
    ensure_vfs()

    # отладочный вывод параметров (этап 2)
    if args.debug:
        print(f"[DEBUG] vfs          = {args.vfs!r}")
        print(f"[DEBUG] start-script = {args.start_script!r}")
        print(f"[DEBUG] title        = {build_title()}")

    # VFS
    try:
        vfs = VFS(args.vfs) if args.vfs else VFS()
    except VFSError as e:
        print(f"Ошибка VFS: {e}", file=sys.stderr)
        sys.exit(1)

    shell = Shell(vfs)
    root = tk.Tk()
    gui = ShellGUI(root, shell)

    root.after(200, lambda: gui.text.focus_force())

    # если передан скрипт, запускаем его
    if args.start_script:
        run_start_script(shell, gui, args.start_script)

    root.mainloop()

if __name__ == '__main__':
    main()
