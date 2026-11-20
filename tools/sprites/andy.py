"""Andy desde hojas/andy.png (fondo magenta, una animación por fila):
  trofeo (7) · teclado (6) · derrota (6) · dormido con el mate (4) · espera (4) · mate (8)

Uso:  python andy.py hojas/andy.png salida/andy
"""
import sys
from magenta import procesar

procesar(sys.argv[1], sys.argv[2],
    filas=['trofeo', 'teclado', 'derrota', 'dormido', 'espera', 'mate'],
    cuadros=[7, 6, 6, 4, 4, 8],
    referencia=('espera', 0),
    igualar=['trofeo', 'derrota', 'mate'],
    poses={'parado': ('espera', 0), 'festejo': ('trofeo', 6), 'sentado': ('dormido', 0)},
    anims={
        'trofeo':  dict(fila='trofeo',  titulo='levanta la copa', ms=420, pausa=1400),
        'teclado': dict(fila='teclado', titulo='toca el teclado', ms=380, pausa=900),
        'derrota': dict(fila='derrota', titulo='queda tirado en el piso', ms=450, pausa=2000, anclaje='talon'),
    },
    podio={'gana': 'trofeo', 'otro': 'teclado', 'ultimo': 'derrota'},
    prev='salida/prev_andy.png')
