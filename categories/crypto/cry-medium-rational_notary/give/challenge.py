from core import *
from math import gcd
BITS=512
SHIFT_BITS=48

def build(rng,flag):
    p=prime(rng,BITS);q=prime(rng,BITS)
    while q==p:q=prime(rng,BITS)
    n=p*q
    while True:
        message=2+rng.below(n-3)
        if gcd(message+1,n)==1:break
    shift=(1<<(SHIFT_BITS-1))|rng.bits(SHIFT_BITS-1)
    transformed=(message+shift)*pow(message+1,-1,n)%n
    return {"n":str(n),"c1":str(pow(message,3,n)),"c2":str(pow(transformed,3,n)),
            "box":seal(flag,[message,shift])}
