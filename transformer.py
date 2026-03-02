from lexer import Lexer
from parser import Parser, print_ast
from parser import (
    Program, Number, String, Identifier,
    BinaryOp, Assignment, Print, If, While, FunctionCall
)
from semantic import SemanticAnalyzer


class Transformer:
    def transform(self, node):
        if isinstance(node, Program):
            return Program([s for s in (self.transform(st) for st in node.statements) if s])

        elif isinstance(node, Assignment):
            return Assignment(node.name, self.transform(node.value))

        elif isinstance(node, Print):
            return Print(self.transform(node.expression))

        elif isinstance(node, BinaryOp):
            return self.transform_binary(node)

        elif isinstance(node, FunctionCall):
            return FunctionCall(node.name, [self.transform(a) for a in node.args])

        elif isinstance(node, If):
            return self.transform_if(node)

        elif isinstance(node, While):
            return self.transform_while(node)

        elif isinstance(node, (Number, String, Identifier)):
            return node

        return node

    def transform_binary(self, node):
        left  = self.transform(node.left)
        right = self.transform(node.right)

        # constant folding
        if isinstance(left, Number) and isinstance(right, Number):
            return self.fold_constants(left, node.op, right)

        # identity rules  (only safe for numeric zero/one)
        if node.op.name == "PLUS":
            if isinstance(right, Number) and right.value in ("0", "0.0"):
                return left
            if isinstance(left, Number) and left.value in ("0", "0.0"):
                return right
        if node.op.name == "MULTIPLY":
            if isinstance(right, Number) and right.value in ("1", "1.0"):
                return left
            if isinstance(left, Number) and left.value in ("1", "1.0"):
                return right
            if isinstance(right, Number) and right.value in ("0", "0.0"):
                return Number("0")
            if isinstance(left, Number) and left.value in ("0", "0.0"):
                return Number("0")

        return BinaryOp(left, node.op, right)

    def fold_constants(self, left, op, right):
        l = float(left.value)
        r = float(right.value)
        ops = {
            "PLUS":     l + r,
            "MINUS":    l - r,
            "MULTIPLY": l * r,
            "MODULO":   l % r if r != 0 else None,
        }
        if op.name == "DIVIDE":
            return Number(str(l / r)) if r != 0 else BinaryOp(left, op, right)
        if op.name == "FLOOR_DIVIDE":
            return Number(str(int(l // r))) if r != 0 else BinaryOp(left, op, right)
        result = ops.get(op.name)
        if result is not None:
            val = int(result) if result == int(result) else result
            return Number(str(val))
        return BinaryOp(left, op, right)

    def transform_if(self, node):
        condition = self.transform(node.condition)
        body = [s for s in (self.transform(st) for st in node.body) if s]
        elif_clauses = [
            (self.transform(c), [s for s in (self.transform(st) for st in b) if s])
            for c, b in node.elif_clauses
        ]
        else_body = [s for s in (self.transform(st) for st in node.else_body) if s]
        return If(condition, body, elif_clauses, else_body)

    def transform_while(self, node):
        condition = self.transform(node.condition)
        if isinstance(condition, Number) and float(condition.value) == 0:
            return None
        body = [s for s in (self.transform(st) for st in node.body) if s]
        return While(condition, body)


if __name__ == "__main__":
    print("Enter Python code (press Enter twice to finish):\n")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    source_code = "\n".join(lines)
    try:
        tokens   = Lexer(source_code).tokenize()
        ast      = Parser(tokens).parse()
        SemanticAnalyzer().analyze(ast)
        new_ast  = Transformer().transform(ast)
        print("\n========== TRANSFORMED AST ==========\n")
        print_ast(new_ast)
    except Exception as e:
        print("Error:", e)