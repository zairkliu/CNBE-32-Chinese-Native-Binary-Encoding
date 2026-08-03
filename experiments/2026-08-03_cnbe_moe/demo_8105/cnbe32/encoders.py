"""Domain-specific CNBE encoders from v9.0-v10.8 experiments"""
import numpy as np


class TreeEncoder:
    """v9.0: Tree growth [species(4)+height(6)+crown(6)+health(4)+light(4)+water(4)+age(4)]"""
    def encode(self, species, height, crown, health, light, water, age):
        return (
            (min(species, 15) & 0xF) << 28 |
            (min(height,   63) & 0x3F) << 22 |
            (min(crown,    63) & 0x3F) << 16 |
            (min(health,   15) & 0xF) << 12 |
            (min(light,    15) & 0xF) << 8 |
            (min(water,    15) & 0xF) << 4 |
            (min(age,      15) & 0xF)
        )

class TyphoonEncoder:
    """v10.3: Typhoon path [lat(8)+lon(8)+wind(8)+pressure(8)]"""
    def encode(self, lat, lon, wind, pressure):
        return (
            (int(lat / 50 * 255) & 0xFF) << 24 |
            (int((lon - 100) / 80 * 255) & 0xFF) << 16 |
            (int(wind / 85 * 255) & 0xFF) << 8 |
            (int((pressure - 900) / 120 * 255) & 0xFF)
        )

class BlackHoleEncoder:
    """v10.5: BH spacetime [r_Rs(8)+redshift(8)+tidal(8)+deflection(8)]"""
    def encode(self, r_rs, redshift, tidal, deflection):
        return (
            (min(int((r_rs - 1) / 99 * 255), 255) & 0xFF) << 24 |
            (min(redshift, 255) & 0xFF) << 16 |
            (min(tidal, 255) & 0xFF) << 8 |
            (min(deflection, 255) & 0xFF)
        )

class SocialEncoder:
    """v10.6: Urban state [traffic(8)+livelihood(6)+infra(6)+env(4)+emergency(3)+region(3)+time(2)]"""
    def encode(self, traffic, livelihood, infra, env, emergency, region, time_slot):
        return (
            (min(traffic, 255) & 0xFF) << 24 |
            (min(livelihood, 63) & 0x3F) << 18 |
            (min(infra, 63) & 0x3F) << 12 |
            (min(env, 15) & 0xF) << 8 |
            (min(emergency, 7) & 0x7) << 5 |
            (min(region, 7) & 0x7) << 2 |
            (min(time_slot, 3) & 0x3)
        )

class MathEncoder:
    """v10.7-10.8: Math token [type(4)+value(4)]"""
    def encode(self, token_type, value):
        return (
            (token_type & 0xF) << 28 |
            (value & 0xF) << 24
        )

class RawEncoder:
    def encode(self, x): return x

class OneHotEncoder:
    def __init__(self, dim=20):
        self.dim = dim
    def encode(self, x):
        if not 0 <= x < self.dim:
            raise ValueError(f"OneHotEncoder: index {x} out of range [0, {self.dim})")
        oh = np.zeros(self.dim)
        oh[x] = 1.0
        return oh

class RandomEncoder:
    def __init__(self, dim=32):
        self.dim = dim
    def encode(self, x): return np.random.randn(self.dim)
