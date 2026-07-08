import sys, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from generate_data import generate_dataset
from financial_encoder import CNBEFinancialEncoder, RawFinancialEncoder, OneHotFinancialEncoder, RandomFinancialEncoder

class JEPAModel(nn.Module):
    def __init__(self, input_dim: int, latent_dim: int = 32):
        super().__init__()
        self.ctx = nn.Sequential(nn.Linear(input_dim, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, latent_dim))
        self.tgt = nn.Sequential(nn.Linear(input_dim, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, latent_dim))
        self.pred = nn.Sequential(nn.Linear(latent_dim + 1, 32), nn.ReLU(), nn.Linear(32, latent_dim))
        self.ema = 0.99
        for pq, pk in zip(self.ctx.parameters(), self.tgt.parameters()):
            pk.data.copy_(pq.data); pk.requires_grad = False

    def update_tgt(self):
        with torch.no_grad():
            for pq, pk in zip(self.ctx.parameters(), self.tgt.parameters()):
                pk.data = self.ema * pk.data + (1 - self.ema) * pq.data

    def forward(self, x, a, y):
        z = self.ctx(x)
        zp = self.pred(torch.cat([z, a], dim=-1))
        with torch.no_grad():
            zt = self.tgt(y)
        return F.mse_loss(zp, zt)

def run(enc_name, enc, data, epochs=80):
    """data: numpy array [close, chg_pct, vol_ratio, ma_dev, vola, mom, crisis, width, trend]"""
    xs = enc.encode_dataset(data[:-1])
    ys = enc.encode_dataset(data[1:])
    
    # Actions based on volatility and change
    chg = data[:-1, 1]; vol = data[:-1, 4]
    acts = np.zeros((len(xs), 1))
    for i in range(len(acts)):
        acts[i] = 2 if (abs(chg[i]) > 3 or vol[i] > 3) else (1 if (abs(chg[i]) > 1.5 or vol[i] > 1.5) else 0)
    
    n = len(xs); idx = np.random.permutation(n); n_train = int(n * 0.8)
    input_dim = xs.shape[1]
    model = JEPAModel(input_dim=input_dim, latent_dim=32)
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    
    best_val = float("inf")
    for ep in range(epochs):
        model.train()
        for s in range(0, n_train, 16):
            e = min(s + 16, n_train); ids = idx[s:e]
            x = torch.FloatTensor(xs[ids]); a = torch.FloatTensor(acts[ids]); y = torch.FloatTensor(ys[ids])
            opt.zero_grad(); loss = model(x, a, y)
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1)
            opt.step(); model.update_tgt()
        model.eval()
        with torch.no_grad():
            vl = model(torch.FloatTensor(xs[idx[n_train:]]), torch.FloatTensor(acts[idx[n_train:]]), torch.FloatTensor(ys[idx[n_train:]])).item()
        best_val = min(best_val, vl)
        if (ep+1) % 20 == 0: print(f"  [{enc_name}] E{ep+1} Val:{vl:.6f}")
    
    return {"encoder": enc_name, "final_val": vl, "min_val": best_val, "input_dim": input_dim}

def main():
    print("="*60)
    print("  CNBE-32 v9.2: 2008 Financial Crisis Prediction")
    print("="*60)
    print("\nGenerating financial data...")
    data = generate_dataset()
    print(f"  {len(data)} trading days")
    
    encoders = [
        ("CNBE", CNBEFinancialEncoder()),
        ("Raw", RawFinancialEncoder()),
        ("OneHot", OneHotFinancialEncoder()),
        ("Random", RandomFinancialEncoder(dim=32)),
    ]
    
    results = []
    for name, enc in encoders:
        print(f"\n>>> {name}...")
        t0 = time.time()
        try:
            r = run(name, enc, data)
            r["time"] = time.time() - t0
            results.append(r)
            print(f"    Done in {r['time']:.1f}s | Val: {r['final_val']:.6f} | Min: {r['min_val']:.6f}")
        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback; traceback.print_exc()
            results.append({"encoder": name, "error": str(e)})
    
    print("\n"+"="*60); print("  RESULTS"); print("="*60)
    print(f"{'Enc':<8} {'Dim':<6} {'Val':<14} {'MinVal':<14}")
    print("-"*42)
    best = None
    for r in results:
        if "error" in r: print(f"{r['encoder']:<8} ERROR")
        else:
            print(f"{r['encoder']:<8} {r['input_dim']:<6} {r['final_val']:<14.6f} {r['min_val']:<14.6f}")
            if best is None or r["min_val"] < best["min_val"]: best = r
    if best: print(f"\nBEST: {best['encoder']} (Min: {best['min_val']:.6f})")
    
    out = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out, exist_ok=True)
    json.dump(results, open(os.path.join(out, "v92_results.json"), "w"), indent=2)
    print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
