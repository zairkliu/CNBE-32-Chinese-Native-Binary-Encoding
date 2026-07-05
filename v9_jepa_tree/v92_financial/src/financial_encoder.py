import numpy as np

class CNBEFinancialEncoder:
    """CNBE金融编码器——将多维金融指标编码为32位结构化位域"""
    
    def encode_state(self, row: np.ndarray) -> np.ndarray:
        """
        编码单个交易日状态
        row: [close, change_pct, volume_ratio, ma_dev, volatility, momentum, crisis_signal, market_width, trend_strength]
        """
        chg_pct = float(row[1])     # 涨跌幅(%)
        vol_ratio = float(row[2])   # 成交量比
        ma_dev = float(row[3])      # 均线偏离(%)
        vola = float(row[4])        # 波动率
        momentum = float(row[5])    # 动量
        crisis = int(row[6])        # 危机信号 0-3
        width = float(row[7])       # 市场宽度 0-1
        trend = float(row[8])       # 趋势强度
        
        code = 0
        # [31:29] 指数类型 (固定为道琼斯=0)
        # [28] 方向: 0=跌, 1=涨
        code |= (1 if chg_pct >= 0 else 0) << 28
        # [27:24] 变化等级
        chg_level = min(int(abs(chg_pct) / 10 * 15), 15)
        code |= (chg_level & 0xF) << 24
        # [23:20] 波动率等级
        vol_level = min(int(vola / 5 * 15), 15)
        code |= (vol_level & 0xF) << 20
        # [19:16] 成交量等级
        vol_ratio_level = min(int(vol_ratio / 4 * 15), 15)
        code |= (vol_ratio_level & 0xF) << 16
        # [15:12] 均线偏离
        dev_level = min(int(abs(ma_dev) / 10 * 15), 15)
        code |= (dev_level & 0xF) << 12
        # [11:8] 市场宽度
        width_level = min(int(width * 15), 15)
        code |= (width_level & 0xF) << 8
        # [7:4] 危机信号
        code |= (min(crisis, 15) & 0xF) << 4
        # [3:0] 趋势强度
        trend_level = min(int(trend / 5 * 15), 15)
        code |= (trend_level & 0xF)
        
        return np.array([float(code)], dtype=np.float32) / 4294967295.0
    
    def encode_dataset(self, data: np.ndarray) -> np.ndarray:
        """编码完整数据集 N行×M特征"""
        codes = []
        for i in range(len(data)):
            codes.append(self.encode_state(data[i]))
        return np.array(codes).reshape(len(data), -1)

class RawFinancialEncoder:
    def encode_dataset(self, data: np.ndarray) -> np.ndarray:
        return data.astype(np.float32)

class OneHotFinancialEncoder:
    def encode_dataset(self, data: np.ndarray) -> np.ndarray:
        oh = np.zeros((len(data), 50))
        for i, row in enumerate(data):
            for j, v in enumerate(row[:8]):
                idx = min(int(abs(v)), 5)
                oh[i, j * 6 + idx] = 1.0
        return oh

class RandomFinancialEncoder:
    def __init__(self, dim=32):
        self.dim = dim
    def encode_dataset(self, data: np.ndarray) -> np.ndarray:
        return np.random.randn(len(data), self.dim).astype(np.float32)
