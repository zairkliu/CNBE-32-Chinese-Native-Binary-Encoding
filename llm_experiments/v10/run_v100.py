import sys, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from generate_data_v100 import generate_month

EPOCHS = 30; THRESHOLD = 0.005

class Predictor(nn.Module):
    def __init__(self, inp, out):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(inp+1,64),nn.ReLU(),nn.Linear(64,32),nn.ReLU(),nn.Linear(32,out))
    def forward(self,x,a): return self.net(torch.cat([x,a],-1))

def encode_cnbe(feats, zero=None):
    codes=np.zeros((len(feats),1))
    for i in range(len(feats)):
        f=feats[i].copy()
        if zero:
            for z in zero: f[z]=0
        c=0
        c|=(min(int(f[0]*15),15)&0xF)<<28;c|=(min(int(f[1]*15),15)&0xF)<<24
        c|=(min(int(f[2]*15),15)&0xF)<<20;c|=(min(int(f[3]*15),15)&0xF)<<16
        c|=(min(int(f[4]*15),15)&0xF)<<12;c|=(min(int(f[5]*15),15)&0xF)<<8
        c|=(min(int(f[6]*3),3)&0x3)<<6;c|=(min(int(f[7]*3),3)&0x3)<<4
        c|=(min(int(f[8]*3),3)&0x3)<<2;c|=(min(int(f[9]*3),3)&0x3)
        codes[i]=float(c)/4294967295.0
    return codes

ENC={"CNBE-Abl2": lambda f:encode_cnbe(f,[1,2]),"Raw":lambda f:f.astype(np.float32)}
COST={"US":0.0002,"A":0.0014}

def run_day(feats,close,enc_name,is_a):
    enc=ENC[enc_name](feats); n=len(feats); sp=int(n*0.8); cost=COST["A" if is_a else "US"]
    xs=enc[:sp-1]; ys=enc[1:sp]
    m=Predictor(xs.shape[1],ys.shape[1]); o=torch.optim.Adam(m.parameters(),lr=0.001)
    for _ in range(EPOCHS):
        idx=np.random.permutation(len(xs))
        for s in range(0,len(xs),32):
            e=min(s+32,len(xs)); ids=idx[s:e]
            x=torch.FloatTensor(xs[ids]);y=torch.FloatTensor(ys[ids]);a=torch.zeros(len(ids),1)
            o.zero_grad();F.mse_loss(m(x,a),y).backward()
            nn.utils.clip_grad_norm_(m.parameters(),1);o.step()
    
    m.eval(); cp=close[sp:n]; ar=np.diff(cp)/cp[:-1]
    trades=[]; eq=[1.0]; pos=0
    for i in range(sp,n-1):
        nxt=m(torch.FloatTensor(enc[i:i+1]),torch.zeros(1,1))
        diff=(nxt[0,0]-enc[i,0]).detach().item() if hasattr(nxt[0,0],"item") else float(nxt[0,0])-float(enc[i,0])
        if abs(diff)>THRESHOLD:
            sig=1 if diff>0 else -1
            if is_a: sig=max(0,sig)
            if sig!=pos:
                if pos:eq[-1]*=(1-cost)
                pos=sig;eq[-1]*=(1-cost)
            trades.append(sig)
        if pos: eq.append(eq[-1]*(1+ar[i-sp]*pos))
        else: eq.append(eq[-1])
    if pos:eq[-1]*=(1-cost)
    
    net=eq[-1]-1.0
    correct=sum(1 for i in range(min(len(trades),len(ar))) if trades[i]*ar[i]>0)
    acc=correct/max(len(trades),1)
    pos_pred=sum(1 for t in trades if t>0)/max(len(trades),1)
    return {"net":float(net),"trades":len(trades),"acc":acc,"pos_ratio":pos_pred}

def main():
    print("="*70)
    print("  CNBE v10.0: Backtest + Cross-Market")
    print(f"  Threshold: {THRESHOLD}")
    print("="*70)
    t0=time.time()
    us_data=generate_month("US",390,5300.0)
    a_data=generate_month("A",240,3800.0)
    print(f"Data: {time.time()-t0:.1f}s")
    
    all_r=[]
    for mkt,data,ia in [("US",us_data,False),("A",a_data,True)]:
        print(f"\n--- {mkt} ---")
        for enc in ["CNBE-Abl2","Raw"]:
            dr=[]; days=list(data.keys())
            for dk in days:
                dd=data[dk]; rr=run_day(dd["features"],dd["close"],enc,ia)
                rr["day"]=dk; rr["market"]=mkt; rr["encoder"]=enc; dr.append(rr)
            tr=sum(r["net"] for r in dr); sr=np.mean([r["net"] for r in dr])/max(np.std([r["net"] for r in dr]),1e-8)*np.sqrt(252)
            md=min(r["net"] for r in dr); ac=np.mean([r["acc"] for r in dr])
            trd=sum(r["trades"] for r in dr)

            all_r.extend(dr)
            print(f"  {enc:<12} Ret:{tr*100:+6.2f}% Sharpe:{sr:5.2f} MaxDD:{md*100:+6.2f}% Acc:{ac*100:5.1f}% Trades:{trd}")
    
    print("\n"+"="*70); print("  SUMMARY"); print("="*70)
    for mkt,data in [("US",us_data),("A",a_data)]:
        bhr=np.mean([(d["close"][-1]/d["close"][0]-1)*100 for _,d in data.items()])
        print(f"{mkt} Buy&Hold: {bhr:+6.2f}%")
    
    out=os.path.join(os.path.dirname(__file__),"results")
    os.makedirs(out,exist_ok=True); json.dump(all_r,open(os.path.join(out,"v100_results.json"),"w"),indent=2)
    print(f"Saved {len(all_r)} to {out}")

if __name__=="__main__":
    main()

