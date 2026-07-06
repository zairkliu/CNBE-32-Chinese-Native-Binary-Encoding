"""CNBE v10.7: Pretraining foundation model - CNBE as frozen embedding for Transformer"""
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, json, os, time

CFG = type("Cfg",(),{"hdim":128,"nlay":4,"nhead":4,"ff":256,"seq":16,"bs":64,"ep":50,
                      "lr":0.001,"device":"cuda" if torch.cuda.is_available() else "cpu",
                      "vocab":14})()
TOK = {"+":10,"-":11,"x":12,"=":13}

def cnbe_bits(tok_id):
    if tok_id<10: typ,val=0,tok_id
    elif tok_id in [10,11,12]: typ,val=1,tok_id-10
    else: typ,val=2,0
    c=(typ<<28)|(val<<24)
    return [(c>>i)&1 for i in range(32)]

class MathDataset(torch.utils.data.Dataset):
    def __init__(self,n=5000):
        self.data=[]
        np.random.seed(42)
        for _ in range(n*2):
            a=np.random.randint(0,10); b=np.random.randint(0,10)
            op=np.random.choice(["+","-","x"])
            ans={"+":a+b,"-":a-b,"x":a*b}[op]
            if ans<0 or ans>81: continue
            seq=[a,TOK[op],b,TOK["="]]+[int(d) for d in str(ans)]
            self.data.append(seq)
            if len(self.data)>=n: break
        maxlen=max(len(s) for s in self.data)
        self.data=[s+[0]*(maxlen-len(s)) for s in self.data]
    def __len__(self): return len(self.data)
    def __getitem__(self,i):
        s=self.data[i]; return torch.tensor(s[:-1]),torch.tensor(s[1:])

def make_embed(method,vocab,hdim):
    if method=="cnbe":
        t=torch.zeros(vocab,32)
        for i in range(vocab): t[i]=torch.tensor(cnbe_bits(i))
        e=nn.Embedding.from_pretrained(t,freeze=True)
        p=nn.Linear(32,hdim); p.weight.requires_grad=False; return nn.Sequential(e,p)
    elif method=="learned": return nn.Embedding(vocab,hdim)
    elif method=="onehot":
        return nn.Sequential(nn.Embedding.from_pretrained(torch.eye(vocab),freeze=True),
                             nn.Linear(vocab,hdim,bias=False))
    elif method=="random":
        return nn.Sequential(nn.Embedding.from_pretrained(torch.randn(vocab,32),freeze=True),
                             nn.Linear(32,hdim,bias=False))

class TinyGPT(nn.Module):
    def __init__(self,method):
        super().__init__()
        self.embed=make_embed(method,CFG.vocab,CFG.hdim)
        self.pos=nn.Embedding(CFG.seq,CFG.hdim)
        self.layers=nn.ModuleList()
        for _ in range(CFG.nlay):
            self.layers.append(nn.TransformerEncoderLayer(
                CFG.hdim,CFG.nhead,CFG.ff,batch_first=True,dropout=0.1))
        self.head=nn.Linear(CFG.hdim,CFG.vocab)
    def forward(self,x):
        b,s=x.shape
        x=self.embed(x)+self.pos(torch.arange(s,device=x.device))
        m=torch.triu(torch.full((s,s),float("-inf"),device=x.device),diagonal=1)
        for l in self.layers: x=l(x,src_mask=m)
        return self.head(x)

def run_exp(method):
    ds=MathDataset(3000); dl=torch.utils.data.DataLoader(ds,CFG.bs,shuffle=True)
    model=TinyGPT(method).to(CFG.device)
    opt=torch.optim.Adam(model.parameters(),CFG.lr)
    los=[]; t0=time.time()
    for ep in range(CFG.ep):
        model.train(); tl=0
        for x,y in dl:
            x,y=x.to(CFG.device),y.to(CFG.device)
            opt.zero_grad()
            l=F.cross_entropy(model(x).reshape(-1,CFG.vocab),y.reshape(-1))
            l.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1)
            opt.step(); tl+=l.item()*len(x)
        los.append(tl/len(ds))
        if (ep+1)%10==0: print(f"  [{method}] E{ep+1}: {los[-1]:.4f}")
    return {"losses":los,"final":float(los[-1]),"min":float(min(los)),
            "time":time.time()-t0,"init":float(los[0])}

def main():
    print("="*75)
    print("  CNBE v10.7: Pretraining Foundation Model (TinyGPT + Math)")
    print("="*75)
    ds=MathDataset(1); print(f"  Data samples: {len(MathDataset(3000))}")
    
    results={}
    for m in ["cnbe","learned","onehot","random"]:
        print(f"\n>>> {m.upper()}...")
        r=run_exp(m); results[m]=r
        print(f"  {r['time']:.1f}s | Init:{r['init']:.4f} Final:{r['final']:.4f} Min:{r['min']:.4f}")
    
    print("\n"+"="*75); print("  FROZEN EMBEDDING COMPARISON"); print("="*75)
    print(f"{'Method':<10} {'Init':<12} {'Final':<12} {'Min':<12} {'Time':<8} {'vsRnd':<8}")
    base=results["random"]["min"]
    for m in ["cnbe","learned","onehot","random"]:
        r=results[m]; imp=(base-r["min"])/base*100 if base>0 else 0
        print(f"{m:<10} {r['init']:<12.4f} {r['final']:<12.4f} {r['min']:<12.4f} {r['time']:<8.1f} {imp:<+7.1f}%")
    
    out=os.path.join(os.path.dirname(__file__),"..","results","v107_results.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    json.dump(results,open(out,"w"))
    print(f"\nSaved to {out}")

if __name__=="__main__":
    main()
