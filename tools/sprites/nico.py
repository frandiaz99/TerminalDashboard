"""Nico desde hojas/nico.png (fondo magenta, una animación por fila):
  trofeo (7) · juega con el dino (6) · derrota (6) · dormido leyendo (4) · espera (4) · dino solo (4)

Uso:  python nico.py hojas/nico.png salida/nico      (también escribe salida/nico_dino.png, la mascota)
"""
import sys, os
from magenta import procesar
from skin import tone

out = sys.argv[2]
procesar(sys.argv[1], out,
    filas=['trofeo', 'dino', 'derrota', 'dormido', 'espera', 'dino_solo'],
    cuadros=[7, 6, 6, 4, 4, 4],
    referencia=('espera', 0),
    igualar=['trofeo', 'derrota'],
    por_columnas=['dino'],
    # un tono de piel más oscuro que en la hoja (3.º de la paleta de tonos)
    transformar=lambda a: tone(a, (252, 172, 100), (226, 134, 70), smin=.30, smax=.80),
    poses={'parado': ('espera', 0), 'festejo': ('trofeo', 6), 'sentado': ('dormido', 0)},
    anims={
        'trofeo':  dict(fila='trofeo',  titulo='levanta la copa', ms=420, pausa=1400),
        'dino':    dict(fila='dino',    titulo='juega a la pelota con el dino', ms=450, pausa=1600, anclaje='talon', mascota=True),
        'derrota': dict(fila='derrota', titulo='queda tirado en el piso', ms=450, pausa=2000, anclaje='talon'),
    },
    podio={'gana': 'trofeo', 'otro': 'dino', 'ultimo': 'derrota'},
    mascota=('dino_solo', 0, os.path.join(os.path.dirname(out) or '.', 'nico_dino.png')),
    prev='salida/prev_nico.png')
