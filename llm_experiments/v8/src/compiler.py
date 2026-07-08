import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lexer import Lexer
from parser import Parser
from codegen import CodeGen

def compile_file(fname, out=None):
    print("Compiling:", fname)
    with open(fname, "r", encoding="utf-8") as f:
        src = f.read()
    print("  [1/4] Lexing...")
    toks = Lexer(src).tok()
    print("    %d tokens" % len(toks))
    print("  [2/4] Parsing...")
    try:
        ast = Parser(toks).parse()
        print("    %d subprograms" % len(ast.subprograms))
    except SyntaxError as e:
        print("    ERROR:", e)
        return False
    print("  [3/4] Code generation...")
    insts = CodeGen().gen(ast)
    print("    %d RISC-V insns" % len(insts))
    if not out:
        out = fname.replace(".cnbe", ".s")
    print("  [4/4] Saving...")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(insts))
    print("    ->", out)
    return True

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="CNBE Chinese Compiler")
    ap.add_argument("input", help=".cnbe source")
    ap.add_argument("-o", "--output", help="output .s")
    args = ap.parse_args()
    if not os.path.exists(args.input):
        print("File not found:", args.input)
        sys.exit(1)
    success = compile_file(args.input, args.output)
    sys.exit(0 if success else 1)