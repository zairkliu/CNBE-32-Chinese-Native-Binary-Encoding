"""Skill table loader (v6.0 8105-character CJK encoding)"""
import numpy as np
import os

class SkillTable:
    """81.6KB Skill table for 20902 CJK characters"""
    def __init__(self, path=None):
        self.table = np.zeros(20902, dtype=np.uint32)
        if path and os.path.exists(path):
            self.load(path)
    def load(self, path):
        if path.endswith(".npy"):
            self.table = np.load(path)
        elif path.endswith(".bin"):
            self.table = np.frombuffer(open(path,"rb").read(), dtype=np.uint32)
        print(f"Loaded SkillTable: {len(self.table)} chars")
    def lookup(self, unicode):
        if 0x4E00 <= unicode <= 0x9FA5:
            idx = unicode - 0x4E00
            if idx < len(self.table):
                return self.table[idx]
        return 0
    def __getitem__(self, char):
        return self.lookup(ord(char))
