import sys
import os
import io
from contextlib import redirect_stdout

# ── Add src/ to path so all original modules are imported unchanged ──
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from lexer import Lexer, LexerError, TokenType
from parser import Parser, print_ast
from semantic import SemanticAnalyzer, SemanticError
from transformer import Transformer
from codegen import CodeGenerator, CodeGenError
from symbol_table import SymbolTableGenerator, print_symbol_table
from transpiler import print_tokens

app = Flask(__name__)
CORS(app)

# ── Serve index2.html from web/ folder ──
@app.route('/')
def index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web'), 'index2.html')

@app.route('/transpile', methods=['POST'])
def transpile():
    data = request.get_json()
    source_code = data.get('source', '')

    result = {
        'tokens': None,
        'ast': None,
        'symbol_table': None,
        'semantic': None,
        'optimized_ast': None,
        'js_code': None,
        'errors': {}
    }

    # ── STAGE 1: Lexical Analysis ──
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_tokens(tokens)
        result['tokens'] = buf.getvalue()
    except LexerError as e:
        msg = f"Line {e.line}, Col {e.column}: {e.message}"
        if e.suggestion:
            msg += f"\nSuggestion: {e.suggestion}"
        result['errors']['tokens'] = msg
        return jsonify(result)
    except Exception as e:
        result['errors']['tokens'] = str(e)
        return jsonify(result)

    # ── STAGE 2: Syntax Analysis (AST) ──
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_ast(ast)
        result['ast'] = buf.getvalue()
    except Exception as e:
        result['errors']['ast'] = str(e)
        return jsonify(result)

    # ── STAGE 3: Symbol Table Generation ──
    try:
        generator = SymbolTableGenerator()
        table = generator.generate(ast)
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_symbol_table(table)
        result['symbol_table'] = buf.getvalue()
    except Exception as e:
        result['errors']['symbol_table'] = str(e)

    # ── STAGE 4: Semantic Analysis ──
    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        result['semantic'] = "✔ No semantic errors found"
    except SemanticError as e:
        result['errors']['semantic'] = str(e)
    except Exception as e:
        result['errors']['semantic'] = str(e)

    # ── STAGE 5: AST Optimization ──
    optimized_ast = ast  # fallback if transformer fails
    try:
        transformer = Transformer()
        optimized_ast = transformer.transform(ast)
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_ast(optimized_ast)
        result['optimized_ast'] = buf.getvalue()
    except Exception as e:
        result['errors']['opt'] = str(e)

    # ── STAGE 6: Code Generation (JavaScript) ──
    try:
        codegen = CodeGenerator()
        result['js_code'] = codegen.generate(optimized_ast)
    except CodeGenError as e:
        result['errors']['js'] = str(e)
    except Exception as e:
        result['errors']['js'] = str(e)

    return jsonify(result)

if __name__ == '__main__':
    print("Starting server at http://localhost:5000")
    app.run(debug=False, port=5000, use_reloader=False)