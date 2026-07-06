"""CNBE-32 v10.5 黑洞物理引擎"""
import numpy as np
from dataclasses import dataclass

@dataclass
class BlackHole:
    mass_solar: float = 9.62
    G: float = 6.674e-11
    c: float = 2.998e8

    @property
    def mass_kg(self):
        return self.mass_solar * 1.989e30

    @property
    def schwarzschild_radius(self):
        return 2 * self.G * self.mass_kg / self.c**2

    @property
    def schwarzschild_radius_km(self):
        return self.schwarzschild_radius / 1000


def gravitational_redshift(r, rs):
    if r <= rs: return np.inf
    return 1.0 / np.sqrt(1 - rs / r) - 1.0


def tidal_force(r, rs, delta_r=1.0):
    if r <= rs: return np.inf
    return (rs / r**3) * delta_r


def time_dilation(r, rs):
    if r <= rs: return np.inf
    return 1.0 / np.sqrt(1 - rs / r)


def light_deflection(r, rs):
    if r <= rs: return np.inf
    return 2.0 * rs / r


def generate_spacetime_samples(bh, num_samples=1000, r_min=1.5, r_max=100.0):
    rs = bh.schwarzschild_radius
    radii = np.linspace(r_min * rs, r_max * rs, num_samples)
    samples = []
    for r in radii:
        if r <= rs: continue
        samples.append({"r": r, "r_schwarzschild": r / rs,
                        "redshift": gravitational_redshift(r, rs),
                        "tidal": tidal_force(r, rs),
                        "time_dilation": time_dilation(r, rs),
                        "deflection": light_deflection(r, rs)})
    return samples


class CNBEBHEncoder:
    def __init__(self):
        self.rs_min, self.rs_max = 1.0, 100.0
        self.z_min, self.z_max = 0, 5.0
        self.tidal_min, self.tidal_max = 0, 1000.0
        self.dil_min, self.dil_max = 1.0, 10.0
        self.def_min, self.def_max = 0, np.pi

    def _q(self, v, lo, hi, bits):
        if v is None or not np.isfinite(v): return 0
        n = np.clip((v - lo) / (hi - lo), 0, 1)
        return int(round(n * ((1 << bits) - 1)))

    def encode(self, s):
        """Encode spacetime sample into 32-bit CNBE code"""
        code = 0
        code |= (self._q(s["r_schwarzschild"], self.rs_min, self.rs_max, 8) << 24)
        code |= (self._q(s["redshift"], self.z_min, self.z_max, 8) << 16)
        code |= (self._q(s["tidal"], self.tidal_min, self.tidal_max, 8) << 8)
        code |= (self._q(s["deflection"], self.def_min, self.def_max, 8))
        return code

    def encode_bits(self, s):
        code = self.encode(s)
        return np.array([(code >> i) & 1 for i in range(32)], dtype=np.float32)


def prepare_features(samples, encoding="cnbe"):
    enc = CNBEBHEncoder()
    if encoding == "cnbe":
        return np.array([enc.encode_bits(s) for s in samples])
    elif encoding == "raw":
        return np.array([[s["r_schwarzschild"], s["redshift"], s["tidal"], s["deflection"]] for s in samples])
    elif encoding == "onehot":
        n_bins = 20
        oh = np.zeros((len(samples), n_bins))
        for i, s in enumerate(samples):
            idx = int(np.clip((s["r_schwarzschild"] - 1) / 99 * n_bins, 0, n_bins - 1))
            oh[i, idx] = 1.0
        return oh
    elif encoding == "random":
        return np.random.randn(len(samples), 32)
    raise ValueError(f"Unknown: {encoding}")


def prepare_targets(samples, target="redshift"):
    return np.array([s[target] for s in samples])
