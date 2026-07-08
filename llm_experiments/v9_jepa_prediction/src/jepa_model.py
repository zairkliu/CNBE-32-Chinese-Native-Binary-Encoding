import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

class JEPAModel(nn.Module):
    """JEPA树木预测模型"""
    def __init__(self, input_dim: int, latent_dim: int = 64, action_dim: int = 6, n_trees: int = 10):
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.action_dim = action_dim
        self.n_trees = n_trees
        
        # 上下文编码器
        self.context_encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim)
        )
        
        # 目标编码器
        self.target_encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim)
        )
        
        # 预测器
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim + n_trees, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim)
        )
        
        self.ema_decay = 0.99
        self._init_target_encoder()
    
    def _init_target_encoder(self):
        for param_q, param_k in zip(
            self.context_encoder.parameters(),
            self.target_encoder.parameters()
        ):
            param_k.data.copy_(param_q.data)
            param_k.requires_grad = False
    
    def update_target_encoder(self):
        with torch.no_grad():
            for param_q, param_k in zip(
                self.context_encoder.parameters(),
                self.target_encoder.parameters()
            ):
                param_k.data = self.ema_decay * param_k.data + (1 - self.ema_decay) * param_q.data
    
    def encode_context(self, state: torch.Tensor) -> torch.Tensor:
        return self.context_encoder(state)
    
    def encode_target(self, state: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return self.target_encoder(state)
    
    def predict(self, z: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        x = torch.cat([z, actions], dim=-1)
        return self.predictor(x)
    
    def forward(self, state, actions, next_state):
        z = self.encode_context(state)
        z_pred = self.predict(z, actions)
        z_target = self.encode_target(next_state)
        loss = F.mse_loss(z_pred, z_target)
        return loss, z_pred, z_target

def train_epoch(model, optimizer, states, actions, next_states, batch_size=32):
    """训练一个epoch"""
    model.train()
    total_loss = 0
    n = len(states)
    indices = np.random.permutation(n)
    
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        idx = indices[start:end]
        
        s = torch.FloatTensor(states[idx])
        a = torch.FloatTensor(actions[idx])
        ns = torch.FloatTensor(next_states[idx])
        
        optimizer.zero_grad()
        loss, _, _ = model(s, a, ns)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        model.update_target_encoder()
        total_loss += loss.item() * len(idx)
    
    return total_loss / n


