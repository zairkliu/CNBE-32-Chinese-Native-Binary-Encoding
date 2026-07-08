import numpy as np

class CNBETreeEncoder:
    """将树木状态编码为CNBE风格的结构化32位编码"""
    
    def __init__(self):
        self.species_bits = 4   # bits 31:28
        self.height_bits = 6    # bits 27:22
        self.crown_bits = 6     # bits 21:16
        self.health_bits = 4    # bits 15:12
        self.light_bits = 4     # bits 11:8
        self.water_bits = 4     # bits 7:4
        self.age_bits = 4       # bits 3:0
        
        self.height_max = 30.0
        self.crown_max = 15.0
        self.age_max = 200
        self.n_features = 7
    
    def encode_single(self, tree_features: np.ndarray) -> int:
        species, height, crown, health, light, water, age = tree_features[:7]
        code = 0
        code |= (int(species) & 0xF) << 28
        height_level = int((height / self.height_max) * 63)
        code |= (min(height_level, 63) & 0x3F) << 22
        crown_level = int((crown / self.crown_max) * 63)
        code |= (min(crown_level, 63) & 0x3F) << 16
        health_level = int(health * 15)
        code |= (min(health_level, 15) & 0xF) << 12
        light_level = int(light * 15)
        code |= (min(light_level, 15) & 0xF) << 8
        water_level = int(water * 15)
        code |= (min(water_level, 15) & 0xF) << 4
        age_level = int((age / self.age_max) * 15)
        code |= (min(age_level, 15) & 0xF)
        return code
    
    def encode_batch(self, state: np.ndarray) -> np.ndarray:
        codes = np.zeros(state.shape[0], dtype=np.uint32)
        for i in range(state.shape[0]):
            codes[i] = self.encode_single(state[i])
        return codes
    
    def encode_state(self, state: np.ndarray) -> np.ndarray:
        """编码整个环境状态（N棵树）为向量"""
        codes = self.encode_batch(state)
        return codes.astype(np.float32) / 4294967295.0
    
    def decode(self, code: int) -> dict:
        return {
            "species": (code >> 28) & 0xF,
            "height": ((code >> 22) & 0x3F) / 63 * self.height_max,
            "crown": ((code >> 16) & 0x3F) / 63 * self.crown_max,
            "health": ((code >> 12) & 0xF) / 15,
            "light": ((code >> 8) & 0xF) / 15,
            "water": ((code >> 4) & 0xF) / 15,
            "age": ((code) & 0xF) / 15 * self.age_max
        }

class RawEncoder:
    """原始特征编码器（对照）"""
    def encode_state(self, state: np.ndarray) -> np.ndarray:
        return state[:, :7].astype(np.float32).flatten()

class RandomEncoder:
    """随机编码器（对照）"""
    def __init__(self, dim=32):
        self.dim = dim
    def encode_state(self, state: np.ndarray) -> np.ndarray:
        return np.random.randn(self.dim).astype(np.float32)

class OneHotEncoder:
    """One-hot编码器（对照）"""
    def encode_state(self, state: np.ndarray) -> np.ndarray:
        flat = state[:, :7].astype(np.float32).flatten()
        # Convert to one-hot-like (discretize)
        oh = np.zeros(64)
        for i, v in enumerate(flat[:6]):
            idx = min(int(v * 10), 9)
            oh[i * 10 + idx] = 1.0
        return oh

