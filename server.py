import os, re, secrets, sys
from flask import Flask, request, jsonify, send_from_directory

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, BASE_DIR)

from lexer import Lexer, LexerError
from parser import (
    Parser, Program, Number, String, Identifier,
    BinaryOp, Assignment, Print, If, While, For, FunctionCall,
)
from semantic import SemanticAnalyzer, SemanticError
from transformer import Transformer
from codegen import CodeGenerator, CodeGenError
from symbol_table import SymbolTableGenerator

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

app = Flask(__name__, static_folder=WEB_DIR, static_url_path="")


_PY_TO_JS = {"Number": "NumberNode", "String": "StringNode"}

def _ast_to_dict(node):
    cls = type(node).__name__
    t   = _PY_TO_JS.get(cls, cls)

    if isinstance(node, Program):
        return {"type": t, "statements": [_ast_to_dict(s) for s in node.statements]}

    if isinstance(node, Assignment):
        return {"type": t, "name": node.name, "value": _ast_to_dict(node.value)}

    if isinstance(node, Print):
        return {"type": t, "expression": _ast_to_dict(node.expression)}

    if isinstance(node, BinaryOp):
        return {
            "type": t,
            "left": _ast_to_dict(node.left),
            "op": {"name": node.op.name, "value": node.op.value},
            "right": _ast_to_dict(node.right),
        }

    if isinstance(node, If):
        return {
            "type": t,
            "condition": _ast_to_dict(node.condition),
            "body": [_ast_to_dict(s) for s in node.body],
            "elif_clauses": [
                [_ast_to_dict(c), [_ast_to_dict(s) for s in b]]
                for c, b in node.elif_clauses
            ],
            "else_body": [_ast_to_dict(s) for s in (node.else_body or [])],
        }

    if isinstance(node, While):
        return {
            "type": t,
            "condition": _ast_to_dict(node.condition),
            "body": [_ast_to_dict(s) for s in node.body]
        }

    if isinstance(node, For):
        return {
            "type": t,
            "var": node.var,
            "start": _ast_to_dict(node.start),
            "stop": _ast_to_dict(node.stop),
            "step": _ast_to_dict(node.step) if node.step else None,
            "body": [_ast_to_dict(s) for s in node.body],
        }

    if isinstance(node, FunctionCall):
        return {
            "type": t,
            "name": node.name,
            "args": [_ast_to_dict(a) for a in node.args]
        }

    if isinstance(node, (Number, String)):
        return {"type": t, "value": node.value}

    if isinstance(node, Identifier):
        return {"type": t, "name": node.name}

    return {"type": cls}

def _token_to_dict(tok):
    return {
        "type": tok.type.name,
        "value": tok.value,
        "line": tok.line,
        "column": tok.column
    }

_UNSUPPORTED = {
    r"\bdef\b":    "function definition",
    r"\breturn\b": "return statement",
    r"\bimport\b": "import statement",
    r"\bclass\b":  "class definition",
    r"\blambda\b": "lambda expression",
    r"\btry\b":    "try/except block",
    r"\bexcept\b": "try/except block",
}

def _check_unsupported(src):
    found = []
    for pat, name in _UNSUPPORTED.items():
        if re.search(pat, src) and name not in found:
            found.append(name)
    return found


# Serve frontend
@app.route("/")
def index():
    return send_from_directory(WEB_DIR, "app.html")


@app.route("/transpiler.js")
def transpiler_js():
    return send_from_directory(WEB_DIR, "transpiler.js")


@app.route("/api/transpile", methods=["POST"])
def transpile():
    data   = request.get_json(force=True, silent=True) or {}
    source = data.get("source", "")
    if not source.strip():
        return jsonify({"error": "No source code provided"}), 400
    result = {
        "tokens": None,
        "ast": None,
        "symbolTable": None,
        "optimizedAst": None,
        "jsCode": None,
        "error": None,
        "unsupported": _check_unsupported(source),
    }

    # 1. Lexer
    try:
        tokens = Lexer(source).tokenize()
        result["tokens"] = [_token_to_dict(t) for t in tokens]
    except LexerError as e:
        result["error"] = {
            "stage": "Lexer",
            "message": e.message,
            "line": e.line,
            "col": e.column,
        }
        return jsonify(result)

    # 2. Parser
    try:
        ast = Parser(tokens).parse()
        result["ast"] = _ast_to_dict(ast)
    except Exception as e:
        result["error"] = {"stage": "Parser", "message": str(e)}
        return jsonify(result)

    # 3. Symbol Table
    try:
        result["symbolTable"] = SymbolTableGenerator().generate(ast)
    except:
        pass

    # 4. Semantic
    try:
        SemanticAnalyzer().analyze(ast)
    except SemanticError as e:
        result["error"] = {"stage": "Semantic", "message": str(e)}
        return jsonify(result)

    # 5. Optimizer
    try:
        opt_ast = Transformer().transform(ast)
        result["optimizedAst"] = _ast_to_dict(opt_ast)
    except Exception as e:
        result["error"] = {"stage": "Transformer", "message": str(e)}
        return jsonify(result)

    # 6. Codegen
    try:
        result["jsCode"] = CodeGenerator().generate(opt_ast)
    except CodeGenError as e:
        result["error"] = {"stage": "CodeGen", "message": str(e)}
        return jsonify(result)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
