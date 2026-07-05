import sys, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from generate_tick_data import generate_tick_data

# ===== Reusable JEPA Model =====
class JEPAModel(nn.Module):
    def __init__(self, input_dim, latent_dim=64):
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
        z = self.ctx(x); zp = self.pred(torch.cat([z, a], dim=-1))
        with torch.no_grad(): zt = self.tgt(y)
        return F.mse_loss(zp, zt)

# ===== Ablation Encoders =====
class CNBEEncoder:
    """Full CNBE: 10 features → 32-bit code"""
    def encode(self, feats):
        code = 0
        code |= (min(int(feats[0]*15),15) & 0xF) << 28  # trend
        code |= (min(int(feats[1]*15),15) & 0xF) << 24  # volatility
        code |= (min(int(feats[2]*15),15) & 0xF) << 20  # momentum
        code |= (min(int(feats[3]*15),15) & 0xF) << 16  # volume
        code |= (min(int(feats[4]*15),15) & 0xF) << 12  # crisis
        code |= (min(int(feats[5]*15),15) & 0xF) << 8   # width
        code |= (min(int(feats[6]*3),3) & 0x3) << 6     # time phase
        code |= (min(int(feats[7]*3),3) & 0x3) << 4     # overnight gap
        code |= (min(int(feats[8]*3),3) & 0x3) << 2     # support/resistance
        code |= (min(int(feats[9]*3),3) & 0x3)           # trend strength
        return np.array([float(code)], dtype=np.float32) / 4294967295.0
    
    def encode_all(self, feats):
        return np.array([self.encode(feats[i]) for i in range(len(feats))]).reshape(len(feats), -1)

def make_abl_encoder(mask_desc):
    """Factory for ablation encoders with specific bit masks"""
    class AblEncoder:
        def __init__(self, desc):
            self.desc = desc
            # Define which feature fields to ZERO OUT in the 32-bit code
            # mask: list of (bit_start, bit_end, feat_indices)
            self.feats_zero = []
            if "no_trend" in desc: self.feats_zero.extend([0])
            if "no_vol_mom" in desc: self.feats_zero.extend([1,2])
            if "no_mkt_struct" in desc: self.feats_zero.extend([4,5])
            if "no_time" in desc: self.feats_zero.extend([6,7])
            if "no_support" in desc: self.feats_zero.extend([8,9])
        
        def encode(self, feats):
            f = feats.copy()
            for idx in self.feats_zero: f[idx] = 0
            code = 0
            code |= (min(int(f[0]*15),15) & 0xF) << 28
            code |= (min(int(f[1]*15),15) & 0xF) << 24
            code |= (min(int(f[2]*15),15) & 0xF) << 20
            code |= (min(int(f[3]*15),15) & 0xF) << 16
            code |= (min(int(f[4]*15),15) & 0xF) << 12
            code |= (min(int(f[5]*15),15) & 0xF) << 8
            code |= (min(int(f[6]*3),3) & 0x3) << 6
            code |= (min(int(f[7]*3),3) & 0x3) << 4
            code |= (min(int(f[8]*3),3) & 0x3) << 2
            code |= (min(int(f[9]*3),3) & 0x3)
            return np.array([float(code)], dtype=np.float32) / 4294967295.0
        
        def encode_all(self, feats):
            return np.array([self.encode(feats[i]) for i in range(len(feats))]).reshape(len(feats), -1)
    return AblEncoder(mask_desc)

class RawEncoder:
    def encode_all(self, feats): return feats.astype(np.float32)

class OneHotEncoder:
    def encode_all(self, feats):
        oh = np.zeros((len(feats), 100))
        for i, f in enumerate(feats):
            for j, v in enumerate(f[:10]):
                oh[i, j*10 + min(int(v*10), 9)] = 1.0
        return oh

class RandomEncoder:
    def __init__(self, dim=32): self.dim = dim
    def encode_all(self, feats):
        return np.random.randn(len(feats), self.dim).astype(np.float32)

# ===== Experiment Runner =====
def run_exp(name, enc, feats, epochs=80):
    xs = enc.encode_all(feats[:-1])
    ys = enc.encode_all(feats[1:])
    chg = feats[:-1, 2]; vol = feats[:-1, 1]
    acts = np.zeros((len(xs), 1))
    for i in range(len(acts)):
        acts[i] = 2 if (abs(chg[i])>0.5 or vol[i]>0.5) else (1 if (abs(chg[i])>0.2 or vol[i]>0.2) else 0)
    
    n = len(xs); idx = np.random.permutation(n); n_train = int(n*0.8)
    model = JEPAModel(input_dim=xs.shape[1]); opt = torch.optim.Adam(model.parameters(), lr=0.001)
    best_val = float("inf")
    for ep in range(epochs):
        model.train()
        for s in range(0, n_train, 16):
            e=min(s+16, n_train); ids=idx[s:e]
            x=torch.FloatTensor(xs[ids]); a=torch.FloatTensor(acts[ids]); y=torch.FloatTensor(ys[ids])
            opt.zero_grad(); loss=model(x,a,y)
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),1)
            opt.step(); model.update_tgt()
        model.eval()
        with torch.no_grad():
            vl=model(torch.FloatTensor(xs[idx[n_train:]]), torch.FloatTensor(acts[idx[n_train:]]), torch.FloatTensor(ys[idx[n_train:]])).item()
        best_val=min(best_val, vl)
        if (ep+1)%20==0: print(f"  [{name}] E{ep+1} Val:{vl:.6f}")
    return {"name":name,"val":vl,"min":best_val,"dim":xs.shape[1]}

def main():
    print("="*65)
    print("  CNBE-32 v9.3: Ablation Study + S&P500 Tick Data (June 1)")
    print("="*65)
    
    _, feats = generate_tick_data(seed=42)
    print(f"  {len(feats)} minutes of tick data, {feats.shape[1]} features\n")
    
    encoders = [
        ("CNBE-Full", CNBEEncoder()),
        ("Abl-1 NoTrend", make_abl_encoder("no_trend")),
        ("Abl-2 NoVolMom", make_abl_encoder("no_vol_mom")),
        ("Abl-3 NoMktStruc", make_abl_encoder("no_mkt_struct")),
        ("Abl-4 NoTimeCtx", make_abl_encoder("no_time")),
        ("Abl-5 NoSupport", make_abl_encoder("no_support")),
        ("Raw", RawEncoder()),
        ("OneHot", OneHotEncoder()),
        ("Random", RandomEncoder(dim=32)),
    ]
    
    results = []
    for name, enc in encoders:
        print(f">>> {name}...")
        t0=time.time()
        try:
            r=run_exp(name, enc, feats)
            r["time"]=time.time()-t0
            results.append(r)
            print(f"  Done in {r['time']:.1f}s | Val:{r['val']:.6f} | Min:{r['min']:.6f}\n")
        except Exception as e:
            print(f"  ERROR: {e}\n"); import traceback; traceback.print_exc()
            results.append({"name":name,"error":str(e)})
    
    print("="*65); print("  RESULTS"); print("="*65)
    print(f"{'Encoder':<18} {'Dim':<6} {'Val':<14} {'MinVal':<14} {'InfoRatio':<10}")
    print("-"*62)
    best=None
    for r in results:
        if "error" in r: print(f"{r['name']:<18} ERROR")
        else:
            ir = r["min"]/max(r["dim"],1)
            print(f"{r['name']:<18} {r['dim']:<6} {r['val']:<14.6f} {r['min']:<14.6f} {ir:<10.2e}")
            if best is None or r["min"]<best["min"]: best=r
    if best: print(f"\nBEST: {best['name']} (Min: {best['min']:.6f})")
    
    out=os.path.join(os.path.dirname(__file__),"results")
    os.makedirs(out,exist_ok=True)
    json.dump(results, open(os.path.join(out,"v93_results.json"),"w"),indent=2)
    print(f"\nSaved to {out}")

if __name__=="__main__":
    main()
