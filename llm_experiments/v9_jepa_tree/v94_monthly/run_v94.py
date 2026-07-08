import sys, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from generate_month_data import generate_month, TRADING_DAYS

SEEDS = [42, 123]
MAX_EPOCHS = 50
PATIENCE = 10

# ===== JEPA Model =====
class JEPAModel(nn.Module):
    def __init__(self, input_dim, latent=64):
        super().__init__()
        self.ctx = nn.Sequential(nn.Linear(input_dim,64),nn.ReLU(),nn.Linear(64,32),nn.ReLU(),nn.Linear(32,latent))
        self.tgt = nn.Sequential(nn.Linear(input_dim,64),nn.ReLU(),nn.Linear(64,32),nn.ReLU(),nn.Linear(32,latent))
        self.pred = nn.Sequential(nn.Linear(latent+1,32),nn.ReLU(),nn.Linear(32,latent))
        self.ema=0.99
        for pq,pk in zip(self.ctx.parameters(),self.tgt.parameters()):
            pk.data.copy_(pq.data); pk.requires_grad=False
    def update(self):
        with torch.no_grad():
            for pq,pk in zip(self.ctx.parameters(),self.tgt.parameters()):
                pk.data=self.ema*pk.data+(1-self.ema)*pq.data
    def forward(self,x,a,y):
        z=self.ctx(x); zp=self.pred(torch.cat([z,a],-1))
        with torch.no_grad(): zt=self.tgt(y)
        return F.mse_loss(zp,zt)

# ===== Encoders =====
def encode_cnbe(feats, zero_feats=None):
    """Encode features to 32-bit CNBE code, optionally zeroing some fields"""
    codes = np.zeros((len(feats),1))
    for i in range(len(feats)):
        f=feats[i].copy()
        if zero_feats:
            for idx in zero_feats: f[idx]=0
        code=0
        code|=(min(int(f[0]*15),15)&0xF)<<28
        code|=(min(int(f[1]*15),15)&0xF)<<24
        code|=(min(int(f[2]*15),15)&0xF)<<20
        code|=(min(int(f[3]*15),15)&0xF)<<16
        code|=(min(int(f[4]*15),15)&0xF)<<12
        code|=(min(int(f[5]*15),15)&0xF)<<8
        code|=(min(int(f[6]*3),3)&0x3)<<6
        code|=(min(int(f[7]*3),3)&0x3)<<4
        code|=(min(int(f[8]*3),3)&0x3)<<2
        code|=(min(int(f[9]*3),3)&0x3)
        codes[i]=float(code)/4294967295.0
    return codes

ENC={
    "CNBE-Full": lambda f: encode_cnbe(f),
    "Abl-2": lambda f: encode_cnbe(f, zero_feats=[1,2]),
    "Abl-5": lambda f: encode_cnbe(f, zero_feats=[8,9]),
    "Raw": lambda f: f.astype(np.float32),
}

def run_day(day, feats, total_results):
    """Run all encodings and seeds for one day"""
    for enc_name, enc_fn in ENC.items():
        for seed in SEEDS:
            torch.manual_seed(seed); np.random.seed(seed)
            xs=enc_fn(feats[:-1]); ys=enc_fn(feats[1:])
            n=len(xs); idx=np.random.permutation(n); n_train=int(n*0.8)
            chg=feats[:-1,2]; vol=feats[:-1,1]
            acts=np.zeros((n,1))
            for i in range(n):
                acts[i]=2 if(abs(chg[i])>0.5 or vol[i]>0.5)else(1 if(abs(chg[i])>0.2 or vol[i]>0.2)else 0)
            
            model=JEPAModel(xs.shape[1]); opt=torch.optim.Adam(model.parameters(),lr=0.001)
            best_val=float("inf"); best_ep=0
            t0=time.time()
            for ep in range(MAX_EPOCHS):
                model.train()
                for s in range(0,n_train,16):
                    e=min(s+16,n_train); ids=idx[s:e]
                    x=torch.FloatTensor(xs[ids]); a=torch.FloatTensor(acts[ids]); y=torch.FloatTensor(ys[ids])
                    opt.zero_grad(); loss=model(x,a,y)
                    loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),1)
                    opt.step(); model.update()
                model.eval()
                with torch.no_grad():
                    vl=model(torch.FloatTensor(xs[idx[n_train:]]),torch.FloatTensor(acts[idx[n_train:]]),torch.FloatTensor(ys[idx[n_train:]])).item()
                if vl<best_val: best_val=vl; best_ep=ep
                if ep-best_ep>PATIENCE: break
            
            dt=time.time()-t0
            total_results.append({
                "day":day,"enc":enc_name,"seed":seed,
                "val":vl,"min_val":best_val,"best_ep":best_ep,
                "dim":xs.shape[1],"time":round(dt,2)
            })

def main():
    print("="*65)
    print("  CNBE-32 v9.4: Cross-Period Robustness (June 2026 Full Month)")
    print("="*65)
    
    print("\nGenerating monthly data...")
    t0=time.time()
    all_data=generate_month()
    print(f"  {len(all_data)} days generated in {time.time()-t0:.1f}s")
    
    total_results=[]
    for day,data in all_data.items():
        print(f"\n>>> {day} ({data['regime']})...",end="",flush=True)
        run_day(day,data["features"],total_results)
        print(f" done ({len([r for r in total_results if r['day']==day])} exps)")
    
    # Compute summary
    print("\n"+"="*65); print("  MONTHLY SUMMARY"); print("="*65)
    
    summary={}
    for enc in ENC:
        day_results={}
        vals=[]; min_vals=[]; raw_div=0
        for day in TRADING_DAYS:
            dr=[r for r in total_results if r["day"]==day and r["enc"]==enc]
            if dr:
                mv=np.mean([r["min_val"] for r in dr])
                day_results[day]=mv
                vals.append(mv)
                if enc=="Raw" and mv>1.0: raw_div+=1
        
        mn=np.mean(vals); sd=np.std(vals)
        summary[enc]={"mean":float(mn),"std":float(sd),"max":float(max(vals)),
                      "daily":day_results}
        if enc=="Raw": summary[enc]["div_days"]=raw_div
    
    # Ranking consistency
    abl2_wins=0; full_wins=0; total_days=0
    for day in TRADING_DAYS:
        d={enc:np.mean([r["min_val"] for r in total_results if r["day"]==day and r["enc"]==enc]) for enc in ENC}
        if d["Abl-2"]<d["CNBE-Full"]: abl2_wins+=1
        elif d["CNBE-Full"]<d["Abl-2"]: full_wins+=1
        total_days+=1
    
    print(f"{'Encoding':<14} {'Mean Loss':<12} {'Std Dev':<12} {'Max Loss':<12}")
    print("-"*50)
    best_enc=None
    for enc in ENC:
        s=summary[enc]
        line=f"{enc:<14} {s['mean']:<12.6f} {s['std']:<12.6f} {s['max']:<12.6f}"
        if best_enc is None or s["mean"]<summary[best_enc]["mean"]: best_enc=enc
        print(line)
    print(f"\nBEST: {best_enc} (mean={summary[best_enc]['mean']:.6f})")
    print(f"Abl-2 wins vs Full: {abl2_wins}/{total_days} ({abl2_wins/total_days*100:.0f}%)")
    print(f"Raw divergence days: {summary['Raw'].get('div_days',0)}/{total_days}")
    
    # Save results
    out=os.path.join(os.path.dirname(__file__),"results")
    os.makedirs(out,exist_ok=True)
    json.dump({"experiments":total_results,"summary":summary}, 
              open(os.path.join(out,"v94_results.json"),"w"),indent=2)
    print(f"\nSaved to {out}")

if __name__=="__main__":
    main()
