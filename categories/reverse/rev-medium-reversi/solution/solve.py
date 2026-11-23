#!/usr/bin/env python3
"""
Решение: правит VIP-очки в сохранении и пересчитывает подпись.

    python3 solve.py [путь_к_profile.sav] [--vip 1000]

После этого запустить игру и открыть «VIP-зал».
"""
import argparse
import os
import re
import subprocess

# Ключ, восстановленный из бинарника (XOR-массив, ключ байта = 0x37 + 13*i)
BLOB = [0x0e, 0x22, 0x05, 0x7d, 0x1a, 0x4a, 0xc9, 0xea,
        0xbe, 0xda, 0xeb, 0xfe, 0x93, 0x8d, 0xb7, 0xcb]
KEY = "".join(chr(b ^ ((0x37 + 13 * i) & 0xff)) for i, b in enumerate(BLOB))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?",
                    default=os.path.expanduser("~/.reversi/profile.sav"))
    ap.add_argument("--vip", type=int, default=1000)
    args = ap.parse_args()

    text = open(args.path).read()
    f = dict(re.findall(r"^(\w+)=(.*)$", text, re.M))
    f["vip"] = str(args.vip)

    salt = f["sign"].split("$")[2]
    payload = "|".join([KEY, f["name"], f["vip"], f["coins"],
                        f["wins"], f["losses"], f["draws"]])

    # Тот самый «стандартный юниксовый» хэш: SHA-512 crypt ($6$)
    sign = subprocess.run(["openssl", "passwd", "-6", "-salt", salt, payload],
                          capture_output=True, text=True, check=True).stdout.strip()

    with open(args.path, "w") as out:
        out.write("[profile]\n")
        for k in ("name", "wins", "losses", "draws", "coins", "vip"):
            out.write(f"{k}={f[k]}\n")
        out.write(f"sign={sign}\n")

    print(f"key     = {KEY}")
    print(f"payload = {payload}")
    print(f"sign    = {sign}")
    print(f"[+] {args.path} обновлён, открой VIP-зал в игре")


if __name__ == "__main__":
    main()
