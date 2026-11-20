"""Animación "moto" de Dante desde hojas/dante_moto.png (fondo magenta, 8 cuadros en una fila: anda,
levanta la rueda, caballito, aterriza y vuelve a andar; con rayitas de velocidad y polvo detrás).

Uso:  python dante_moto.py hojas/dante_moto.png salida/dante
Se corre después de dante.py (usa salida/dante/parado.png para igualar la escala) y antes de pixelize.py.
Reemplaza la "moto" que venía de la hoja original y queda como la animación del podio para 2.º y 3.º.
"""
import sys, os, json, shutil, numpy as np
from PIL import Image
from scipy import ndimage as nd

src, out = sys.argv[1], sys.argv[2]
ALTO = int(os.environ.get('ALTO', 104))

a = np.array(Image.open(src).convert('RGB')).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
magenta = (r > 150) & (b > 150) & (g < 120) & (np.abs(r - b) < 70)
fg = nd.binary_opening(~magenta, iterations=1)
lab, n = nd.label(fg)
sizes = nd.sum(fg, lab, range(1, n + 1))
objs = nd.find_objects(lab)
figs = sorted([i for i in range(n) if sizes[i] > 5000], key=lambda i: objs[i].__getitem__(1).start)
assert len(figs) == 8, f'se esperaban 8 cuadros y hay {len(figs)}'
# rayitas y polvo: van detrás (a la izquierda) de su moto → al primer cuadro que empieza a su derecha
grupos = {f: [f] for f in figs}
for i in range(n):
    if i in grupos or sizes[i] < 20: continue
    x = objs[i][1].start
    dueño = next((f for f in figs if objs[f][1].start >= x - 20), figs[-1])
    grupos[dueño].append(i)


def cabeza(alpha):
    rows = np.where(alpha.any(1))[0]
    t = rows[0]
    return max(np.ptp(np.where(alpha[y])[0]) for y in range(t, t + max(4, len(rows) // 7)) if alpha[y].any())


# escala: cabeza del cuadro 1 igual a la de Dante parado
ref = np.array(Image.open(os.path.join(out, 'parado.png')))[..., 3] > 0
k = cabeza(ref) / cabeza(lab == figs[0] + 1)


def recorte(mask):
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([a[y0:y1, x0:x1].astype(np.uint8), (mask[y0:y1, x0:x1] * 255).astype(np.uint8)])
    im = Image.fromarray(rgba, 'RGBA')
    return im.convert('RGBa').resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS).convert('RGBA'), x0, y1


# piso común: el de la mayoría de los cuadros (así el que va en el aire queda en el aire)
piso = int(np.median([objs[f][0].stop for f in figs]))
cuadros, anclas = [], []
for f in figs:
    moto = nd.binary_erosion(lab == f + 1, iterations=2)       # a la figura grande se le saca el borde rosado
    extras = np.isin(lab, [i + 1 for i in grupos[f] if i != f])  # rayitas y polvo: finitos, se dejan enteros
    todo = moto | extras
    todo[piso:] = False                                       # nada por debajo del piso
    im, x0, y1 = recorte(todo)
    # ancla x: rueda de atrás de la moto sola (sin rayitas ni polvo), para que no "patine"
    ys, xs = np.where(moto)
    abajo = ys >= ys.max() - (ys.max() - ys.min()) * .1
    ax = (xs[abajo].min() - x0) * k
    cuadros.append(im); anclas.append((ax, (piso - y1) * k))  # cuánto queda el recorte por encima del piso

L = max(ax for ax, _ in anclas); R = max(c.width - ax for c, (ax, _) in zip(cuadros, anclas))
H = int(np.ceil(max(c.height + up for c, (_, up) in zip(cuadros, anclas))))
W = int(np.ceil(L + R))
for viejo in ('moto', 'caballito'):
    shutil.rmtree(os.path.join(out, viejo), ignore_errors=True)
os.makedirs(os.path.join(out, 'moto'), exist_ok=True)
for j, (c, (ax, ay)) in enumerate(zip(cuadros, anclas)):
    lienzo = Image.new('RGBA', (W, H)); lienzo.alpha_composite(c, (int(round(L - ax)), int(round(H - ay - c.height))))
    lienzo.save(os.path.join(out, 'moto', f'{j + 1}.png'))

fj = os.path.join(out, 'animaciones.json')
man = json.load(open(fj, encoding='utf-8'))
man['animaciones'].pop('caballito', None)
man['animaciones']['moto'] = {'titulo': 'anda en moto y hace un caballito', 'cuadros': len(cuadros), 'ms': 160, 'pausa': 1400, 'alto': ALTO}
man['podio']['otro'] = 'moto'
lines = ',\n'.join(f'    {json.dumps(n) + ":":<10} {json.dumps(v, ensure_ascii=False)}' for n, v in man['animaciones'].items())
open(fj, 'w', encoding='utf-8').write('{\n  "podio": ' + json.dumps(man['podio']).replace('{', '{ ').replace('}', ' }') + ',\n  "animaciones": {\n' + lines + '\n  }\n}\n')
print(f'moto: {len(cuadros)} cuadros de {W}x{H} (escala {k:.3f})')
