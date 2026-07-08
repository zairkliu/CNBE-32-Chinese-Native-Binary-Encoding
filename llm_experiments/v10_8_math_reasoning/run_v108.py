import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, json, os, time

CFG = type("Cfg",(),{"H":128,"L":4,"Hd":4,"FF":256,"B":64,"EP":30,"LR":0.001,
                      "DEV":"cuda" if torch.cuda.is_available() else "cpu","V":20,"N":2000})()
TASKS=["parity","prime","seq"]

def cnbe_bits(tid):
    if tid==0: return [0]*32
    if tid<11: return [(0<<28|(tid if tid<10 else 0)<<24)>>b&1 for b in range(32)]
    if tid<14: return [(1<<28|(tid-11)<<24)>>b&1 for b in range(32)]
    if tid==14: return [(2<<28)>>b&1 for b in range(32)]
    if tid==15: return [(3<<28)>>b&1 for b in range(32)]
    return [(4<<28|(tid-16)<<24)>>b&1 for b in range(32)]

def is_prime(n):
    if n<2: return False
    for i in range(2,int(n**0.5)+1):
        if n%i==0: return False
    return True

def mk_emb(m,V,H):
    if m=="cnbe":
        t=torch.zeros(V,32)
        for i in range(V): t[i]=torch.tensor(cnbe_bits(i))
        return nn.Sequential(nn.Embedding.from_pretrained(t,freeze=True),nn.Linear(32,H,bias=False))
    elif m=="learned": return nn.Embedding(V,H)
    elif m=="onehot":
        return nn.Sequential(nn.Embedding.from_pretrained(torch.eye(V),freeze=True),nn.Linear(V,H,bias=False))
    elif m=="random":
        return nn.Sequential(nn.Embedding.from_pretrained(torch.randn(V,32),freeze=True),nn.Linear(32,H,bias=False))

class TinyGPT(nn.Module):
    def __init__(self,m):
        super().__init__()
        self.emb=mk_emb(m,CFG.V,CFG.H)
        self.pos=nn.Embedding(12,CFG.H)
        self.lays=nn.ModuleList([nn.TransformerEncoderLayer(CFG.H,CFG.Hd,CFG.FF,batch_first=True,dropout=0.1) for _ in range(CFG.L)])
        self.head=nn.Linear(CFG.H,CFG.V)
    def forward(self,x):
        b,s=x.shape
        x=self.emb(x)+self.pos(torch.arange(s,device=x.device))
        m=torch.triu(torch.full((s,s),float("-inf"),device=x.device),diagonal=1)
        for l in self.lays: x=l(x,src_mask=m)
        return self.head(x)

def gen_parity(n):
    X,Y=[],[]
    np.random.seed(42)
    for _ in range(n*2):
        a=np.random.randint(0,10); b=np.random.randint(0,10)
        par=(a+b)%2
        seq=[a or 10,11,b or 10,14,16 if par==0 else 17]
        X.append(seq[:-1]); Y.append(seq[1:])
        if len(X)>=n: break
    return X,Y

def gen_prime(n):
    X,Y=[],[]
    np.random.seed(42)
    for _ in range(n*2):
        a=np.random.randint(0,10); b=np.random.randint(0,10)
        ans=a+b; pr=is_prime(ans)
        seq=[a or 10,11,b or 10,14,18 if pr else 19]
        X.append(seq[:-1]); Y.append(seq[1:])
        if len(X)>=n: break
    return X,Y

def gen_seq(n):
    X,Y=[],[]
    np.random.seed(42)
    for _ in range(n*2):
        s=np.random.randint(0,5)
        seq=[(s+i)or 10 for i in range(5)]+[14]
        seq.append((s+5)%10 or 10)
        X.append(seq[:-1]); Y.append(seq[1:])
        if len(X)>=n: break
    return X,Y

def run_task(task,m):
    gens={"parity":gen_parity,"prime":gen_prime,"seq":gen_seq}
    X,Y=gens[task](CFG.N)
    maxl=max(len(s) for s in X)
    Xp=torch.tensor([s+[0]*(maxl-len(s)) for s in X])
    Yp=torch.tensor([s+[0]*(maxl-len(s)) for s in Y])
    ds=torch.utils.data.TensorDataset(Xp,Yp)
    dl=torch.utils.data.DataLoader(ds,CFG.B,shuffle=True)
    
    model=TinyGPT(m).to(CFG.DEV)
    opt=torch.optim.Adam(model.parameters(),CFG.LR)
    los=[]; t0=time.time()
    for ep in range(CFG.EP):
        model.train(); tl=0
        for x,y in dl:
            x,y=x.to(CFG.DEV),y.to(CFG.DEV)
            opt.zero_grad()
            l=F.cross_entropy(model(x).reshape(-1,CFG.V),y.reshape(-1))
            l.backward(); nn.utils.clip_grad_norm_(model.parameters(),1)
            opt.step(); tl+=l.item()*len(x)
        los.append(tl/len(ds))
        if (ep+1)%10==0: print(f"  [{m}] {task} E{ep+1}: {los[-1]:.4f}")
    return {"final":float(los[-1]),"min":float(min(los)),"time":time.time()-t0}

def main():
    print("="*75)
    print("  CNBE v10.8: Pure Math Reasoning Foundation Validation")
    print(f"  TinyGPT ({CFG.L}L/{CFG.Hd}H/{CFG.H}D) | Tasks: Parity/Prime/Seq | {CFG.N} samples")
    print("="*75)
    
    results={}
    for task in TASKS:
        print(f"\n--- {task.upper()} ---")
        for m in ["cnbe","learned","onehot","random"]:
            r=run_task(task,m); results[f"{m}_{task}"]=r
            print(f"  {m}: {r['time']:.1f}s | final={r['final']:.4f} min={r['min']:.4f}")
    
    print("\n"+"="*75); print("  FINAL LOSS"); print("="*75)
    print(f"{'Task':<10} {'CNBE':<12} {'Learn':<12} {'OneHot':<12} {'Random':<12}")
    for t in TASKS:
        print(f"{t:<10} ",end="")
        for m in ["cnbe","learned","onehot","random"]:
            print(f"{results[f'{m}_{t}']['final']:<12.4f}",end="")
        print()
    
    print(f"\n{'='*75}\n  MIN LOSS\n{'='*75}")
    print(f"{'Task':<10} {'CNBE':<12} {'Learn':<12} {'OneHot':<12} {'Random':<12}")
    for t in TASKS:
        print(f"{t:<10} ",end="")
        for m in ["cnbe","learned","onehot","random"]:
            print(f"{results[f'{m}_{t}']['min']:<12.4f}",end="")
        print()
    
    out=os.path.join(os.path.dirname(__file__),"results","v108_results.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    json.dump(results,open(out,"w"))
    print(f"\nSaved: {out}")

if __name__=="__main__":
    main()

