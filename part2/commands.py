from parser import tokenize, ParseError

class Shell:
    def __init__(self):
        self.exit_requested = False
        self.commands = {
            'ls':   self.cmd_ls,
            'cd':   self.cmd_cd,
            'exit': self.cmd_exit,
        }

    def execute(self, line: str) -> str:
        line = line.strip()
        if not line:
            return ''
        try:
            tokens = tokenize(line)
        except ParseError as e:
            return f"parse error: {e}"
        if not tokens:
            return ''
        cmd, args = tokens[0], tokens[1:]
        fn = self.commands.get(cmd)
        if not fn:
            return f"{cmd}: команда не найдена"
        return fn(args)

    def cmd_ls(self, args):
        return f"ls called with args={args}"

    def cmd_cd(self, args):
        return f"cd called with args={args}"

    def cmd_exit(self, args):
        self.exit_requested = True
        return "Завершение работы..."
