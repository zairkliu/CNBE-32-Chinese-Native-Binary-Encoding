# CNBE-32 v8.0: Chinese Programming Language Compiler

中文源码 → CNBE语义函数 → RISC-V汇编的完整编译工具链。

## 目录结构

```
v8_chinese_programming/
├── docs/language_spec.md      # 中文编程语言规范
├── src/
│   ├── lexer.py               # 中文词法分析器
│   ├── parser.py               # 中文语法分析器
│   ├── codegen.py              # CNBE指令生成器(RISC-V)
│   ├── compiler.py             # 完整编译器入口
│   └── runtime/
│       ├── cnbe_runtime.h      # CNBE运行时头文件
│       └── cnbe_runtime.c      # 运行时实现
├── tests/
│   ├── test_loop.cnbe          # 循环求和(1+2+...+10=55)
│   ├── test_struct.cnbe        # 汉字结构比较(CNBE语义)
│   └── test_cluster.cnbe       # 汉字聚类距离(CNBE比较)
├── output/                     # 生成的RISC-V汇编
└── README.md
```

## 快速开始

```bash
# 编译测试程序
python src/compiler.py tests/test_loop.cnbe -o output/test_loop.s

# 用RISC-V工具链汇编
riscv64-linux-gnu-gcc -march=rv64im -static output/test_loop.s -o output/test_loop.elf

# 在QEMU上运行
qemu-riscv64 output/test_loop.elf
```

## 语法示例

```
.版本 2
程序集 CNBETest

子程序 loop_sum, 整数
    整数 总和 = 0
    整数 i = 0
    计次循环 (10)
        总和 = 总和 + i
        i = i + 1
    结束循环
    输出(总和)
返回 (0)
```

## CNBE语义函数

| 中文函数 | RISC-V等效 | 说明 |
|----------|:----------:|------|
| 取编码(char) | cnhe.map | Unicode → CNBE编码 |
| 取部首(code) | cnhe.extract f=0 | 提取部首区 |
| 取笔画(code) | cnhe.extract f=1 | 提取笔画数 |
| 取结构(code) | cnhe.extract f=2 | 提取结构类型 |
| 比较(c1,c2) | cnhe.cmp | 加权汉明距离 |

## 验证状态

- ✅ test_loop.cnbe: 完整编译通过(34条RISC-V指令)
- 🔄 test_struct.cnbe: 词法分析通过(82 tokens)
- 🔄 test_cluster.cnbe: 词法分析通过(50 tokens)

## 许可证

木兰宽松许可证 v2 (Mulan PSL v2)
