import zipfile
import io
import base64
from pathlib import PurePosixPath

class VFSError(Exception):
    pass

class VFS:
    def __init__(self, zip_path: str | None = None):
        self.files: dict[str, bytes] = {}
        self.cwd = '/'
        if zip_path:
            self._load_zip(zip_path)
        self._ensure_root()

    #загрузка
    def _load_zip(self, zip_path: str):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for info in zf.infolist():
                    name = '/' + info.filename.lstrip('/')
                    data = zf.read(info) if not info.is_dir() else b''
                    self.files[name] = data
                    if info.is_dir() and not name.endswith('/'):
                        self.files[name + '/'] = b''
        except FileNotFoundError:
            raise VFSError(f"ZIP не найден: {zip_path}")
        except zipfile.BadZipFile:
            raise VFSError(f"Повреждённый ZIP: {zip_path}")

    def _ensure_root(self):
        self.files.setdefault('/', b'')

    #утилиты
    def _normalize(self, path: str) -> str:
        if not path.startswith('/'):
            path = str(PurePosixPath(self.cwd) / path)
        parts = []
        for p in path.split('/'):
            if p in ('', '.'):
                continue
            if p == '..':
                if parts:
                    parts.pop()
            else:
                parts.append(p)
        return '/' + '/'.join(parts)

    def _is_dir(self, path: str) -> bool:
        if path == '/':
            return True
        return path in self.files and (path.endswith('/') or any(
            k.startswith(path + '/') for k in self.files
        ))

    #публичное API
    def resolve(self, path: str) -> str:
        return self._normalize(path)

    def exists(self, path: str) -> bool:
        p = self._normalize(path)
        return p == '/' or p in self.files or self._is_dir(p)

    def listdir(self, path: str) -> list[str]:
        p = self._normalize(path)
        if not self._is_dir(p):
            raise VFSError(f"Не директория: {path}")
        prefix = '' if p == '/' else p + '/'
        result = set()
        for k in self.files:
            if k == p:
                continue
            if k.startswith(prefix):
                rest = k[len(prefix):]
                if rest:
                    result.add(rest.split('/')[0])
        return sorted(result)

    def is_dir(self, path: str) -> bool:
        return self._is_dir(self._normalize(path))

    def read_file(self, path: str) -> bytes:
        p = self._normalize(path)
        if p not in self.files or self._is_dir(p):
            raise VFSError(f"Нет такого файла: {path}")
        return self.files[p]

    def getcwd(self) -> str:
        return self.cwd

    def chdir(self, path: str):
        p = self._normalize(path)
        if not self._is_dir(p):
            raise VFSError(f"Не директория: {path}")
        self.cwd = p
