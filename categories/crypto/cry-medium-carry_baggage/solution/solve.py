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

from flint import fmpz_mat
n=challenge.N;p=challenge.P;B=1<<challenge.LOW
centers=[h*B+B//2 for h in data["heads"]]
for phase in range(18):
    w0=data["weights"][0]
    w1=[data["weights"][1][(j-4*phase)%n] for j in range(n)]
    rows=[]
    for i in range(n):
        row=[0]*(n+3);row[i]=2*B
        row[n]=2*w0[i];row[n+1]=2*w1[i]
        rows.append(row)
    for i in range(2):
        row=[0]*(n+3);row[n+i]=2*p;rows.append(row)
    rows.append([B]*n+[2*c for c in centers]+[B])
    reduced=fmpz_mat(rows).lll(delta=0.99)
    for row in reduced.tolist():
        v=list(map(int,row))
        if abs(v[-1])!=B:continue
        sign=1 if v[-1]>0 else -1
        if any(abs(x)!=B for x in v[:n]):continue
        bits=[(1-sign*x//B)//2 for x in v[:n]]
        if any((sum(w*b for w,b in zip(weights,bits))%p)>>challenge.LOW != h
               for weights,h in zip((w0,w1),data["heads"])):continue
        secret=sum(b<<i for i,b in enumerate(bits))
        finish([secret,phase])
raise ValueError("no binary vector recovered; lattice parameters may need tuning")
