"""Dante desde hojas/dante.png (fondo magenta, una animación por fila):
  espera (4) · trofeo (7) · moto con caballito (8) · derrota con la moto (6) · dormido en el casco (4) · caminar (8)

Uso:  python dante.py hojas/dante.png salida/dante
"""
import sys
from magenta import procesar

procesar(sys.argv[1], sys.argv[2],
    filas=['espera', 'trofeo', 'moto', 'derrota', 'dormido', 'caminar'],
    cuadros=[4, 7, 8, 6, 4, 8],
    referencia=('espera', 0),
    igualar=['trofeo', 'caminar'],
    por_columnas=['moto', 'derrota'],
    sin_tinte=True,
    poses={'parado': ('espera', 0), 'caminando': ('caminar', 2), 'festejo': ('trofeo', 6), 'sentado': ('dormido', 0)},
    anims={
        'trofeo':  dict(fila='trofeo',  titulo='levanta la copa', ms=420, pausa=1400),
        'moto':    dict(fila='moto',    titulo='anda en moto y hace un caballito', ms=160, pausa=1400, anclaje='grande'),
        'derrota': dict(fila='derrota', titulo='se le pincha la rueda y sale volando', ms=380, pausa=2200, anclaje='grande'),
    },
    podio={'gana': 'trofeo', 'otro': 'moto', 'ultimo': 'derrota'},
    prev='salida/prev_dante.png')
