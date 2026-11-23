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
from random import Random
p=challenge.P;B=1<<challenge.LOW
rand=Random(0xC10C)
subsets=[list(range(i,i+8)) for i in (0,8,16,24)]
subsets += [sorted(rand.sample(range(32),8)) for _ in range(28)]

def recover(indices,ab):
    pairs=[ab[i] for i in indices]
    targets=[((data["words"][i]*B+B//2)-ab[i][1])%p for i in indices]
    m=len(indices);rows=[]
    for i in range(m):
        row=[0]*(m+2);row[i]=p*p;rows.append(row)
    rows.append([p*A for A,_ in pairs]+[B,0])
    rows.append([p*t for t in targets]+[0,p*B])
    reduced=fmpz_mat(rows).lll()
    for row in reduced.tolist():
        v=list(map(int,row))
        if abs(v[-1])==p*B and v[-2]%B==0:
            yield (-v[-2]//B*(1 if v[-1]>0 else -1))%p

for stride in range(2,62):
    ab=[challenge.jump(data["a"],data["b"],(i+1)*stride) for i in range(32)]
    seen=set()
    for indices in subsets:
        for initial in recover(indices,ab):
            if initial in seen:continue
            seen.add(initial)
            count=sum(((A*initial+C)%p)>>challenge.LOW == y for (A,C),y in zip(ab,data["words"]))
            if count>=27:finish([initial,stride])
raise ValueError("no robust lattice candidate; increase sample schedule")
