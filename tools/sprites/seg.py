import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
src = sys.argv[1] if len(sys.argv) > 1 else "hojas/andy.png"
a = np.array(Image.open(src).convert('RGB')).astype(int)
BANDS = {  # name: (x0,x1,y0,y1)
 'final': (5, 832, 48, 258), 'poses': (846, 1446, 48, 258),
 'mate': (2, 818, 322, 530), 'piano': (828, 1446, 322, 530),
 'trofeo': (2, 674, 592, 770), 'piso': (686, 1446, 592, 770),
}
mn, mx = a.min(2), a.max(2)
bgish = ((mn > 222) & (mx - mn < 22)) | ((mn > 100) & (mx - mn < 18))   # fondo + sombras grises
def band(name):
    x0, x1, y0, y1 = BANDS[name]
    sub = bgish[y0:y1, x0:x1]
    lab, _ = nd.label(sub)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(edge))
    fg = ~bg
    fg = nd.binary_opening(fg, iterations=1)
    # quitar manchitas sueltas
    l2, n2 = nd.label(fg)
    sizes = nd.sum(fg, l2, range(1, n2 + 1))
    fg = np.isin(l2, [i + 1 for i, s in enumerate(sizes) if s >= 12])
    return fg, (x0, y0)
def frames(fg, gap=6):
    col = fg.sum(0) > 0
    runs, x = [], 0
    while x < len(col):
        if col[x]:
            s = x
            while x < len(col) and col[x]: x += 1
            runs.append([s, x])
        else: x += 1
    out = []
    for r in runs:
        if out and r[0] - out[-1][1] < gap: out[-1][1] = r[1]
        else: out.append(r)
    return out
if __name__ == '__main__':
    for n in BANDS:
        fg, (ox, oy) = band(n)
        fr = frames(fg)
        info = []
        for s, e in fr:
            rows = np.where(fg[:, s:e].any(1))[0]
            info.append((s + ox, e + ox, rows[0] + oy, rows[-1] + oy))
        print(n, len(fr), info)

def groups(name, big=1500):
    """Figuras (componentes grandes) con sus agregados chicos (chispas, notas, zzz) asignados a la más cercana."""
    fg, (ox, oy) = band(name)
    lab, n = nd.label(fg, structure=np.ones((3, 3)))
    objs = nd.find_objects(lab)
    sizes = nd.sum(fg, lab, range(1, n + 1))
    figs = [i for i in range(n) if sizes[i] >= big]
    figs.sort(key=lambda i: objs[i][1].start)
    assign = {i: [i] for i in figs}
    for i in range(n):
        if i in assign: continue
        sy, sx = objs[i]
        cx = (sx.start + sx.stop) / 2
        best = min(figs, key=lambda f: 0 if objs[f][1].start <= cx <= objs[f][1].stop else min(abs(cx - objs[f][1].start), abs(cx - objs[f][1].stop)))
        assign[best].append(i)
    out = []
    for f in figs:
        m = np.isin(lab, [k + 1 for k in assign[f]])
        ys, xs = np.where(m)
        out.append(dict(mask=m, box=(xs.min(), ys.min(), xs.max() + 1, ys.max() + 1), off=(ox, oy)))
    return out
