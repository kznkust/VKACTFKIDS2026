from core import *
P=(1<<127)-1
N=72
LOW=40

def build(rng,flag):
    weights=[[rng.below(P) for _ in range(N)] for _ in range(2)]
    secret=rng.bits(N);phase=rng.below(18)
    bits=[(secret>>i)&1 for i in range(N)]
    first=sum(weights[0][i]*bits[i] for i in range(N))%P
    second=sum(weights[1][i]*bits[(i+4*phase)%N] for i in range(N))%P
    return {"weights":weights,"heads":[first>>LOW,second>>LOW],"box":seal(flag,[secret,phase])}
