#!/usr/bin/env python3
"""Recover a flag from the public spool alone; no organizer imports."""
from pathlib import Path
import argparse
import math
import struct

def xs(x):
    x ^= (x << 13) & 0xffffffff
    x ^= x >> 17
    return (x ^ (x << 5)) & 0xffffffff

def solve(path):
    data = Path(path).read_bytes()
    if len(data) < 16:
        raise ValueError('short spool')
    magic, version, n, step, offset, seed, carry = struct.unpack_from('<4sBBBBII',data)
    if magic != b'CCP2' or version != 1 or len(data) != 16+n or math.gcd(step,n) != 1:
        raise ValueError('invalid spool')
    flag = bytearray(n)
    wheel=list(range(256))
    wheel_seed=seed^0x70617072
    for i in range(255,0,-1):
        wheel_seed=xs(wheel_seed)
        j=wheel_seed%(i+1)
        wheel[i],wheel[j]=wheel[j],wheel[i]
    for k,y in enumerate(data[16:]):
        seed = xs(seed)
        z = y ^ (seed & 255)
        r = k%7+1
        z = ((z >> r) | (z << (8-r))) & 255
        x = (wheel.index(z)-carry-13*k) & 255
        flag[(offset+step*k)%n] = x
        u,v=(carry+k)&255,(y+x)&255
        wheel[u],wheel[v]=wheel[v],wheel[u]
        carry = (y+x+7*k) & 255
    result = flag.decode('ascii')
    if not (result.startswith('vka{') and result.endswith('}')):
        raise ValueError('flag framing failed')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spool',nargs='?',default=Path(__file__).resolve().parents[1]/'give/last.spool')
    print(solve(parser.parse_args().spool))
