from core import *
P=(1<<61)-1
N=12

def evaluate(forms,linear,constant,x):
    return [(sum(x[i]*forms[k][i][j]*x[j] for i in range(N) for j in range(N))
             +sum(linear[k][i]*x[i] for i in range(N))+constant[k])%P for k in range(N)]

def build(rng,flag):
    A=random_matrix(rng,N,P);B=random_matrix(rng,N,P)
    c=[rng.below(P) for _ in range(N)];d=[rng.below(P) for _ in range(N)]
    forms=[[[sum(B[k][t]*A[t][i]*A[t][j] for t in range(N))%P
              for j in range(N)] for i in range(N)] for k in range(N)]
    linear=[[sum(2*B[k][t]*c[t]*A[t][i] for t in range(N))%P for i in range(N)] for k in range(N)]
    constant=[(sum(B[k][t]*c[t]*c[t] for t in range(N))+d[k])%P for k in range(N)]
    x=[rng.below(P) for _ in range(N)]
    return {"forms":forms,"linear":linear,"constant":constant,
            "target":evaluate(forms,linear,constant,x),"box":seal(flag,x)}
