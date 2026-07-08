import numpy as np

class CNBEV91Encoder:
    """v9.1 扩展版CNBE编码器——包含生存/天气/雷击"""
    
    def __init__(self, n_trees: int = 10):
        self.n_trees = n_trees
    
    def encode_tree(self, tree_arr: np.ndarray) -> int:
        """单棵树状态→32位编码"""
        species, height, crown, health, tilt, struck, alive, age, _ = tree_arr[:9]
        code = 0
        # [31:28] 树种
        code |= (int(species) & 0xF) << 28
        # [27:22] 高度 (6bit, 0-63)
        code |= (min(int(height / 30.0 * 63), 63) & 0x3F) << 22
        # [21:16] 冠幅 (6bit, 0-63)
        code |= (min(int(crown / 15.0 * 63), 63) & 0x3F) << 16
        # [15:13] 健康度 (3bit, 0-7)
        code |= (min(int(health * 7), 7) & 0x7) << 13
        # [12:10] 倾斜度 (3bit, 0-7)
        code |= (min(int(tilt / 90.0 * 7), 7) & 0x7) << 10
        # [9] 存活
        code |= (int(alive) & 1) << 9
        # [8] 被雷击
        code |= (int(struck) & 1) << 8
        return code
    
    def encode_batch(self, state: np.ndarray) -> np.ndarray:
        codes = np.zeros(state.shape[0], dtype=np.uint32)
        for i in range(state.shape[0]):
            codes[i] = self.encode_tree(state[i])
        return codes
    
    def encode_state(self, state: np.ndarray) -> np.ndarray:
        codes = self.encode_batch(state)
        return codes.astype(np.float32) / 4294967295.0

class RawV91Encoder:
    def encode_state(self, state: np.ndarray) -> np.ndarray:
        return state[:, :9].astype(np.float32).flatten()

class OneHotV91Encoder:
    def encode_state(self, state: np.ndarray) -> np.ndarray:
        flat = state[:, :9].astype(np.float32).flatten()
        oh = np.zeros(100)
        for i, v in enumerate(flat[:9]):
            idx = min(int(v), 9)
            oh[i * 10 + idx] = 1.0
        return oh

class RandomV91Encoder:
    def __init__(self, dim=32):
        self.dim = dim
    def encode_state(self, state: np.ndarray) -> np.ndarray:
        return np.random.randn(self.dim).astype(np.float32)
