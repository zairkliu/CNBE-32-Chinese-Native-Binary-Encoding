"""CNBE v10.6: Social info distribution & decision center simulation (numpy only)"""
import numpy as np, json, os, time
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import kendalltau

# ===== City Simulator =====
REGIONS = ["CBD","OldCity","HiTech","UniTown","Industry","NewCity","EcoPark","TransitHub"]
TIMES = ["Dawn","Day","Rush","Night"]
RTYPES = ["commercial","residential","tech","education","industrial","mixed","ecological","transport"]

PARAMS = {"commercial":{"tb":200,"ls":0.5,"iv":0.3},"residential":{"tb":100,"ls":0.8,"iv":0.7},
          "tech":{"tb":100,"ls":0.5,"iv":0.3},"education":{"tb":80,"ls":0.5,"iv":0.3},
          "industrial":{"tb":150,"ls":0.5,"iv":0.7},"mixed":{"tb":100,"ls":0.8,"iv":0.3},
          "ecological":{"tb":80,"ls":0.5,"iv":0.3},"transport":{"tb":200,"ls":0.5,"iv":0.3}}
TF = [0.4,1.0,1.8,0.3]

def gen_data(n_days=30, seed=42):
    np.random.seed(seed)
    arr=np.zeros((n_days*8*4,7))
    row=0
    for d in range(n_days):
        for ri in range(8):
            tp=RTYPES[ri]; p=PARAMS[tp]
            for ti in range(4):
                tr=np.clip(p["tb"]*TF[ti]+np.random.normal(0,20),0,255)
                lv=np.clip(50+np.random.normal(0,10)-(30 if np.random.random()<0.05 else 0),0,100)
                inf=np.clip(80+np.random.normal(0,5)-(40 if np.random.random()<0.02 else 0),0,100)
                env=int(np.clip((12 if tp in ["industrial","transport"] else (3 if tp=="ecological" else 8))+np.random.normal(0,2),0,15))
                em=0
                if tr>200: em=1
                elif lv<20: em=2
                elif inf<30: em=3
                elif env>13: em=4
                if sum([tr>180,lv<30,inf<40,env>12])>=2: em=5
                arr[row]=[ri,ti,tr,lv,inf,env,em]; row+=1
    return arr

# ===== CNBE Encoder =====
def encode_cnbe(data_row):
    ri,ti,tr,lv,inf,env,em=[int(data_row[i]) for i in range(7)]
    code=0
    code|=(min(tr,255)&0xFF)<<24
    code|=(min(lv,63)&0x3F)<<18
    code|=(min(inf,63)&0x3F)<<12
    code|=(min(env,15)&0xF)<<8
    code|=(min(em,7)&0x7)<<5
    code|=(min(ri,7)&0x7)<<2
    code|=(min(ti,3)&0x3)
    return code

def prep(data, method):
    if method=="cnbe":
        bits=np.zeros((len(data),32))
        for i in range(len(data)):
            c=encode_cnbe(data[i])
            for b in range(32): bits[i,b]=float((c>>b)&1)
        return bits
    elif method=="raw":
        X=data[:,:7].copy()
        mn,mx=X.min(0),X.max(0); mx=np.where(mx-mn==0,mn+1,mx)
        return (X-mn)/(mx-mn)
    elif method=="onehot":
        n=len(data); oh=np.zeros((n,8+4+8+40))
        for i in range(n):
            ri,ti,em=[int(data[i,j]) for j in [0,1,6]]
            oh[i,ri]=1; oh[i,8+ti]=1; oh[i,12+em]=1
            for jj,val in enumerate([data[i,2],data[i,3],data[i,4],data[i,5]]):
                bidx=min(int((val-0)/(255-0)*10),9); oh[i,20+jj*10+bidx]=1
        return oh
    elif method=="random":
        return np.random.randn(len(data),32)

# ===== Experiment Runner =====
TASKS={"prediction":0,"ranking":None,"alert":None}
ENCS=["cnbe","raw","onehot","random"]

def main():
    print("="*70)
    print("  CNBE v10.6: Social Decision Center Simulation")
    print("="*70)
    t0=time.time()
    data=gen_data(30,42)
    print(f"  {len(data)} records ({len(data)//32} days x 8 regions x 4 slots) in {time.time()-t0:.1f}s")
    
    results={}
    for task in ["prediction","ranking","alert"]:
        print(f"\n--- {task.upper()} ---")
        y=np.zeros(len(data))
        if task=="prediction":
            y=data[:,2]/255.0  # traffic as target
        elif task=="ranking":
            y=(data[:,2]/255)*0.4+(1-data[:,3]/100)*0.3+(1-data[:,4]/100)*0.2+(data[:,5]/15)*0.1
        elif task=="alert":
            y=((data[:,6]>0)|((data[:,2]/255)*0.4+(1-data[:,3]/100)*0.3+(1-data[:,4]/100)*0.2+(data[:,5]/15)*0.1>0.7)).astype(int)
        
        for enc in ENCS:
            X=prep(data,enc)
            Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.2,random_state=42)
            knn=KNeighborsRegressor(n_neighbors=5).fit(Xtr,ytr)
            yp=knn.predict(Xte)
            
            if task=="prediction":
                mse=mean_squared_error(yte,yp); r2=r2_score(yte,yp)
                results[f"{enc}_{task}"]={"mse":float(mse),"r2":float(r2)}
                print(f"  {enc:>8}: MSE={mse:.6f} R2={r2:.4f}")
            elif task=="ranking":
                tau,_=kendalltau(yte,yp)
                results[f"{enc}_{task}"]={"tau":float(tau)}
                print(f"  {enc:>8}: tau={tau:.4f}")
            elif task=="alert":
                acc=np.mean((yp>0.5).astype(int)==yte)
                results[f"{enc}_{task}"]={"acc":float(acc)}
                print(f"  {enc:>8}: Acc={acc:.4f}")
        
        cm=results[f"cnbe_{task}"]; rm=results[f"raw_{task}"]
        if task=="prediction": imp=(rm["mse"]-cm["mse"])/rm["mse"]*100
        elif task=="ranking": imp=(cm["tau"]-rm["tau"])/abs(rm["tau"])*100
        else: imp=(cm["acc"]-rm["acc"])/rm["acc"]*100
        print(f"  CNBE vs Raw: {imp:+.1f}%")
    
    print("\n"+"="*70); print("  SUMMARY"); print("="*70)
    print(f"{'Method':>8} ",end="")
    for t in ["prediction","ranking","alert"]: print(f"  {t[:5]:>10}",end="")
    print()
    for enc in ENCS:
        print(f"{enc:>8} ",end="")
        for t in ["prediction","ranking","alert"]:
            r=results[f"{enc}_{t}"]
            if t=="prediction": print(f"  MSE={r['mse']:.4f}",end="")
            elif t=="ranking": print(f"  tau={r['tau']:.4f}",end="")
            else: print(f"  Acc={r['acc']:.4f}",end="")
        print()
    
    out=os.path.join(os.path.dirname(__file__),"results","v106_results.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    json.dump(results,open(out,"w"),indent=2)
    print(f"\nSaved to {out}")

if __name__=="__main__":
    main()

