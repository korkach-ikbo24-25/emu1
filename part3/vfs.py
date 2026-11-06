import zipfile
from pathlib import PurePosixPath

# ошибка файловой системы
class VFSError(Exception):
    pass

class VFS:
    def __init__(self, zip_path: str | None = None):
        # словарь, где ключ - путь к файлу, значение - его содержимое в байтах
        self.files: dict[str, bytes] = {}
        # текущая папка (по умолчанию корень)
        self.cwd = '/'
        if zip_path:
            self._load_zip(zip_path)
        self._ensure_root()

    def _load_zip(self, zip_path: str):
        # загружаем zip-архив в память
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for info in zf.infolist():
                    # делаем так, чтобы все пути начинались с /
                    name = '/' + info.filename.lstrip('/')
                    # если это папка, данных нет, иначе читаем байты
                    data = zf.read(info) if not info.is_dir() else b''
                    self.files[name] = data
                    # если это папка, добавляем ей слеш на конце для удобства
                    if info.is_dir() and not name.endswith('/'):
                        self.files[name + '/'] = b''
        except FileNotFoundError:
            raise VFSError(f"ZIP не найден: {zip_path}")
        except zipfile.BadZipFile:
            raise VFSError(f"Повреждённый ZIP: {zip_path}")

    def _ensure_root(self):
        # гарантируем, что корень всегда существует
        self.files.setdefault('/', b'')

    def _normalize(self, path: str) -> str:
        # превращает относительный путь (типа data/../file) в абсолютный
        if not path.startswith('/'):
            path = str(PurePosixPath(self.cwd) / path)
        parts = []
        for p in path.split('/'):
            if p in ('', '.'):
                continue
            if p == '..':
                # если видим две точки, удаляем предыдущую папку из списка
                if parts:
                    parts.pop()
            else:
                parts.append(p)
        return '/' + '/'.join(parts)

    def _is_dir(self, path: str) -> bool:
        # проверяет, является ли путь папкой
        if path == '/':
            return True
        if path + '/' in self.files:
            return True
        prefix = path + '/'
        if any(k.startswith(prefix) for k in self.files):
            return True
        return False

    def listdir(self, path: str) -> list[str]:
        # реализация команды ls (выводит список файлов)
        p = self._normalize(path)
        if not self._is_dir(p):
            raise VFSError(f"Не директория: {path}")
            
        prefix = '' if p == '/' else p + '/'
        result = set()
        
        for k in self.files:
            if k == p or k == p + '/':
                continue
            if k.startswith(prefix):
                rest = k[len(prefix):]
                if rest:
                    # берем только первый уровень (то есть саму папку или файл)
                    result.add(rest.split('/')[0])
                    
        return sorted(result)

    def read_file(self, path: str) -> bytes:
        # реализация чтения файла (для команды cat)
        p = self._normalize(path)
        if p not in self.files or self._is_dir(p):
            raise VFSError(f"Нет такого файла: {path}")
        return self.files[p]

    def getcwd(self) -> str:
        # возвращает текущую папку (для pwd)
        return self.cwd

    def chdir(self, path: str):
        # реализация команды cd (смена папки)
        p = self._normalize(path)
        if not self._is_dir(p):
            raise VFSError(f"Не директория: {path}")
        self.cwd = p
