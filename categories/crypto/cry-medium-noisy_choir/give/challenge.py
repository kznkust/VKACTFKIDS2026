from core import *
SPECS=[(19,0b100111),(20,0b1001),(21,0b101)]
COUNT=8192
PERIOD=17

def stream(state,degree,taps,count=COUNT):
    out=0
    for i in range(count):
        out |= (state&1)<<i
        state=(state>>1)|(((state&taps).bit_count()&1)<<(degree-1))
    return out

def majority(a,b,c):return (a&b)^(a&c)^(b&c)

def repeated(mask,count=COUNT):
    return sum(((mask>>(i%PERIOD))&1)<<i for i in range(count))

def build(rng,flag):
    states=[1+rng.below((1<<degree)-1) for degree,_ in SPECS]
    seq=[stream(s,d,t) for s,(d,t) in zip(states,SPECS)]
    mask=rng.bits(PERIOD)
    output=majority(*seq)^repeated(mask)
    for i in rng.sample(COUNT,COUNT//33):output ^= 1<<i
    return {"trace":output.to_bytes(COUNT//8,"little").hex(),"box":seal(flag,[states,mask])}
