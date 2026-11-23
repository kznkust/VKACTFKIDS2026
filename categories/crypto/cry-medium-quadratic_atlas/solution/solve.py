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

from flint import nmod_mat
from itertools import product
p=challenge.P;n=challenge.N
Q=data["forms"]
# The pencil has right eigenvectors A^{-1}*e_i.
M=mm(inv(Q[0],p),Q[1],p)
_,factors=nmod_mat(M,p).charpoly().factor()
eigenvalues=[]
for factor,mult in factors:
    assert factor.degree()==1 and mult==1,"need a different pencil"
    eigenvalues.append((-int(factor[0])*pow(int(factor[1]),-1,p))%p)
assert len(eigenvalues)==n
columns=[]
for lam in sorted(eigenvalues):
    eq=[[(M[i][j]-(lam if i==j else 0))%p for j in range(n)] for i in range(n)]
    basis=nullspace(eq,p)
    assert len(basis)==1
    columns.append(basis[0])
V=transpose(columns)
center=mv(inv(Q[0],p),[(-x*pow(2,-1,p))%p for x in data["linear"][0]],p)
assert all([(2*a+b)%p for a,b in zip(mv(q,center,p),linear)]==[0]*n for q,linear in zip(Q,data["linear"]))
D=[]
for q in Q:
    diagonal=mm(mm(transpose(V),q,p),V,p)
    assert all(diagonal[i][j]==0 for i in range(n) for j in range(n) if i!=j)
    D.append([diagonal[i][i] for i in range(n)])
base=challenge.evaluate(Q,data["linear"],data["constant"],center)
squares=mv(inv(D,p),[(a-b)%p for a,b in zip(data["target"],base)],p)
roots=[pow(x,(p+1)//4,p) for x in squares]
assert all(r*r%p==x for r,x in zip(roots,squares))
for signs in product((1,-1),repeat=n):
    z=[s*r%p for s,r in zip(signs,roots)]
    shift=mv(V,z,p)
    x=[(a+b)%p for a,b in zip(center,shift)]
    if finish(x):break
else:raise ValueError("no preimage passed MAC")
