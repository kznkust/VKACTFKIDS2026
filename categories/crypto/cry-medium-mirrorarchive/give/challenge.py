from core import *
P=1000003
N=7

def build(rng,flag):
    L=random_matrix(rng,N,P);R=random_matrix(rng,N,P)
    xs=[random_matrix(rng,N,P) for _ in range(9)]
    ys=[scale(mm(mm(L,x,P),R,P),1+rng.below(P-1),P) for x in xs]
    ys += [random_matrix(rng,N,P) for _ in range(4)]
    rng.shuffle(ys)
    return {"left":xs,"right":ys,"box":seal(flag,[projective(L,P),projective(R,P)])}
