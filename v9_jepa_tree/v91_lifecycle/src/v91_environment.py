import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

# 树种定义
SPECIES = {
    0: {"name": "松树", "wind_resist": 0.7, "growth": 0.3, "max_h": 30.0},
    1: {"name": "柏树", "wind_resist": 0.8, "growth": 0.2, "max_h": 25.0},
    2: {"name": "杉树", "wind_resist": 0.6, "growth": 0.4, "max_h": 35.0},
    3: {"name": "杨树", "wind_resist": 0.4, "growth": 0.7, "max_h": 25.0},
    4: {"name": "柳树", "wind_resist": 0.3, "growth": 0.6, "max_h": 20.0},
    5: {"name": "榕树", "wind_resist": 0.9, "growth": 0.2, "max_h": 20.0},
    6: {"name": "橡树", "wind_resist": 0.8, "growth": 0.2, "max_h": 30.0},
    7: {"name": "枫树", "wind_resist": 0.6, "growth": 0.4, "max_h": 25.0},
    8: {"name": "梧桐", "wind_resist": 0.5, "growth": 0.5, "max_h": 25.0},
    9: {"name": "银杏", "wind_resist": 0.7, "growth": 0.2, "max_h": 30.0},
}

@dataclass
class TreeState:
    species: int       # 0-9
    height: float      # 0-30m
    crown: float       # 0-15m
    health: float      # 0.0-1.0
    tilt: float        # 0-90度
    struck: int        # 0/1 是否被雷击
    alive: int         # 0/1 是否存活
    age: int           # 0-200年
    ring_width: float  # 当年年轮宽度

    def to_array(self):
        return np.array([self.species, self.height, self.crown, self.health,
                         self.tilt, self.struck, self.alive, self.age, self.ring_width], dtype=np.float32)

class TreeLifecycleEnvironment:
    """树木生命周期模拟环境——包含台风、雷击、生命周期"""
    
    N_ACTIONS = 6
    
    def __init__(self, n_trees: int = 10, max_steps: int = 500, seed: Optional[int] = None):
        self.n_trees = n_trees
        self.max_steps = max_steps
        self.step_count = 0
        self.trees: List[TreeState] = []
        if seed is not None:
            np.random.seed(seed)
        self._init_trees()
        self._init_weather()
    
    def _init_trees(self):
        for i in range(self.n_trees):
            sp = i % 10  # 均匀分配树种
            s = SPECIES[sp]
            self.trees.append(TreeState(
                species=sp,
                height=np.random.uniform(0.5, 3.0),
                crown=np.random.uniform(0.3, 1.5),
                health=np.random.uniform(0.8, 1.0),
                tilt=0.0, struck=0, alive=1,
                age=np.random.randint(1, 10),
                ring_width=0.0
            ))
    
    def _init_weather(self):
        self.wind = 0.0          # 0-12级
        self.rain = 0.0          # 0-200 mm/h
        self.lightning = 0       # 0/1
        self.light = 1.0         # 0-1
    
    def _update_weather(self):
        step = self.step_count
        # 5-stage weather cycle
        if step < 100:  # 微风期
            self.wind = np.random.uniform(0, 2)
            self.rain = np.random.uniform(0, 10)
            self.light = np.random.uniform(0.8, 1.0)
        elif step < 180:  # 台风发展期
            progress = (step - 100) / 80.0
            self.wind = 3 + progress * 9  # 3→12
            self.rain = 20 + progress * 130  # 20→150
            self.light = max(0.1, 1.0 - progress * 0.9)
        elif step < 220:  # 台风峰值期
            self.wind = np.random.uniform(10, 12)
            self.rain = np.random.uniform(150, 200)
            self.light = np.random.uniform(0.0, 0.1)
            self.lightning = 1 if np.random.random() < 0.3 else 0
        elif step < 280:  # 台风消退期
            progress = (step - 220) / 60.0
            self.wind = 12 - progress * 9
            self.rain = 150 - progress * 130
            self.light = min(0.8, 0.1 + progress * 0.7)
            self.lightning = 0
        else:  # 恢复期
            self.wind = np.random.uniform(0, 2)
            self.rain = np.random.uniform(0, 20)
            self.light = np.random.uniform(0.8, 1.0)
    
    def step(self, actions: Optional[np.ndarray] = None) -> Tuple[np.ndarray, bool]:
        self._update_weather()
        for i in range(self.n_trees):
            self._update_tree(i)
        self.step_count += 1
        done = self.step_count >= self.max_steps
        return self.get_state(), done
    
    def _update_tree(self, idx: int):
        t = self.trees[idx]
        if not t.alive:
            return
        
        s = SPECIES[t.species]
        wr = s["wind_resist"]  # 抗风系数
        gr = s["growth"]       # 生长速度
        
        # 风对树木的影响
        wind_damage = max(0, self.wind - 8 * wr) * 0.02
        if wind_damage > 0:
            t.tilt = min(90, t.tilt + wind_damage * (1 - wr) * 5)
            t.crown = max(0.1, t.crown - wind_damage * 0.5)
            t.health = max(0, t.health - wind_damage * 0.1)
        
        # 雷击
        if self.lightning and t.height > 5:
            if np.random.random() < 0.15:
                t.struck = 1
                t.health = max(0, t.health - 0.5)
        
        # 光照影响生长
        growth_factor = self.light * (1 - t.tilt / 90)
        if t.health > 0.3:
            grow = gr * growth_factor * 0.05
            t.height = min(s["max_h"], t.height + grow)
            t.crown = min(15, t.crown + grow * 0.5)
            t.ring_width = grow * 0.01
            t.health = min(1.0, t.health + (self.light - 0.3) * 0.005)
        else:
            t.health = max(0, t.health - 0.01)  # 恶化
        
        # 年龄
        t.age += 1
        
        # 死亡判定
        if t.tilt > 45 or t.health <= 0:
            t.alive = 0
            t.health = 0
    
    def get_state(self) -> np.ndarray:
        state = []
        for t in self.trees:
            state.append(t.to_array())
        return np.array(state, dtype=np.float32)
    
    def get_weather(self) -> np.ndarray:
        return np.array([self.wind, self.rain, self.lightning, self.light], dtype=np.float32)
    
    def reset(self):
        self.step_count = 0
        self.trees = []
        self._init_trees()
        self._init_weather()
        return self.get_state()
    
    def generate_trajectory(self, steps: int = 200, seed: int = 0) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        np.random.seed(seed)
        self.reset()
        states, weathers, next_states = [], [], []
        for _ in range(steps):
            s = self.get_state().copy()
            w = self.get_weather().copy()
            ns = self.get_state().copy(); _, done = self.step()
            states.append(s)
            weathers.append(w)
            next_states.append(ns)
            if done:
                break
        return np.array(states), np.array(weathers), np.array(next_states), np.array([s.alive for s in self.trees])
    
    def generate_trajectories(self, n_traj: int = 30, steps: int = 200):
        trajs = []
        for t in range(n_traj):
            trajs.append(self.generate_trajectory(steps, seed=t * 100))
        return trajs

