#!/usr/bin/env python3
"""Reconstruct every route block from the public replay; enumerate all candidates."""
from pathlib import Path
import argparse
import struct
import sys

MASK=0xffffffff
LETTERS='wasd'

def xs(x):
    x ^= (x<<13)&MASK
    x ^= x>>17
    return (x^(x<<5))&MASK

def rol(x,r,bits=32):
    x&=(1<<bits)-1
    r%=bits
    return ((x<<r)|(x>>((bits-r)%bits)))&((1<<bits)-1)

def step(s,c,t,board):
    x,y,f,e,a=s
    f=(f+(0,3,2,1)[c]+(e>>7))&3
    x=(x+(0,1,0,-1)[f])&7
    y=(y+(-1,0,1,0)[f])&7
    bell=rol((board[8*y+x]*13)^(x*17+y*29)^((t*7)&255),f+1,8)
    a=(rol(a^(((e+0x9d)*0x01010101)&MASK),5)+bell*0x045d9f3b+(c+1)*0x9e3779b1)&MASK
    return x,y,f,(bell^(e>>1)^(c*41))&255,a

def candidates(start,target,group,board):
    found=[]
    def visit(s,depth,word):
        if depth==8:
            if s==target:
                found.append(word)
            return
        for c in range(4):
            visit(step(s,c,group*8+depth,board),depth+1,word+LETTERS[c])
    visit(start,0,'')
    return found

def solve(path,verbose=False):
    data=Path(path).read_bytes()
    if len(data)<84:
        raise ValueError('short replay')
    magic,version,groups,block,seed,acc,x,y,f,e=struct.unpack_from('<4sBBHII4B',data)
    if magic!=b'ECHO' or version!=2 or block!=8 or len(data)!=84+groups*8:
        raise ValueError('bad replay')
    board=[]
    for i in range(64):
        seed=xs(seed)
        board.append(data[20+((17*i+9)&63)]^(seed&255))
    if any(v>15 for v in board):
        raise ValueError('bad board')
    state=(x,y,f,e,acc)
    answer=''
    for group in range(groups):
        x,y,f,e,a=state
        key=a^(e<<24)^(x<<16)^(y<<8)^f^0xa53c19e7^((group*0x6d2b79f5)&MASK)
        raw=bytearray()
        for b in data[84+8*group:92+8*group]:
            key=xs(key)
            raw.append(b^(key&255))
        target=struct.unpack('<4BI',raw)
        matches=candidates(state,target,group,board)
        if verbose:
            print(f'block {group+1}: {len(matches)} candidate(s)',file=sys.stderr)
        if len(matches)!=1:
            raise ValueError(f'block {group+1}: expected a unique path, got {matches!r}')
        answer+=matches[0]
        state=target
    body=bytearray()
    for offset in range(0,len(answer),4):
        value=0
        for gesture in answer[offset:offset+4]:
            value=(value<<2)|LETTERS.index(gesture)
        body.append(value)
    return 'vka{'+body.decode('ascii')+'}'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('replay',nargs='?',default=Path(__file__).resolve().parents[1]/'give/auditorium.rpl')
    parser.add_argument('-v','--verbose',action='store_true')
    args=parser.parse_args()
    print(solve(args.replay,args.verbose))
