"""Preparación offline de datos para la beta de Gearly (Amazon Reviews 2023, Sports and Outdoors).

Uso:
    python -I scripts/preparar_datos.py <carpeta_con_csv_y_meta_filtrado.jsonl>

Entradas (en la carpeta indicada):
    Sports_and_Outdoors.{train,valid,test}.csv   (benchmark 5-core, partición temporal)
    meta_filtrado.jsonl                          (metadatos de los productos con interacciones)

Salidas (en data/):
    catalogo_beta.json   catálogo acotado con disciplina y tipo
    modelo_beta.json     popularidad y vecinos producto-producto, calculados SOLO con `train`

Sólo biblioteca estándar. El servidor no entrena nada: carga estos archivos al arrancar.
"""
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / 'data'
VERSION_CATALOGO = 'BETA-01'
VERSION_MODELO = 'POP-CONT2-CF-HIB-BETA-02'  # 02: el contenido pasa de disciplina/tipo a TF-IDF con categorías y título

CUPOS = {'running': 400, 'ciclismo': 900, 'entrenamiento': 900}
VECINOS_POR_PRODUCTO = 30
MAX_ITEMS_POR_USUARIO = 100

COLORES = {'running': '#cfe6d5', 'ciclismo': '#d4e8ff', 'entrenamiento': '#e7ddf8'}
ICONOS = {'calzado': '👟', 'ropa': '👕', 'accesorios': '🎒', 'proteccion': '🛡️', 'equipamiento': '🏋️'}


def palabra(texto, *claves):
    return any(re.search(r'\b' + k, texto) for k in claves)


def disciplina_de(cats, titulo):
    sub = cats[2] if len(cats) > 2 else ''
    todo = ' | '.join(cats).lower()
    t = titulo.lower()
    ruido = palabra(t, 'watts', 'generator', 'pepper', 'spray', 'medal', 'trophy', 'hanger', 'engine', 'flask', 'whiskey', 'rum\\b', 'cocktail') \
        or sub in ('Tactical & Personal Defense', 'Trophies, Medals & Awards', 'Auto Accessories', 'Fan Shop')
    if sub == 'Running' or (not ruido and sub != 'Cycling' and palabra(t, 'running', 'jogging', 'marathon', 'runners?\\b')):
        return 'running'
    if sub == 'Cycling':
        return 'ciclismo'
    if any(k in todo for k in ('strength training', 'cardio training', 'yoga', 'exercise machine',
                               'fitness technology', 'exercise balls', 'resistance bands', 'pilates',
                               'exercise & fitness', 'aerobic', 'balance trainers')):
        return 'entrenamiento'
    return None


def tipo_de(cats, titulo):
    t = (titulo + ' | ' + ' | '.join(cats)).lower()
    if palabra(titulo.lower(), 'shoes?\\b', 'sneakers?\\b', 'footwear') and not palabra(
            t, 'brake', 'clip', 'light', 'cover', 'gaiter', 'shield', 'sock', 'insole', 'lace', 'tire', 'bag', 'rack',
            'cleat', 'protector', 'polish', 'deodor', 'dryer'):
        return 'calzado'
    if palabra(t, 'helmet', 'knee pad', 'elbow pad', 'guard', 'protector', 'goggle', 'sunglass', 'eyewear', 'armor'):
        return 'proteccion'
    if palabra(t, 'jersey', 'shorts', 'bib\\b', 'apparel', 'clothing', 'socks?\\b', 'gloves?\\b', 'shirt',
               'tights', 'jacket', 'sleeves?\\b', 'headband', 'leggings', 'hoodie', 'pants'):
        return 'ropa'
    if palabra(t, 'parts & components', 'tires?\\b', 'tubes?\\b', 'bikes\\b', 'bicycles?\\b', 'machine', 'bench',
               'weights', 'dumbbell', 'kettlebell', 'barbell', 'plates', 'racks?\\b', 'trainer', 'mats?\\b',
               'rollers?\\b', 'resistance bands?', 'exercise balls?', 'treadmill', 'tools?\\b', 'pedals?\\b'):
        return 'equipamiento'
    return 'accesorios'


STOP = set('''the and for with from that this your you are our can has have not but all any one two set pack pcs piece
inch inches size sizes new best top high low use used using made make fits fit most more very per each also its
men women mens womens adult adults kids kid black white red blue green gray grey silver gold pink purple orange
yellow brown color colors colour compatible replacement perfect great good quality premium heavy duty easy
non lightweight'''.split())


def tokens_titulo(titulo, maximo=15):
    vistos = []
    for t in re.findall(r'[a-z]{3,}', titulo.lower()):
        if t not in STOP and t not in vistos:
            vistos.append(t)
    return vistos[:maximo]


def atributos_contenido(o, disciplina, tipo):
    """Rasgos del producto para el contenido v2: disciplina/tipo, ruta de categorías, palabras del título y marca."""
    cats = o['categories'] or []
    marca = (o.get('store') or '').strip().lower()
    return {
        'dt': [f'd:{disciplina}', f't:{tipo}'],
        'c': [c.strip() for c in cats[2:6] if c.strip()],
        'w': tokens_titulo(o['title']) + ([f'b:{marca}'] if marca else []),
    }


def limpiar(titulo, n=90):
    titulo = re.sub(r'\s+', ' ', re.sub('[\ufeff\u200b]', '', titulo)).strip()  # quita espacios y caracteres invisibles
    return titulo if len(titulo) <= n else titulo[:n - 1].rsplit(' ', 1)[0] + '…'


def leer_interacciones(carpeta, particion):
    with open(carpeta / f'Sports_and_Outdoors.{particion}.csv', encoding='utf-8') as f:
        lector = csv.reader(f)
        next(lector)
        for usuario, asin, _rating, ts in lector:
            yield usuario, asin, int(ts)


def main(carpeta):
    carpeta = Path(carpeta)
    meta = {}
    for linea in open(carpeta / 'meta_filtrado.jsonl', encoding='utf-8'):
        o = json.loads(linea)
        if o['title']:
            meta[o['parent_asin']] = o

    conteo = Counter()
    historial = defaultdict(list)
    for usuario, asin, ts in leer_interacciones(carpeta, 'train'):
        conteo[asin] += 1
        historial[usuario].append((ts, asin))

    candidatos = defaultdict(list)
    sin_clasificar = 0
    for asin, o in meta.items():
        cats = o['categories'] or []
        d = disciplina_de(cats, o['title'])
        if d is None:
            sin_clasificar += 1
            continue
        candidatos[d].append((conteo[asin], asin))

    catalogo = []
    atributos = {}
    for d, cupo in CUPOS.items():
        elegidos = sorted(candidatos[d], reverse=True)[:cupo]
        for n, asin in elegidos:
            if n == 0:
                continue
            o = meta[asin]
            cats = o['categories'] or []
            t = tipo_de(cats, o['title'])
            atributos[asin] = atributos_contenido(o, d, t)
            ruta = ' › '.join(cats[2:5]) or 'Deportes'
            tienda = f' · {o["store"]}' if o.get('store') else ''
            catalogo.append({
                'id': asin, 'nombre': limpiar(o['title']), 'disciplina': d, 'tipo': t,
                'descripcion': f'{ruta}{tienda}', 'color': COLORES[d], 'icono': ICONOS[t],
            })
    catalogo.sort(key=lambda p: p['id'])
    ids = {p['id'] for p in catalogo}

    # Popularidad: interacciones en train (sin mirar valid/test).
    popularidad = {i: conteo[i] for i in ids}

    # Filtrado colaborativo producto-producto (coseno sobre interacciones binarias, sólo train).
    co = defaultdict(Counter)
    for usuario, items in historial.items():
        items = [a for _, a in sorted(items) if a in ids]
        items = list(dict.fromkeys(items))[-MAX_ITEMS_POR_USUARIO:]
        for i in items:
            for j in items:
                if i != j:
                    co[i][j] += 1
    vecinos = {}
    for i, fila in co.items():
        sims = [(j, c / math.sqrt(popularidad[i] * popularidad[j])) for j, c in fila.items()]
        sims.sort(key=lambda x: (-x[1], x[0]))
        vecinos[i] = [[j, round(s, 5)] for j, s in sims[:VECINOS_POR_PRODUCTO]]

    SALIDA.mkdir(exist_ok=True)
    (SALIDA / 'catalogo_beta.json').write_text(json.dumps(catalogo, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (SALIDA / 'modelo_beta.json').write_text(json.dumps({
        'version': VERSION_MODELO, 'catalogo': VERSION_CATALOGO, 'fuente': 'Amazon Reviews 2023 · Sports and Outdoors · 5-core · partición temporal (train)',
        'popularidad': popularidad, 'vecinos': vecinos, 'atributos': atributos}, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')

    print('productos con metadatos:', len(meta), '· sin clasificar:', sin_clasificar)
    print('catálogo:', len(catalogo), dict(Counter(p['disciplina'] for p in catalogo)))
    print('tipos:', dict(Counter(p['tipo'] for p in catalogo)))
    print('productos con vecinos CF:', len(vecinos), 'de', len(ids))
    for f in ('catalogo_beta.json', 'modelo_beta.json'):
        print(f, round((SALIDA / f).stat().st_size / 1e6, 2), 'MB')


if __name__ == '__main__':
    main(sys.argv[1])
