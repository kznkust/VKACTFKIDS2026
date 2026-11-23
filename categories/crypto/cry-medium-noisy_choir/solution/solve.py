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

count=challenge.COUNT;lag=challenge.PERIOD
observed=int.from_bytes(bytes.fromhex(data["trace"]),"little")
length=count-lag;keep=(1<<length)-1
target=(observed^(observed>>lag))&keep
states=[]
for degree,taps in challenge.SPECS:
    basis=[]
    for i in range(degree):
        seq=challenge.stream(1<<i,degree,taps)
        basis.append((seq^(seq>>lag))&keep)
    best_score=length+1;best_state=None
    value=0;gray=0
    for k in range(1,1<<degree):
        bit=(k&-k).bit_length()-1
        gray ^= 1<<bit
        value ^= basis[bit]
        score=(value^target).bit_count()
        if score<best_score:
            best_score=score;best_state=gray
    assert best_score < length*0.46,"no meaningful correlation"
    states.append(best_state)
clean=challenge.majority(*(challenge.stream(s,d,t) for s,(d,t) in zip(states,challenge.SPECS)))
residual=observed^clean
mask=0
for j in range(lag):
    positions=list(range(j,count,lag))
    ones=sum((residual>>i)&1 for i in positions)
    mask |= int(ones*2>len(positions))<<j
assert (residual^challenge.repeated(mask)).bit_count()==count//33
finish([states,mask])
raise ValueError("correlation candidate did not authenticate")
