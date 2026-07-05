import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Tree:
    species: int       # 0-9
    height: float      # 0-30m
    crown: float       # 0-15m
    health: float      # 0-1
    light: float       # 0-1
    water: float       # 0-1
    age: int           # 0-200
    ring_width: float  # 当年年轮宽度

class TreeEnvironment:
    """树木生长与互动模拟环境"""
    
    N_ACTIONS = 6  # 0=无, 1=浇水, 2=施肥, 3=修剪, 4=种植, 5=移除
    
    def __init__(self, n_trees: int = 10, grid_size: int = 20, random_seed: Optional[int] = None):
        self.n_trees = n_trees
        self.grid_size = grid_size
        self.trees: List[Tree] = []
        self.positions: List[Tuple[int, int]] = []
        self.step_count = 0
        
        if random_seed is not None:
            np.random.seed(random_seed)
        self._init_trees()
    
    def _init_trees(self):
        species_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        for i in range(self.n_trees):
            species = np.random.choice(species_list)
            height = np.random.uniform(0.5, 5.0)
            crown = np.random.uniform(0.3, 3.0)
            health = np.random.uniform(0.6, 1.0)
            age = np.random.randint(1, 20)
            self.trees.append(Tree(
                species=species, height=height, crown=crown,
                health=health, light=1.0, water=1.0,
                age=age, ring_width=0.001
            ))
            x = np.random.randint(0, self.grid_size)
            y = np.random.randint(0, self.grid_size)
            self.positions.append((x, y))
    
    def step(self, actions: np.ndarray) -> Tuple[np.ndarray, float, bool]:
        """执行一步模拟，返回 (state, reward, done)"""
        self._compute_light_competition()
        self._compute_water_competition()
        for i in range(self.n_trees):
            self._apply_action(i, int(actions[i]) if actions.ndim > 0 else int(actions))
        for i in range(self.n_trees):
            if self.trees[i].health > 0:
                self._update_growth(i)
        self.step_count += 1
        
        done = self.step_count >= 100
        return self.get_state(), self._compute_reward(), done
    
    def _compute_light_competition(self):
        for i in range(self.n_trees):
            shade = 0.0
            for j in range(self.n_trees):
                if i != j and self.trees[j].health > 0 and self.trees[j].height > self.trees[i].height:
                    dist = self._distance(i, j)
                    if dist < self.trees[j].crown + 1.0:
                        shade += (self.trees[j].height - self.trees[i].height) / 30.0
            self.trees[i].light = float(np.clip(1.0 - shade * 0.15, 0.05, 1.0))
    
    def _compute_water_competition(self):
        for i in range(self.n_trees):
            density = 0.0
            for j in range(self.n_trees):
                if i != j:
                    dist = self._distance(i, j)
                    if dist < 3.0:
                        density += 1.0 / max(dist + 0.1, 0.1)
            self.trees[i].water = float(np.clip(1.0 - density * 0.05, 0.05, 1.0))
    
    def _update_growth(self, idx: int):
        tree = self.trees[idx]
        growth_rate = (tree.light * 0.4 + tree.water * 0.3 + tree.health * 0.2) * 0.5
        age_factor = max(0.1, 1.0 - tree.age / 200.0)
        growth_rate *= age_factor * np.random.uniform(0.9, 1.1)
        
        tree.height = float(np.clip(tree.height + growth_rate * 0.1, 0.0, 30.0))
        tree.crown = float(np.clip(tree.crown + growth_rate * 0.05, 0.0, 15.0))
        tree.ring_width = float(growth_rate * 0.01)
        tree.age += 1
        
        tree.health = float(np.clip(
            tree.health + (tree.light - 0.5) * 0.02 + (tree.water - 0.5) * 0.01,
            0.0, 1.0
        ))
    
    def get_state(self) -> np.ndarray:
        state = []
        for tree in self.trees:
            state.append([
                tree.species, tree.height, tree.crown,
                tree.health, tree.light, tree.water,
                tree.age, tree.ring_width
            ])
        return np.array(state, dtype=np.float32)
    
    def _distance(self, i: int, j: int) -> float:
        x1, y1 = self.positions[i]
        x2, y2 = self.positions[j]
        return float(np.sqrt((x1-x2)**2 + (y1-y2)**2))
    
    def _apply_action(self, idx: int, action: int):
        tree = self.trees[idx]
        if action == 1:  # 浇水
            tree.water = min(1.0, tree.water + 0.2)
        elif action == 2:  # 施肥
            tree.health = min(1.0, tree.health + 0.1)
        elif action == 3:  # 修剪
            tree.crown = max(0.5, tree.crown * 0.9)
            tree.health = min(1.0, tree.health + 0.05)
        elif action == 5:  # 移除
            tree.health = 0.0
    
    def _compute_reward(self) -> float:
        return float(np.mean([t.health for t in self.trees]) * 
                     np.mean([t.height for t in self.trees]) / 30.0)
    
    def reset(self, random_seed: Optional[int] = None):
        self.trees = []
        self.positions = []
        self.step_count = 0
        if random_seed is not None:
            np.random.seed(random_seed)
        self._init_trees()
        return self.get_state()
    
    def generate_trajectory(self, steps: int = 50, seed: int = 0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """生成一条轨迹：(states, actions, next_states)"""
        np.random.seed(seed)
        self.reset(seed)
        states, actions_list, next_states = [], [], []
        
        for _ in range(steps):
            s = self.get_state().copy()
            a = np.random.randint(0, self.N_ACTIONS, size=self.n_trees)
            ns, _, done = self.step(a)
            states.append(s)
            actions_list.append(a)
            next_states.append(ns)
            if done:
                break
        
        return np.array(states), np.array(actions_list), np.array(next_states)
    
    def generate_trajectories(self, n_traj: int = 50, steps: int = 50) -> list:
        """生成多条轨迹"""
        trajectories = []
        for t in range(n_traj):
            traj = self.generate_trajectory(steps, seed=t)
            trajectories.append(traj)
        return trajectories
