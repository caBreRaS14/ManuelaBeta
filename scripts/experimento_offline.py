"""Experimento offline reproducible de Gearly (protocolo del capítulo III/IV).

Uso:
    python -I scripts/experimento_offline.py <carpeta_con_los_CSV> [--max-usuarios N]

Qué mide: la recuperación de interacciones POSTERIORES de un usuario a partir de k señales previas
(1, 3 o 5), comparando popularidad (POP), contenido (CONT), colaborativo entre productos (CF) e
híbrido (HIB). Usa el mismo `recomendar()` que sirve la aplicación, el catálogo beta y el modelo
precalculado con la partición `train` (data/modelo_beta.json).

Protocolo (fijado antes de ver resultados):
  * Partición temporal del benchmark 5-core de Amazon Reviews 2023: train < valid < test.
  * Señales = las k interacciones MÁS RECIENTES del usuario con productos del catálogo, anteriores al
    periodo evaluado. No se reconstruyen intereses declarados: el perfil sale sólo de esas señales.
  * Candidatos = catálogo menos las k señales (igual que la aplicación).
  * Relevantes = interacciones del usuario en el periodo evaluado con productos del catálogo.
  * Usuarios elegibles: >= 5 interacciones previas en el catálogo y >= 1 relevante. Mismo conjunto de
    usuarios para k = 1, 3 y 5. Si hay más de --max-usuarios se muestrea con semilla fija.
  * AJUSTE (valid): sólo se usa para explorar el peso del híbrido (0.25, 0.5, 0.75). Es exploratorio.
  * PRUEBA (test): historial = train + valid; peso del híbrido = 0.5 FIJO (el de la aplicación).
  * Análisis principal: k = 3, K = 10, diferencia media de NDCG@10 HIB - CONT con IC 95 % bootstrap.
    Los demás escenarios son secundarios y no sustituyen al principal.
  * Listas que caen a la alternativa genérica NO se descartan: se evalúa la lista genérica que vería el
    usuario y se informa la frecuencia.

Sólo biblioteca estándar.
"""
import argparse
import csv
import json
import math
import random
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'backend'))
from app import recommender as R  # noqa: E402

K = 10
SENALES = (1, 3, 5)
# contenido_v1 = representación binaria disciplina/tipo (4.1.5 del documento); contenido = v2 (TF-IDF con categorías y título).
METODOS = ('popularidad', 'contenido_v1', 'contenido', 'colaborativo', 'hibrido')
SIGLAS = {'popularidad': 'POP', 'contenido_v1': 'CONT-v1', 'contenido': 'CONT', 'colaborativo': 'CF', 'hibrido': 'HIB'}
SEMILLA = 20261104
MIN_HISTORIAL = 5


def leer(carpeta, particion, ids):
    with open(Path(carpeta) / f'Sports_and_Outdoors.{particion}.csv', encoding='utf-8') as f:
        lector = csv.reader(f)
        next(lector)
        for usuario, asin, _rating, ts in lector:
            if asin in ids:
                yield usuario, asin, int(ts)


def por_usuario(filas):
    d = defaultdict(list)
    for u, a, ts in filas:
        d[u].append((ts, a))
    for u in d:
        d[u].sort()
    return d


def metricas(lista, relevantes):
    aciertos = [1 if i in relevantes else 0 for i in lista]
    dcg = sum(r / math.log2(pos + 2) for pos, r in enumerate(aciertos))
    idcg = sum(1 / math.log2(pos + 2) for pos in range(min(len(relevantes), K)))
    n = sum(aciertos)
    return dcg / idcg if idcg else 0.0, n / K, n / len(relevantes)


def evaluar(usuarios, historiales, objetivos, productos, modelo, ks, metodos, alfa):
    """Devuelve {(k, metodo): {'ndcg': [...], 'prec': [...], 'rec': [...], 'items': set, 'genericas': n}}."""
    R.PESO_CONTENIDO = alfa
    modelo_v1 = {k: v for k, v in modelo.items() if k != 'atributos'}
    out = {(k, m): {'ndcg': [], 'prec': [], 'rec': [], 'items': set(), 'genericas': 0} for k in ks for m in metodos}
    for u in usuarios:
        hist = [a for _, a in historiales[u]]
        rel = {a for _, a in objetivos[u]}
        for k in ks:
            senales = hist[-k:]
            for m in metodos:
                r = R.recomendar(productos, [], [], senales, limite=K, metodo='contenido' if m == 'contenido_v1' else m,
                                 modelo=modelo_v1 if m == 'contenido_v1' else modelo)
                lista = [x['producto']['id'] for x in r['resultados']]
                nd, pr, rc = metricas(lista, rel)
                o = out[(k, m)]
                o['ndcg'].append(nd)
                o['prec'].append(pr)
                o['rec'].append(rc)
                o['items'].update(lista)
                o['genericas'] += r['metodo'] == 'generico'
    return out


def linea_base_azar(usuarios, historiales, objetivos, productos, ks, repeticiones=30):
    """NDCG@10 de 10 productos al azar (candidatos = catálogo menos las señales), promedio de varias repeticiones."""
    rng = random.Random(SEMILLA)
    ids = [p['id'] for p in productos]
    out = {}
    for k in ks:
        medias = []
        for _ in range(repeticiones):
            nd = []
            for u in usuarios:
                senales = {a for _, a in historiales[u][-k:]}
                lista = rng.sample([i for i in ids if i not in senales], K)
                nd.append(metricas(lista, {a for _, a in objetivos[u]})[0])
            medias.append(media(nd))
        out[k] = {'media': media(medias), 'min': min(medias), 'max': max(medias)}
    return out


def media(xs):
    return sum(xs) / len(xs) if xs else 0.0


def bootstrap_ic(difs, n=2000):
    rng = random.Random(SEMILLA)
    N = len(difs)
    medias = sorted(sum(rng.choices(difs, k=N)) / N for _ in range(n))
    return medias[int(0.025 * n)], medias[int(0.975 * n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('carpeta')
    ap.add_argument('--max-usuarios', type=int, default=5000)
    ap.add_argument('--salida', default='resultados_offline.json')
    args = ap.parse_args()
    t0 = time.perf_counter()

    productos = json.loads((RAIZ / 'data' / 'catalogo_beta.json').read_text(encoding='utf-8'))
    modelo = json.loads((RAIZ / 'data' / 'modelo_beta.json').read_text(encoding='utf-8'))
    ids = {p['id'] for p in productos}
    train, valid, test = (por_usuario(leer(args.carpeta, s, ids)) for s in ('train', 'valid', 'test'))

    def elegibles(historial_fn, objetivos):
        us = sorted(u for u in objetivos if len(historial_fn(u)) >= MIN_HISTORIAL)
        total = len(us)
        if len(us) > args.max_usuarios:
            us = sorted(random.Random(SEMILLA).sample(us, args.max_usuarios))
        return us, total

    # --- AJUSTE (valid): historial = train
    h_val = {u: train[u] for u in valid if u in train}
    us_val, tot_val = elegibles(lambda u: h_val.get(u, []), {u: valid[u] for u in valid if u in h_val})
    ajuste = {}
    for alfa in (0.25, 0.5, 0.75):
        o = evaluar(us_val, h_val, valid, productos, modelo, (3,), ('hibrido',), alfa)
        ajuste[alfa] = media(o[(3, 'hibrido')]['ndcg'])
    o_cont = evaluar(us_val, h_val, valid, productos, modelo, (3,), ('contenido', 'contenido_v1'), 0.5)
    cont_val, cont_val_v1 = o_cont[(3, 'contenido')]['ndcg'], o_cont[(3, 'contenido_v1')]['ndcg']
    print(f'[ajuste] usuarios={len(us_val)} (elegibles {tot_val})', {a: round(v, 4) for a, v in ajuste.items()}, 'CONT', round(media(cont_val), 4), 'CONT-v1', round(media(cont_val_v1), 4), flush=True)

    # --- PRUEBA (test): historial = train + valid (ambos anteriores a test)
    h_test = {u: sorted(train.get(u, []) + valid.get(u, [])) for u in test}
    us_test, tot_test = elegibles(lambda u: h_test[u], test)
    res = evaluar(us_test, h_test, test, productos, modelo, SENALES, METODOS, 0.5)
    print(f'[prueba] usuarios={len(us_test)} (elegibles {tot_test})', flush=True)

    azar = linea_base_azar(us_test, h_test, test, productos, SENALES)
    print('[azar] NDCG@10', {k: round(v['media'], 4) for k, v in azar.items()}, flush=True)

    # --- salida
    filas = []
    for k in SENALES:
        for m in METODOS:
            o = res[(k, m)]
            filas.append({'k': k, 'metodo': SIGLAS[m], 'ndcg10': media(o['ndcg']), 'precision10': media(o['prec']),
                          'recall10': media(o['rec']), 'cobertura': len(o['items']) / len(productos),
                          'listas_genericas': o['genericas'] / len(us_test)})
    difs = {}
    for k in SENALES:
        for m in ('popularidad', 'colaborativo', 'hibrido'):
            base = 'contenido'
            d = [a - b for a, b in zip(res[(k, m)]['ndcg'], res[(k, base)]['ndcg'])]
            lo, hi = bootstrap_ic(d)
            difs[f'{SIGLAS[m]} - CONT (k={k})'] = {'media': media(d), 'ic95': [lo, hi]}
    for k in SENALES:
        for m, base, nombre in (('contenido', 'contenido_v1', 'CONT - CONT-v1'), ('hibrido', 'contenido_v1', 'HIB - CONT-v1')):
            d = [a - b for a, b in zip(res[(k, m)]['ndcg'], res[(k, base)]['ndcg'])]
            lo, hi = bootstrap_ic(d)
            difs[f'{nombre} (k={k})'] = {'media': media(d), 'ic95': [lo, hi]}
    dh = [a - b for a, b in zip(res[(3, 'hibrido')]['ndcg'], res[(3, 'popularidad')]['ndcg'])]
    lo, hi = bootstrap_ic(dh)
    difs['HIB - POP (k=3)'] = {'media': media(dh), 'ic95': [lo, hi]}
    dc = [a - b for a, b in zip(res[(3, 'hibrido')]['ndcg'], res[(3, 'colaborativo')]['ndcg'])]
    lo, hi = bootstrap_ic(dc)
    difs['HIB - CF (k=3)'] = {'media': media(dc), 'ic95': [lo, hi]}

    resultado = {
        'fecha': date.today().isoformat(), 'semilla': SEMILLA, 'K': K, 'catalogo': modelo['catalogo'], 'modelo': modelo['version'],
        'usuarios_prueba': len(us_test), 'usuarios_elegibles_prueba': tot_test, 'usuarios_ajuste': len(us_val),
        'usuarios_elegibles_ajuste': tot_val, 'peso_hibrido_prueba': 0.5,
        'ajuste_ndcg10_hib_k3_por_peso_contenido': {str(a): v for a, v in ajuste.items()}, 'ajuste_ndcg10_cont_k3': media(cont_val), 'ajuste_ndcg10_cont_v1_k3': media(cont_val_v1),
        'azar_ndcg10': {str(k): v for k, v in azar.items()},
        'resultados': filas, 'diferencias_ndcg10': difs, 'segundos': round(time.perf_counter() - t0, 1)}
    (RAIZ / 'evidencias').mkdir(exist_ok=True)
    (RAIZ / 'evidencias' / args.salida).write_text(json.dumps(resultado, indent=1, ensure_ascii=False), encoding='utf-8')

    print('\nk  método   NDCG@10  P@10    R@10    cobertura  genéricas')
    for f in filas:
        print(f"{f['k']}  {f['metodo']:<7}  {f['ndcg10']:.4f}   {f['precision10']:.4f}  {f['recall10']:.4f}  {f['cobertura']:.3f}      {f['listas_genericas']:.3f}")
    print()
    for n, v in difs.items():
        print(f"{n}: {v['media']:+.4f}  IC95% [{v['ic95'][0]:+.4f}, {v['ic95'][1]:+.4f}]")
    print('segundos', resultado['segundos'])


if __name__ == '__main__':
    main()
