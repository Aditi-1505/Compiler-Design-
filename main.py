from lexer import Lexer, LexerError, TokenType
from parser import Parser, print_ast
from semantic import SemanticAnalyzer, SemanticError
from transformer import Transformer


def print_tokens(tokens):
    print(f"{'TYPE':<20} {'VALUE'}")
    print("-" * 40)
    for token in tokens:
        if token.type not in (TokenType.EOF,):
            print(f"{token.type.name:<20} {str(token.value)!r}")


if __name__ == "__main__":

    print("\nEnter Python code (press Enter twice to finish):\n")

    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    source_code = "\n".join(lines)

    # ── STAGE 1 : LEXER ──────────────────────────────────────────────────────
    print("\n" + "═" * 45)
    print("  STAGE 1 — LEXER  (Token Stream)")
    print("═" * 45 + "\n")
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        print_tokens(tokens)
    except LexerError as e:
        print(f"Lexer Error at line {e.line}, col {e.column}: {e.message}")
        if e.suggestion:
            print(f"  Suggestion: {e.suggestion}")
        exit(1)

    # ── STAGE 2 : PARSER ─────────────────────────────────────────────────────
    print("\n" + "═" * 45)
    print("  STAGE 2 — PARSER  (Abstract Syntax Tree)")
    print("═" * 45 + "\n")
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        print_ast(ast)
    except Exception as e:
        print(f"Parser Error: {e}")
        exit(1)

    # ── STAGE 3 : SEMANTIC ANALYSIS ──────────────────────────────────────────
    print("\n" + "═" * 45)
    print("  STAGE 3 — SEMANTIC ANALYSIS")
    print("═" * 45 + "\n")
    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print("✔  No semantic errors found.")
        print(f"   Variables declared: {sorted(analyzer.symbol_table) or 'none'}")
    except SemanticError as e:
        print(f"Semantic Error: {e}")
        exit(1)

    # ── STAGE 4 : TRANSFORMER ────────────────────────────────────────────────
    print("\n" + "═" * 45)
    print("  STAGE 4 — TRANSFORMER  (Optimised AST)")
    print("═" * 45 + "\n")
    try:
        transformer = Transformer()
        optimised_ast = transformer.transform(ast)
        print_ast(optimised_ast)
    except Exception as e:
        print(f"Transformer Error: {e}")
        exit(1)

    print("\n" + "═" * 45)
    print("  ✔  Pipeline complete.")
    print("═" * 45 + "\n")