from core import *
P=(1<<127)-1
LOW=80

def jump(a,b,t):
    A=pow(a,t,P)
    B=b*(A-1)*pow(a-1,-1,P)%P
    return A,B

def build(rng,flag):
    a=2+rng.below(P-3);b=1+rng.below(P-1)
    initial=rng.below(P);stride=2+rng.below(60)
    rows=[]
    for i in range(1,33):
        A,B=jump(a,b,i*stride)
        rows.append(((A*initial+B)%P)>>LOW)
    for i in rng.sample(32,5):rows[i]=rng.below(1<<(127-LOW))
    return {"a":a,"b":b,"words":rows,"box":seal(flag,[initial,stride])}
