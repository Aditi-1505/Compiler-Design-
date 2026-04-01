from transpiler import run_transpiler
from executor import run_executor
from lexer import LexerError, Lexer
from semantic import SemanticError, SemanticAnalyzer
from codegen import CodeGenError
from parser import Parser
from transformer import Transformer

def launch_visualizer(source_code):
    try:
        import tkinter as tk
        from visualize import ASTVisualizerApp, draw_tree
    except ImportError as e:
        print(f"\n[Visualizer] Could not import required module: {e}")
        return
    tokens = Lexer(source_code).tokenize()
    ast    = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)
    tokens2   = Lexer(source_code).tokenize()
    ast2      = Parser(tokens2).parse()
    opt_ast   = Transformer().transform(ast2)
    app = ASTVisualizerApp()
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", source_code)
    draw_tree(app.canvas, opt_ast)
    app.mainloop()
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
        run_transpiler(source_code)
        run_executor(source_code)
    except LexerError as e:
        print(f"\nLexer Error at line {e.line}, column {e.column}")
        print(e.message)
        if e.suggestion:
            print("Suggestion:", e.suggestion)
    except SemanticError as e:
        print("Semantic Error:", e)
    except CodeGenError as e:
        print("Code Generation Error:", e)
    except Exception as e:
        print("Unexpected Error:", e)
    finally:
        launch_visualizer(source_code)
