import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class JEPAV91Model(nn.Module):
    """v9.1 JEPA预测模型"""
    def __init__(self, input_dim: int, latent_dim: int = 64, n_trees: int = 10):
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.n_trees = n_trees
        
        self.context_encoder = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, latent_dim)
        )
        self.target_encoder = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, latent_dim)
        )
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim + n_trees, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, latent_dim)
        )
        self.ema_decay = 0.99
        self._init_target()
    
    def _init_target(self):
        for pq, pk in zip(self.context_encoder.parameters(), self.target_encoder.parameters()):
            pk.data.copy_(pq.data)
            pk.requires_grad = False
    
    def update_target(self):
        with torch.no_grad():
            for pq, pk in zip(self.context_encoder.parameters(), self.target_encoder.parameters()):
                pk.data = self.ema_decay * pk.data + (1 - self.ema_decay) * pq.data
    
    def forward(self, state, actions, next_state):
        z = self.context_encoder(state)
        z_pred = self.predictor(torch.cat([z, actions], dim=-1))
        with torch.no_grad():
            z_target = self.target_encoder(next_state)
        return F.mse_loss(z_pred, z_target), z_pred, z_target

def train_epoch(model, opt, states, actions, next_states, batch_size=32):
    model.train()
    total, n = 0, len(states)
    idx = np.random.permutation(n)
    for s in range(0, n, batch_size):
        e = min(s + batch_size, n)
        ids = idx[s:e]
        s_t = torch.FloatTensor(states[ids])
        a_t = torch.FloatTensor(actions[ids])
        ns_t = torch.FloatTensor(next_states[ids])
        opt.zero_grad()
        loss, _, _ = model(s_t, a_t, ns_t)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        model.update_target()
        total += loss.item() * len(ids)
    return total / n

def evaluate_survival(model, states, actions, states_flat):
    """评估存活预测准确率"""
    model.eval()
    with torch.no_grad():
        z = model.context_encoder(torch.FloatTensor(states))
        z_pred = model.predictor(torch.cat([z, torch.FloatTensor(actions)], dim=-1))
        surv_pred = z_pred[:, 9].numpy()  # 存活状态在潜空间第9维
    surv_true = states_flat[:, 9]
    # 简单分类：使用阈值
    if surv_pred.max() > surv_pred.min():
        surv_pred_bin = (surv_pred > np.median(surv_pred)).astype(int)
    else:
        surv_pred_bin = np.zeros_like(surv_true)
    acc = (surv_pred_bin == surv_true).mean()
    return float(acc)
