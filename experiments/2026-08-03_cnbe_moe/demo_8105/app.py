# -*- coding: utf-8 -*-
"""CNBE-32 8105 规范汉字 Win11 桌面 Demo（Tkinter）。"""

from __future__ import annotations

import sqlite3
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from cnbe32 import count, decode_cnbe, lookup, resolve_db_path

APP_TITLE = "CNBE-32 8105 规范汉字演示程序"

ABOUT_TEXT = """CNBE-32 8105 规范汉字演示程序

功能：
1. 输入汉字，逐字查询 CNBE-32 编码与字段拆解；
2. 浏览 8105 通用规范汉字表的标准轨记录；
3. 按汉字 / 部首 / 笔画筛选标准轨字符；
4. 复制查询结果用于报告与展示。

说明：
- CNBE-32 不替代 Unicode，Unicode 承担字符身份，CNBE-32 承载结构特征；
- 本项目为中文原生层级编码的中间层系统，本演示程序仅用于展示项目结构、
  数据流向与运行流程，不包含全部源程序；
- 当前运行时数据库共 %(rows)s 条，标准轨已编码 %(standard)s 条，
  8105 通用规范汉字表为项目对齐基线，不代表国家标准认证。
"""


class Demo8105App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg="#f4f6f8")
        self._rows: list[dict] = []
        self._build_style()
        self._build_layout()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6f8")
        style.configure("Header.TFrame", background="#0f172a")
        style.configure("Header.TLabel", background="#0f172a", foreground="#ffffff", font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("Subheader.TLabel", background="#0f172a", foreground="#cbd5e1", font=("Microsoft YaHei UI", 10))
        style.configure("TLabel", background="#f4f6f8", foreground="#111827", font=("Microsoft YaHei UI", 10))
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(12, 7))
        style.configure("Accent.TButton", background="#14532d", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#166534")])
        style.configure("Treeview", rowheight=28, font=("Microsoft YaHei UI", 10))
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))

    def _build_layout(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text=APP_TITLE, style="Header.TLabel").pack(anchor="w", padx=22, pady=(16, 2))
        db_text = f"运行时记录：{count():,} 条    数据库：{resolve_db_path()}"
        ttk.Label(header, text=db_text, style="Subheader.TLabel").pack(anchor="w", padx=22, pady=(0, 14))

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=16)
        self._build_query_tab()
        self._build_8105_tab()
        self._add_about_tab()

    def _build_query_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="编码查询")
        input_frame = ttk.Frame(tab)
        input_frame.pack(fill="x", padx=14, pady=14)
        ttk.Label(input_frame, text="输入汉字文本").pack(anchor="w")
        self.input_text = tk.Text(input_frame, height=3, wrap="word", font=("Microsoft YaHei UI", 13), undo=True)
        self.input_text.pack(fill="x", pady=(6, 8))
        self.input_text.insert("1.0", "中国软件著作权 CNBE-32")
        btns = ttk.Frame(input_frame)
        btns.pack(fill="x")
        ttk.Button(btns, text="执行编码查询", style="Accent.TButton", command=self._run_query).pack(side="left")
        ttk.Button(btns, text="清空", command=self._clear_query).pack(side="left", padx=8)
        ttk.Button(btns, text="复制结果", command=self._copy_result).pack(side="left")

        cols = ("char", "unicode", "cnbe", "binary", "radix", "strokes", "struct", "index", "track", "status")
        self.tree = ttk.Treeview(tab, columns=cols, show="headings")
        heads = {
            "char": "字符",
            "unicode": "Unicode",
            "cnbe": "CNBE-32",
            "binary": "32 位二进制",
            "radix": "部首/根",
            "strokes": "笔画",
            "struct": "结构",
            "index": "索引",
            "track": "轨道",
            "status": "状态",
        }
        widths = {
            "char": 56,
            "unicode": 88,
            "cnbe": 106,
            "binary": 240,
            "radix": 100,
            "strokes": 66,
            "struct": 90,
            "index": 66,
            "track": 88,
            "status": 180,
        }
        for key in cols:
            self.tree.heading(key, text=heads[key])
            self.tree.column(key, width=widths[key], minwidth=widths[key], stretch=key in {"binary", "status"})
        self.tree.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        self.detail = tk.Text(tab, height=8, wrap="word", font=("Consolas", 10), bg="#ffffff")
        self.detail.pack(fill="x", padx=14, pady=(0, 14))

    def _build_8105_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="8105 规范汉字表")
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=14, pady=12)
        ttk.Label(top, text="搜索：").pack(side="left")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search_var, width=24, font=("Microsoft YaHei UI", 11))
        entry.pack(side="left", padx=(4, 8))
        ttk.Button(top, text="筛选", command=self._filter_8105).pack(side="left")
        ttk.Button(top, text="重置", command=self._reset_8105).pack(side="left", padx=8)
        self.stats_var = tk.StringVar(value="标准轨（8105 基线）已编码记录")
        ttk.Label(top, textvariable=self.stats_var).pack(side="right")

        cols = ("char", "unicode", "cnbe", "radix", "strokes", "struct")
        self.table = ttk.Treeview(tab, columns=cols, show="headings")
        heads = {
            "char": "字符",
            "unicode": "Unicode",
            "cnbe": "CNBE-32",
            "radix": "部首/根",
            "strokes": "笔画",
            "struct": "结构",
        }
        widths = {"char": 70, "unicode": 110, "cnbe": 120, "radix": 160, "strokes": 80, "struct": 140}
        for key in cols:
            self.table.heading(key, text=heads[key])
            self.table.column(key, width=widths[key], minwidth=widths[key])
        self.table.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self._filter_8105()

    def _add_about_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="说明")
        text = tk.Text(tab, wrap="word", font=("Microsoft YaHei UI", 12), bg="#ffffff", padx=18, pady=18)
        text.pack(fill="both", expand=True, padx=14, pady=14)
        text.insert("1.0", ABOUT_TEXT % {"rows": count(), "standard": _standard_count()})
        text.configure(state="disabled")

    def _run_query(self) -> None:
        text = self.input_text.get("1.0", "end").strip()
        self._rows = []
        for ch in text:
            if ch.isspace():
                continue
            self._rows.append(_encode_char(ch))
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self._rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["char"],
                    row["unicode"],
                    row["cnbe"] or "-",
                    row["binary"] or "-",
                    row["radix"],
                    row["strokes"],
                    row["struct"],
                    row["index"],
                    row["track"] or "-",
                    row["status"],
                ),
            )
        self._render_detail()

    def _render_detail(self) -> None:
        lines: list[str] = []
        for row in self._rows:
            lines.append(f"{row['char']} {row['unicode']}")
            lines.append(f"  CNBE-32 : {row['cnbe'] or '-'} / {row['decimal'] if row['decimal'] is not None else '-'}")
            lines.append(f"  Binary  : {row['binary'] or '-'}")
            lines.append(
                f"  Fields  : radix={row['radix']}, stroke={row['strokes']}, "
                f"struct={row['struct']}, index={row['index']}, ext={row['ext']}"
            )
            lines.append(f"  Status  : {row['status']}")
            lines.append("")
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", "\n".join(lines) if lines else "请输入汉字后执行编码查询。")
        self.detail.configure(state="disabled")

    def _filter_8105(self) -> None:
        keyword = self.search_var.get().strip()
        rows = _search_standard(keyword)
        for item in self.table.get_children():
            self.table.delete(item)
        for r in rows:
            self.table.insert(
                "",
                "end",
                values=(r["char"], r["unicode"], r["cnbe"], r["radix"], r["strokes"], r["struct"]),
            )
        self.stats_var.set(f"标准轨已编码 {_standard_count():,} / 8105 基线 · 显示 {len(rows):,} 条")

    def _reset_8105(self) -> None:
        self.search_var.set("")
        self._filter_8105()

    def _clear_query(self) -> None:
        self.input_text.delete("1.0", "end")
        self._rows = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._render_detail()

    def _copy_result(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.detail.get("1.0", "end").strip())


def _standard_count() -> int:
    conn = sqlite3.connect(resolve_db_path())
    try:
        return int(conn.execute("SELECT COUNT(*) FROM cnbe32 WHERE track='standard'").fetchone()[0])
    finally:
        conn.close()


def _search_standard(keyword: str) -> list[dict]:
    conn = sqlite3.connect(resolve_db_path())
    rows: list[dict] = []
    try:
        sql = "SELECT unicode, char, cnbe, radix, radix_name, strokes, struct_type, struct_name FROM cnbe32 WHERE track='standard'"
        params: tuple = ()
        if keyword:
            if len(keyword) == 1 and "\u4e00" <= keyword <= "\u9fff":
                sql += " AND char = ?"
                params = (keyword,)
            elif keyword.isdigit():
                sql += " AND (radix = ? OR strokes = ?)"
                n = int(keyword)
                params = (n, n)
            else:
                sql += " AND radix_name LIKE ?"
                params = (f"%{keyword}%",)
        sql += " ORDER BY unicode LIMIT 2000"
        for u, ch, cnbe, radix, rname, strokes, stype, sname in conn.execute(sql, params):
            rows.append(
                {
                    "char": ch,
                    "unicode": f"U+{u:04X}" if isinstance(u, int) else str(u),
                    "cnbe": f"0x{int(cnbe):08X}" if cnbe is not None else "-",
                    "radix": f"{radix}/{rname}" if radix is not None else "-",
                    "strokes": strokes if strokes is not None else "-",
                    "struct": f"{stype}/{sname}" if stype is not None else "-",
                }
            )
    finally:
        conn.close()
    return rows


def _encode_char(char: str) -> dict:
    codepoint = ord(char)
    row = lookup(char)
    if row is None:
        return {
            "char": char,
            "unicode": f"U+{codepoint:04X}",
            "cnbe": None,
            "decimal": None,
            "binary": None,
            "radix": "-",
            "strokes": "-",
            "struct": "-",
            "index": "-",
            "ext": "-",
            "track": None,
            "status": "未收录",
        }
    cnbe_value = row.get("cnbe")
    needs = bool(row.get("needs_encoding", 0))
    decoded = decode_cnbe(int(cnbe_value)) if cnbe_value is not None else {}
    track = row.get("track")
    if cnbe_value is None or needs:
        status = "已收录：待授权编码" if cnbe_value is None or needs else "已编码"
    elif track == "standard":
        status = "已编码：标准轨（8105 基线）"
    else:
        status = "已编码：历史/扩展轨"
    return {
        "char": char,
        "unicode": f"U+{codepoint:04X}",
        "cnbe": f"0x{int(cnbe_value):08X}" if cnbe_value is not None else None,
        "decimal": int(cnbe_value) if cnbe_value is not None else None,
        "binary": f"{int(cnbe_value):032b}" if cnbe_value is not None else None,
        "radix": f"{row.get('radix')}/{row.get('radix_name')}" if row.get("radix") is not None else "-",
        "strokes": row.get("strokes") if row.get("strokes") is not None else "-",
        "struct": f"{row.get('struct_type')}/{row.get('struct_name')}" if row.get("struct_type") is not None else "-",
        "index": decoded.get("index", row.get("idx")) if (decoded.get("index") is not None or row.get("idx") is not None) else "-",
        "ext": decoded.get("ext", "-") if decoded.get("ext") is not None else "-",
        "track": track,
        "status": status,
    }


def main() -> None:
    app = Demo8105App()
    app.mainloop()


if __name__ == "__main__":
    main()
