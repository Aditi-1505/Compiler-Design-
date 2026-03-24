import re
import sys
import subprocess
import tempfile
import os

from lexer import Lexer, LexerError
from parser import Parser
from semantic import SemanticAnalyzer, SemanticError
from transformer import Transformer
from codegen import CodeGenerator, CodeGenError


# ── Unsupported feature patterns ────────────────────────
UNSUPPORTED_FEATURES = {

    r'\bdef\b':    "function definition",
    r'\breturn\b': "return statement",
    r'\bimport\b': "import statement",
    r'\bclass\b':  "class definition",
    r'\blambda\b': "lambda expression",
    r'\btry\b':    "try/except block",
    r'\bexcept\b': "try/except block",
}


def check_unsupported(source_code):
    """Return a list of unsupported feature names found in the source."""
    found = []
    for pattern, name in UNSUPPORTED_FEATURES.items():
        if re.search(pattern, source_code) and name not in found:
            found.append(name)
    return found


def get_js_code(source_code):
    """Run the transpiler pipeline and return the generated JS code."""
    tokens = Lexer(source_code).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)
    optimized_ast = Transformer().transform(ast)
    return CodeGenerator().generate(optimized_ast)


def count_inputs(source_code):
    """Count how many input() calls exist in the source."""
    return len(re.findall(r'\binput\s*\(', source_code))


def collect_user_inputs(source_code):
    """
    If the code uses input(), ask the user to provide values upfront.
    Returns a list of strings (one per input() call).
    """
    n = count_inputs(source_code)
    if n == 0:
        return []

    print(f"\n[ This program requires {n} input value(s) ]")
    print("-" * 30)
    values = []
    for i in range(1, n + 1):
        val = input(f"  Input {i}: ")
        values.append(val)
    return values


def run_python(source_code, user_inputs):
    """Run Python source as a subprocess, feeding user_inputs via stdin."""
    stdin_data = "\n".join(user_inputs) + ("\n" if user_inputs else "")
    try:
        result = subprocess.run(
            [sys.executable, "-c", source_code],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            err = result.stderr.strip().splitlines()
            return f"[Runtime Error] {err[-1]}"
        return result.stdout.rstrip("\n")
    except subprocess.TimeoutExpired:
        return "[Error] Python execution timed out."


def run_js(js_code, user_inputs):
    """
    Run generated JS in Node.js.
    Injects a prompt() shim so Node doesn't crash on input() calls.
    """
    inputs_js = "[" + ", ".join(f'"{v}"' for v in user_inputs) + "]"
    shim = (
        f"const _inputs = {inputs_js};\n"
        f"let _inputIndex = 0;\n"
        f"function prompt(msg) {{\n"
        f"  if (msg) process.stdout.write(msg);\n"
        f"  return _inputs[_inputIndex++] || '';\n"
        f"}}\n\n"
    )
    full_js = shim + js_code

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as f:
            f.write(full_js)
            tmp_path = f.name

        result = subprocess.run(
            ["node", tmp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            err = result.stderr.strip().splitlines()
            for line in err:
                if "Error" in line:
                    return f"[JS Runtime Error] {line.strip()}"
            return f"[JS Runtime Error] {err[-1]}"
        return result.stdout.rstrip("\n")

    except FileNotFoundError:
        return "[Error] Node.js is not installed or not found in PATH."
    except subprocess.TimeoutExpired:
        return "[Error] JS execution timed out."
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def run_executor(source_code):
    print("\n" + "=" * 50)
    print("         OUTPUT COMPARISON")
    print("=" * 50)

    # ── Check for unsupported features ──────────────────
    unsupported = check_unsupported(source_code)
    if unsupported:
        print("\n[ UNSUPPORTED FEATURE DETECTED ]")
        print("-" * 30)
        for feature in unsupported:
            print(f"  \u2718  '{feature}' is not supported by this transpiler.")
        print("\n  Cannot execute \u2014 please rewrite using supported constructs:")
        print("  \u2714  for loops, while loops, if/elif/else, assignments, print, built-in functions")
        print("=" * 50)
        return

    # ── Collect inputs once, reuse for both runs ────────
    user_inputs = collect_user_inputs(source_code)

    # ── Transpile ───────────────────────────────────────
    try:
        js_code = get_js_code(source_code)
    except (LexerError, SemanticError, CodeGenError) as e:
        print(f"\nTranspiler Error: {e}")
        return
    except Exception as e:
        print(f"\nUnexpected Transpiler Error: {e}")
        return

    # ── Python output ───────────────────────────────────
    print("\n[ PYTHON OUTPUT ]")
    print("-" * 30)
    py_output = run_python(source_code, user_inputs)
    print(py_output if py_output else "(no output)")

    # ── JavaScript output ───────────────────────────────
    print("\n[ JAVASCRIPT OUTPUT ]")
    print("-" * 30)
    js_output = run_js(js_code, user_inputs)
    print(js_output if js_output else "(no output)")

    # ── Match check ─────────────────────────────────────
    print("\n" + "=" * 50)
    if py_output == js_output:
        print("\u2714  Both outputs MATCH \u2014 transpilation is correct!")
    else:
        print("\u2718  Outputs DO NOT match \u2014 check transpilation logic.")
        print(f"   Python : {repr(py_output)}")
        print(f"   JS     : {repr(js_output)}")
    print("=" * 50)


if __name__ == "__main__":
    print("\nEnter Python code (press Enter twice to finish):\n")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    source_code = "\n".join(lines)

    try:
        run_executor(source_code)
    except LexerError as e:
        print(f"\nLexer Error at line {e.line}, column {e.column}: {e.message}")
        if e.suggestion:
            print("Suggestion:", e.suggestion)
    except SemanticError as e:
        print("Semantic Error:", e)
    except CodeGenError as e:
        print("Code Generation Error:", e)
    except Exception as e:
        print("Unexpected Error:", e)