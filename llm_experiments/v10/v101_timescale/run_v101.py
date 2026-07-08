import sys, os, json, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F

# === Reuse v10.0 data generator ===
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "v100_backtest", "src"))
from generate_data_v100 import generate_month, TRADING_DAYS

# === Constants ===
SCALES = {"5min":5, "15min":15, "daily":240}
THRESHOLDS = {"5min":0.005, "15min":0.003, "daily":0.002}  # lower threshold = more sensitive at lower freq
EPOCHS = 50; COST = 0.0014  # A-share cost

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

def _feats(ohlcv):
    """Compute 10 features from OHLCV"""
    close,high,low,vol=ohlcv[:,3],ohlcv[:,1],ohlcv[:,2],ohlcv[:,4]
    n=len(close); feat=np.zeros((n,10))
    for i in range(n):
        ma5=np.mean(close[max(0,i-4):i+1]);ma20=np.mean(close[max(0,i-19):i+1])
        feat[i,0]=(close[i]-ma20)/ma20*100 if ma20>0 else 0
        tr=max(high[i]-low[i],abs(high[i]-close[max(0,i-1)]),abs(low[i]-close[max(0,i-1)])) if i>0 else high[i]-low[i]
        feat[i,1]=tr/close[i]*100
        feat[i,2]=(close[i]-close[max(0,i-5)])/close[max(0,i-5)]*100 if i>=5 else 0
        avg_v=np.mean(vol[max(0,i-19):i+1])
        feat[i,3]=vol[i]/max(avg_v,1)
        rets=[close[max(0,i-j)]/close[max(0,i-j-1)]-1 for j in range(min(5,i)) if close[max(0,i-j-1)]>0]
        neg=[r for r in rets if r<0]
        feat[i,4]=abs(np.mean(neg))*100 if neg else 0
        feat[i,5]=np.clip(np.random.randn()*0.3+0.5,0,1)
        feat[i,6]=min(i/(n/4),3)
        feat[i,7]=abs(close[i]-close[i-1])/close[i-1]*100 if i>0 else 0
        ma=np.mean(close[max(0,i-19):i+1]);std=np.std(close[max(0,i-19):i+1]) if i>=20 else 1
        feat[i,8]=(close[i]-ma)/max(std,0.01)
        dp=np.mean([max(close[max(0,i-j)]-close[max(0,i-j-1)],0) for j in range(min(14,i))]) if i>=14 else 0.1
        dn=np.mean([max(close[max(0,i-j-1)]-close[max(0,i-j)],0) for j in range(min(14,i))]) if i>=14 else 0.1
        feat[i,9]=abs(dp-dn)/max(dp+dn,0.01)*100 if (dp+dn)>0 else 0
    for j in range(10):
        mn,mx=feat[:,j].min(),feat[:,j].max()
        if mx-mn>0: feat[:,j]=(feat[:,j]-mn)/(mx-mn)
    return feat

def aggregate_scale(day_data, scale_min):
    """Aggregate 1min data to target scale (5min/15min/daily)"""
    ohlcv=day_data["ohlcv"]; step=scale_min
    n=len(ohlcv); n_bars=n//step
    if n_bars<3: return None  # too few bars
    
    agg=np.zeros((n_bars,5))
    for b in range(n_bars):
        chunk=ohlcv[b*step:(b+1)*step]
        agg[b,0]=chunk[0,0]  # open = first
        agg[b,1]=chunk[:,1].max()  # high
        agg[b,2]=chunk[:,2].min()  # low
        agg[b,3]=chunk[-1,3]  # close = last
        agg[b,4]=chunk[:,4].sum()  # volume sum
    
    feats=_feats(agg)
    return {"close":agg[:,3].copy(),"features":feats,"ohlcv":agg}

def run_scale(scale_name, data, enc_name, threshold):
    """Run backtest for one scale-encoding combination"""
    enc_fn=ENC[enc_name]; scale_min=SCALES[scale_name]
    results=[]
    for day,d in data.items():
        ad=aggregate_scale(d,scale_min)
        if ad is None: continue
        feats=ad["features"]; close=ad["close"]; n=len(feats)
        if n<10: continue
        
        enc=enc_fn(feats); sp=max(int(n*0.7),5)
        xs=enc[:sp-1]; ys=enc[1:sp]
        if len(xs)<5: continue
        
        m=Predictor(xs.shape[1],ys.shape[1]); o=torch.optim.Adam(m.parameters(),lr=0.001)
        for _ in range(EPOCHS):
            idx=np.random.permutation(len(xs))
            for s in range(0,len(xs),min(16,len(xs))):
                e=min(s+16,len(xs)); ids=idx[s:e]
                x=torch.FloatTensor(xs[ids]);y=torch.FloatTensor(ys[ids]);a=torch.zeros(len(ids),1)
                o.zero_grad();F.mse_loss(m(x,a),y).backward()
                nn.utils.clip_grad_norm_(m.parameters(),1);o.step()
        
        m.eval(); cp=close[sp:n]; ar=np.diff(cp)/cp[:-1]
        trades=[]; eq=[1.0]; pos=0
        for i in range(sp,n-1):
            nxt=m(torch.FloatTensor(enc[i:i+1]),torch.zeros(1,1))
            diff=nxt[0,0].item()-float(enc[i,0])
            if abs(diff)>threshold:
                sig=1 if diff>0 else (-1 if not True else max(0,1 if diff>0 else -1))
                sig=max(0,1 if diff>0 else -1)  # A-share long only
                if sig!=pos:
                    if pos:eq[-1]*=(1-COST)
                    pos=sig;eq[-1]*=(1-COST)
                trades.append(sig)
            if pos: eq.append(eq[-1]*(1+ar[i-sp]*pos))
            else: eq.append(eq[-1])
        if pos:eq[-1]*=(1-COST)
        
        net=eq[-1]-1.0
        correct=sum(1 for i in range(min(len(trades),len(ar))) if trades[i]*ar[i]>0)
        acc=correct/max(len(trades),1)
        results.append({"day":day,"net":float(net),"trades":len(trades),"acc":acc,"scale":scale_name})
    return results

def main():
    print("="*70)
    print("  CNBE v10.1: A-Share Multi-Scale Backtest")
    print("="*70)
    t0=time.time()
    
    print("\nGenerating A-share 1min data...")
    a_data=generate_month("A",240,3800.0)
    print(f"  {len(a_data)} days in {time.time()-t0:.1f}s")
    
    all_results=[]
    for scale_name in ["5min","15min","daily"]:
        th=THRESHOLDS[scale_name]
        print(f"\n--- {scale_name} (threshold={th}) ---")
        for enc in ["CNBE-Abl2","Raw"]:
            rr=run_scale(scale_name,a_data,enc,th)
            tr=sum(r["net"] for r in rr); sr=np.mean([r["net"] for r in rr])/max(np.std([r["net"] for r in rr]),1e-8)*np.sqrt(252)
            md=min(r["net"] for r in rr); ac=np.mean([r["acc"] for r in rr])
            td=sum(r["trades"] for r in rr)
            for r in rr: r["encoder"]=enc
            all_results.extend(rr)
            print(f"  {enc:<12} Ret:{tr*100:+6.2f}% Sharpe:{sr:5.2f} MaxDD:{md*100:+6.2f}% Acc:{ac*100:5.1f}% Trades:{td}")
    
    # Buy & Hold
    bhr=np.mean([(d["close"][-1]/d["close"][0]-1)*100 for _,d in a_data.items()])
    print(f"\n  Buy&Hold: {bhr:+6.2f}%")
    
    # Summary
    print("\n"+"="*70); print("  MULTI-SCALE SUMMARY"); print("="*70)
    print(f"{'Scale':<8} {'Enc':<12} {'NetRet':<10} {'Sharpe':<8} {'MaxDD':<10} {'Acc':<8} {'Trades':<8}")
    print("-"*64)
    for sc in ["5min","15min","daily"]:
        for enc in ["CNBE-Abl2","Raw"]:
            rr=[r for r in all_results if r["scale"]==sc and r["encoder"]==enc]
            tr=sum(r["net"] for r in rr); sr=np.mean([r["net"] for r in rr])/max(np.std([r["net"] for r in rr]),1e-8)*np.sqrt(252)
            md=min(r["net"] for r in rr); ac=np.mean([r["acc"] for r in rr]); td=sum(r["trades"] for r in rr)
            print(f"{sc:<8} {enc:<12} {tr*100:<+9.2f}% {sr:<8.2f} {md*100:<9.2f}% {ac*100:<7.1f}% {td:<8}")
    print(f"{'--':<8} {'Buy&Hold':<12} {bhr:<+9.2f}%")
    
    out=os.path.join(os.path.dirname(__file__),"results")
    os.makedirs(out,exist_ok=True); json.dump(all_results,open(os.path.join(out,"v101_results.json"),"w"),indent=2)
    print(f"\nSaved {len(all_results)} to {out}")

if __name__=="__main__":
    main()
