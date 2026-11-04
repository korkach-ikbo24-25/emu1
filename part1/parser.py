import os
import re

class ParseError(Exception):
    pass

_VAR_RE = re.compile(r'\$(\w+|\{[^}]+\})')

def expand_vars(token: str) -> str:
    def repl(m):
        name = m.group(1)
        if name.startswith('{') and name.endswith('}'):
            name = name[1:-1]
        return os.environ.get(name, '')
    return _VAR_RE.sub(repl, token)

def tokenize(line: str) -> list:
    tokens, cur, quote = [], '', None
    for c in line:
        if quote:
            if c == quote:
                quote = None
            else:
                cur += c
        elif c in ('"', "'"):
            quote = c
        elif c.isspace():
            if cur:
                tokens.append(cur)
                cur = ''
        else:
            cur += c
    if quote:
        raise ParseError(f"Незакрытая кавычка {quote}")
    if cur:
        tokens.append(cur)
    return [expand_vars(t) for t in tokens]
