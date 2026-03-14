from enum import Enum

class TokenType(Enum):
    DEF = "def"
    IF = "if"
    ELIF = "elif"
    ELSE = "else"
    FOR = "for"
    WHILE = "while"
    IN = "in"
    RETURN = "return"
    PRINT = "print"
    TRUE = "True"
    FALSE = "False"
    NONE = "None"
    AND = "and"
    OR = "or"
    NOT = "not"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    FLOOR_DIVIDE = "//"
    MODULO = "%"
    POWER = "**"
    EQUALS = "="
    DOUBLE_EQUALS = "=="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    LPAREN = "("
    RPAREN = ")"
    COMMA = ","
    COLON = ":"
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    COMMENT = "COMMENT"
    EOF = "EOF"

class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
    def __repr__(self):
        return f"Token({self.type.name}, {self.value}, {self.line}:{self.column})"

class LexerError(Exception):
    def __init__(self, message, line, column, suggestion=None):
        self.message = message
        self.line = line
        self.column = column
        self.suggestion = suggestion
        super().__init__(message)

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.indent_stack = [0]
        self.keywords = {
            "def", "if", "elif", "else",
            "for", "while", "in",
            "return", "print",
            "True", "False", "None",
            "and", "or", "not"
        }
    def tokenize(self):
        self.code = self.code.replace("\r\n", "\n").replace("\r", "\n")
        lines = self.code.split("\n")
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            self.invalid_char(line, line_num)
            self.mixed_indent(line, line_num)
            indent_level = len(line) - len(line.lstrip())
            self.handleindentation(indent_level, line_num)
            stripped = line.strip()
            if stripped.startswith("#"):
                self.tokens.append(Token(TokenType.COMMENT, stripped, line_num, 1))
                continue
            self.tokenizeline(stripped, line_num, indent_level)
            self.tokens.append(Token(TokenType.NEWLINE, "\\n", line_num, len(line)))
        final_line = len(lines)
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, "", final_line, 0))
        self.tokens.append(Token(TokenType.EOF, "", final_line, 0))
        return self.tokens
    def invalid_char(self, line, line_num):
        if "\t" in line:
            pos = line.index("\t") + 1
            raise LexerError(
                "Tab character found",
                line_num,
                pos,
                "Use spaces instead of tabs"
            )
    def mixed_indent(self, line, line_num):
        indent = line[:len(line) - len(line.lstrip())]
        if "\t" in indent and " " in indent:
            raise LexerError(
                "Mixed tabs and spaces",
                line_num,
                1,
                "Use only spaces for indentation"
            )
    def handleindentation(self, indent_level, line_num):
        current = self.indent_stack[-1]
        if indent_level > current:
            self.indent_stack.append(indent_level)
            self.tokens.append(Token(TokenType.INDENT, "", line_num, 1))
        elif indent_level < current:
            while self.indent_stack and indent_level < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, "", line_num, 1))
    def tokenizeline(self, line, line_num, base_column):
        i = 0
        while i < len(line):
            char = line[i]
            column = base_column + i + 1
            if char.isspace():
                i += 1
                continue
            if char.isdigit():
                num, length = self.parsenumber(line, i)
                self.tokens.append(Token(TokenType.NUMBER, num, line_num, column))
                i += length
                continue
            if char in ("'", '"'):
                string, length = self.parsestring(line, i)
                self.tokens.append(Token(TokenType.STRING, string, line_num, column))
                i += length
                continue
            if char.isalpha() or char == "_":
                identifier, length = self.parseidentifier(line, i)
                if identifier in self.keywords:
                    token_type = TokenType(identifier)
                else:
                    token_type = TokenType.IDENTIFIER
                self.tokens.append(Token(token_type, identifier, line_num, column))
                i += length
                continue
            if i + 1 < len(line):
                two = line[i:i+2]
                two_ops = {
                    "//": TokenType.FLOOR_DIVIDE,
                    "**": TokenType.POWER,
                    "==": TokenType.DOUBLE_EQUALS,
                    "!=": TokenType.NOT_EQUALS,
                    "<=": TokenType.LESS_EQUAL,
                    ">=": TokenType.GREATER_EQUAL
                }
                if two in two_ops:
                    self.tokens.append(Token(two_ops[two], two, line_num, column))
                    i += 2
                    continue
            single = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.MULTIPLY,
                "/": TokenType.DIVIDE,
                "%": TokenType.MODULO,
                "=": TokenType.EQUALS,
                "<": TokenType.LESS_THAN,
                ">": TokenType.GREATER_THAN,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                ",": TokenType.COMMA,
                ":": TokenType.COLON
            }
            if char in single:
                self.tokens.append(Token(single[char], char, line_num, column))
                i += 1
                continue
            raise LexerError(
                f"Unrecognized character '{char}'",
                line_num,
                column
            )
    def parsenumber(self, line, start):
        i = start
        while i < len(line) and (line[i].isdigit() or line[i] == "."):
            i += 1
        return line[start:i], i - start
    def parsestring(self, line, start):
        quote = line[start]
        i = start + 1
        string = ""
        while i < len(line):
            if line[i] == quote:
                return string, i - start + 1
            string += line[i]
            i += 1
        raise LexerError("Unclosed string", 0, start)
    def parseidentifier(self, line, start):
        i = start
        while i < len(line) and (line[i].isalnum() or line[i] == "_"):
            i += 1
        return line[start:i], i - start

if __name__ == "__main__":
    print("Enter Python code (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    source_code = "\n".join(lines)
    lexer = Lexer(source_code)
    try:
        tokens = lexer.tokenize()
        print("\nTOKEN OUTPUT\n")
        print(f"{'TYPE':<15}{'VALUE'}")
        print("-" * 30)
        for token in tokens:
            print(f"{token.type.name:<15}{token.value}")
    except LexerError as e:
        print("\nLEXER ERROR")
        print("Message:", e.message)
        print("Line:", e.line, "Column:", e.column)
        if e.suggestion:
            print("Suggestion:", e.suggestion)
