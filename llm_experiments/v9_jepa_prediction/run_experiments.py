import os
import sys
import json
import time
import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from environment import TreeEnvironment
from cnbe_tree_encoder import CNBETreeEncoder, RawEncoder, RandomEncoder, OneHotEncoder
from jepa_model import JEPAModel, train_epoch

def run_experiment(
    encoder_name: str,
    encoder,
    n_trees: int = 10,
    n_traj: int = 30,
    traj_steps: int = 30,
    epochs: int = 100,
    lr: float = 0.001,
    seed: int = 42
) -> dict:
    """运行单一编码实验"""
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    # 生成轨迹数据
    env = TreeEnvironment(n_trees=n_trees, grid_size=20)
    all_states, all_actions, all_next = [], [], []
    for t in range(n_traj):
        states, actions, next_states = env.generate_trajectory(steps=traj_steps, seed=seed + t)
        for i in range(len(states)):
            all_states.append(encoder.encode_state(states[i]))
            act_flat = actions[i].flatten()
            all_actions.append(act_flat)
            all_next.append(encoder.encode_state(next_states[i]))
    
    states = np.array(all_states)
    actions = np.array(all_actions)
    next_states = np.array(all_next)
    
    input_dim = states.shape[1]
    action_dim = TreeEnvironment.N_ACTIONS
    
    # 划分训练/验证
    n = len(states)
    n_train = int(n * 0.8)
    idx = np.random.permutation(n)
    train_s, train_a, train_ns = states[idx[:n_train]], actions[idx[:n_train]], next_states[idx[:n_train]]
    val_s, val_a, val_ns = states[idx[n_train:]], actions[idx[n_train:]], next_states[idx[n_train:]]
    
    # 初始化模型
    model = JEPAModel(input_dim=input_dim, latent_dim=64, 
                      action_dim=action_dim, n_trees=n_trees)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    # 训练
    history = {"train_loss": [], "val_loss": []}
    for epoch in range(epochs):
        train_loss = train_epoch(model, optimizer, train_s, train_a, train_ns)
        
        model.eval()
        with torch.no_grad():
            s = torch.FloatTensor(val_s)
            a = torch.FloatTensor(val_a)
            ns = torch.FloatTensor(val_ns)
            val_loss, _, _ = model(s, a, ns)
        
        history["train_loss"].append(float(train_loss))
        history["val_loss"].append(float(val_loss))
        
        if (epoch + 1) % 20 == 0:
            print(f"  [{encoder_name}] Epoch {epoch+1}/{epochs}  Train: {train_loss:.6f}  Val: {val_loss:.6f}")
    
    return {
        "encoder": encoder_name,
        "final_train_loss": float(history["train_loss"][-1]),
        "final_val_loss": float(history["val_loss"][-1]),
        "min_val_loss": float(min(history["val_loss"])),
        "history": history,
        "input_dim": input_dim
    }

def main():
    print("=" * 60)
    print("  CNBE-32 v9.0: JEPA Prediction on Tree Growth")
    print("=" * 60)
    
    EXP_CONFIG = {
        "n_trees": 10,
        "n_traj": 30,
        "traj_steps": 30,
        "epochs": 80,
        "lr": 0.001,
        "seed": 42
    }
    
    # 初始化编码器
    cnbe_enc = CNBETreeEncoder()
    raw_enc = RawEncoder()
    rnd_enc = RandomEncoder(dim=32)
    oh_enc = OneHotEncoder()
    
    encoders = [
        ("CNBE", cnbe_enc),
        ("Raw", raw_enc),
        ("Random", rnd_enc),
        ("OneHot", oh_enc),
    ]
    
    results = []
    for name, enc in encoders:
        print(f"\n>>> Running {name} encoding...")
        t0 = time.time()
        try:
            r = run_experiment(name, enc, **EXP_CONFIG)
            r["time"] = time.time() - t0
            results.append(r)
            print(f"    Done in {r['time']:.1f}s  |  Final Val Loss: {r['final_val_loss']:.6f}")
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({"encoder": name, "error": str(e)})
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Encoder':<10} {'Final Train':<15} {'Final Val':<15} {'Min Val':<15} {'Input Dim':<10}")
    print("-" * 65)
    
    best = None
    for r in results:
        if "error" in r:
            print(f"{r['encoder']:<10} ERROR: {r['error']}")
        else:
            print(f"{r['encoder']:<10} {r['final_train_loss']:<15.6f} {r['final_val_loss']:<15.6f} {r['min_val_loss']:<15.6f} {r['input_dim']:<10}")
            if best is None or r["min_val_loss"] < best["min_val_loss"]:
                best = r
    
    if best:
        print(f"\n  BEST: {best['encoder']} (Min Val Loss: {best['min_val_loss']:.6f})")
    
    # 保存结果
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)
    
    # 保存为JSON
    save_results = []
    for r in results:
        if "error" not in r:
            save_results.append({
                "encoder": r["encoder"],
                "final_train_loss": r["final_train_loss"],
                "final_val_loss": r["final_val_loss"],
                "min_val_loss": r["min_val_loss"],
                "input_dim": r["input_dim"],
                "time": r["time"]
            })
        else:
            save_results.append({"encoder": r["encoder"], "error": r["error"]})
    
    with open(os.path.join(out_dir, "v90_results.json"), "w") as f:
        json.dump(save_results, f, indent=2)
    
    # 保存训练历史
    histories = {}
    for r in results:
        if "history" in r:
            histories[r["encoder"]] = r["history"]
    with open(os.path.join(out_dir, "v90_histories.json"), "w") as f:
        json.dump(histories, f, indent=2)
    
    print(f"\nResults saved to: {out_dir}")
    return results

if __name__ == "__main__":
    main()

