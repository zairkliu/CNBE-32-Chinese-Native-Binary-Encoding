"""CNBE-32 专用异常类体系"""

class CNBEError(Exception):
    """CNBE-32 基础异常类——所有 CNBE 异常的基类"""

class CNBECodePointError(CNBEError):
    """Unicode 码点映射失败"""

class CNBEValueError(CNBEError, ValueError):
    """数值超出有效位域范围"""

class CNBEFormatError(CNBEError):
    """编码格式错误（位布局异常）"""

class CNBECharNotInTableError(CNBEError):
    """字符不在 CNBE 编码表中"""
    def __init__(self, char, code_point=None):
        self.char = char
        self.code_point = code_point
        msg = f"字符 '{char}' (U+{code_point:04X}) 不在 CNBE 编码表中" if code_point else f"字符 '{char}' 不在 CNBE 编码表中"
        super().__init__(msg)

class CNBEStructureError(CNBEError):
    """结构类型解析错误"""
