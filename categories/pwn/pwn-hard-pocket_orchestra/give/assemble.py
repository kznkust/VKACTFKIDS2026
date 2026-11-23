#!/usr/bin/env python3
"""Build the public Pocket Orchestra assembler; no third party dependencies."""
import argparse
import pathlib
import struct
import sys

OPCODES = {name: i for i, name in enumerate(
    ('set', 'add', 'xor', 'rol', 'save', 'load', 'jz', 'jnz', 'mul', 'end'))}

def assemble(text):
    labels, rows = {}, []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        if line.endswith(':'):
            label = line[:-1].strip()
            if not label.isidentifier() or label in labels:
                raise ValueError(f'line {lineno}: invalid/duplicate label')
            labels[label] = len(rows)
            continue
        rows.append((lineno, line.split()))
    if not 1 <= len(rows) <= 160:
        raise ValueError('a score must contain 1..160 notes')
    output = bytearray()
    for pc, (lineno, words) in enumerate(rows):
        name = words[0].lower()
        if name not in OPCODES or len(words) != (1 if name == 'end' else 2):
            raise ValueError(f'line {lineno}: invalid instruction/operand count')
        arg = imm = 0
        if name != 'end':
            value = labels[words[1]] if name in ('jz', 'jnz') and words[1] in labels else int(words[1], 0)
            if name in ('save', 'load'):
                if not 0 <= value < 8:
                    raise ValueError(f'line {lineno}: voice must be 0..7')
                arg = value
            elif name in ('jz', 'jnz'):
                if not pc < value <= len(rows):
                    raise ValueError(f'line {lineno}: branches must go forward')
                arg = value
            else:
                if name == 'rol' and not 0 <= value <= 63:
                    raise ValueError(f'line {lineno}: rotation must be 0..63')
                imm = value & ((1 << 64) - 1)
        output.extend(struct.pack('<BBHQ', OPCODES[name], 0, arg, imm))
    return bytes(output)

def main():
    parser = argparse.ArgumentParser(description='Assemble a Pocket Orchestra score into a load command.')
    parser.add_argument('score', help='UTF-8 score file, or - for stdin')
    args = parser.parse_args()
    try:
        source = sys.stdin.read() if args.score == '-' else pathlib.Path(args.score).read_text(encoding='utf-8-sig')
        print('load ' + assemble(source).hex())
    except (OSError, ValueError) as error:
        parser.exit(2, f'error: {error}\n')

if __name__ == '__main__':
    main()
