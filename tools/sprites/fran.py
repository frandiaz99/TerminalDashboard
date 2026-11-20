import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sheet import Sheet
BANDS = {
 'final': (4, 722, 8, 190),
 'caminata': (4, 452, 232, 358), 'corrida': (461, 934, 232, 358), 'saltar': (943, 1180, 232, 358), 'caer': (1189, 1444, 232, 358),
 'bloques': (4, 802, 392, 566),
 'caparazon': (4, 754, 650, 764), 'powerups': (764, 1444, 650, 764),
 'tubos': (4, 518, 808, 927), 'trofeo': (971, 1444, 776, 927),
 'derrota': (4, 415, 970, 1062), 'idle': (425, 792, 970, 1062),
}
BLANK = [(0, 399, 400, 404), (432, 399, 805, 404), (0, 566, 805, 608), (975, 770, 1358, 808)]
S = Sheet(sys.argv[1], BANDS, blank=BLANK)
if __name__ == '__main__' and len(sys.argv) < 3:
    for n in BANDS:
        g = S.groups(n, big=2600 if n == 'bloques' else 1500)
        print(n, len(g), [(int(b['box'][0] + b['off'][0]), int(b['box'][2] - b['box'][0]), int(b['box'][3] - b['box'][1])) for b in g])

if __name__ == '__main__' and len(sys.argv) >= 3:
    from build import build
    S.groups('bloques', big=2600)
    stand = dict(final=155, caminata=103, corrida=103, saltar=103, caer=103, bloques=110, caparazon=103, powerups=104, tubos=101, trofeo=103, derrota=102, idle=91)
    r = lambda b, n, s=0: [(b, i) for i in range(s, s + n)]
    build(S, stand, sys.argv[2],
        poses={'parado': ('final', 0), 'caminando': ('caminata', 2), 'festejo': ('powerups', 6)},
        anims={
            'trofeo':    dict(titulo='levanta la copa', frames=r('trofeo', 6), ms=420, pausa=1400),
            'bloques':   dict(titulo='golpea el bloque', frames=r('bloques', 5), ms=330, pausa=1100, anclaje='bloque', suelo=0),
            'derrota':   dict(titulo='queda tirado en el piso', frames=r('derrota', 4), ms=550, pausa=2000, anclaje='talon'),
        },
        podio={'gana': 'trofeo', 'otro': 'bloques', 'ultimo': 'derrota'},
        preview='salida/prev_fran.png')
