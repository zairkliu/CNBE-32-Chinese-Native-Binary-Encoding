from lexer import Token, TT
from nodes import *

class Parser:
    def __init__(self,toks):
        self.t=toks; self.p=0
    def peek(self):
        return self.t[self.p] if self.p<len(self.t) else None
    def nxt(self):
        t=self.peek(); self.p+=1; return t
    def m(self,tt):
        if self.peek() and self.peek().type==tt: self.nxt(); return True
        return False
    def e(self,tt):
        t=self.nxt()
        if t.type!=tt: raise SyntaxError("Expected %s got %s L%d"%(tt,t.type,t.line))
        return t
    def parse(self):
        if self.m(TT.DOT): self.e(TT.ID); self.e(TT.INT_C)
        self.e(TT.PROGRAM)
        p=Program(name=self.e(TT.ID).value)
        while self.peek() and self.peek().type!=TT.EOF:
            if self.peek().type==TT.SUBPROC: p.subprograms.append(self.sub())
            else: self.nxt()
        return p
    def sub(self):
        self.e(TT.SUBPROC); n=self.e(TT.ID).value
        rt="int"
        if self.peek() and self.peek().type==TT.COMMA:
            self.nxt()
            if self.peek().type in (TT.INT,TT.FLOAT,TT.STRING,TT.CHAR,TT.CODE): rt=self.nxt().value
        pa=[]
        if self.m(TT.LPAREN):
            while self.peek() and self.peek().type!=TT.RPAREN:
                pt=self.nxt().value; pn=self.e(TT.ID).value; pa.append((pn,pt))
                self.m(TT.COMMA)
            self.e(TT.RPAREN)
        b=[]
        while self.peek() and self.peek().type not in (TT.EOF,TT.SUBPROC):
            s=self.stmt()
            if s: b.append(s)
        return SubProgram(name=n,return_type=rt,params=pa,body=b)
    def stmt(self):
        t=self.peek()
        if not t: return None
        if t.type in (TT.INT,TT.FLOAT,TT.STRING,TT.CHAR,TT.CODE):
            vt=self.nxt().value; nm=self.e(TT.ID).value; init=None
            if self.m(TT.ASSIGN): init=self.expr()
            return VarDecl(var_type=vt,name=nm,init=init)
        if t.type==TT.ID:
            nm=self.nxt().value; self.e(TT.ASSIGN); v=self.expr()
            return AssignStmt(target=nm,value=v)
        if t.type==TT.IF:
            self.nxt(); self.e(TT.LPAREN); c=self.expr(); self.e(TT.RPAREN)
            tb=[]
            while self.peek() and self.peek().type not in (TT.ELSE,TT.ENDIF):
                s=self.stmt()
                if s: tb.append(s)
            eb=[]
            if self.m(TT.ELSE):
                while self.peek() and self.peek().type!=TT.ENDIF:
                    s=self.stmt()
                    if s: eb.append(s)
            self.e(TT.ENDIF)
            st=IfStmt(condition=c, then_body=tb, else_body=eb); return st
        if t.type==TT.FOR:
            self.nxt(); self.e(TT.LPAREN); c=self.expr(); self.e(TT.RPAREN)
            b=[]
            while self.peek() and self.peek().type!=TT.ENDLOOP:
                s=self.stmt()
                if s: b.append(s)
            self.e(TT.ENDLOOP)
            st=ForLoop(count=c, body=b); return st
        if t.type==TT.RETURN:
            self.nxt(); v=None
            if self.peek() and self.peek().type!=TT.EOF: v=self.expr()
            st=ReturnStmt(value=v); return st
        if t.type==TT.OUTPUT:
            self.nxt(); self.e(TT.LPAREN); v=self.expr(); self.e(TT.RPAREN)
            st=OutputStmt(value=v); return st
        self.nxt(); return None
    def expr(self):
        return self._b(0)
    def _b(self,m):
        l=self._p()
        P_d = {TT.EQ:2,TT.NE:2,TT.LT:3,TT.GT:3,TT.LE:3,TT.GE:3,TT.PLUS:4,TT.MINUS:4,TT.MUL:5,TT.DIV:5}
        while True:
            t=self.peek()
            if not t or t.type not in P_d: break
            if P_d[t.type]<m: break
            op=self.nxt().type
            r=self._b(P_d[op]+1)
            e=BinOp(operator=op.name, left=l, right=r); l=e
        return l
    def _p(self):
        t=self.peek()
        if not t: return None
        if t.type==TT.INT_C: self.nxt(); return IntLiteral(value=int(t.value))
        if t.type==TT.STRING_C: self.nxt(); return StringLiteral(value=t.value)
        if t.type==TT.LPAREN: self.nxt(); e=self.expr(); self.e(TT.RPAREN); return e
        if t.type==TT.ID:
            nm=self.nxt().value
            if self.peek() and self.peek().type==TT.LPAREN: return self._c(nm)
            return Identifier(name=nm)
        if t.type in (TT.GET_CODE,TT.GET_RADICAL,TT.GET_STROKE,TT.GET_STRUCT,TT.COMPARE):
            nm=self.nxt().type.name; return self._c(nm)
        return None
    def _c(self,n):
        self.e(TT.LPAREN); a=[]
        while self.peek() and self.peek().type!=TT.RPAREN:
            a.append(self.expr()); self.m(TT.COMMA)
        self.e(TT.RPAREN); return FuncCall(name=n,args=a)
