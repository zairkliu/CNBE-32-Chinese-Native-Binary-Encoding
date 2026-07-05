import sys, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from datetime import datetime, timedelta

# ===== Known Price Reference Points =====
# A-share (沪深300): Monthly reference prices
A_REF = {
    "2026-01-05":3850,"2026-01-30":3980,"2026-02-27":3900,
    "2026-03-06":3820,"2026-03-20":3760,"2026-03-31":3721,
    "2026-04-15":3850,"2026-04-30":3950,"2026-05-15":4020,
    "2026-05-29":4080,"2026-06-15":4100,"2026-06-30":4050,
}

# S&P500: Monthly reference prices (provided in design doc)
US_REF = {
    "2026-01-30":6939.03,"2026-02-27":6878.88,"2026-03-31":6528.52,
    "2026-04-30":7209.01,"2026-05-29":7580.06,"2026-06-30":7609.78,
}

HOLIDAYS_2026_H1 = [
    # New Year
    "2026-01-01","2026-01-02","2026-01-03",
    # Spring Festival
    "2026-02-15","2026-02-16","2026-02-17","2026-02-18","2026-02-19",
    "2026-02-20","2026-02-21","2026-02-22","2026-02-23",
    # Qingming
    "2026-04-04","2026-04-05","2026-04-06",
    # Labor Day
    "2026-05-01","2026-05-02","2026-05-03","2026-05-04","2026-05-05",
    # Dragon Boat
    "2026-06-19","2026-06-20","2026-06-21",
]

def generate_daily(market="A", seed=42):
    """Generate 6 months of daily OHLCV data from reference points"""
    np.random.seed(seed)
    ref = A_REF if market == "A" else US_REF
    
    # Generate all trading days
    start = datetime(2026, 1, 1); end = datetime(2026, 6, 30)
    all_days = []
    d = start
    while d <= end:
        ds = d.strftime("%Y-%m-%d")
        if ds not in HOLIDAYS_2026_H1 and d.weekday() < 5:
            all_days.append(ds)
        d += timedelta(days=1)
    
    # Generate prices by interpolating between reference points
    ref_dates = sorted(ref.keys())
    prices = np.zeros(len(all_days))
    
    ref_idx = 0
    for i, day in enumerate(all_days):
        # Find which reference period we're in
        while ref_idx < len(ref_dates) - 1 and day >= ref_dates[ref_idx + 1]:
            ref_idx += 1
        
        if ref_idx >= len(ref_dates) - 1:
            # After last reference point
            prices[i] = ref[ref_dates[-1]] + np.random.randn() * 10
        else:
            # Interpolate between reference points
            d1 = datetime.strptime(ref_dates[ref_idx], "%Y-%m-%d")
            d2 = datetime.strptime(ref_dates[ref_idx + 1], "%Y-%m-%d")
            cd = datetime.strptime(day, "%Y-%m-%d")
            t = (cd - d1).days / max((d2 - d1).days, 1)
            base = ref[ref_dates[ref_idx]] + (ref[ref_dates[ref_idx + 1]] - ref[ref_dates[ref_idx]]) * t
            prices[i] = base + np.random.randn() * 8
    
    # Create OHLCV
    ohlcv = np.zeros((len(all_days), 5))
    for i in range(len(all_days)):
        ohlcv[i, 0] = prices[max(0, i-1)]  # Open
        ohlcv[i, 1] = prices[i] + abs(np.random.randn() * 5)  # High
        ohlcv[i, 2] = prices[i] - abs(np.random.randn() * 5)  # Low
        ohlcv[i, 3] = prices[i]  # Close
        ohlcv[i, 4] = (np.random.rand() * 0.5 + 0.5) * 1e8  # Volume
    
    return all_days, ohlcv

def compute_features(ohlcv):
    """Compute 10 features from OHLCV"""
    close, high, low, vol = ohlcv[:,3], ohlcv[:,1], ohlcv[:,2], ohlcv[:,4]
    n = len(close)
    feat = np.zeros((n, 10))
    for i in range(n):
        ma5 = np.mean(close[max(0,i-4):i+1]); ma20 = np.mean(close[max(0,i-19):i+1])
        feat[i,0] = (close[i]-ma20)/ma20*100 if ma20>0 else 0
        tr = max(high[i]-low[i], abs(high[i]-close[max(0,i-1)]), abs(low[i]-close[max(0,i-1)])) if i>0 else high[i]-low[i]
        feat[i,1] = tr/close[i]*100
        feat[i,2] = (close[i]-close[max(0,i-5)])/close[max(0,i-5)]*100 if i>=5 else 0
        avg_v = np.mean(vol[max(0,i-19):i+1])
        feat[i,3] = vol[i]/max(avg_v,1) if avg_v>0 else 1
        rets = [close[max(0,i-j)]/close[max(0,i-j-1)]-1 for j in range(min(5,i)) if close[max(0,i-j-1)]>0]
        neg = [r for r in rets if r<0]
        feat[i,4] = abs(np.mean(neg))*100 if neg else 0
        feat[i,5] = np.clip(np.random.randn()*0.3+0.5,0,1)
        feat[i,6] = 0  # daily = no time phase
        feat[i,7] = abs(close[i]-close[i-1])/close[i-1]*100 if i>0 else 0
        ma = np.mean(close[max(0,i-19):i+1]); std = np.std(close[max(0,i-19):i+1]) if i>=20 else 1
        feat[i,8] = (close[i]-ma)/max(std,0.01)
        dp = np.mean([max(close[max(0,i-j)]-close[max(0,i-j-1)],0) for j in range(min(14,i))]) if i>=14 else 0.1
        dn = np.mean([max(close[max(0,i-j-1)]-close[max(0,i-j)],0) for j in range(min(14,i))]) if i>=14 else 0.1
        feat[i,9] = abs(dp-dn)/max(dp+dn,0.01)*100 if (dp+dn)>0 else 0
    for j in range(10):
        mn, mx = feat[:,j].min(), feat[:,j].max()
        if mx-mn>0: feat[:,j] = (feat[:,j]-mn)/(mx-mn)
    return feat

def encode_cnbe(feats, zero=None):
    codes = np.zeros((len(feats), 1))
    for i in range(len(feats)):
        f = feats[i].copy()
        if zero:
            for z in zero: f[z] = 0
        c = 0
        c|=(min(int(f[0]*15),15)&0xF)<<28;c|=(min(int(f[1]*15),15)&0xF)<<24
        c|=(min(int(f[2]*15),15)&0xF)<<20;c|=(min(int(f[3]*15),15)&0xF)<<16
        c|=(min(int(f[4]*15),15)&0xF)<<12;c|=(min(int(f[5]*15),15)&0xF)<<8
        c|=(min(int(f[6]*3),3)&0x3)<<6;c|=(min(int(f[7]*3),3)&0x3)<<4
        c|=(min(int(f[8]*3),3)&0x3)<<2;c|=(min(int(f[9]*3),3)&0x3)
        codes[i] = float(c)/4294967295.0
    return codes

class Predictor(nn.Module):
    def __init__(self, inp, out):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(inp+1, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, out))
    def forward(self, x, a): return self.net(torch.cat([x,a], -1))

ENCODERS = {"CNBE-Abl2": lambda f: encode_cnbe(f, [1,2]), "Raw": lambda f: f.astype(np.float32)}
COST = 0.0014; EPOCHS = 30; THRESHOLD = 0.003

def backtest_scale(close, feats, enc_name, scale_name, split_ratio=0.7):
    """Backtest for one scale"""
    enc_fn = ENCODERS[enc_name]
    n = len(feats); sp = int(n * split_ratio)
    if sp < 10 or n < 20: return None
    
    enc = enc_fn(feats)
    xs = enc[:sp-1]; ys = enc[1:sp]
    if len(xs) < 5: return None
    
    model = Predictor(xs.shape[1], ys.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    for _ in range(EPOCHS):
        idx = np.random.permutation(len(xs))
        for s in range(0, len(xs), min(16, len(xs))):
            e = min(s+16, len(xs)); ids = idx[s:e]
            x = torch.FloatTensor(xs[ids]); y = torch.FloatTensor(ys[ids]); a = torch.zeros(len(ids), 1)
            opt.zero_grad(); F.mse_loss(model(x,a), y).backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1); opt.step()
    
    model.eval()
    cp = close[sp:n]; ar = np.diff(cp) / cp[:-1]
    trades = []; eq = [1.0]; pos = 0
    
    for i in range(sp, n-1):
        nxt = model(torch.FloatTensor(enc[i:i+1]), torch.zeros(1,1))
        diff = nxt[0,0].item() - float(enc[i,0])
        if abs(diff) > THRESHOLD:
            sig = 1 if diff > 0 else 0  # long only for A-share
            if sig != pos:
                if pos: eq[-1] *= (1-COST)
                pos = sig; eq[-1] *= (1-COST)
            trades.append(sig)
        if pos: eq.append(eq[-1] * (1 + ar[i-sp] * pos))
        else: eq.append(eq[-1])
    if pos: eq[-1] *= (1-COST)
    
    net = eq[-1] - 1.0
    correct = sum(1 for i in range(min(len(trades), len(ar))) if trades[i] * ar[i] > 0)
    acc = correct / max(len(trades), 1)
    return {"net": float(net), "trades": len(trades), "acc": acc, "scale": scale_name}

def main():
    print("="*70)
    print("  CNBE v10.2: 6-Month Cross-Period Validation (Jan-Jun 2026)")
    print("="*70)
    t0 = time.time()
    
    print("\nGenerating 6-month daily data...")
    days_a, ohlcv_a = generate_daily("A")
    days_u, ohlcv_u = generate_daily("US")
    feats_a = compute_features(ohlcv_a)
    feats_u = compute_features(ohlcv_u)
    print(f"  A-share: {len(days_a)} days ({time.time()-t0:.1f}s)")
    print(f"  US:      {len(days_u)} days")
    
    bha = (ohlcv_a[-1,3] / ohlcv_a[0,3] - 1) * 100
    bhu = (ohlcv_u[-1,3] / ohlcv_u[0,3] - 1) * 100
    
    all_results = []
    for mkt_name, days, ohlcv, feats, bh in [("A", days_a, ohlcv_a, feats_a, bha),
                                               ("US", days_u, ohlcv_u, feats_u, bhu)]:
        print(f"\n--- {mkt_name} Daily (6 months) ---")
        for enc_name in ["CNBE-Abl2", "Raw"]:
            rr = backtest_scale(ohlcv[:,3], feats, enc_name, "daily")
            if rr:
                rr["market"] = mkt_name; rr["encoder"] = enc_name; rr["bh"] = bh
                all_results.append(rr)
                cost_pct = rr["trades"] * COST / len(days) * 100
                print(f"  {enc_name:<12} Ret:{rr['net']*100:+6.2f}% Trades:{rr['trades']} Acc:{rr['acc']*100:5.1f}% Cost/day:{cost_pct:.2f}%")
        print(f"  {'Buy&Hold':<12} Ret:{bh:+6.2f}%")
    
    print("\n"+"="*70); print("  FINAL SUMMARY"); print("="*70)
    print(f"{'Mkt':<5} {'Scale':<8} {'Enc':<12} {'NetRet':<10} {'Trades':<8} {'Acc':<8} {'vsB&H':<10}")
    print("-"*61)
    for r in all_results:
        vs_bh = r["net"]*100 - r["bh"]
        print(f"{r['market']:<5} {r['scale']:<8} {r['encoder']:<12} {r['net']*100:<+9.2f}% {r['trades']:<8} {r['acc']*100:<7.1f}% {vs_bh:<+9.2f}%")
    print(f"{'A':<5} {'daily':<8} {'Buy&Hold':<12} {bha:<+9.2f}%")
    print(f"{'US':<5} {'daily':<8} {'Buy&Hold':<12} {bhu:<+9.2f}%")
    
    out = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out, exist_ok=True)
    json.dump(all_results, open(os.path.join(out, "v102_results.json"), "w"), indent=2)
    print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
