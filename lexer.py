from enum import Enum
import re


class TokenType(Enum):
    DEF = 'def'
    IF = 'if'
    ELIF = 'elif'
    ELSE = 'else'
    FOR = 'for'
    WHILE = 'while'
    IN = 'in'
    RETURN = 'return'
    PRINT = 'print'
    TRUE = 'True'
    FALSE = 'False'
    NONE = 'None'
    AND = 'and'
    OR = 'or'
    NOT = 'not'

    IDENTIFIER = 'IDENTIFIER'
    NUMBER = 'NUMBER'
    STRING = 'STRING'

    PLUS = '+'
    MINUS = '-'
    MULTIPLY = '*'
    DIVIDE = '/'
    FLOOR_DIVIDE = '//'
    MODULO = '%'
    POWER = '**'
    EQUALS = '='
    DOUBLE_EQUALS = '=='
    NOT_EQUALS = '!='
    LESS_THAN = '<'
    GREATER_THAN = '>'
    LESS_EQUAL = '<='
    GREATER_EQUAL = '>='

    LPAREN = '('
    RPAREN = ')'
    LBRACKET = '['
    RBRACKET = ']'
    LBRACE = '{'
    RBRACE = '}'
    COMMA = ','
    COLON = ':'
    DOT = '.'
    SEMI = ';'

    NEWLINE = 'NEWLINE'
    INDENT = 'INDENT'
    DEDENT = 'DEDENT'
    COMMENT = 'COMMENT'
    EOF = 'EOF'


class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class LexerError(Exception):
    def __init__(self, message, line, column, suggestion=None):
        self.message = message
        self.line = line
        self.column = column
        self.suggestion = suggestion
        super().__init__(self.message)


class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.indent_stack = [0]
        self.keywords = {
            'def', 'if', 'elif', 'else', 'for', 'while', 'in',
            'return', 'print', 'True', 'False', 'None', 'and', 'or', 'not'
        }

    def tokenize(self):
        try:
            self.code = self.code.replace('\r\n', '\n').replace('\r', '\n')

            if not self.code.strip():
                raise LexerError("Empty input", line=1, column=1,
                                  suggestion="Provide Python code to transpile")

            lines = self.code.split('\n')

            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue

                self._check_invalid_characters(line, line_num)

                if line.strip().startswith('#'):
                    self.tokens.append(Token(TokenType.COMMENT, line.strip(), line_num, 1))
                    continue

                self._check_mixed_indentation(line, line_num)

                indent_level = len(line) - len(line.lstrip())
                stripped = line.strip()

                self._handle_indentation(indent_level, line_num)
                self._tokenize_line(stripped, line_num, indent_level)
                self.tokens.append(Token(TokenType.NEWLINE, '\\n', line_num, len(line)))

            final_line = len(lines)
            while len(self.indent_stack) > 1:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, '', final_line, 0))

            self.tokens.append(Token(TokenType.EOF, '', final_line, 0))
            return self.tokens

        except LexerError:
            raise
        except Exception as e:
            raise LexerError(f"Unexpected lexer error: {str(e)}", line=1, column=1)

    def _check_invalid_characters(self, line, line_num):
        if '\t' in line and line.strip() and not line.strip().startswith('#'):
            tab_pos = line.index('\t') + 1
            raise LexerError("Tab character found", line=line_num, column=tab_pos,
                              suggestion="Use spaces for indentation instead of tabs")

    def _check_mixed_indentation(self, line, line_num):
        indent_part = line[:len(line) - len(line.lstrip())]
        if '\t' in indent_part and ' ' in indent_part:
            raise LexerError("Mixed tabs and spaces in indentation", line=line_num, column=1,
                              suggestion="Use either tabs OR spaces consistently, not both")

    def _handle_indentation(self, indent_level, line_num):
        current_indent = self.indent_stack[-1]

        if indent_level > current_indent:
            if indent_level - current_indent > 8:
                raise LexerError(
                    f"Excessive indentation increase ({indent_level - current_indent} spaces)",
                    line=line_num, column=1,
                    suggestion="Typically use 4 spaces per indentation level"
                )
            self.indent_stack.append(indent_level)
            self.tokens.append(Token(TokenType.INDENT, ' ' * indent_level, line_num, 1))

        elif indent_level < current_indent:
            if indent_level not in self.indent_stack:
                raise LexerError(
                    "Indentation doesn't match any outer indentation level",
                    line=line_num, column=1,
                    suggestion=f"Expected {current_indent} or {self.indent_stack[-2] if len(self.indent_stack) > 1 else 0} spaces"
                )
            while self.indent_stack[-1] > indent_level:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, '', line_num, 1))

    def _tokenize_line(self, line, line_num, base_column):
        i = 0
        while i < len(line):
            char = line[i]
            column = base_column + i + 1

            if char.isspace():
                i += 1
                continue

            if char.isdigit() or (char == '.' and i + 1 < len(line) and line[i + 1].isdigit()):
                try:
                    num_str, consumed = self._parse_number(line, i, line_num, column)
                    self.tokens.append(Token(TokenType.NUMBER, num_str, line_num, column))
                    i += consumed
                except ValueError as e:
                    raise LexerError(str(e), line_num, column, "Check number format")
                continue

            if char in ('"', "'"):
                try:
                    string_val, consumed = self._parse_string(line, i, line_num, column)
                    self.tokens.append(Token(TokenType.STRING, string_val, line_num, column))
                    i += consumed
                except LexerError:
                    raise
                continue

            if char == '#':
                break

            if char.isalpha() or char == '_':
                identifier, consumed = self._parse_identifier(line, i)
                if identifier in self.keywords:
                    token_type = TokenType(identifier)
                else:
                    token_type = TokenType.IDENTIFIER
                self.tokens.append(Token(token_type, identifier, line_num, column))
                i += consumed
                continue

            if i + 1 < len(line):
                two_char = line[i:i+2]
                two_char_ops = {
                    '//': TokenType.FLOOR_DIVIDE,
                    '**': TokenType.POWER,
                    '==': TokenType.DOUBLE_EQUALS,
                    '!=': TokenType.NOT_EQUALS,
                    '<=': TokenType.LESS_EQUAL,
                    '>=': TokenType.GREATER_EQUAL
                }
                if two_char in two_char_ops:
                    self.tokens.append(Token(two_char_ops[two_char], two_char, line_num, column))
                    i += 2
                    continue

            single_char_map = {
                '+': TokenType.PLUS, '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY, '/': TokenType.DIVIDE,
                '%': TokenType.MODULO, '=': TokenType.EQUALS,
                '<': TokenType.LESS_THAN, '>': TokenType.GREATER_THAN,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                ',': TokenType.COMMA, ':': TokenType.COLON,
                '.': TokenType.DOT, ';': TokenType.SEMI
            }

            if char in single_char_map:
                self.tokens.append(Token(single_char_map[char], char, line_num, column))
                i += 1
                continue

            raise LexerError(f"Unrecognized character: '{char}'", line_num, column,
                              "Remove or escape special characters")

    def _parse_number(self, line, start, line_num, column):
        i = start
        has_dot = False
        has_e = False
        num_str = ''

        while i < len(line):
            char = line[i]

            if char.isdigit():
                num_str += char
                i += 1
            elif char == '.' and not has_dot and not has_e:
                if i + 1 < len(line) and line[i + 1].isdigit():
                    has_dot = True
                    num_str += char
                    i += 1
                elif num_str:
                    break
                else:
                    raise ValueError("Invalid number: starts with dot")
            elif char in ('e', 'E') and not has_e and num_str:
                has_e = True
                num_str += char
                i += 1
                if i < len(line) and line[i] in ('+', '-'):
                    num_str += line[i]
                    i += 1
            elif char in ('x', 'X') and num_str == '0' and i == start + 1:
                num_str += char
                i += 1
                while i < len(line) and line[i] in '0123456789abcdefABCDEF':
                    num_str += line[i]
                    i += 1
                break
            elif char in ('b', 'B') and num_str == '0' and i == start + 1:
                num_str += char
                i += 1
                while i < len(line) and line[i] in '01':
                    num_str += line[i]
                    i += 1
                break
            elif char in ('o', 'O') and num_str == '0' and i == start + 1:
                num_str += char
                i += 1
                while i < len(line) and line[i] in '01234567':
                    num_str += line[i]
                    i += 1
                break
            else:
                break

        if not num_str or num_str in ('.', 'e', 'E'):
            raise ValueError("Invalid number format")

        try:
            if '0x' in num_str.lower():
                int(num_str, 16)
            elif '0b' in num_str.lower():
                int(num_str, 2)
            elif '0o' in num_str.lower():
                int(num_str, 8)
            elif 'e' in num_str.lower() or '.' in num_str:
                float(num_str)
            else:
                int(num_str)
        except ValueError:
            raise ValueError(f"Invalid number format: {num_str}")

        return num_str, i - start

    def _parse_string(self, line, start, line_num, column):
        quote_char = line[start]
        i = start + 1
        string = ''

        if i + 1 < len(line) and line[i:i+2] == quote_char * 2:
            raise LexerError("Multi-line strings not supported", line_num, column,
                              "Use single-line strings or concatenation")

        while i < len(line):
            char = line[i]
            if char == '\\' and i + 1 < len(line):
                next_char = line[i + 1]
                escape_chars = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', quote_char: quote_char}
                if next_char in escape_chars:
                    string += escape_chars[next_char]
                    i += 2
                else:
                    string += char
                    i += 1
            elif char == quote_char:
                return string, i - start + 1
            else:
                string += char
                i += 1

        raise LexerError("Unclosed string", line_num, column,
                         f"Add closing {quote_char} at end of string")

    def _parse_identifier(self, line, start):
        i = start
        identifier = ''
        while i < len(line) and (line[i].isalnum() or line[i] == '_'):
            identifier += line[i]
            i += 1
        return identifier, i - start

    def _is_valid_identifier(self, identifier):
        if not identifier:
            return False
        if not (identifier[0].isalpha() or identifier[0] == '_'):
            return False
        return all(c.isalnum() or c == '_' for c in identifier)


if __name__ == "__main__":
    print("Enter Python code (press Enter twice to finish):\n")

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
        print("\n========== TOKEN OUTPUT ==========\n")
        print(f"{'TYPE':<15}{'VALUE'}")
        print("-" * 35)
        for token in tokens:
            print(f"{token.type.name:<15}{str(token.value)}")

    except LexerError as e:
        print("\nLEXER ERROR")
        print("Message:", e.message)
        if e.suggestion:
            print("Suggestion:", e.suggestion)