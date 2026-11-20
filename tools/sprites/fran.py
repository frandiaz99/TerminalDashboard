"""Fran científico loco desde hojas/fran.png (fondo magenta, una animación por fila):
  espera (4) · invento (7) · mezcla (6) · explosión (6) · caminar (8) · dormido (4)

Uso:  python fran.py hojas/fran.png salida/fran
"""
import sys, os
from magenta import procesar

procesar(sys.argv[1], sys.argv[2],
    filas=['espera', 'invento', 'mezcla', 'explosion', 'caminar', 'dormido'],
    cuadros=[4, 7, 6, 6, 8, 4],
    referencia=('espera', 0),
    igualar={'caminar': 'caminar', 'hulk': 'hulk'},
    sin_tinte=['hulk'],
    extras=[dict(src=os.path.join(os.path.dirname(sys.argv[1]), 'fran_hulk.png'), filas=['hulk'], cuadros=[20], por_columnas=['hulk'])],
    poses={'parado': ('espera', 0), 'caminando': ('caminar', 2), 'festejo': ('invento', 5), 'sentado': ('dormido', 0)},
    anims={
        'invento':   dict(fila='invento',   titulo='su invento funciona', ms=330, pausa=1400),
        'hulk':      dict(fila='hulk',      titulo='se toma la mezcla y se vuelve Hulk', ms=200, pausa=1500, anclaje='talon', bucle='natural', pausaEn=13),
        'explosion': dict(fila='explosion', titulo='le explota el experimento', ms=420, pausa=2000),
        'espera':  dict(fila='espera',  titulo='espera', ms=600, pausa=600, bucle='natural'),
        'dormido': dict(fila='dormido', titulo='se queda dormido', ms=700, pausa=2400),
    },
    podio={'gana': 'invento', 'otro': 'hulk', 'ultimo': 'explosion'},
    prev='salida/prev_fran.png')
