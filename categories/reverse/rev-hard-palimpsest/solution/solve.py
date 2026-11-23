#!/usr/bin/env python3
"""Decode public notebook, lift VM rounds, invert the live state. No private imports."""
from pathlib import Path
import argparse
import struct
import sys

MASK=0xffffffff
MOV,ADD,XOR,ROL,MULI,ADDI,XORI,SWAP,NOT,BSWAP,LOADI,SUB,ROR,MULR,NOP,HALT=range(16)
NAMES=('mov','add','xor','rol','muli','addi','xori','swap','not','bswap','loadi','sub','ror','mulr','nop','halt')

def xs(x):
    x^=(x<<13)&MASK
    x^=x>>17
    return (x^(x<<5))&MASK

def rol(x,r):
    r&=31
    return ((x<<r)|(x>>((32-r)&31)))&MASK

def checksum(data):
    result=0x811c9dc5
    for b in data:
        result=((result^b)*0x01000193)&MASK
    return result

def decode(path):
    data=Path(path).read_bytes()
    if len(data)<120:
        raise ValueError('short notebook')
    magic,ver,regs,page_size,pages,count,physical,ink,salt=struct.unpack_from('<4sBBBBIIII',data)
    if (magic,ver,regs,page_size)!=(b'PLM3',1,16,16) or len(data)!=120+144*pages:
        raise ValueError('invalid header')
    banks=[data[24+16*b:40+16*b] for b in range(4)]
    if any(sorted(bank)!=list(range(16)) for bank in banks):
        raise ValueError('invalid opcode bank')
    program=[]
    seen=set()
    for page_no in range(pages):
        if physical>=pages or physical in seen:
            raise ValueError('broken page chain')
        seen.add(physical)
        offset=88+144*physical
        following,used,nonce,digest=struct.unpack_from('<4I',data,offset)
        if not 1<=used<=16 or (page_no+1<pages and used!=16):
            raise ValueError('invalid page length')
        key=ink^nonce^((physical*0x9e3779b9)&MASK)
        raw=bytearray()
        for j,enc in enumerate(data[offset+16:offset+144]):
            key=xs(key)
            b=enc^(key&255)
            raw.append(b)
            key=(key+b+17*j)&MASK
        if checksum(raw)!=digest:
            raise ValueError(f'page checksum failed at physical page {physical}')
        for j in range(used):
            ip=len(program)
            op,d,s,r,k=struct.unpack_from('<4BI',raw,j*8)
            bank=(ip//16+(ink&3))&3
            op=banks[bank][op]
            d^=(ink>>8)&15
            s^=(ink>>12)&15
            r^=(ink>>16)&31
            k^=rol(ink,ip&31)
            if d>=16 or s>=16 or r>=32:
                raise ValueError('bad operand')
            program.append((op,d,s,r,k))
        ink=(rol(ink^digest^nonce,7)+0x6d2b79f5)&MASK
        physical=following
    if physical!=MASK or len(program)!=count or program[-1][0]!=HALT:
        raise ValueError('bad program end')
    target=bytearray()
    key=ink^salt
    for b in data[88+pages*144:]:
        key=xs(key)
        target.append(b^(key&255))
    return program,list(struct.unpack('<8I',target))

def lift(program):
    events=[]
    ip=0
    while ip<len(program):
        op,d,s,r,k=program[ip]
        if op==MOV and d==8 and s<8:
            block=program[ip:ip+10]
            if len(block)!=10 or [i[0] for i in block]!=[MOV,ROL,MOV,MULI,XOR,ADDI,XOR,ADD,ROL,XORI]:
                raise ValueError(f'unknown round at {ip}')
            a,b,c,src=block[7][1],s,block[2][2],block[6][2]
            rb,odd,key,ra,xkey=block[1][3],block[3][4],block[5][4],block[8][3],block[9][4]
            expected=[(MOV,8,b,0,0),(ROL,8,0,rb,0),(MOV,9,c,0,0),(MULI,9,0,0,odd),
                      (XOR,8,9,0,0),(ADDI,8,0,0,key),(XOR,8,src,0,0),
                      (ADD,a,8,0,0),(ROL,a,0,ra,0),(XORI,a,0,0,xkey)]
            if block!=expected or len({a,b,c,src})!=4 or max(a,b,c,src)>=8:
                raise ValueError(f'invalid round dependencies at {ip}')
            events.append(('round',a,b,c,src,rb,odd,key,ra,xkey))
            ip+=10
            continue
        if op==SWAP and d<8 and s<8:
            events.append(('swap',d,s))
        elif op==NOT and d<8:
            events.append(('not',d))
        elif op==BSWAP and d<8:
            events.append(('bswap',d))
        elif op in (NOP,HALT):
            pass
        elif d>=12 and op in (LOADI,SUB,ROR,MULR) and (op==LOADI or s>=12):
            pass
        else:
            raise ValueError(f'unrecognized live instruction at {ip}: {program[ip]}')
        ip+=1
    return events

def bswap(x):
    return int.from_bytes(x.to_bytes(4,'little'),'big')

def evaluate(program,flag):
    regs=list(struct.unpack('<8I',flag))+[0]*8
    for op,d,s,r,k in program:
        if op==MOV: regs[d]=regs[s]
        elif op==ADD: regs[d]=(regs[d]+regs[s])&MASK
        elif op==XOR: regs[d]^=regs[s]
        elif op==ROL: regs[d]=rol(regs[d],r)
        elif op==MULI: regs[d]=(regs[d]*k)&MASK
        elif op==ADDI: regs[d]=(regs[d]+k)&MASK
        elif op==XORI: regs[d]^=k
        elif op==SWAP: regs[d],regs[s]=regs[s],regs[d]
        elif op==NOT: regs[d]^=MASK
        elif op==BSWAP: regs[d]=bswap(regs[d])
        elif op==LOADI: regs[d]=k
        elif op==SUB: regs[d]=(regs[d]-regs[s])&MASK
        elif op==ROR: regs[d]=rol(regs[d],-r)
        elif op==MULR: regs[d]=(regs[d]*regs[s])&MASK
        elif op==NOP: pass
        elif op==HALT: break
        else: raise ValueError('unknown opcode')
    return regs[:8]

def solve(path,verbose=False,dump=None):
    program,target=decode(path)
    if dump:
        # A reconstructed disassembly, useful while reading the write-up.
        with Path(dump).open('w',encoding='utf-8') as out:
            for ip,(op,d,s,r,k) in enumerate(program):
                out.write(f'{ip:04d}  {NAMES[op]:5s} d={d:2d} s={s:2d} r={r:2d} k={k:08x}\n')
    events=lift(program)
    state=target[:]
    for event in reversed(events):
        if event[0]=='round':
            _,a,b,c,src,rb,odd,key,ra,xkey=event
            f=(rol(state[b],rb)^((state[c]*odd)&MASK))
            f=((f+key)&MASK)^state[src]
            state[a]=(rol(state[a]^xkey,-ra)-f)&MASK
        elif event[0]=='swap':
            _,a,b=event
            state[a],state[b]=state[b],state[a]
        elif event[0]=='not':
            state[event[1]]^=MASK
        elif event[0]=='bswap':
            state[event[1]]=bswap(state[event[1]])
    raw=struct.pack('<8I',*state)
    if evaluate(program,raw)!=target:
        raise ValueError('independent forward VM verification failed')
    flag=raw.decode('ascii')
    if not flag.startswith('vka{') or not flag.endswith('}'):
        raise ValueError('flag framing failed')
    if verbose:
        rounds=sum(e[0]=='round' for e in events)
        print(f'{len(program)} decoded instructions; {rounds} reversible rounds; {len(events)} live events',file=sys.stderr)
    return flag

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('notebook',nargs='?',default=Path(__file__).resolve().parents[1]/'give/classroom.palm')
    parser.add_argument('-v','--verbose',action='store_true')
    parser.add_argument('--dump',metavar='FILE',help='write recovered VM disassembly')
    args=parser.parse_args()
    print(solve(args.notebook,args.verbose,args.dump))
