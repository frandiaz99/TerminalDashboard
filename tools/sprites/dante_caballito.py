"""Agrega a Dante la animación "caballito" desde hojas/dante_caballito.png (fondo magenta, 3 cuadros:
andando, levantando la rueda, caballito completo).

Uso:  python dante_caballito.py hojas/dante_caballito.png salida/dante
Se corre después de dante.py (necesita salida/dante/moto/ para igualar la escala) y antes de pixelize.py.
"""
import sys, os, json, numpy as np
from PIL import Image
from scipy import ndimage as nd

src, out = sys.argv[1], sys.argv[2]
ALTO = int(os.environ.get('ALTO', 104))

a = np.array(Image.open(src).convert('RGB')).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
magenta = (r > 150) & (b > 150) & (g < 120) & (np.abs(r - b) < 70)
fg = nd.binary_opening(~magenta, iterations=2)
fg = nd.binary_erosion(fg, iterations=2)          # saca el borde rosado que deja el fondo
lab, n = nd.label(fg)
sizes = nd.sum(fg, lab, range(1, n + 1))
figs = sorted([i + 1 for i in range(n) if sizes[i] > 5000], key=lambda i: np.where(lab == i)[1].min())
assert len(figs) == 3, f'se esperaban 3 cuadros y hay {len(figs)}'


def cabeza(alpha):
    """Ancho de la cabeza: el más ancho de las primeras filas con contenido (pelo)."""
    rows = np.where(alpha.any(1))[0]
    t = rows[0]
    return max(np.ptp(np.where(alpha[y])[0]) for y in range(t, t + max(4, len(rows) // 7)) if alpha[y].any())


# escala: la cabeza del cuadro 1 igual que la de la moto que ya tiene Dante
ref = np.array(Image.open(os.path.join(out, 'moto', '1.png')))[..., 3] > 0
m1 = lab == figs[0]
k = cabeza(ref) / cabeza(m1)

cuadros = []
for f in figs:
    m = lab == f
    ys, xs = np.where(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([a[y0:y1, x0:x1].astype(np.uint8), (m[y0:y1, x0:x1] * 255).astype(np.uint8)])
    im = Image.fromarray(rgba, 'RGBA')
    im = im.convert('RGBa').resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS).convert('RGBA')
    cuadros.append(im.crop(im.getbbox()))

# la rueda de atrás queda apoyada en el mismo lugar: se alinea por el punto más a la izquierda de abajo
def talon(im):
    al = np.array(im)[..., 3] > 0
    h = al.shape[0]
    return np.where(al[int(h * .9):].any(0))[0].min()

secuencia = [0, 1, 2, 2, 2, 1, 0]          # sube, se sostiene arriba, baja; en el último cuadro sigue andando (pausa)
anc = [talon(c) for c in cuadros]
L = max(anc); R = max(c.width - t for c, t in zip(cuadros, anc)); H = max(c.height for c in cuadros)
W = int(L + R)
os.makedirs(os.path.join(out, 'caballito'), exist_ok=True)
for j, i in enumerate(secuencia):
    c = Image.new('RGBA', (W, H)); c.alpha_composite(cuadros[i], (int(L - anc[i]), H - cuadros[i].height))
    c.save(os.path.join(out, 'caballito', f'{j + 1}.png'))

# animaciones.json: se agrega "caballito" y pasa a ser la del podio para 2.º y 3.º
fj = os.path.join(out, 'animaciones.json')
man = json.load(open(fj, encoding='utf-8'))
man['animaciones']['caballito'] = {'titulo': 'hace un caballito', 'cuadros': len(secuencia), 'ms': 200, 'pausa': 1800, 'alto': ALTO}
man['podio']['otro'] = 'caballito'
lines = ',\n'.join(f'    {json.dumps(n) + ":":<10} {json.dumps(v, ensure_ascii=False)}' for n, v in man['animaciones'].items())
open(fj, 'w', encoding='utf-8').write('{\n  "podio": ' + json.dumps(man['podio']).replace('{', '{ ').replace('}', ' }') + ',\n  "animaciones": {\n' + lines + '\n  }\n}\n')
print(f'caballito: {len(secuencia)} cuadros de {W}×{H} (escala {k:.3f})')
