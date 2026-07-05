import sys, os, json, time, numpy as np, torch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from v91_environment import TreeLifecycleEnvironment
from v91_tree_state import CNBEV91Encoder, RawV91Encoder, OneHotV91Encoder, RandomV91Encoder
from v91_jepa_model import JEPAV91Model, train_epoch, evaluate_survival

def run(enc_name, enc, n_trees=10, n_traj=30, steps=200, epochs=80, lr=0.001, seed=42):
    torch.manual_seed(seed)
    np.random.seed(seed)
    all_s, all_a, all_ns = [], [], []
    env = TreeLifecycleEnvironment(n_trees=n_trees, max_steps=steps)
    
    for t in range(n_traj):
        s, w, ns, _ = env.generate_trajectory(steps, seed=t * 100)
        for i in range(len(s)):
            all_s.append(enc.encode_state(s[i]))
            act = np.zeros(n_trees, dtype=np.float32)
            all_a.append(act)
            all_ns.append(enc.encode_state(ns[i]))
    
    ss = np.array(all_s); aa = np.array(all_a); nns = np.array(all_ns)
    input_dim = ss.shape[1]
    n = len(ss); n_train = int(n * 0.8)
    idx = np.random.permutation(n)
    
    model = JEPAV91Model(input_dim=input_dim, n_trees=n_trees)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    
    hist = {"train": [], "val": []}
    best_val = float("inf")
    for ep in range(epochs):
        tl = train_epoch(model, opt, ss[idx[:n_train]], aa[idx[:n_train]], nns[idx[:n_train]])
        model.eval()
        with torch.no_grad():
            s_v = torch.FloatTensor(ss[idx[n_train:]])
            a_v = torch.FloatTensor(aa[idx[n_train:]])
            ns_v = torch.FloatTensor(nns[idx[n_train:]])
            vl, _, _ = model(s_v, a_v, ns_v)
            vl = float(vl)
        hist["train"].append(tl); hist["val"].append(vl)
        best_val = min(best_val, vl)
        if (ep+1) % 20 == 0:
            print(f"  [{enc_name}] E{ep+1}  Train: {tl:.6f}  Val: {vl:.6f}")
    
    surv_acc = evaluate_survival(model, ss, aa, nns)
    return {"encoder": enc_name, "final_val": float(hist["val"][-1]), "min_val": best_val,
            "final_train": float(hist["train"][-1]), "input_dim": input_dim, "survival_acc": surv_acc,
            "history": hist}

def main():
    print("=" * 60)
    print("  CNBE-32 v9.1: Tree Lifecycle JEPA Prediction")
    print("  [Wind/Rain/Lightning/Lifecycle Simulation]")
    print("=" * 60)
    
    config = {"n_trees": 10, "n_traj": 30, "steps": 200, "epochs": 80, "lr": 0.001, "seed": 42}
    
    encoders = [
        ("CNBE", CNBEV91Encoder()),
        ("Raw", RawV91Encoder()),
        ("OneHot", OneHotV91Encoder()),
        ("Random", RandomV91Encoder(dim=32)),
    ]
    
    results = []
    for name, enc in encoders:
        print(f"\n>>> {name}...")
        t0 = time.time()
        try:
            r = run(name, enc, **config)
            r["time"] = time.time() - t0
            results.append(r)
            print(f"    Done in {r['time']:.1f}s | Val: {r['final_val']:.6f} | Sur: {r['survival_acc']:.3f}")
        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback; traceback.print_exc()
            results.append({"encoder": name, "error": str(e)})
    
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"{'Enc':<8} {'Dim':<6} {'Train':<12} {'Val':<12} {'MinVal':<12} {'Surv':<8}")
    print("-" * 58)
    best = None
    for r in results:
        if "error" in r:
            print(f"{r['encoder']:<8} ERROR: {r['error']}")
        else:
            print(f"{r['encoder']:<8} {r['input_dim']:<6} {r['final_train']:<12.6f} {r['final_val']:<12.6f} {r['min_val']:<12.6f} {r['survival_acc']:<8.3f}")
            if best is None or r["final_val"] < best["final_val"]:
                best = r
    if best:
        print(f"\nBEST: {best['encoder']} (Val: {best['final_val']:.6f})")
    
    out = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out, exist_ok=True)
    json.dump([{k: v for k, v in r.items() if k != "history"} for r in results],
              open(os.path.join(out, "v91_results.json"), "w"), indent=2)
    print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
