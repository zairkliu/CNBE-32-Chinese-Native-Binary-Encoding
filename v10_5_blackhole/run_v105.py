import sys, os, json, time, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from physics_engine import BlackHole, generate_spacetime_samples

N=1000; TARGETS=["redshift","tidal","deflection"]
ENCS=["cnbe","raw","onehot","random"]

class BHEncoder:
    """Fixed encoders - no data leakage (input only: r_schwarzschild)"""
    def encode(self, samples, method):
        rs=np.array([s["r_schwarzschild"] for s in samples])
        if method=="cnbe":
            codes=np.zeros((len(samples),32))
            for i,r in enumerate(rs):
                code=int((r-1)/99*255)&0xFF
                for b in range(8):
                    codes[i,b]=float((code>>b)&1)
            return codes
        elif method=="raw":
            return rs.reshape(-1,1)
        elif method=="onehot":
            nb=20; oh=np.zeros((len(samples),nb))
            for i,r in enumerate(rs):
                oh[i,min(int((r-1)/99*nb),nb-1)]=1.0
            return oh
        elif method=="random":
            return np.random.randn(len(samples),32)
        raise ValueError(f"Unknown: {method}")

def main():
    print("="*70)
    print("  CNBE-32 v10.5: Black Hole Gravitational Field (Gaia BH1)")
    print("  Input: r/Rs  |  Predict: redshift / tidal / deflection")
    print("="*70)
    t0=time.time()
    
    bh=BlackHole()
    samples=generate_spacetime_samples(bh,N,1.5,100.0)
    print(f"\nGaia BH1: {bh.mass_solar}M*  Rs={bh.schwarzschild_radius_km:.1f}km  Samples={len(samples)}")
    
    enc=BHEncoder()
    all_r={}
    for target in TARGETS:
        print(f"\n--- {target.upper()} ---")
        y=np.array([s[target] for s in samples])
        
        for method in ENCS:
            X=enc.encode(samples,method)
            Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.2,random_state=42)
            knn=KNeighborsRegressor(n_neighbors=5).fit(Xtr,ytr)
            yp=knn.predict(Xte)
            mse=mean_squared_error(yte,yp); r2=r2_score(yte,yp)
            all_r[f"{method}_{target}"]={"mse":float(mse),"r2":float(r2)}
            print(f"  {method:>8}: MSE={mse:.6f}  R2={r2:.4f}")
        
        cm=all_r[f"cnbe_{target}"]["mse"]; rm=all_r[f"raw_{target}"]["mse"]
        print(f"  CNBE vs Raw: {(rm-cm)/rm*100 if rm>0 else 0:+.1f}%")
    
    print(f"\nTime: {time.time()-t0:.1f}s")
    print("\n"+"="*70); print("  RESULTS"); print("="*70)
    print(f"{'Method':>8} ",end="")
    for t in TARGETS: print(f"  {t[:4]} MSE  {t[:4]} R2 ",end="")
    print(f"\n{'-'*55}")
    for m in ENCS:
        print(f"{m:>8} ",end="")
        for t in TARGETS:
            r=all_r[f"{m}_{t}"]
            print(f" {r['mse']:.6f} {r['r2']:.4f} ",end="")
        print()
    
    out=os.path.join(os.path.dirname(__file__),"results","v105_results.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    json.dump(all_r,open(out,"w"),indent=2)
    print(f"\nSaved to {out}")

if __name__=="__main__":
    main()
