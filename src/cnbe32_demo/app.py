"""Tkinter desktop application for demonstrating CNBE-32 on Windows."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from cnbe32 import count, resolve_db_path

from .presenter import CharacterEncoding, encode_text_for_demo

APP_TITLE = "CNBE-32 中文原生二进制编码展示程序"

PROJECT_OVERVIEW = """CNBE-32 是面向 CJK 汉字的 32 位结构指纹研究原型。

本展示程序用于软件著作权申请、项目路演和内部评审演示，重点展示：
1. 输入汉字到 CNBE-32 输出的完整路径；
2. Unicode 身份、部首、笔画、结构、索引和扩展位的字段拆解；
3. 8105 通用规范汉字表优先的标准对齐路线；
4. 运行时数据库、Python SDK、C/硬件示例、报告和审计材料的项目组成。

定位说明：CNBE-32 不替代 Unicode。它以 Unicode 承担字符身份，以 CNBE-32 承载结构化运行时特征。"""

WORKFLOW = """演示操作流程

1. 输入待演示文本，例如：中国软件著作权 CNBE-32。
2. 点击“执行编码演示”。
3. 程序逐字查询运行时数据库。
4. 对已编码字符输出 CNBE-32 整数、十六进制、32 位二进制和字段拆解。
5. 对未收录或待编码字符保留状态说明，避免把未审定数据误展示为正式结果。
6. 可通过“清空”和“复制结果”完成现场演示。

编码字段

31..24  部首/根编号 Radix，8 bits
23..19  笔画数 Stroke，5 bits
18..15  汉字结构 Struct，4 bits
14..4   字形索引 Glyph Index，11 bits
3..0    扩展位 Ext，4 bits"""

ROADMAP = """项目规划展示

第一阶段：运行时稳定演示
- Python SDK、SQLite 运行时数据库、桌面展示程序。
- 支持单字和短文本编码输出。
- 保持 Unicode 优先、证据优先和审计状态展示。

第二阶段：标准对齐深化
- 以 8105 通用规范汉字表为核心。
- 分离 national_standard、standard_derived、agent_standard。
- 持续补充结构、部首、笔顺、拆解证据。

第三阶段：多端集成
- C 接口、RISC-V/硬件友好查表、Web/API 演示。
- CNBE64/CNBE128 保存更完整证据归档。
- 为 AI 特征、OCR 辅助、汉字结构分析提供可复现输入。

第四阶段：软著与产品化材料
- 固定软件名称、版本号、功能说明、操作手册、界面截图。
- 形成源代码清单、说明书、测试记录和演示视频素材。"""

COPYRIGHT_NOTES = """软著申请材料建议

软件名称：CNBE-32 中文原生二进制编码展示程序
建议版本：V1.0
运行环境：Windows 11 64 位
开发语言：Python 3 / Tkinter / SQLite

主要功能：
1. 汉字 CNBE-32 编码查询；
2. 编码字段拆解展示；
3. Unicode 与 CNBE 对照输出；
4. 项目技术路线展示；
5. 标准对齐、审计状态和后续规划展示。

材料清单：
- exe 可执行文件；
- 操作说明书；
- 软件功能说明；
- 源代码前后连续页；
- 界面截图；
- 测试记录；
- 项目 README、治理文档和报告摘要。

注意：申请材料应表述为“中文结构编码研究与展示软件”，避免宣称已获得国家标准认证。"""


class CNBEDemoApp(tk.Tk):
    """Main CNBE-32 demo window."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(960, 640)
        self.configure(bg="#f4f6f8")

        self._result_rows: list[CharacterEncoding] = []
        self._build_style()
        self._build_layout()
        self._run_demo()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6f8")
        style.configure("Header.TFrame", background="#0f172a")
        style.configure("Header.TLabel", background="#0f172a", foreground="#ffffff", font=("Microsoft YaHei UI", 17, "bold"))
        style.configure("Subheader.TLabel", background="#0f172a", foreground="#cbd5e1", font=("Microsoft YaHei UI", 10))
        style.configure("TLabel", background="#f4f6f8", foreground="#111827", font=("Microsoft YaHei UI", 10))
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(12, 7))
        style.configure("Accent.TButton", background="#14532d", foreground="#ffffff")
        style.configure("Treeview", rowheight=30, font=("Microsoft YaHei UI", 10))
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#166534")])

    def _build_layout(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text=APP_TITLE, style="Header.TLabel").pack(anchor="w", padx=22, pady=(16, 2))
        db_text = f"运行时记录：{count():,} 条    数据库：{resolve_db_path()}"
        ttk.Label(header, text=db_text, style="Subheader.TLabel").pack(anchor="w", padx=22, pady=(0, 14))

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=16)

        self._build_encoding_tab()
        self._add_text_tab("项目展示", PROJECT_OVERVIEW)
        self._add_text_tab("操作流程", WORKFLOW)
        self._add_text_tab("实施规划", ROADMAP)
        self._add_text_tab("软著材料", COPYRIGHT_NOTES)

    def _build_encoding_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="编码演示")

        input_frame = ttk.Frame(tab)
        input_frame.pack(fill="x", padx=14, pady=14)
        ttk.Label(input_frame, text="输入文本").pack(anchor="w")
        self.input_text = tk.Text(input_frame, height=4, wrap="word", font=("Microsoft YaHei UI", 13), undo=True)
        self.input_text.pack(fill="x", pady=(6, 10))
        self.input_text.insert("1.0", "中国软件著作权 CNBE-32")

        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="执行编码演示", style="Accent.TButton", command=self._run_demo).pack(side="left")
        ttk.Button(button_frame, text="清空", command=self._clear).pack(side="left", padx=8)
        ttk.Button(button_frame, text="复制结果", command=self._copy_result).pack(side="left")

        columns = ("char", "unicode", "cnbe_hex", "cnbe_binary", "radix", "strokes", "struct", "index", "track", "status")
        self.tree = ttk.Treeview(tab, columns=columns, show="headings")
        headings = {
            "char": "字符",
            "unicode": "Unicode",
            "cnbe_hex": "CNBE-32",
            "cnbe_binary": "32 位二进制",
            "radix": "部首/根",
            "strokes": "笔画",
            "struct": "结构",
            "index": "索引",
            "track": "轨道",
            "status": "状态",
        }
        widths = {
            "char": 58,
            "unicode": 90,
            "cnbe_hex": 110,
            "cnbe_binary": 250,
            "radix": 95,
            "strokes": 70,
            "struct": 90,
            "index": 70,
            "track": 90,
            "status": 190,
        }
        for key in columns:
            self.tree.heading(key, text=headings[key])
            self.tree.column(key, width=widths[key], minwidth=widths[key], stretch=key in {"cnbe_binary", "status"})
        self.tree.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        detail_frame = ttk.Frame(tab)
        detail_frame.pack(fill="x", padx=14, pady=(0, 14))
        ttk.Label(detail_frame, text="输出详情").pack(anchor="w")
        self.detail = tk.Text(detail_frame, height=8, wrap="word", font=("Consolas", 10), bg="#ffffff")
        self.detail.pack(fill="x", pady=(6, 0))

    def _add_text_tab(self, title: str, body: str) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text=title)
        text = tk.Text(tab, wrap="word", font=("Microsoft YaHei UI", 12), bg="#ffffff", padx=18, pady=18)
        text.pack(fill="both", expand=True, padx=14, pady=14)
        text.insert("1.0", body)
        text.configure(state="disabled")

    def _run_demo(self) -> None:
        text = self.input_text.get("1.0", "end").strip()
        self._result_rows = encode_text_for_demo(text)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self._result_rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.char,
                    row.unicode_hex,
                    row.cnbe_hex or "-",
                    row.cnbe_binary or "-",
                    _join_code_name(row.radix, row.radix_name),
                    row.strokes if row.strokes is not None else "-",
                    _join_code_name(row.struct_type, row.struct_name),
                    row.index if row.index is not None else "-",
                    row.track or "-",
                    row.display_status,
                ),
            )
        self._render_detail()

    def _render_detail(self) -> None:
        lines: list[str] = []
        for row in self._result_rows:
            lines.append(f"{row.char} {row.unicode_hex}")
            lines.append(f"  CNBE-32: {row.cnbe_hex or '-'} / {row.cnbe_decimal if row.cnbe_decimal is not None else '-'}")
            lines.append(f"  Binary : {row.cnbe_binary or '-'}")
            lines.append(
                "  Fields : "
                f"radix={_join_code_name(row.radix, row.radix_name)}, "
                f"stroke={row.strokes if row.strokes is not None else '-'}, "
                f"struct={_join_code_name(row.struct_type, row.struct_name)}, "
                f"index={row.index if row.index is not None else '-'}, "
                f"ext={row.ext if row.ext is not None else '-'}"
            )
            lines.append(f"  Status : {row.display_status}")
            lines.append("")
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", "\n".join(lines) if lines else "请输入汉字后执行编码演示。")
        self.detail.configure(state="disabled")

    def _clear(self) -> None:
        self.input_text.delete("1.0", "end")
        self._result_rows = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._render_detail()

    def _copy_result(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.detail.get("1.0", "end").strip())


def _join_code_name(code: int | None, name: str | None) -> str:
    if code is None and not name:
        return "-"
    if code is None:
        return str(name)
    if not name:
        return str(code)
    return f"{code}/{name}"


def main() -> None:
    app = CNBEDemoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
