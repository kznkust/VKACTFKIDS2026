"""Reference solver: only reads the distributed executable; stdlib only."""
import argparse
from pathlib import Path
import struct
import hashlib

MASK = (1 << 64) - 1


def emulate(program):
    r = [0] * 4
    pc = 0
    while pc < len(program):
        op, a = program[pc:pc + 2]
        pc += 2
        if op == 0x31:
            r[a] = struct.unpack_from('<Q', program, pc)[0]
            pc += 8
        elif op == 0xFE:
            return r[a]
        else:
            b = program[pc]
            pc += 1
            if op == 0xA7:
                r[a] ^= r[b]
            elif op == 0x52:
                r[a] = (r[a] + r[b]) & MASK
            elif op == 0xC3:
                r[a] = ((r[a] << b) | (r[a] >> (64 - b))) & MASK
            elif op == 0x68:
                r[a], r[b] = r[b], r[a]
            else:
                raise ValueError(f'Unknown opcode {op:#x}')
    raise ValueError('Missing emit')


def solve(path):
    data = Path(path).read_bytes()
    offset = data.index(b'BOARDVM1')
    magic, version, count, size, length, initial, target = struct.unpack_from('<8s4H2Q', data, offset)
    assert version == 2 and count == 64
    start = offset + 32
    columns = [emulate(data[start + i * size:start + (i + 1) * size]) for i in range(count)]
    rhs = initial ^ target
    rows = [sum(((columns[c] >> bit) & 1) << c for c in range(64))
            | (((rhs >> bit) & 1) << 64) for bit in range(64)]
    for col in range(64):
        pivot = next((i for i in range(col, 64) if (rows[i] >> col) & 1), None)
        if pivot is None:
            raise ValueError('Singular board')
        rows[col], rows[pivot] = rows[pivot], rows[col]
        for i in range(64):
            if i != col and (rows[i] >> col) & 1:
                rows[i] ^= rows[col]
    key = sum((rows[i] >> 64) << i for i in range(64))
    check = initial
    for i in range(64):
        if key >> i & 1:
            check ^= columns[i]
    assert check == target
    moves = ' '.join(f'{chr(65 + i % 8)}{i // 8 + 1}' for i in range(64) if key >> i & 1)
    cipher = data[start + count * size:start + count * size + length]
    plain = bytearray()
    for i, byte in enumerate(cipher):
        if i % 32 == 0:
            digest = hashlib.sha256(b'last-turn/flag/v2' + struct.pack('<QI', key, i // 32)).digest()
        plain.append(byte ^ digest[i % 32])
    return moves, plain.decode()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', type=Path)
    parser.add_argument('--moves-only', action='store_true')
    args = parser.parse_args()
    moves, flag = solve(args.binary)
    print(moves)
    if not args.moves_only:
        print(flag)
