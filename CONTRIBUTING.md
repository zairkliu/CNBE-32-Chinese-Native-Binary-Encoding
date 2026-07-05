# 贡献指南 / Contribution Guide

感谢你对 CNBE-32 项目的兴趣！我们欢迎任何形式的贡献，包括但不限于：

Thank you for your interest in the CNBE-32 project! We welcome all forms of contribution, including:

- 报告 Bug 或提出改进建议（Issues）/ Report bugs or suggest improvements
- 提交代码修复或新功能（Pull Requests）/ Submit code fixes or new features
- 完善文档或翻译 / Improve documentation or translations
- 复现实验并报告结果 / Reproduce experiments and report results

在开始贡献之前，请阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。
Before contributing, please read our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 1. 报告问题 / Reporting Issues

- 检查已有的 Issues，避免重复报告 / Check existing Issues first
- 使用清晰的标题描述问题 / Use a clear, descriptive title
- 提供重现步骤、预期结果和实际结果 / Include reproduction steps
- 如果是编码数据问题，请提供受影响的字符 / Include affected characters for encoding issues
- 如果是运行环境问题，请说明操作系统和工具链版本 / Specify OS and toolchain versions

## 2. 提交代码 / Submitting Code (Pull Requests)

我们采用标准 GitHub Flow 工作流：
We follow the standard GitHub Flow workflow:

1. **Fork** 本仓库到你的账户下 / Fork this repository
2. **Clone** 你的 Fork 到本地 / Clone your fork locally
3. 创建新分支用于你的修改 / Create a new branch for your changes
4. 进行修改并提交 / Make changes and commit
5. 确保代码符合项目的代码风格 / Ensure code style compliance
6. Push 到你的 Fork / Push to your fork
7. 创建 Pull Request / Create a Pull Request

### 提交信息格式 / Commit Message Format

```
<type>: <subject>

<body>
```

**Type**: `fix`, `feat`, `docs`, `test`, `refactor`, `chore`
**Subject**: 简短描述（中英文均可）/ Brief description in Chinese or English
**Body**（可选）: 更详细的说明 / More detailed explanation

### PR 评审要求 / PR Review Requirements

- 所有 PR 至少需要一名维护者 Review / At least one maintainer review required
- 涉及核心编码逻辑的变更必须提供测试用例 / Core logic changes need test cases
- 涉及新增数据需注明来源 / New data contributions need source attribution

## 3. 代码风格 / Code Style

### Python (LLM 实验 / LLM Experiments)

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 风格
- 使用 4 个空格缩进 / 4-space indentation
- 行长度限制 120 字符 / Line length: 120 characters
- 函数和类包含 docstring（Google 风格）/ Google-style docstrings

### C / Assembly (RISC-V / OS)

- 使用 K&R 缩进风格 / K&R indentation style
- 使用 4 个空格缩进 / 4-space indentation
- 函数名使用 `snake_case` / Function names: snake_case
- 头文件使用 include guard / Header files: include guards
- 汇编代码添加注释说明每行功能 / Assembly: comment each instruction

## 4. 实验复现 / Reproducing Experiments

CNBE-32 项目包含大量可复现实验。如果你想复现或改进实验：

- **LLM 实验** (v1-v6): 在 `skill/scripts/` 目录使用 `experiment.py`
- **中文编译器** (v8.0-v8.2): 在 `v8_chinese_programming/` 目录
- **RISC-V 硬件** (v7): 需要 WSL Ubuntu 26.04 + riscv64-linux-gnu-gcc
- **中文操作系统** (v8.3): 需要 qemu-system-riscv64

```bash
# 复现 LLM 实验
cd skill/scripts
python experiment.py v2 --model qwen3.5:0.8b

# 复现编译器测试
cd v8_chinese_programming
bash scripts/run_qemu.sh
```

## 5. 文档贡献 / Documentation

- 文档使用 Markdown 编写 / Documentation uses Markdown
- 如果添加新章节，请在 README.md 更新目录索引 / Update README.md when adding sections
- 我们鼓励中英双语 / Bilingual (Chinese + English) encouraged
- 中文为正式语言，英文供国际参考 / Chinese primary, English for reference

## 6. 数据贡献 / Data Contributions

- 本项目依赖 Unicode 标准 / This project follows the Unicode standard
- 所有编码规则基于官方 CNBE-32 规范 / All encoding follows CNBE-32 specification
- 调整部首映射或结构类型需附上来源引用 / Provide source citations for mapping changes
- 生成编码表后需验证无重复和越界 / Validate no collisions after table changes

## 7. 法律与许可 / License

所有贡献将被视为在 **木兰宽松许可证 v2** (Mulan PSL v2) 下发布。
提交 PR 即表示您同意将您的贡献在相同的许可证下发布。

All contributions are considered to be released under the **Mulan Permissive Software License v2** (Mulan PSL v2).
By submitting a Pull Request, you agree to have your contributions licensed under the same license.

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)

## 8. 联系方式 / Contact

- 通过 GitHub Issues 提交问题和建议 / Open GitHub Issues for questions and suggestions
- 通过 Pull Requests 提交代码 / Submit code via Pull Requests
- 如有任何疑问，请创建 Issue 联系维护者 / Create an Issue to contact maintainers

再次感谢你的贡献！Thank you for your contribution!