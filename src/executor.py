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


UNSUPPORTED_FEATURES = {
    r'\bdef\b': "function definition",
    r'\breturn\b': "return statement",
    r'\bimport\b': "import statement",
    r'\bclass\b': "class definition",
    r'\blambda\b': "lambda expression",
    r'\btry\b': "try/except block",
    r'\bexcept\b': "try/except block",
}


def check_unsupported(source_code):
    found = []
    for pattern, name in UNSUPPORTED_FEATURES.items():
        if re.search(pattern, source_code) and name not in found:
            found.append(name)
    return found


def get_js_code(source_code):
    tokens = Lexer(source_code).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)
    optimized_ast = Transformer().transform(ast)
    return CodeGenerator().generate(optimized_ast)


def extract_input_prompts(source_code):
    """
    Extract prompt messages from input() calls in order.
    Supports:
      input("Enter your name")
      input('Enter limit: ')
      input()   -> falls back to "Input N"
    """
    prompts = []
    # Match input(...) capturing everything inside the parens
    for match in re.finditer(r'\binput\s*\(([^)]*)\)', source_code):
        inner = match.group(1).strip()
        # Try to extract a string literal (single or double quoted)
        str_match = re.match(r'^["\'](.+?)["\']$', inner)
        if str_match:
            prompts.append(str_match.group(1).rstrip(": ").strip())
        else:
            prompts.append(None)   # No prompt string, will use fallback
    return prompts


def collect_user_inputs(source_code):
    prompts = extract_input_prompts(source_code)
    if not prompts:
        return []

    print(f"\n[ This program requires {len(prompts)} input value(s) ]")
    print("-" * 30)

    values = []
    for i, prompt in enumerate(prompts, 1):
        label = prompt if prompt else f"Input {i}"
        val = input(f"  {label}: ")
        values.append(val)

    return values


def run_python(source_code, user_inputs):
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

    unsupported = check_unsupported(source_code)
    if unsupported:
        print("\n[ UNSUPPORTED FEATURE DETECTED ]")
        print("-" * 30)
        for feature in unsupported:
            print(f"  \u2718  '{feature}' is not supported by this transpiler.")
        print("\n  Cannot execute — please rewrite using supported constructs:")
        print("  \u2714  for loops, while loops, if/elif/else, assignments, print, built-in functions")
        print("=" * 50)
        return

    user_inputs = collect_user_inputs(source_code)

    try:
        js_code = get_js_code(source_code)
    except (LexerError, SemanticError, CodeGenError) as e:
        print(f"\nTranspiler Error: {e}")
        return
    except Exception as e:
        print(f"\nUnexpected Transpiler Error: {e}")
        return

    print("\n[ PYTHON OUTPUT ]")
    print("-" * 30)
    py_output = run_python(source_code, user_inputs)
    print(py_output if py_output else "(no output)")

    print("\n[ JAVASCRIPT OUTPUT ]")
    print("-" * 30)
    js_output = run_js(js_code, user_inputs)
    print(js_output if js_output else "(no output)")

    print("\n" + "=" * 50)
    if py_output == js_output:
        print("\u2714  Both outputs MATCH — transpilation is correct!")
    else:
        print("\u2718  Outputs DO NOT match — check transpilation logic.")
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
