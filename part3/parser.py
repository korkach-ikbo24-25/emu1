import os
import re

# ошибка, которая возникает, если пользователь не закрыл кавычку
class ParseError(Exception):
    pass

# регулярное выражение для поиска переменных типа $HOME или ${USER}
_VAR_RE = re.compile(r'\$(\w+|\{[^}]+\})')

def expand_vars(token: str) -> str:
    # функция, которая подставляет реальные значения переменных окружения
    def repl(m):
        name = m.group(1)
        if name.startswith('{') and name.endswith('}'):
            name = name[1:-1]
        
        # чтобы $HOME и $USER всегда находились
        if name == 'HOME':
            val = os.environ.get('HOME') or os.environ.get('USERPROFILE')
        elif name == 'USER':
            val = os.environ.get('USER') or os.environ.get('USERNAME')
        else:
            val = os.environ.get(name)
            
        return val or '' # если переменная не найдена, возвращаем пустоту
        
    return _VAR_RE.sub(repl, token)

def tokenize(line: str) -> list:
    # разбивает строку на слова, учитывая кавычки
    tokens, cur, quote = [], '', None
    for c in line:
        if quote:
            # если мы внутри кавычек, проверяем, не закрылась ли она
            if c == quote:
                quote = None
            else:
                cur += c
        elif c in ('"', "'"):
            # если встретили кавычку, запоминаем ее и начинаем собирать слово
            quote = c
        elif c.isspace():
            # если пробел и мы не в кавычках, значит слово закончилось
            if cur:
                tokens.append(cur)
                cur = ''
        else:
            # обычный символ, добавляем к текущему слову
            cur += c
    if quote:
        raise ParseError(f"Незакрытая кавычка {quote}")
    if cur:
        tokens.append(cur)
    # в конце прогоняем каждое слово через подстановку переменных
    return [expand_vars(t) for t in tokens]
