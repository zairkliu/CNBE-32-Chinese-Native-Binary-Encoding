from dataclasses import dataclass
from enum import Enum, auto

class TT(Enum):
    PROGRAM=auto();SUBPROC=auto();VAR=auto()
    INT=auto();FLOAT=auto();STRING=auto();CHAR=auto();CODE=auto()
    IF=auto();ELSE=auto();ENDIF=auto()
    FOR=auto();WHILE=auto();ENDLOOP=auto()
    RETURN=auto();OUTPUT=auto();INPUT=auto()
    GET_CODE=auto();GET_RADICAL=auto();GET_STROKE=auto()
    GET_STRUCT=auto();COMPARE=auto()
    ID=auto();INT_C=auto();FLOAT_C=auto();STRING_C=auto()
    ASSIGN=auto();EQ=auto();NE=auto();LT=auto();GT=auto()
    LE=auto();GE=auto();PLUS=auto();MINUS=auto()
    MUL=auto();DIV=auto();LPAREN=auto();RPAREN=auto()
    LBRACK=auto();RBRACK=auto();COMMA=auto();COLON=auto()
    DOT=auto();EOF=auto()

@dataclass
class Token:
    type: TT; value: str; line: int; col: int

class Lexer:
    def __init__(self, src):
        self.s = src; self.p = 0; self.l = 1; self.c = 1

    def tok(self):
        KW = {
            '程序集': TT.PROGRAM,
            '子程序': TT.SUBPROC,
            '变量': TT.VAR,
            '整数': TT.INT,
            '小数': TT.FLOAT,
            '文本': TT.STRING,
            '汉字': TT.CHAR,
            '编码': TT.CODE,
            '如果': TT.IF,
            '否则': TT.ELSE,
            '结束如果': TT.ENDIF,
            '计次循环': TT.FOR,
            '判断循环': TT.WHILE,
            '结束循环': TT.ENDLOOP,
            '返回': TT.RETURN,
            '输出': TT.OUTPUT,
            '输入': TT.INPUT,
            '取编码': TT.GET_CODE,
            '取部首': TT.GET_RADICAL,
            '取笔画': TT.GET_STROKE,
            '取结构': TT.GET_STRUCT,
            '比较': TT.COMPARE,
        }
        OP = {
            '=': TT.ASSIGN,
            '==': TT.EQ,
            '!=': TT.NE,
            '<': TT.LT,
            '><': TT.GE,
            '>': TT.GT,
            '+': TT.PLUS,
            '-': TT.MINUS,
            '*': TT.MUL,
            '/': TT.DIV,
            '(': TT.LPAREN,
            ')': TT.RPAREN,
            '[': TT.LBRACK,
            ']': TT.RBRACK,
            ',': TT.COMMA,
            ':': TT.COLON,
            '.': TT.DOT,
        }
        r = []
        while self.p < len(self.s):
            ch = self.s[self.p]
            if ch.isspace():
                if ch == chr(10): self.l += 1; self.c = 1
                else: self.c += 1
                self.p += 1; continue
            if chr(0x4e00) <= ch <= chr(0x9fff):
                w = self._rd()
                r.append(Token(KW.get(w, TT.ID), w, self.l, self.c - len(w)))
                continue
            if chr(97) <= ch <= chr(122) or chr(65) <= ch <= chr(90) or ch == chr(95):
                w = self._rascii()
                r.append(Token(TT.ID, w, self.l, self.c - len(w)))
                continue
            if ch.isdigit() or (ch == chr(46) and self.p+1 < len(self.s) and self.s[self.p+1].isdigit()):
                n = self._rn()
                r.append(Token(TT.FLOAT_C if chr(46) in n else TT.INT_C, n, self.l, self.c - len(n)))
                continue
            if ch in OP:
                if self.p + 1 < len(self.s):
                    t = ch + self.s[self.p + 1]
                    if t in ("==", "!=", "<=", ">="):
                        r.append(Token(OP[t], t, self.l, self.c))
                        self.p += 2; self.c += 2; continue
                r.append(Token(OP[ch], ch, self.l, self.c))
                self.p += 1; self.c += 1; continue
            self.p += 1; self.c += 1
        r.append(Token(TT.EOF, "", self.l, self.c))
        return r

    def _rd(self):
        s = self.p
        while self.p < len(self.s) and (chr(0x4e00) <= self.s[self.p] <= chr(0x9fff) or self.s[self.p].isdigit() or self.s[self.p] == chr(95)):
            self.p += 1; self.c += 1
        return self.s[s:self.p]

    def _rascii(self):
        s = self.p
        while self.p < len(self.s) and (chr(97) <= self.s[self.p] <= chr(122) or chr(65) <= self.s[self.p] <= chr(90) or self.s[self.p].isdigit() or self.s[self.p] == chr(95)):
            self.p += 1; self.c += 1
        return self.s[s:self.p]

    def _rn(self):
        s = self.p; d = False
        while self.p < len(self.s):
            ch = self.s[self.p]
            if ch.isdigit(): self.p += 1; self.c += 1
            elif ch == chr(46) and not d: d = True; self.p += 1; self.c += 1
            else: break
        return self.s[s:self.p]