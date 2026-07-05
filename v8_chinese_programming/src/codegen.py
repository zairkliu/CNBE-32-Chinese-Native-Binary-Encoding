from nodes import *

class CodeGen:
    def __init__(self):
        self.i=[]; self.v={}; self.lc=0; self.tc=0; self.s={}
    def gen(self,p):
        self.i=[".text",".globl main","main:"]
        for sub in p.subprograms:
            self.v={}
            self.i.append(""); self.i.append("# "+sub.name)
            self.i.append(sub.name+":")
            for st in sub.body: self._s(st)
        if self.s:
            self.i.append(""); self.i.append(".data")
            for val,lbl in self.s.items(): self.i.append(f"{lbl}: .string|{val}|")
        self.i.append(""); self.i.append("# CNBE runtime stubs")
        self.i.append("cnhe_map: ret")
        self.i.append("cnhe_extract: ret")
        self.i.append("cnhe_cmp: ret")
        return self.i
    def _s(self,s):
        if isinstance(s,VarDecl):
            r=self._a(s.name)
            if s.init: self.i.append("    mv %s, %s"%(r,self._e(s.init)))
            else: self.i.append("    li %s, 0"%r)
        elif isinstance(s,AssignStmt):
            self.i.append("    mv %s, %s"%(self._g(s.target),self._e(s.value)))
        elif isinstance(s,OutputStmt):
            vr_ = self._e(s.value)
            self.i.append("    addi sp, sp, -16")
            self.i.append("    sw %s, 0(sp)" % vr_)
            self.i.append("    li a7, 64")
            self.i.append("    li a0, 1")
            self.i.append("    mv a1, sp")
            self.i.append("    li a2, 4")
            self.i.append("    ecall")
            self.i.append("    addi sp, sp, 16")
        elif isinstance(s,ReturnStmt):
            if s.value: self.i.append("    mv a0, %s"%self._e(s.value))
            self.i.append("    li a7, 93")
            self.i.append("    ecall")
        elif hasattr(s,"condition") and hasattr(s,"then_body"): self._if(s)
        elif hasattr(s,"count") and hasattr(s,"body"): self._for(s)
    def _if(self,s):
        le=self.nl(); le2=self.nl()
        self.i.append("    beqz %s, %s"%(self._e(s.condition),le))
        for st in s.then_body: self._s(st)
        self.i.append("    j %s"%le2)
        self.i.append("%s:"%le)
        for st in s.else_body: self._s(st)
        self.i.append("%s:"%le2)
    def _for(self,s):
        l1=self.nl(); l2=self.nl()
        cr=self._e(s.count); lr=self.nt()
        self.i.append("    li %s, 0"%lr)
        self.i.append("%s:"%l1)
        self.i.append("    bge %s, %s, %s"%(lr,cr,l2))
        for st in s.body: self._s(st)
        self.i.append("    addi %s, %s, 1"%(lr,lr))
        self.i.append("    j %s"%l1)
        self.i.append("%s:"%l2)
    def _e(self,e):
        if isinstance(e,IntLiteral):
            r=self.nt(); self.i.append("    li %s, %d"%(r,e.value)); return r
        if isinstance(e,CharLiteral):
            r=self.nt(); self.i.append("    li %s, %d"%(r,ord(e.value))); return r
        if isinstance(e,Identifier): return self._g(e.name)
        if isinstance(e,BinOp):
            l=self._e(e.left); r=self._e(e.right); ri=self.nt(); op=e.operator
            if op=="PLUS": self.i.append("    add %s, %s, %s"%(ri,l,r))
            elif op=="MINUS": self.i.append("    sub %s, %s, %s"%(ri,l,r))
            elif op=="MUL": self.i.append("    mul %s, %s, %s"%(ri,l,r))
            elif op=="DIV": self.i.append("    div %s, %s, %s"%(ri,l,r))
            elif op in ("EQ","NE"):
                le=self.nl(); le2=self.nl()
                b="bne" if op=="EQ" else "beq"
                self.i.append("    %s %s, %s, %s"%(b,l,r,le))
                self.i.append("    li %s, 1"%ri)
                self.i.append("    j %s"%le2)
                self.i.append("%s: li %s, 0"%(le,ri))
                self.i.append("%s:"%le2)
            elif op=="LT": self.i.append("    slt %s, %s, %s"%(ri,l,r))
            elif op=="GT": self.i.append("    slt %s, %s, %s"%(ri,r,l))
            elif op=="LE":
                self.i.append("    slt %s, %s, %s"%(ri,r,l))
                self.i.append("    xori %s, %s, 1"%(ri,ri))
            elif op=="GE":
                self.i.append("    slt %s, %s, %s"%(ri,l,r))
                self.i.append("    xori %s, %s, 1"%(ri,ri))
            return ri
        if isinstance(e,FuncCall): return self._c(e)
        r=self.nt(); self.i.append("    li %s, 0"%r); return r
    def _c(self,e):
        r=self.nt(); a=[self._e(x) for x in e.args]; n=e.name
        if n=="GET_CODE" and a: self.i.append("    mv %s, %s"%(r,a[0]))
        elif n=="GET_RADICAL" and a:
            self.i.append("    srli %s, %s, 24"%(r,a[0]))
            self.i.append("    andi %s, %s, 0xFF"%(r,r))
        elif n=="GET_STROKE" and a:
            self.i.append("    srli %s, %s, 19"%(r,a[0]))
            self.i.append("    andi %s, %s, 0x1F"%(r,r))
        elif n=="GET_STRUCT" and a:
            self.i.append("    srli %s, %s, 15"%(r,a[0]))
            self.i.append("    andi %s, %s, 0xF"%(r,r))
        elif n=="COMPARE" and len(a)>=2:
            self.i.append("    xor %s, %s, %s"%(r,a[0],a[1]))
        return r
    def nt(self):
        self.tc+=1; return "t%d"%(self.tc%6)
    def nl(self):
        self.lc+=1; return ".L%d"%self.lc
    def _a(self,n):
        self.v[n]="s%d"%(len(self.v)%8); return self.v[n]
    def _g(self,n):
        if n not in self.v: return self._a(n)
        return self.v[n]