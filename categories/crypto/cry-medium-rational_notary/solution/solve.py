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

from flint import fmpz_mat,fmpz_poly
from math import gcd
n=int(data["n"]);c1=int(data["c1"]);c2=int(data["c2"])
x=fmpz_poly([0,1])
a=x**3+((1-c2)*c1-c2)
b=3*x**2-3*c2
c=3*x-3*c2
resultant=a**3+c1*b**3+c1*c1*c**3-3*c1*a*b*c
coeff=[int(v)%n for v in resultant]
assert coeff[-1]==1
f=fmpz_poly([v if v<=n//2 else v-n for v in coeff])
X=1<<challenge.SHIFT_BITS;degree=f.degree();m=2;t=degree
dimension=degree*m+t
polys=[]
for i in range(m):
    for j in range(degree):polys.append((n**(m-i))*(x**j)*(f**i))
for j in range(t):polys.append((x**j)*(f**m))
rows=[[int(poly[k])*X**k for k in range(dimension)] for poly in polys]
reduced=fmpz_mat(rows).lll()
lifted=[]
for row in reduced.tolist():
    v=list(map(int,row))
    assert all(v[k]%(X**k)==0 for k in range(dimension))
    lifted.append(fmpz_poly([v[k]//(X**k) for k in range(dimension)]))
candidates=set()
for i in range(min(8,len(lifted)-1)):
    common=lifted[i].gcd(lifted[i+1])
    if 0<common.degree()<degree*2:
        for root,_ in common.roots():
            r=int(root)
            if 0<=r<X and int(f(r))%n==0:candidates.add(r)
assert candidates,"no small resultant root"

def trim(a):
    while a and a[-1]%n==0:a.pop()
    return a

def remainder(a,b):
    a=a[:]
    factor=gcd(b[-1],n)
    if factor!=1:raise ArithmeticError(factor)
    inverse=pow(b[-1],-1,n)
    while len(a)>=len(b):
        z=a[-1]*inverse%n;offset=len(a)-len(b)
        for j,v in enumerate(b):a[offset+j]=(a[offset+j]-z*v)%n
        trim(a)
    return a

for shift in sorted(candidates):
    a=[-c1%n,0,0,1]
    b=[(shift**3-c2)%n,(3*shift**2-3*c2)%n,(3*shift-3*c2)%n,(1-c2)%n]
    try:
        while b:a,b=b,remainder(a,b)
        if len(a)!=2:continue
        message=-a[0]*pow(a[1],-1,n)%n
    except ArithmeticError as err:
        p=int(err.args[0]);q=n//p
        if not 1<p<n or p*q!=n:continue
        message=pow(c1,pow(3,-1,(p-1)*(q-1)),n)
    if pow(message,3,n)!=c1:continue
    if gcd(message+1,n)!=1:continue
    if pow((message+shift)*pow(message+1,-1,n)%n,3,n)!=c2:continue
    finish([message,shift])
raise ValueError("no related-message key authenticated")
