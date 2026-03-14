from parser import Program, Assignment, Identifier, BinaryOp, Print, FunctionCall, If, While

class SymbolTableGenerator:

    def __init__(self):
        self.symbol_table = {}

    def generate(self, node):

        if isinstance(node, Program):
            for stmt in node.statements:
                self.generate(stmt)

        elif isinstance(node, Assignment):
            name = node.name
            self.symbol_table[name] = "variable"
            self.generate(node.value)

        elif isinstance(node, Identifier):
            if node.name not in self.symbol_table:
                self.symbol_table[node.name] = "variable"

        elif isinstance(node, BinaryOp):
            self.generate(node.left)
            self.generate(node.right)

        elif isinstance(node, Print):
            self.generate(node.expression)

        elif isinstance(node, FunctionCall):
            self.symbol_table[node.name] = "function"
            for arg in node.args:
                self.generate(arg)

        elif isinstance(node, If):
            self.generate(node.condition)

            for stmt in node.body:
                self.generate(stmt)

            for cond, body in node.elif_clauses:
                self.generate(cond)
                for stmt in body:
                    self.generate(stmt)

            for stmt in node.else_body:
                self.generate(stmt)

        elif isinstance(node, While):
            self.generate(node.condition)
            for stmt in node.body:
                self.generate(stmt)

        return self.symbol_table
def print_symbol_table(table):

    print("\nSYMBOL TABLE\n")
    print(f"{'NAME':<15} TYPE")
    print("-" * 25)

    for name, typ in table.items():
        print(f"{name:<15} {typ}")