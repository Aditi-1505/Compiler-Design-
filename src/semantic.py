from parser import (
    Program, Number, String, Identifier, BinaryOp,
    Assignment, Print, If, While, FunctionCall
)


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = set()

    def analyze(self, node):
        if isinstance(node, Program):
            for stmt in node.statements:
                self.analyze(stmt)

        elif isinstance(node, Assignment):
            self.analyze(node.value)
            self.symbol_table.add(node.name)

        elif isinstance(node, Print):
            self.analyze(node.expression)

        elif isinstance(node, BinaryOp):
            self.analyze(node.left)
            self.analyze(node.right)
            if node.op.name in ("MINUS", "MULTIPLY", "DIVIDE", "MODULO"):
                if isinstance(node.left, String) or isinstance(node.right, String):
                    raise SemanticError(
                        f"Operator '{node.op.name}' cannot be used with strings"
                    )

        elif isinstance(node, FunctionCall):
            for arg in node.args:
                self.analyze(arg)
            # built-ins are always valid; user-defined not tracked here

        elif isinstance(node, Identifier):
            if node.name not in self.symbol_table:
                raise SemanticError(f"Variable '{node.name}' used before assignment")

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

        elif isinstance(node, (Number, String)):
            pass

        else:
            raise SemanticError(f"Unknown node type: {type(node).__name__}")