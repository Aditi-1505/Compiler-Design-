from lexer import Lexer, LexerError, TokenType
from parser import Parser, print_ast
from semantic import SemanticAnalyzer, SemanticError
from transformer import Transformer
from codegen import CodeGenerator, CodeGenError
from symbol_table import SymbolTableGenerator, print_symbol_table

def print_tokens(tokens):
    print(f"{'TYPE':<20} VALUE")
    print("-" * 40)
    for token in tokens:
        if token.type != TokenType.EOF:
            print(f"{token.type.name:<20} {repr(token.value)}")

def run_transpiler(source_code):
    # STAGE 1 — LEXER
    print("\n" + "═" * 50)
    print("STAGE 1 — LEXICAL ANALYSIS (TOKENS)")
    print("═" * 50)
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    print_tokens(tokens)
    # STAGE 2 — PARSER
    print("\n" + "═" * 50)
    print("STAGE 2 — SYNTAX ANALYSIS (AST)")
    print("═" * 50)
    parser = Parser(tokens)
    ast = parser.parse()
    print_ast(ast)
    # STAGE 3 — SYMBOL TABLE
    print("\n" + "═" * 50)
    print("STAGE 3 — SYMBOL TABLE GENERATION")
    print("═" * 50)
    generator = SymbolTableGenerator()
    table = generator.generate(ast)
    print_symbol_table(table)
    # STAGE 4 — SEMANTIC ANALYSIS
    print("\n" + "═" * 50)
    print("STAGE 4 — SEMANTIC ANALYSIS")
    print("═" * 50)
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    print("✔ No semantic errors found")
    # STAGE 5 — TRANSFORMER
    print("\n" + "═" * 50)
    print("STAGE 5 — AST OPTIMIZATION")
    print("═" * 50)
    transformer = Transformer()
    optimized_ast = transformer.transform(ast)
    print_ast(optimized_ast)
    # STAGE 6 — CODE GENERATION
    print("\n" + "═" * 50)
    print("STAGE 6 — CODE GENERATION (JavaScript)")
    print("═" * 50)
    codegen = CodeGenerator()
    js_code = codegen.generate(optimized_ast)
    print("\nGenerated JavaScript Code:\n")
    print(js_code)
    print("\n" + "═" * 50)
    print("✔ COMPILATION PIPELINE COMPLETED SUCCESSFULLY")
    print("═" * 50)
