import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from seg import *
OUT = sys.argv[2] if len(sys.argv) > 2 else 'out/andy'
ALTO = int(os.environ.get('ALTO', 104))
STAND = {'final': 184, 'poses': 119, 'mate': 160, 'piano': 160, 'trofeo': 137, 'piso': 137}
G = {n: groups(n) for n in BANDS}
# la espiral de mareo queda sobre el 2.º cuadro de "piso": moverla desde el 3.º
p = G['piso']; f2, f3 = p[1], p[2]
lab, n = nd.label(f3['mask'], structure=np.ones((3, 3)))
x2 = f2['box'][2]
for i, sl in enumerate(nd.find_objects(lab)):
    if (lab[sl] == i + 1).sum() < 1500 and sl[1].start < x2 + 40:
        m = lab == i + 1; f3['mask'] &= ~m; f2['mask'] |= m
for f in (f2, f3):
    ys, xs = np.where(f['mask']); f['box'] = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)

def cut(band, i):
    g = G[band][i]; x0, y0, x1, y1 = g['box']; ox, oy = g['off']
    m = nd.binary_erosion(g['mask'], iterations=1)[y0:y1, x0:x1]
    rgb = a[oy + y0:oy + y1, ox + x0:ox + x1].astype(np.uint8)
    im = np.dstack([rgb, (m * 255).astype(np.uint8)])
    k = ALTO / STAND[band]
    img = Image.fromarray(im, 'RGBA')
    w, h = max(1, round(img.width * k)), max(1, round(img.height * k))
    pm = img.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA')
    arr = np.array(pm); al = arr[..., 3]
    arr[..., 3] = np.where(al < 40, 0, np.minimum(255, al * 1.15)).astype(np.uint8)
    out = Image.fromarray(arr, 'RGBA')
    return out.crop(out.getbbox())

def anchor(im, mode):
    al = np.array(im)[..., 3] > 0; h = al.shape[0]
    bot = al[int(h * .92):]
    xs = np.where(bot.any(0))[0]
    return xs.min() if mode == 'talon' else (xs.min() + xs.max()) / 2

def anim(name, frames, mode='pies'):
    ims = [cut(b, i) for b, i in frames]
    anc = [anchor(im, mode) for im in ims]
    L = max(an for an in anc); R = max(im.width - an for im, an in zip(ims, anc)); H = max(im.height for im in ims)
    W = int(np.ceil(L + R))
    os.makedirs(f'{OUT}/{name}', exist_ok=True)
    for j, (im, an) in enumerate(zip(ims, anc)):
        c = Image.new('RGBA', (W, H)); c.alpha_composite(im, (int(round(L - an)), H - im.height)); c.save(f'{OUT}/{name}/{j + 1}.png')
    return len(ims)

os.makedirs(OUT, exist_ok=True)
for pose, (b, i) in {'parado': ('final', 0), 'caminando': ('poses', 2), 'festejo': ('poses', 5), 'sentado': ('poses', 6)}.items():
    cut(b, i).save(f'{OUT}/{pose}.png')
A = {}
A['trofeo'] = dict(titulo='levanta la copa', cuadros=anim('trofeo', [('trofeo', i) for i in range(7)]), ms=420, pausa=1400, alto=ALTO)
A['piano'] = dict(titulo='toca el teclado', cuadros=anim('piano', [('piano', i) for i in range(6)]), ms=380, pausa=900, alto=ALTO)
A['piso'] = dict(titulo='queda tirado en el piso', cuadros=anim('piso', [('piso', i) for i in range(6)], 'talon'), ms=450, pausa=1800, alto=ALTO)
man = {'podio': {'gana': 'trofeo', 'otro': 'piano'}, 'animaciones': A}
lines = ',\n'.join(f'    {json.dumps(k) + ":":<10} {json.dumps(v, ensure_ascii=False)}' for k, v in A.items())
open(f'{OUT}/animaciones.json', 'w', encoding='utf-8').write('{\n  "podio": { "gana": "trofeo", "otro": "piano", "ultimo": "piso" },\n  "animaciones": {\n' + lines + '\n  }\n}\n')

# preview
rows = [[Image.open(f'{OUT}/{p}.png') for p in ['parado', 'caminando', 'festejo', 'sentado']]]
for k, v in A.items(): rows.append([Image.open(f'{OUT}/{k}/{j + 1}.png') for j in range(v['cuadros'])])
W = max(sum(i.width + 8 for i in r) for r in rows); H = sum(max(i.height for i in r) + 8 for r in rows)
c = Image.new('RGBA', (W, H), (70, 110, 70, 255)); y = 0
for r in rows:
    h = max(i.height for i in r); x = 0
    for i in r: c.alpha_composite(i, (x, y + h - i.height)); x += i.width + 8
    y += h + 8
c.resize((W * 2, H * 2), Image.NEAREST).save(os.environ.get('PREVIEW', 'preview.png'))
