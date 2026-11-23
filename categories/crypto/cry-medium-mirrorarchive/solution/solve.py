from pathlib import Path
import json
import re
import sys

GIVE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/"give"
sys.path.insert(0,str(GIVE))
from core import *
import challenge

data=json.loads((GIVE/"data.json").read_text())

def finish(secret):
    flag=unseal(data["box"],secret)
    if flag is not None:
        assert re.fullmatch(r"vkactf\{[a-zA-Z_]+\}",flag)
        print(flag)
        raise SystemExit(0)
    return False

p=challenge.P;n=challenge.N
xs,ys=data["left"],data["right"]

def normalized_trace(a):
    return scale(a,pow(trace(a,p),-1,p),p)

def fingerprint(a):
    a=normalized_trace(a)
    power=identity(n);out=[]
    for _ in range(4):
        power=mm(power,a,p);out.append(trace(power,p))
    return tuple(out[1:])

x0inv=inv(xs[0],p)
c=[mm(x,x0inv,p) for x in xs]
sigs=[fingerprint(x) for x in c]
for base,y0 in enumerate(ys):
    yi=inv(y0,p)
    raw=[mm(y,yi,p) for y in ys]
    buckets={}
    for j,a in enumerate(raw):
        try:buckets.setdefault(fingerprint(a),[]).append(j)
        except ValueError:continue
    if any(len(buckets.get(s,[]))!=1 for s in sigs):continue
    mapping=[buckets[s][0] for s in sigs]
    if mapping[0]!=base or len(set(mapping))!=len(xs):continue
    equations=[]
    for i in range(1,len(xs)):
        C=normalized_trace(c[i]);D=normalized_trace(raw[mapping[i]])
        for r in range(n):
            for col in range(n):
                row=[0]*(n*n)
                for k in range(n):
                    row[k*n+col]=(row[k*n+col]+D[r][k])%p
                    row[r*n+k]=(row[r*n+k]-C[k][col])%p
                equations.append(row)
    basis=nullspace(equations,p)
    if len(basis)!=1:continue
    L=[basis[0][i*n:(i+1)*n] for i in range(n)]
    try:R=mm(mm(x0inv,inv(L,p),p),y0,p)
    except ValueError:continue
    if all(projective(mm(mm(L,x,p),R,p),p)==projective(ys[j],p) for x,j in zip(xs,mapping)):
        finish([projective(L,p),projective(R,p)])
raise ValueError("no projective equivalence")
