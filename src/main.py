from transpiler import run_transpiler
from lexer import LexerError
from semantic import SemanticError
from codegen import CodeGenError

if __name__ == "__main__":
    print("\nEnter Python code (press Enter twice to finish):\n")
    lines=[]
    while True:
        line=input()
        if line=="":
            break
        lines.append(line)
    source_code ="\n".join(lines)
    try:
        run_transpiler(source_code)
    except LexerError as e:
        print(f"\nLexer Error at line{e.line},column{e.column}")
        print(e.message)
        if e.suggestion:
            print("Suggestion:",e.suggestion)
    except SemanticError as e:
        print("Semantic Error:",e)
    except CodeGenError as e:
        print("Code Generation Error:",e)
    except Exception as e:
        print("Unexpected Error:",e)
