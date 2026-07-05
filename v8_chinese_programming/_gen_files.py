import os

BASE = '/mnt/c/Users/zairk/Documents/Codex/2026-07-02/codex-dangerously-bypass-approvals-and-sandbox/github-upload/v8_chinese_programming'

def w(fname, content):
    path = os.path.join(BASE, fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: ' + fname)

# Language spec
w('docs/language_spec.md', '# CNBE Chinese Programming Language\n\n## Data Types\nint, float, string, char, code\n\n## Functions\nget_code(char) -> cnhe.map\nget_radical(code) -> cnhe.extract f=0\nget_stroke(code) -> cnhe.extract f=1\nget_struct(code) -> cnhe.extract f=2\ncompare(c1,c2) -> cnhe.cmp\n')

# AST
w('src/ast.py', 'from dataclasses import dataclass, field\nfrom typing import List, Optional\n\n@dataclass\nclass Program:\n    name: str; subprograms: list = None\n    def __post_init__(self):\n        if self.subprograms is None: self.subprograms = []\n\n@dataclass\nclass SubProgram:\n    name: str; return_type: str = "int"\n    params: list = None; body: list = None\n    def __post_init__(self):\n        if self.params is None: self.params = []\n        if self.body is None: self.body = []\n\n@dataclass\nclass VarDecl:\n    var_type: str; name: str; init = None\n\n@dataclass\nclass AssignStmt:\n    target: str; value = None\n\n@dataclass\nclass IfStmt:\n    condition = None; then_body: list = None; else_body: list = None\n    def __post_init__(self):\n        if self.then_body is None: self.then_body = []\n        if self.else_body is None: self.else_body = []\n\n@dataclass\nclass ForLoop:\n    count = None; body: list = None\n    def __post_init__(self):\n        if self.body is None: self.body = []\n\n@dataclass\nclass ReturnStmt:\n    value = None\n\n@dataclass\nclass OutputStmt:\n    value = None\n\n@dataclass\nclass IntLiteral:\n    value: int\n\n@dataclass\nclass StringLiteral:\n    value: str\n\n@dataclass\nclass CharLiteral:\n    value: str\n\n@dataclass\nclass Identifier:\n    name: str\n\n@dataclass\nclass BinOp:\n    operator: str; left = None; right = None\n\n@dataclass\nclass FuncCall:\n    name: str; args: list = None\n    def __post_init__(self):\n        if self.args is None: self.args = []\n')

# Runtime header
w('src/runtime/cnbe_runtime.h', '#ifndef CNBE_RUNTIME_H\n#define CNBE_RUNTIME_H\n#include <stdint.h>\nuint32_t cnhe_map(uint32_t unicode);\nuint32_t cnhe_extract(uint32_t code, uint32_t field);\nuint32_t cnhe_cmp(uint32_t a, uint32_t b);\nint cnhe_compare_chars(uint32_t a, uint32_t b);\n#endif\n')

# Runtime C
w('src/runtime/cnbe_runtime.c', '#include <stdint.h>\n#include "cnbe_runtime.h"\nstatic uint32_t skill_table[20902] = {0};\nuint32_t cnhe_map(uint32_t u) { return (u>=0x4E00&&u<=0x9FA5)?skill_table[u-0x4E00]:0; }\nuint32_t cnhe_extract(uint32_t c, uint32_t f) { switch(f) { case 0: return (c>>24)&0xFF; case 1: return (c>>19)&0x1F; case 2: return (c>>15)&0xF; default: return 0; } }\nuint32_t cnhe_cmp(uint32_t a, uint32_t b) { uint32_t ra=(a>>24)&0xFF,rb=(b>>24)&0xFF,sa=(a>>19)&0x1F,sb=(b>>19)&0x1F,ta=(a>>15)&0xF,tb=(b>>15)&0xF; return (ra>rb?(ra-rb)*8:(rb-ra)*8)+(sa>sb?(sa-sb)*5:(sb-sa)*5)+(ta>tb?(ta-tb)*4:(tb-ta)*4); }\nint cnhe_compare_chars(uint32_t a, uint32_t b) { uint32_t ca=cnhe_map(a),cb=cnhe_map(b); if(!ca||!cb)return -1; return (int)cnhe_cmp(ca,cb); }\n')

# Tests
w('tests/test_struct.cnbe', '.version 2\n.program CNBETest\n.sub struct_compare, int\n    char c1 = "\\u68ee"\n    char c2 = "\\u6797"\n    code k1 = get_code(c1)\n    code k2 = get_code(c2)\n    int r1 = get_radical(k1)\n    int r2 = get_radical(k2)\n    if (r1 == r2)\n        output("same radical")\n    else\n        output("different radical")\n    endif\nreturn (0)\n')

w('tests/test_cluster.cnbe', '.version 2\n.program CNBETest\n.sub cluster_test, int\n    code k1 = get_code("\\u6c5f")\n    code k2 = get_code("\\u6cb3")\n    code k3 = get_code("\\u6e56")\n    code k4 = get_code("\\u6d77")\n    int d = compare(k1, k2)\n    output(d)\nreturn (0)\n')

w('tests/test_loop.cnbe', '.version 2\n.program CNBETest\n.sub loop_sum, int\n    int sum = 0\n    int i = 0\n    for (10)\n        sum = sum + i\n        i = i + 1\n    endloop\n    output(sum)\nreturn (0)\n')

print("All base files written. Total: 8 files")