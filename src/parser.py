from lexer import TokenType, Token, LexerError, Lexer

class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class Number(ASTNode):
    def __init__(self, value):
        self.value = value

class String(ASTNode):
    def __init__(self, value):
        self.value = value

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class BinaryOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Assignment(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class Print(ASTNode):
    def __init__(self, expression):
        self.expression = expression

class If(ASTNode):
    def __init__(self, condition, body, elif_clauses=None, else_body=None):
        self.condition = condition
        self.body = body
        self.elif_clauses = elif_clauses or []
        self.else_body = else_body or []

class While(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class For(ASTNode):
    def __init__(self, var, start, stop, step, body):
        self.var = var      # loop variable name (string)
        self.start = start  # ASTNode expression
        self.stop = stop    # ASTNode expression
        self.step = step    # ASTNode expression or None
        self.body = body    # list of statements

class FunctionCall(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args


_COMPARE_OPS = (
    TokenType.DOUBLE_EQUALS, TokenType.NOT_EQUALS,
    TokenType.LESS_THAN, TokenType.GREATER_THAN,
    TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL,
)
_ADD_OPS = (TokenType.PLUS, TokenType.MINUS)
_MUL_OPS = (
    TokenType.MULTIPLY,
    TokenType.DIVIDE,
    TokenType.FLOOR_DIVIDE,
    TokenType.MODULO,
)

class _Op:
    def __init__(self, token_type):
        self.name = token_type.name
        self.value = token_type.value

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.current = self.tokens[0]
    def eat(self, token_type):
        if self.current.type == token_type:
            self.position += 1
            if self.position < len(self.tokens):
                self.current = self.tokens[self.position]
        else:
            raise Exception(
                f"Expected {token_type}, got {self.current.type} ({self.current.value})"
            )
    def skip_newlines(self):
        while self.current.type == TokenType.NEWLINE:
            self.eat(TokenType.NEWLINE)
    def parse(self):
        statements = []
        while self.current.type != TokenType.EOF:
            self.skip_newlines()
            if self.current.type == TokenType.EOF:
                break
            statements.append(self.statement())
        return Program(statements)
    def statement(self):
        if self.current.type == TokenType.PRINT:
            return self.print_statement()
        if self.current.type == TokenType.IF:
            return self.if_statement()
        if self.current.type == TokenType.WHILE:
            return self.while_statement()
        if self.current.type == TokenType.FOR:
            return self.for_statement()
        if self.current.type == TokenType.IDENTIFIER:
            next_pos = self.position + 1
            if next_pos < len(self.tokens) and \
               self.tokens[next_pos].type == TokenType.EQUALS:
                return self.assignment()
            return self.expression()
        raise Exception(f"Unexpected token {self.current.type}")
    def assignment(self):
        name = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.EQUALS)
        return Assignment(name, self.expression())
    def print_statement(self):
        self.eat(TokenType.PRINT)
        self.eat(TokenType.LPAREN)
        args = []
        if self.current.type != TokenType.RPAREN:
            args.append(self.expression())
            while self.current.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                args.append(self.expression())
        self.eat(TokenType.RPAREN)
        if len(args) == 1:
            return Print(args[0])
        return FunctionCall("print", args)
    def if_statement(self):
        self.eat(TokenType.IF)
        condition = self.expression()
        self.eat(TokenType.COLON)
        body = self._parse_block()
        elif_clauses = []
        else_body = []
        while self.current.type == TokenType.ELIF:
            self.eat(TokenType.ELIF)
            cond = self.expression()
            self.eat(TokenType.COLON)
            elif_clauses.append((cond, self._parse_block()))
        if self.current.type == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            self.eat(TokenType.COLON)
            else_body = self._parse_block()
        return If(condition, body, elif_clauses, else_body)
    def while_statement(self):
        self.eat(TokenType.WHILE)
        condition = self.expression()
        self.eat(TokenType.COLON)
        body = self._parse_block()
        return While(condition, body)
    def for_statement(self):
        self.eat(TokenType.FOR)
        var = self.current.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.IN)
        # only range(...) is supported
        if self.current.type != TokenType.IDENTIFIER or self.current.value != "range":
            raise Exception("For loop only supports 'range(...)' as iterable")
        self.eat(TokenType.IDENTIFIER)  # eat 'range'
        self.eat(TokenType.LPAREN)
        args = [self.expression()]
        while self.current.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            args.append(self.expression())
        self.eat(TokenType.RPAREN)
        if len(args) == 1:
            start, stop, step = Number("0"), args[0], None
        elif len(args) == 2:
            start, stop, step = args[0], args[1], None
        elif len(args) == 3:
            start, stop, step = args[0], args[1], args[2]
        else:
            raise Exception("range() takes 1 to 3 arguments")
        self.eat(TokenType.COLON)
        body = self._parse_block()
        return For(var, start, stop, step, body)
    def _parse_block(self):
        self.eat(TokenType.NEWLINE)
        self.eat(TokenType.INDENT)
        statements = []
        while self.current.type not in (TokenType.DEDENT, TokenType.EOF):
            self.skip_newlines()
            if self.current.type in (TokenType.DEDENT, TokenType.EOF):
                break
            statements.append(self.statement())
            if self.current.type == TokenType.NEWLINE:
                self.eat(TokenType.NEWLINE)
        self.eat(TokenType.DEDENT)
        return statements
    def expression(self):
        node = self.add_expr()
        while self.current.type in _COMPARE_OPS:
            op = self.current.type
            self.eat(op)
            node = BinaryOp(node, _Op(op), self.add_expr())
        return node
    def add_expr(self):
        node = self.term()
        while self.current.type in _ADD_OPS:
            op = self.current.type
            self.eat(op)
            node = BinaryOp(node, _Op(op), self.term())
        return node
    def term(self):
        node = self.factor()
        while self.current.type in _MUL_OPS:
            op = self.current.type
            self.eat(op)
            node = BinaryOp(node, _Op(op), self.factor())
        return node
    def factor(self):
        token = self.current
        if token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expression()
            self.eat(TokenType.RPAREN)
            return node
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(token.value)
        if token.type == TokenType.STRING:
            self.eat(TokenType.STRING)
            return String(token.value)
        if token.type == TokenType.IDENTIFIER:
            name = token.value
            self.eat(TokenType.IDENTIFIER)
            if self.current.type == TokenType.LPAREN:
                return self._parse_call(name)
            return Identifier(name)
        if token.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            return BinaryOp(Number("0"), _Op(TokenType.MINUS), self.factor())
        raise Exception(
            f"Unexpected token {token.type} ({token.value})"
        )
    def _parse_call(self, name):
        self.eat(TokenType.LPAREN)
        args = []
        if self.current.type != TokenType.RPAREN:
            args.append(self.expression())
            while self.current.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                args.append(self.expression())
        self.eat(TokenType.RPAREN)
        return FunctionCall(name, args)
def print_ast(node, indent=0):
    space = "  " * indent
    if isinstance(node, Program):
        print(space + "Program")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)
    elif isinstance(node, Assignment):
        print(space + f"Assignment({node.name})")
        print_ast(node.value, indent + 1)
    elif isinstance(node, Print):
        print(space + "Print")
        print_ast(node.expression, indent + 1)
    elif isinstance(node, BinaryOp):
        print(space + f"BinaryOp({node.op.name})")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif isinstance(node, If):
        print(space + "If")
        print_ast(node.condition, indent + 1)
        for stmt in node.body:
            print_ast(stmt, indent + 1)
        for cond, body in node.elif_clauses:
            print(space + "  Elif")
            print_ast(cond, indent + 1)
            for stmt in body:
                print_ast(stmt, indent + 1)
        if node.else_body:
            print(space + "  Else")
            for stmt in node.else_body:
                print_ast(stmt, indent + 1)
    elif isinstance(node, While):
        print(space + "While")
        print_ast(node.condition, indent + 1)
        for stmt in node.body:
            print_ast(stmt, indent + 1)
    elif isinstance(node, For):
        step_str = f", step={node.step.value}" if node.step else ""
        print(space + f"For({node.var}, start, stop{step_str})")
        print_ast(node.start, indent + 1)
        print_ast(node.stop, indent + 1)
        if node.step:
            print_ast(node.step, indent + 1)
        for stmt in node.body:
            print_ast(stmt, indent + 1)
    elif isinstance(node, FunctionCall):
        print(space + f"FunctionCall({node.name})")
        for arg in node.args:
            print_ast(arg, indent + 1)
    elif isinstance(node, Number):
        print(space + f"Number({node.value})")
    elif isinstance(node, String):
        print(space + f"String({node.value})")
    elif isinstance(node, Identifier):
        print(space + f"Identifier({node.name})")
    else:
        print(space + f"Unknown({type(node).__name__})")

if __name__ == "__main__":
    print("Enter Python code (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    source_code = "\n".join(lines)
    try:
        tokens = Lexer(source_code).tokenize()
        ast = Parser(tokens).parse()
        print("\n===== AST OUTPUT =====\n")
        print_ast(ast)
    except Exception as e:
        print("Parser Error:", e)
