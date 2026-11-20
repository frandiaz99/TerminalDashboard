import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from sheet import Sheet
from skin import tone
BANDS = {
 'final': (4, 786, 34, 184), 'poses': (797, 1532, 34, 184),
 'base': (4, 735, 216, 332),
 'salto': (4, 540, 365, 476), 'caida': (548, 980, 365, 476), 'objeto': (990, 1532, 365, 476),
 'caminata': (4, 428, 508, 587), 'carrera': (434, 842, 508, 587), 'idle': (850, 1165, 508, 587), 'girar': (1172, 1532, 508, 587),
 'trofeo': (4, 535, 592, 712), 'derrota': (542, 908, 618, 712), 'mascota': (916, 1532, 618, 712),
 'interaccion': (4, 548, 740, 812), 'escena': (555, 1532, 740, 812),
 'd_idle': (4, 253, 860, 897), 'd_camina': (258, 530, 860, 897), 'd_corre': (535, 836, 860, 897), 'd_salto': (841, 1143, 860, 897), 'd_caida': (1148, 1532, 860, 897),
 'd_giros': (4, 335, 916, 957), 'd_uso': (340, 729, 916, 957), 'd_celebra': (734, 1127, 899, 957), 'd_derrota': (1133, 1532, 916, 957),
 'd_cotidiana': (4, 585, 962, 1016), 'd_escena': (590, 1532, 976, 1016),
}
BLANK = [(0, 589, 445, 618), (740, 899, 900, 916), (10, 960, 330, 976)]
S = Sheet(sys.argv[1], BANDS, blank=BLANK, shadow_azul=True)
S.a = tone(S.a.astype(np.uint8), (253, 176, 108), (227, 137, 76), smin=.30, smax=.80).astype(int)   # un tono de piel más
BIG = {k: 200 for k in BANDS if k.startswith('d_')}
BIG.update(mascota=600)
for n in BANDS: S.groups(n, big=BIG.get(n, 1500))
if __name__ == '__main__' and len(sys.argv) < 3:
    for n in BANDS:
        g = S.groups(n)
        print(n, len(g), [(int(b['box'][0] + b['off'][0]), int(b['box'][2] - b['box'][0]), int(b['box'][3] - b['box'][1])) for b in g])

STAND = dict(final=136, poses=104, base=103, salto=95, caida=95, objeto=122, caminata=86, carrera=86, idle=87, girar=87,
             trofeo=94, derrota=102, interaccion=105, escena=101, mascota=60)
if __name__ == '__main__' and len(sys.argv) >= 3:
    from build import build
    from PIL import Image
    r = lambda b, n, s=0: [(b, i) for i in range(s, s + n)]
    out = sys.argv[2]
    build(S, STAND, out,
        poses={'parado': ('final', 0), 'caminando': ('caminata', 2), 'festejo': ('poses', 5), 'sentado': ('poses', 6)},
        anims={
            'trofeo':  dict(titulo='levanta la copa', frames=r('trofeo', 7), ms=420, pausa=1400),
            'dino':    dict(titulo='juega con el dino', frames=r('interaccion', 4), ms=700, pausa=1600, mascota=True, anclaje='talon'),
            'derrota': dict(titulo='queda tirado en el piso', frames=r('derrota', 6), ms=500, pausa=2000),
            'compu':   dict(titulo='usa la compu con el dino', frames=r('escena', 7), ms=450, mascota=True, anclaje='talon'),
            'caminar': dict(titulo='camina', frames=r('caminata', 8), ms=130),
            'correr':  dict(titulo='corre', frames=r('carrera', 8), ms=100),
            'saltar':  dict(titulo='salta', frames=r('salto', 9), ms=150, pausa=600),
            'caer':    dict(titulo='cae y aterriza', frames=r('caida', 6), ms=180, pausa=900),
            'objetos': dict(titulo='usa sus cosas', frames=r('objeto', 5), ms=1200),
            'espera':  dict(titulo='espera', frames=r('idle', 4), ms=600),
            'girar':   dict(titulo='gira', frames=r('girar', 5), ms=400),
            'posa':    dict(titulo='posa', frames=r('final', 9), ms=1100),
        },
        podio={'gana': 'trofeo', 'otro': 'dino', 'ultimo': 'derrota'},
        preview='salida/prev_nico.png')
    # mascota: imagen fija
    from build import ALTO
    S.cut('mascota', 0, ALTO / STAND['final'] if ALTO < 104 else 1).save(out + '_dino.png')
