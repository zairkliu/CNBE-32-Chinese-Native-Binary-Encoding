from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class Program:
    name: str; subprograms: list = None
    def __post_init__(self):
        if self.subprograms is None: self.subprograms = []

@dataclass
class SubProgram:
    name: str; return_type: str = "int"
    params: list = None; body: list = None
    def __post_init__(self):
        if self.params is None: self.params = []
        if self.body is None: self.body = []

@dataclass
class VarDecl:
    var_type: str; name: str
    init: Optional[Any] = None

@dataclass
class AssignStmt:
    target: str
    value: Optional[Any] = None

@dataclass
class IfStmt:
    condition: Optional[Any] = None
    then_body: list = None
    else_body: list = None
    def __post_init__(self):
        if self.then_body is None: self.then_body = []
        if self.else_body is None: self.else_body = []

@dataclass
class ForLoop:
    count: Optional[Any] = None
    body: list = None
    def __post_init__(self):
        if self.body is None: self.body = []

@dataclass
class ReturnStmt:
    value: Optional[Any] = None

@dataclass
class OutputStmt:
    value: Optional[Any] = None

@dataclass
class IntLiteral:
    value: int

@dataclass
class StringLiteral:
    value: str

@dataclass
class CharLiteral:
    value: str

@dataclass
class Identifier:
    name: str

@dataclass
class BinOp:
    operator: str
    left: Optional[Any] = None
    right: Optional[Any] = None

@dataclass
class FuncCall:
    name: str
    args: list = None
    def __post_init__(self):
        if self.args is None: self.args = []
