ALPHA = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"   # 32 буквы, Ё = Е
N = len(ALPHA)

SCROLL = "ТЮАЮВРЮВЪАЛВЛЪЫОЗЪСРИЭХЗХАВЮУ"            
SPELL = "ЖКЗТАЯШЕИЯЦФЯХХЯОСЙПААУХЗКИЧАНК"          
WINDOWS = ["vka{gr1ll", "3_0f_k0d0", "burg}l_5q", "lnu8wwa7u"]   

def shift(t, k): return "".join(ALPHA[(ALPHA.index(c) + k) % N] for c in t)
def vig_dec(t, key): return "".join(ALPHA[(ALPHA.index(c) - ALPHA.index(key[i % len(key)])) % N] for i, c in enumerate(t))

for k in range(N):
    p = shift(SCROLL, -k)
    if p.startswith("ВОРОТА"):
        print(f"I.   сдвиг {k} (буква {ALPHA[k]}): {p}")
        key = p[len("ВОРОТАОТКРЫТЫКЛЮЧКБАШНЕ"):]
        print(f"     ключ башни = {key}")

p2 = vig_dec(SPELL, key)
print(f"II.  {p2}")
print(f"     печать = {p2[len('ПЕЧАТЬБАШНИ'):-len('ОТКРОЕТРЕШЕТКУ')]}")

msg = "".join(WINDOWS)
print(f"III. {msg}")
print("     флаг = " + msg[:msg.index("}") + 1] + "   (после знака } идёт «пыль»)")
