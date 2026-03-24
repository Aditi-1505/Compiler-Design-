from parser import (
    Program, Number, String, Identifier, BinaryOp,
    Assignment, Print, If, While, For, FunctionCall,
)

_BUILTIN_MAP = {
    "length": None,
    "print": None,
    "int": "Math.trunc",
    "float": "parseFloat",
    "word": "String",
    "abs": "Math.abs",
    "largest": "Math.max",
    "least": "Math.min",
    "round": "Math.round",
    "pow": "Math.pow",
    "sqrt": "Math.sqrt",
    "input": "prompt",
    "type": "typeof",
}

_OP_MAP = {
    "PLUS": "+",
    "MINUS": "-",
    "MULTIPLY": "*",
    "DIVIDE": "/",
    "MODULO": "%",
    "FLOOR_DIVIDE": None,
    "DOUBLE_EQUALS": "===",
    "NOT_EQUALS": "!==",
    "LESS_THAN": "<",
    "GREATER_THAN": ">",
    "LESS_EQUAL": "<=",
    "GREATER_EQUAL": ">=",
    "AND": "&&",
    "OR": "||",
}

class CodeGenError(Exception):
    pass
def _collect_assigned(sta):
    names = set()
    for node in sta:
        if isinstance(node, Assignment):
            names.add(node.name)
        if isinstance(node, If):
            names |= _collect_assigned(node.body)
            for _, body in node.elif_clauses:
                names |= _collect_assigned(body)
            if node.else_body:
                names |= _collect_assigned(node.else_body)
        if isinstance(node, While):
            names |= _collect_assigned(node.body)
    return names

class CodeGenerator:
    def __init__(self, indent_size=2):
        self._indent_size = indent_size
        self._level = 0
        self._declared = set()
    def generate(self, node):
        if not isinstance(node, Program):
            raise CodeGenError(f"Expected Program, got {type(node).__name__}")
        lines = []
        for stmt in node.statements:
            lines.extend(self.gen_stmt(stmt))
        return "\n".join(lines)
    @property
    def pad(self):
        return " " * (self._indent_size * self._level)
    def indent(self):
        self._level += 1
    def dedent(self):
        self._level -= 1
    def gen_stmt(self, node):
        if isinstance(node, Assignment):
            return self.gen_assignment(node)
        if isinstance(node, Print):
            return [f"{self.pad}console.log({self.gen_expr(node.expression)});"]
        if isinstance(node, If):
            return self.gen_if(node)
        if isinstance(node, While):
            return self.gen_while(node)
        if isinstance(node, For):
            return self.gen_for(node)
        if isinstance(node, FunctionCall):
            return [f"{self.pad}{self.gen_expr(node)};"]
        if isinstance(node, BinaryOp):
            return [f"{self.pad}{self.gen_expr(node)};"]
        raise CodeGenError(f"Unknown statement node: {type(node).__name__}")
    def gen_assignment(self, node):
        value = self.gen_expr(node.value)
        if node.name not in self._declared:
            self._declared.add(node.name)
            return [f"{self.pad}let {node.name} = {value};"]
        return [f"{self.pad}{node.name} = {value};"]
    def gen_if(self, node):
        lines = []
        cond = self.gen_expr(node.condition)
        lines.append(f"{self.pad}if ({cond}) {{")
        lines.extend(self.gen_block(node.body))
        for elif_cond, elif_body in node.elif_clauses:
            ec = self.gen_expr(elif_cond)
            lines.append(f"{self.pad}}} else if ({ec}) {{")
            lines.extend(self.gen_block(elif_body))
        if node.else_body:
            lines.append(f"{self.pad}}} else {{")
            lines.extend(self.gen_block(node.else_body))
        lines.append(f"{self.pad}}}")
        return lines
    def gen_while(self, node):
        cond = self.gen_expr(node.condition)
        lines = [f"{self.pad}while ({cond}) {{"]
        lines.extend(self.gen_block(node.body))
        lines.append(f"{self.pad}}}")
        return lines

    def gen_for(self, node):
        var   = node.var
        start = self.gen_expr(node.start)
        stop  = self.gen_expr(node.stop)
        step  = self.gen_expr(node.step) if node.step else None

        # Declare the loop variable if not yet declared
        decl = "let " if var not in self._declared else ""
        self._declared.add(var)

        if step is None:
            header = f"for ({decl}{var} = {start}; {var} < {stop}; {var}++)"
        else:
            header = f"for ({decl}{var} = {start}; {var} < {stop}; {var} += {step})"

        lines = [f"{self.pad}{header} {{"]
        lines.extend(self.gen_block(node.body))
        lines.append(f"{self.pad}}}")
        return lines
    def gen_block(self, stmts):
        self.indent()
        lines = []
        for stmt in stmts:
            lines.extend(self.gen_stmt(stmt))
        self.dedent()
        return lines
    def gen_expr(self, node):
        if isinstance(node, Number):
            return self.gen_number(node)
        if isinstance(node, String):
            return self.gen_string(node)
        if isinstance(node, Identifier):
            return node.name
        if isinstance(node, BinaryOp):
            return self.gen_binary(node)
        if isinstance(node, FunctionCall):
            return self.gen_call(node)
        raise CodeGenError(f"Unknown expression node: {type(node).__name__}")
    def gen_number(self, node):
        v = node.value
        try:
            f = float(v)
            if f == int(f) and "e" not in v.lower():
                return str(int(f))
        except ValueError:
            pass
        return v
    def gen_string(self, node):
        escaped = node.value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    def gen_binary(self, node):
        left = self.gen_expr(node.left)
        right = self.gen_expr(node.right)
        if node.op.name == "FLOOR_DIVIDE":
            return f"Math.floor({left} / {right})"
        js_op = _OP_MAP.get(node.op.name)
        if js_op is None:
            raise CodeGenError(f"Unsupported operator: {node.op.name}")
        if isinstance(node.left, BinaryOp):
            left = f"({left})"
        if isinstance(node.right, BinaryOp):
            right = f"({right})"
        return f"{left} {js_op} {right}"
    def gen_call(self, node):
        name = node.name
        args = [self.gen_expr(a) for a in node.args]
        if name == "length" and len(args) == 1:
            return f"{args[0]}.length"
        if name == "print":
            return f"console.log({', '.join(args)})"
        js_name = _BUILTIN_MAP.get(name, name)
        if js_name is None:
            raise CodeGenError(
                f"Built-in '{name}' cannot be translated to JavaScript by this transpiler"
            )
        return f"{js_name}({', '.join(args)})"
