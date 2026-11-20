"""Fran científico loco desde hojas/fran.png (fondo magenta, una animación por fila):
  1 espera (4) · 2 invento (7) · 3 mezcla (6) · 4 explosión (6) · 5 caminar (8) · 6 dormido (4)

Uso:  python fran.py hojas/fran.png salida/fran
"""
import sys, os, json, numpy as np
from PIL import Image
from scipy import ndimage as nd

src, out = sys.argv[1], sys.argv[2]
ALTO = int(os.environ.get('ALTO', 104))
FILAS = ['espera', 'invento', 'mezcla', 'explosion', 'caminar', 'dormido']
CUADROS = [4, 7, 6, 6, 8, 4]

a = np.array(Image.open(src).convert('RGB')).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
# fondo = magenta conectado con el borde (el líquido violeta de los frascos queda adentro y no se borra)
mag = (r > 150) & (b > 150) & (g < 120) & (np.abs(r - b) < 70)
lab, _ = nd.label(mag)
borde = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
fondo = np.isin(lab, list(borde))
# huecos de fondo encerrados (dentro del humo, del anillo de mareo): magenta puro, rojo ≈ azul y altos.
# Las pociones violetas tienen bastante menos rojo que azul, así que no entran.
fondo |= (g < 30) & (r > 220) & (b > 215) & (np.abs(r - b) < 25)
fg = nd.binary_opening(~fondo, iterations=1)

# filas: franjas horizontales con contenido
filas_y, en, y0 = [], False, 0
for y, hay in enumerate(fg.any(1)):
    if hay and not en: en, y0 = True, y
    if not hay and en:
        en = False
        if y - y0 > 40: filas_y.append((y0, y))
if en: filas_y.append((y0, len(fg)))
assert len(filas_y) == len(FILAS), f'se esperaban {len(FILAS)} filas y hay {len(filas_y)}: {filas_y}'


def cuadros_de(y0, y1, n):
    """Figuras de una fila (las n más grandes) con sus efectos (chispas, humo, zzz) asignados a la más cercana."""
    sub = fg[y0:y1]
    lab, k = nd.label(sub, structure=np.ones((3, 3)))
    objs = nd.find_objects(lab)
    sizes = nd.sum(sub, lab, range(1, k + 1))
    figs = sorted(sorted(range(k), key=lambda i: -sizes[i])[:n], key=lambda i: objs[i][1].start)
    grupos = {f: [f] for f in figs}
    for i in range(k):
        if i in grupos or sizes[i] < 6: continue
        cx = (objs[i][1].start + objs[i][1].stop) / 2
        f = min(figs, key=lambda f: 0 if objs[f][1].start <= cx <= objs[f][1].stop else min(abs(cx - objs[f][1].start), abs(cx - objs[f][1].stop)))
        grupos[f].append(i)
    res = []
    for f in figs:
        cuerpo = nd.binary_erosion(lab == f + 1, iterations=2)          # sin el borde rosado
        extras = np.isin(lab, [i + 1 for i in grupos[f] if i != f])     # efectos finitos: enteros
        res.append((cuerpo, cuerpo | extras, y0))
    return res


filas = {nombre: cuadros_de(y0, y1, n) for nombre, (y0, y1), n in zip(FILAS, filas_y, CUADROS)}
# escala: el alto de Fran parado (1.er cuadro de "espera") pasa a ALTO
cuerpo0 = filas['espera'][0][0]
ys = np.where(cuerpo0.any(1))[0]
k = ALTO / (ys.max() - ys.min() + 1)


# algunas filas vienen dibujadas un poco más chicas: se igualan con el alto de su primer cuadro parado
ESCALA_FILA = {}
for fila in ('caminar',):
    c0 = filas[fila][0][0]; yy = np.where(c0.any(1))[0]
    ESCALA_FILA[fila] = (ys.max() - ys.min() + 1) / (yy.max() - yy.min() + 1)


def recorte(mask, y0, fila=None):
    kk = k * ESCALA_FILA.get(fila, 1)
    ys, xs = np.where(mask)
    t, bt, l, rr = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([a[y0 + t:y0 + bt, l:rr].astype(np.uint8), (mask[t:bt, l:rr] * 255).astype(np.uint8)])
    im = Image.fromarray(rgba, 'RGBA')
    im = im.convert('RGBa').resize((max(1, round(im.width * kk)), max(1, round(im.height * kk))), Image.LANCZOS).convert('RGBA')
    return im, l, bt


def guardar_anim(nombre, frames, carpeta):
    """Cuadros alineados por el centro del cuerpo y con el piso abajo."""
    ims, anc = [], []
    for cuerpo, todo, y0 in frames:
        im, l, bt = recorte(todo, y0)
        ys, xs = np.where(cuerpo)
        cx = (xs.mean() - l) * k
        piso = (np.where(todo.any(1))[0].max() + 1 - ys.max() - 1) * k   # lo que sobresale por debajo de los pies
        ims.append(im); anc.append((cx, piso))
    L = max(cx for cx, _ in anc); R = max(im.width - cx for im, (cx, _) in zip(ims, anc))
    H = max(im.height for im in ims); W = int(np.ceil(L + R))
    os.makedirs(os.path.join(out, carpeta), exist_ok=True)
    for j, (im, (cx, _)) in enumerate(zip(ims, anc)):
        c = Image.new('RGBA', (W, H)); c.alpha_composite(im, (int(round(L - cx)), H - im.height))
        c.save(os.path.join(out, carpeta, f'{j + 1}.png'))
    return len(ims)


os.makedirs(out, exist_ok=True)
POSES = {'parado': ('espera', 0), 'caminando': ('caminar', 2), 'festejo': ('invento', 5), 'sentado': ('dormido', 0)}
for pose, (fila, i) in POSES.items():
    cuerpo, todo, y0 = filas[fila][i]
    recorte(todo, y0, fila)[0].save(os.path.join(out, pose + '.png'))

ANIMS = {
    'invento':   dict(fila='invento',   titulo='su invento funciona', ms=330, pausa=1400),
    'mezcla':    dict(fila='mezcla',    titulo='mezcla dos frascos', ms=380, pausa=1200),
    'explosion': dict(fila='explosion', titulo='le explota el experimento', ms=420, pausa=2000),
}
man = {'podio': {'gana': 'invento', 'otro': 'mezcla', 'ultimo': 'explosion'}, 'animaciones': {}}
for nombre, d in ANIMS.items():
    n = guardar_anim(nombre, filas[d['fila']], nombre)
    man['animaciones'][nombre] = {'titulo': d['titulo'], 'cuadros': n, 'ms': d['ms'], 'pausa': d['pausa'], 'alto': ALTO}
lines = ',\n'.join(f'    {json.dumps(n) + ":":<12} {json.dumps(v, ensure_ascii=False)}' for n, v in man['animaciones'].items())
open(os.path.join(out, 'animaciones.json'), 'w', encoding='utf-8').write(
    '{\n  "podio": ' + json.dumps(man['podio']).replace('{', '{ ').replace('}', ' }') + ',\n  "animaciones": {\n' + lines + '\n  }\n}\n')

# vista previa
prev = [[Image.open(os.path.join(out, p + '.png')) for p in POSES]]
for nombre, v in man['animaciones'].items():
    prev.append([Image.open(os.path.join(out, nombre, f'{j + 1}.png')) for j in range(v['cuadros'])])
W = max(sum(i.width + 8 for i in fila) for fila in prev); H = sum(max(i.height for i in fila) + 8 for fila in prev)
c = Image.new('RGBA', (W, H), (22, 26, 32, 255)); y = 0
for fila in prev:
    h = max(i.height for i in fila); x = 0
    for i in fila: c.alpha_composite(i, (x, y + h - i.height)); x += i.width + 8
    y += h + 8
c.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(os.path.dirname(out) or '.', 'prev_fran.png'))
print(f'fran: escala {k:.3f}')
