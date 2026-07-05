#!/usr/bin/env python3
import numpy as np, json, sys, warnings
import os
from itertools import combinations
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import silhouette_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
warnings.filterwarnings("ignore")

# --- CONFIG ---
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL_TABLE = os.path.join(REPO, "riscv", "skill_table", "skill_table_8105.npy")
DATA_FILE = os.path.join(REPO, "experiments", "v73", "v73_data.json")
OUT_DIR = os.path.join(REPO, "experiments", "v73")

print("=" * 65)
print("  CNBE-32 v7.3 - Hardware Encoding + Semantic Validation")
print("=" * 65)
print("  Repo:", REPO)

if not os.path.exists(SKILL_TABLE):
    print("[FATAL] Skill table not found at", SKILL_TABLE)
    sys.exit(1)
table = np.load(SKILL_TABLE)
print("[0] Skill table: %d entries (%.1f KB)" % (len(table), len(table)*4/1024))

def cnbe_code(char):
    idx = ord(char) - 0x4E00
    if 0 <= idx < len(table):
        c = int(table[idx])
        if c > 0:
            return ((c>>24)&0xFF, (c>>19)&0x1F, (c>>15)&0x0F)
    return (0,0,0)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

SR = data["same_radical_groups"]; SS = data["same_structure_groups"]
SIM = data["semantic_similar_pairs"]; UNR = data["semantic_unrelated_pairs"]

# Build pairs
pairs = []
for _,cs in SR:
    for i in range(min(5,len(cs)-1)):
        for j in range(i+1,min(i+3,len(cs))):
            pairs.append((cs[i],cs[j],"sr",None))
for (_,c1),(_,c2) in combinations(SR[:10],2):
    pairs.append((c1[0],c2[0],"dr",None))
    if len(pairs)>=250: break
for sg in SS:
    for i in range(min(5,len(sg)-1)):
        for j in range(i+1,min(i+3,len(sg))):
            pairs.append((sg[i],sg[j],None,"ss"))
for g1,g2 in combinations(SS[:5],2):
    for i in range(min(3,len(g1))):
        for j in range(min(3,len(g2))):
            pairs.append((g1[i],g2[j],None,"ds"))
for a,b in SIM: pairs.append((a,b,None,None))
for a,b in UNR: pairs.append((a,b,None,None))

chars = sorted(set(c for p in pairs for c in p[:2]))
print("[1] %d pairs, %d chars" % (len(pairs), len(chars)))

# Feature extraction
tv = TfidfVectorizer(analyzer="char",ngram_range=(1,2))
tf = tv.fit_transform(chars).toarray()
uf = np.array([[float(ord(c))] for c in chars])
cf = np.array([[float(x) for x in cnbe_code(c)] for c in chars])
ci = {c:i for i,c in enumerate(chars)}
print("[2] Features: T=%dD U=1D C=3D" % tf.shape[1])

# Cosine similarity
print("\n[3] Cosine similarity...")
res = {}
for feats,nm in [(tf,"PureText"),(uf,"Unicode"),(cf,"CNBEF")]:
    ir,dr,iss,dss,sm,um=[],[],[],[],[],[]
    for c1,c2,r,s in pairs:
        i1,i2=ci[c1],ci[c2]
        d=1.0-cosine_similarity(feats[i1:i1+1],feats[i2:i2+1])[0,0]
        if r=="sr": ir.append(d)
        elif r=="dr": dr.append(d)
        if s=="ss": iss.append(d)
        elif s=="ds": dss.append(d)
        if r is None and s is None:
            if [c1,c2] in SIM or [c2,c1] in SIM: sm.append(d)
            else: um.append(d)
    rs=float(np.mean(dr)-np.mean(ir)) if ir and dr else None
    ss2=float(np.mean(dss)-np.mean(iss)) if iss and dss else None
    ss3=float(np.mean(um)-np.mean(sm)) if sm and um else None
    res[nm]={"rad_sep":rs,"struct_sep":ss2,"sem_sep":ss3}
    print("  %-8s: R=%.4f S=%.4f Sem=%s"%(nm,rs or 0,ss2 or 0,str(ss3)))

# Silhouette
print("\n[4] Silhouette...")
rl={}
for nm,cs in SR:
    for c in cs:
        if c in ci: rl[ci[c]]=nm
for feats,nm in [(tf,"PureText"),(uf,"Unicode"),(cf,"CNBEF")]:
    ix=sorted(rl.keys())
    if len(ix)<3: continue
    X=np.array([feats[i] for i in ix]); y=np.array([rl[i] for i in ix])
    ct=Counter(y)
    if sum(1 for v in ct.values() if v>1)<2: continue
    try:
        sil=silhouette_score(X,y,metric="cosine")
        res[nm]["silhouette"]=float(sil)
        print("  %-8s: S=%.4f"%(nm,sil))
    except: pass

# Hard task KNN
print("\n[5] Hard task KNN...")
Xc,Xu,Xt,yr,yk,ys=[],[],[],[],[],[]
for c in chars:
    r,k,s=cnbe_code(c)
    if r>0:
        i=ci[c];Xc.append(cf[i]);Xu.append(uf[i]);Xt.append(tf[i])
        yr.append(r);yk.append(k);ys.append(s)
Xc=np.array(Xc);Xu=np.array(Xu);Xt=np.array(Xt)
hr={}
for tn,y in [("Radical",np.array(yr)),("Stroke",np.array(yk)),("Struct",np.array(ys))]:
    tr={}
    for X,fn in [(Xc,"CNBE"),(Xu,"Unicode"),(Xt,"Text")]:
        knn=KNeighborsClassifier(n_neighbors=3)
        try:
            sc=cross_val_score(knn,X,y,cv=5)
            tr[fn]=float(sc.mean())
        except: tr[fn]=None
    hr[tn]=tr
    parts=["%s=%.1f%%"%(k,v*100) for k,v in tr.items() if v is not None]
    print("  %s: %s"%(tn," | ".join(parts)))

# Summary
print("\n"+"="*65)
print("  SUMMARY")
print("="*65)
bc=max(res.keys(),key=lambda k:res[k].get("rad_sep",-999)or-999)
bs=max(res.keys(),key=lambda k:res[k].get("silhouette",-999)or-999)
print("H1 Best clustering: %s | Best silhouette: %s"%(bc,bs))
cc=cf[cf.sum(axis=1)>0]
print("H3 CNBE valid chars: %d/%d"%(cc.shape[0],len(cf)))
print("   Ranges: r=%.0f-%.0f s=%.0f-%.0f t=%.0f-%.0f"%(cc[:,0].min(),cc[:,0].max(),cc[:,1].min(),cc[:,1].max(),cc[:,2].min(),cc[:,2].max()))

out_path=os.path.join(OUT_DIR,"v73_results.json")
with open(out_path,"w",encoding="utf-8") as f:
    json.dump({"pairs":len(pairs),"chars":len(chars),"similarity":res,"hard_task":hr},
              f,ensure_ascii=False,indent=2)
print("\nResults -> v73_results.json")