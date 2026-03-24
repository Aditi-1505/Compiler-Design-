from parser import (
    Program, Number, String, Identifier, BinaryOp,
    Assignment, Print, If, While, For, FunctionCall
)
from lexer import Lexer
from parser import Parser

class SemanticError(Exception):
    pass

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}

    def analyze(self, node):
        if isinstance(node, Program):
            for stmt in node.statements:
                self.analyze(stmt)
        elif isinstance(node, Assignment):
            self.analyze(node.value)
            if isinstance(node.value, Number):
                self.symbol_table[node.name] = "number"
            elif isinstance(node.value, String):
                self.symbol_table[node.name] = "string"
            else:
                self.symbol_table[node.name] = "unknown"
        elif isinstance(node, Print):
            self.analyze(node.expression)
        elif isinstance(node, BinaryOp):
            self.analyze(node.left)
            self.analyze(node.right)
            left_type = None
            right_type = None
            if isinstance(node.left, Identifier):
                if node.left.name not in self.symbol_table:
                    raise SemanticError(
                        f"Variable '{node.left.name}' used before assignment"
                    )
                left_type = self.symbol_table[node.left.name]
            if isinstance(node.right, Identifier):
                if node.right.name not in self.symbol_table:
                    raise SemanticError(
                        f"Variable '{node.right.name}' used before assignment"
                    )
                right_type = self.symbol_table[node.right.name]
            if node.op.name in ("MINUS", "MULTIPLY", "DIVIDE", "MODULO"):
                if left_type == "string" or right_type == "string":
                    raise SemanticError(
                        f"Operator '{node.op.name}' cannot be used with strings"
                    )
        elif isinstance(node, FunctionCall):
            for arg in node.args:
                self.analyze(arg)
        elif isinstance(node, Identifier):
            if node.name not in self.symbol_table:
                raise SemanticError(
                    f"Variable '{node.name}' used before assignment"
                )
        elif isinstance(node, If):
            self.analyze(node.condition)
            for stmt in node.body:
                self.analyze(stmt)
            for cond, body in node.elif_clauses:
                self.analyze(cond)
                for stmt in body:
                    self.analyze(stmt)
            for stmt in node.else_body:
                self.analyze(stmt)
        elif isinstance(node, While):
            self.analyze(node.condition)
            for stmt in node.body:
                self.analyze(stmt)
        elif isinstance(node, For):
            self.analyze(node.start)
            self.analyze(node.stop)
            if node.step:
                self.analyze(node.step)
            self.symbol_table[node.var] = "number"
            for stmt in node.body:
                self.analyze(stmt)
        elif isinstance(node, (Number, String)):
            pass
        else:
            raise SemanticError(f"Unknown node type: {type(node).__name__}")

def main():
    try:
        print("Enter your program (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        source_code = "\n".join(lines)
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print("Semantic analysis completed successfully!")
    except SemanticError as e:
        print("Semantic Error:", e)
    except Exception as e:
        print("Error:", e)
if __name__ == "__main__":
    main()
