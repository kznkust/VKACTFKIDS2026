"""Public serialization, capsule and finite-field operations (not secret)."""
import hashlib
import hmac
import json

def encode(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode()

def key_for(secret):
    return hashlib.sha256(b"VKACTF-HARD-v2/key/" + encode(secret)).digest()

def seal(flag, secret):
    key = key_for(secret)
    stream = hashlib.shake_256(b"VKACTF-HARD-v2/pad/" + key).digest(len(flag))
    ct = bytes(a ^ b for a,b in zip(flag.encode(), stream))
    return {"ct": ct.hex(), "tag": hmac.new(key, ct, hashlib.sha256).hexdigest()}

def unseal(box, secret):
    key = key_for(secret)
    ct = bytes.fromhex(box["ct"])
    if not hmac.compare_digest(hmac.new(key, ct, hashlib.sha256).hexdigest(), box["tag"]):
        return None
    stream = hashlib.shake_256(b"VKACTF-HARD-v2/pad/" + key).digest(len(ct))
    return bytes(a ^ b for a,b in zip(ct, stream)).decode()

class RNG:
    """Reproducible private SHA-256 counter generator; seed is never published."""
    def __init__(self, seed):
        self.seed=bytes.fromhex(seed)
        self.counter=0
    def bits(self, n):
        out=b""
        while len(out)*8 < n:
            out += hashlib.sha256(self.seed + self.counter.to_bytes(16,"big")).digest()
            self.counter += 1
        return int.from_bytes(out,"big") & ((1<<n)-1)
    def below(self, n):
        while True:
            x=self.bits(n.bit_length())
            if x<n:return x
    def shuffle(self, a):
        for i in range(len(a)-1,0,-1):
            j=self.below(i+1)
            a[i],a[j]=a[j],a[i]
    def sample(self, n, k):
        a=list(range(n));self.shuffle(a);return a[:k]

def identity(n):
    return [[int(i==j) for j in range(n)] for i in range(n)]

def transpose(a):return [list(row) for row in zip(*a)]
def mm(a,b,p):
    return [[sum(x*y for x,y in zip(row,col))%p for col in zip(*b)] for row in a]
def mv(a,v,p):return [sum(x*y for x,y in zip(row,v))%p for row in a]
def scale(a,k,p):return [[x*k%p for x in row] for row in a]
def trace(a,p):return sum(a[i][i] for i in range(len(a)))%p

def rref(matrix,p,ncols=None):
    a=[row[:] for row in matrix]
    limit=len(a[0]) if ncols is None else ncols
    pivots=[];r=0
    for col in range(limit):
        pivot=next((i for i in range(r,len(a)) if a[i][col]%p),None)
        if pivot is None:continue
        a[r],a[pivot]=a[pivot],a[r]
        z=pow(a[r][col],-1,p)
        a[r]=[x*z%p for x in a[r]]
        for i in range(len(a)):
            if i!=r and a[i][col]:
                z=a[i][col]
                a[i]=[(x-z*y)%p for x,y in zip(a[i],a[r])]
        pivots.append(col);r+=1
        if r==len(a):break
    return a,pivots

def inv(a,p):
    n=len(a)
    rows,pivots=rref([row+eye for row,eye in zip(a,identity(n))],p,n)
    if len(pivots)!=n:raise ValueError("singular")
    return [row[n:] for row in rows]

def nullspace(a,p):
    rows,pivots=rref(a,p)
    n=len(a[0]);basis=[]
    for j in range(n):
        if j in pivots:continue
        v=[0]*n;v[j]=1
        for i,k in enumerate(pivots):v[k]=-rows[i][j]%p
        basis.append(v)
    return basis

def random_matrix(rng,n,p):
    while True:
        a=[[rng.below(p) for _ in range(n)] for _ in range(n)]
        try:inv(a,p);return a
        except ValueError:pass

def projective(a,p):
    x=next(x for row in a for x in row if x)
    return scale(a,pow(x,-1,p),p)

def probable_prime(n):
    if n<2:return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n%p==0:return n==p
    d=n-1;s=0
    while d%2==0:d//=2;s+=1
    for i in range(40):
        a=2+int.from_bytes(hashlib.sha256(str(n).encode()+i.to_bytes(2,"big")).digest(),"big")%(n-3)
        x=pow(a,d,n)
        if x in (1,n-1):continue
        for _ in range(s-1):
            x=x*x%n
            if x==n-1:break
        else:return False
    return True

def prime(rng,bits):
    while True:
        n=rng.bits(bits)|(1<<(bits-1))|1
        if n%3==2 and probable_prime(n):return n
