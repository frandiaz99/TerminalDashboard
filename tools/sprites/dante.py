import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sheet import Sheet
BANDS = {
 'final': (4, 790, 8, 198), 'poses': (802, 1532, 50, 198),
 'caminata': (4, 486, 242, 372), 'corrida': (494, 1029, 242, 372), 'saltar': (1036, 1278, 242, 372), 'caer': (1285, 1532, 242, 372),
 'interaccion': (4, 788, 412, 520), 'moto': (796, 1532, 412, 520),
 'uso': (4, 988, 560, 684), 'trofeo': (996, 1532, 528, 684),
 'idle': (1060, 1532, 722, 806),
 'giros': (4, 330, 842, 926), 'sentarse': (340, 667, 842, 926), 'acostarse': (675, 1031, 842, 926), 'otros': (1039, 1532, 842, 926),
}
S = Sheet(sys.argv[1], BANDS, blank=[(1000, 525, 1436, 561)])
if __name__ == '__main__':
    for n in BANDS:
        g = S.groups(n)
        print(n, len(g), [(int(b['box'][0] + b['off'][0]), int(b['box'][2] - b['box'][0]), int(b['box'][3] - b['box'][1])) for b in g])

    from build import build
    stand = dict(final=164, poses=109, caminata=101, corrida=100, saltar=100, caer=100, interaccion=89, moto=89, uso=107, trofeo=99, idle=76, giros=75, sentarse=88, acostarse=88, otros=75)
    r = lambda b, n, s=0: [(b, i) for i in range(s, s + n)]
    build(S, stand, sys.argv[2],
        poses={'parado': ('final', 0), 'caminando': ('caminata', 2), 'festejo': ('poses', 5), 'sentado': ('sentarse', 1)},
        anims={
            'trofeo':  dict(titulo='levanta la copa', frames=r('trofeo', 6), ms=420, pausa=1400),
            'moto':    dict(titulo='anda en moto', frames=r('moto', 8), ms=130),
            'caminar': dict(titulo='camina', frames=r('caminata', 7), ms=140),
            'correr':  dict(titulo='corre', frames=r('corrida', 8), ms=100),
            'mate':    dict(titulo='toma mate', frames=r('uso', 6), ms=520, pausa=1000),
            'leer':    dict(titulo='lee el mapa', frames=r('uso', 2, 6), ms=900),
            'compu':   dict(titulo='usa la compu', frames=r('uso', 2, 8), ms=700),
            'espera':  dict(titulo='espera', frames=r('idle', 4), ms=600),
            'posa':    dict(titulo='posa', frames=r('final', 8), ms=1100),
        },
        podio={'gana': 'trofeo', 'otro': 'moto'},
        preview='salida/prev_dante.png')
