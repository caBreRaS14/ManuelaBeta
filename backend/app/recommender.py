"""Recomendadores de Gearly: contenido (coseno), popularidad, colaborativo producto-producto e híbrido.

Todo es determinista y se calcula sin entrenar en el servidor: la popularidad y los vecinos
colaborativos vienen precalculados (scripts/preparar_datos.py) y se pasan como `modelo`.
"""
from collections import Counter
from functools import lru_cache
from math import log, sqrt

DISCIPLINAS = ('running', 'ciclismo', 'entrenamiento')
TIPOS = ('calzado', 'ropa', 'accesorios', 'proteccion', 'equipamiento')
VOCAB = tuple(f'd:{d}' for d in DISCIPLINAS) + tuple(f't:{t}' for t in TIPOS)
VERSION = 'CONT-DEMO-01'
CATALOGO_VERSION = 'DEMO-01'
METODOS = ('contenido', 'popularidad', 'colaborativo', 'hibrido')
PESO_CONTENIDO = 0.5  # híbrido: peso del contenido; el resto es colaborativo


def vector(etiquetas):
    return [float(k in etiquetas) for k in VOCAB]


def normalizar(v):
    norma = sqrt(sum(x*x for x in v))
    return [x/norma for x in v] if norma else [0.0 for x in v]


def sumar(*vectores):
    return [sum(v[i] for v in vectores) for i in range(len(VOCAB))]


def atributos(p):
    return {f'd:{p["disciplina"]}', f't:{p["tipo"]}'}


@lru_cache(maxsize=None)
def _vec_item(disciplina, tipo):
    """Vector normalizado de un producto; sólo hay un puñado de combinaciones disciplina/tipo."""
    return tuple(normalizar(vector({f'd:{disciplina}', f't:{tipo}'})))


def _perfil(mapa, disciplinas, tipos, seleccionados):
    """Perfil de contenido = normalización de bloques declarados y seleccionados. None si no hay señal."""
    declaradas = {*(f'd:{x}' for x in disciplinas), *(f't:{x}' for x in tipos)}
    decl = normalizar(vector(declaradas))
    sel_vectors = [normalizar(vector(atributos(mapa[i]))) for i in seleccionados if i in mapa]
    promedio = normalizar([sum(v[k] for v in sel_vectors) / len(sel_vectors) for k in range(len(VOCAB))]) if sel_vectors else [0.0] * len(VOCAB)
    bloques = [b for b in (decl, promedio) if any(b)]
    return normalizar(sumar(*bloques)) if bloques else None


def _explicar(p, mapa, disciplinas, tipos, seleccionados):
    matches = []
    if p['disciplina'] in disciplinas:
        matches.append('tu interés en ' + p['disciplina'])
    if p['tipo'] in tipos:
        matches.append('el tipo ' + p['tipo'])
    if seleccionados and any(p['disciplina'] == mapa[s]['disciplina'] for s in seleccionados if s in mapa):
        matches.append('disciplina similar a tus selecciones')
    if seleccionados and any(p['tipo'] == mapa[s]['tipo'] for s in seleccionados if s in mapa):
        matches.append('tipo similar a tus selecciones')
    return 'Coincide con ' + ', '.join(matches) + '.' if matches else 'Coincidencia parcial del perfil de contenido.'


# ---- Contenido v2 (TF-IDF): disciplina/tipo + ruta de categorías + palabras del título y marca ----
# Cada grupo se normaliza por separado y pesa igual (decisión fijada antes de evaluar; no se ajustó con los resultados).
_GRUPOS = ('dt', 'c', 'w')
_ESPACIO = {}


def _norm_dict(v):
    n = sqrt(sum(x * x for x in v.values()))
    return {k: x / n for k, x in v.items()} if n else {}


def _espacio(modelo):
    """Vectores dispersos de los productos del catálogo; se calculan una vez por modelo cargado."""
    if _ESPACIO.get('modelo') is not modelo:
        attrs = modelo['atributos']
        df = Counter()
        for a in attrs.values():
            df.update({f'c:{x}' for x in a['c']} | {f'w:{x}' for x in a['w']})
        n = len(attrs)
        vecs = {}
        for iid, a in attrs.items():
            total = {}
            for g, feats in (('dt', {x: 1.0 for x in a['dt']}),
                             ('c', {f'c:{x}': log((n + 1) / (df[f'c:{x}'] + 1)) + 1 for x in a['c']}),
                             ('w', {f'w:{x}': log((n + 1) / (df[f'w:{x}'] + 1)) + 1 for x in a['w']})):
                total.update(_norm_dict(feats))
            vecs[iid] = _norm_dict(total)
        _ESPACIO.update(modelo=modelo, vecs=vecs, df=df, n=n)
    return _ESPACIO


def _perfil_v2(esp, disciplinas, tipos, seleccionados):
    declarado = _norm_dict({**{f'd:{x}': 1.0 for x in disciplinas}, **{f't:{x}': 1.0 for x in tipos}})
    vs = [esp['vecs'][i] for i in seleccionados if i in esp['vecs']]
    medio = {}
    for v in vs:
        for k, x in v.items():
            medio[k] = medio.get(k, 0.0) + x / len(vs)
    medio = _norm_dict(medio)
    bloques = [b for b in (declarado, medio) if b]
    if not bloques:
        return None
    suma = {}
    for b in bloques:
        for k, x in b.items():
            suma[k] = suma.get(k, 0.0) + x
    return _norm_dict(suma)


def _puntajes_contenido_v2(candidatos, disciplinas, tipos, seleccionados, modelo):
    esp = _espacio(modelo)
    perfil = _perfil_v2(esp, disciplinas, tipos, seleccionados)
    if perfil is None:
        return None
    out = {}
    for p in candidatos:
        v = esp['vecs'].get(p['id'], {})
        out[p['id']] = sum(x * perfil.get(k, 0.0) for k, x in v.items())
    return out


def _explicar_v2(p, mapa, disciplinas, tipos, seleccionados, modelo):
    esp = _espacio(modelo)
    attrs = modelo['atributos']
    a = attrs.get(p['id'])
    partes = []
    if a and seleccionados:
        sel_c = {x for s in seleccionados if s in attrs for x in attrs[s]['c']}
        sel_w = {x for s in seleccionados if s in attrs for x in attrs[s]['w']}
        idf = lambda f: log((esp['n'] + 1) / (esp['df'][f] + 1)) + 1
        cats = sorted((x for x in a['c'] if x in sel_c), key=lambda x: -idf('c:' + x))[:1]
        pals = sorted((x for x in a['w'] if x in sel_w and not x.startswith('b:')), key=lambda x: -idf('w:' + x))[:3]
        if cats:
            partes.append(f'misma categoría «{cats[0]}»')
        if pals:
            partes.append('comparte ' + ', '.join(f'«{x}»' for x in pals))
    texto = 'Similar a tus selecciones: ' + '; '.join(partes) + '.' if partes else ''
    gustos = []
    if p['disciplina'] in disciplinas:
        gustos.append('tu interés en ' + p['disciplina'])
    if p['tipo'] in tipos:
        gustos.append('el tipo ' + p['tipo'])
    if gustos:
        texto = (texto + ' ' if texto else '') + 'Coincide con ' + ', '.join(gustos) + '.'
    return texto or 'Coincidencia parcial del perfil de contenido.'


def _puntajes_contenido(candidatos, mapa, disciplinas, tipos, seleccionados, modelo=None):
    if modelo and modelo.get('atributos'):
        return _puntajes_contenido_v2(candidatos, disciplinas, tipos, seleccionados, modelo)
    perfil = _perfil(mapa, disciplinas, tipos, seleccionados)
    if perfil is None:
        return None
    return {p['id']: sum(a*b for a, b in zip(perfil, _vec_item(p['disciplina'], p['tipo']))) for p in candidatos}


def _corto(nombre, n=42):
    return nombre if len(nombre) <= n else nombre[:n - 1].rstrip() + '…'


def _generico(candidatos, limite, motivo, explicacion):
    orden = sorted(candidatos, key=lambda p: p['id'])[:limite]
    return {'metodo': 'generico', 'motivo_alternativa': motivo,
            'resultados': [{'producto': p, 'puntaje': None, 'explicacion': explicacion} for p in orden]}


def _texto_contenido(p, mapa, disciplinas, tipos, seleccionados, modelo):
    if modelo and modelo.get('atributos'):
        return _explicar_v2(p, mapa, disciplinas, tipos, seleccionados, modelo)
    return _explicar(p, mapa, disciplinas, tipos, seleccionados)


def _contenido(candidatos, mapa, disciplinas, tipos, seleccionados, limite, modelo=None):
    """Orden estable. La alternativa sin señales usa ID estable y NO se presenta como popularidad.
    Con `modelo['atributos']` usa el contenido v2 (TF-IDF); sin él, la representación binaria disciplina/tipo (v1)."""
    puntajes = _puntajes_contenido(candidatos, mapa, disciplinas, tipos, seleccionados, modelo)
    if puntajes is None:
        return _generico(candidatos, limite, 'Sin preferencias: orden neutro por identificador, no popularidad medida.',
                         'Exploración general del catálogo de demostración.')
    items = sorted(((round(puntajes[p['id']], 6), p) for p in candidatos), key=lambda x: (-x[0], x[1]['id']))
    positivos = [(s, p) for s, p in items if s > 0][:limite]
    if not positivos:
        return _generico(candidatos, limite, 'No hay productos con coincidencias positivas.',
                         'Exploración general: no hubo coincidencia con tus preferencias.')
    return {'metodo': 'contenido', 'motivo_alternativa': None, 'resultados': [
        {'producto': p, 'puntaje': s, 'explicacion': _texto_contenido(p, mapa, disciplinas, tipos, seleccionados, modelo)}
        for s, p in positivos]}


def explicar_parecido(p, productos, semillas, modelo=None):
    """Por qué `p` se parece a los productos `semillas` (misma categoría, palabras en común)."""
    mapa = {x['id']: x for x in productos}
    return _texto_contenido(p, mapa, [], [], list(semillas), modelo)


def _popularidad(candidatos, modelo, limite):
    pop = (modelo or {}).get('popularidad') or {}
    items = [(pop.get(p['id'], 0), p) for p in candidatos]
    items.sort(key=lambda x: (-x[0], x[1]['id']))
    items = [x for x in items if x[0] > 0][:limite]
    return {'metodo': 'popularidad', 'motivo_alternativa': None, 'resultados': [
        {'producto': p, 'puntaje': float(n),
         'explicacion': f'Entre los más populares del catálogo ({n} interacciones en los datos de referencia). No depende de tus preferencias.'}
        for n, p in items]}


def _puntajes_colaborativo(candidatos, mapa, seleccionados, modelo):
    """Suma de similitudes coseno producto-producto con cada selección. Devuelve (puntajes, aportes)."""
    vecinos = (modelo or {}).get('vecinos') or {}
    ids = {p['id'] for p in candidatos}
    puntajes, aportes = {}, {}
    for s in seleccionados:
        for j, sim in vecinos.get(s, []):
            if j in ids:
                puntajes[j] = puntajes.get(j, 0.0) + sim
                if sim > aportes.get(j, (None, 0.0))[1]:
                    aportes[j] = (s, sim)
    return puntajes, aportes


def _colaborativo(candidatos, mapa, seleccionados, modelo, limite):
    puntajes, aportes = _puntajes_colaborativo(candidatos, mapa, seleccionados, modelo)
    if not puntajes:
        motivo = ('El filtrado colaborativo necesita al menos un producto seleccionado.' if not seleccionados
                  else 'Los productos seleccionados no tienen suficientes interacciones compartidas con otros.')
        return _generico(candidatos, limite, motivo, 'Exploración general: sin señal colaborativa disponible.')
    cmap = {p['id']: p for p in candidatos}
    orden = sorted(puntajes.items(), key=lambda x: (-x[1], x[0]))[:limite]
    return {'metodo': 'colaborativo', 'motivo_alternativa': None, 'resultados': [
        {'producto': cmap[i], 'puntaje': round(s, 6),
         'explicacion': f'A quienes eligieron «{_corto(mapa[aportes[i][0]]["nombre"])}» también les interesó.'}
        for i, s in orden]}


def _hibrido(candidatos, mapa, disciplinas, tipos, seleccionados, modelo, limite):
    cont = _puntajes_contenido(candidatos, mapa, disciplinas, tipos, seleccionados, modelo)
    cf, aportes = _puntajes_colaborativo(candidatos, mapa, seleccionados, modelo)
    if cont is None and not cf:
        return _generico(candidatos, limite, 'Sin preferencias ni selecciones: no hay señal para combinar.',
                         'Exploración general del catálogo.')
    cont = cont or {}
    maximo = max(cf.values()) if cf else 0.0
    items = []
    for p in candidatos:
        c = cont.get(p['id'], 0.0)
        f = (cf.get(p['id'], 0.0) / maximo) if maximo else 0.0
        score = PESO_CONTENIDO * c + (1 - PESO_CONTENIDO) * f
        if score <= 0:
            continue
        partes = []
        if c > 0:
            partes.append('encaja con tus intereses y gustos')
        if f > 0:
            partes.append(f'a quienes eligieron «{_corto(mapa[aportes[p["id"]][0]]["nombre"])}» también les interesó')
        texto = '; '.join(partes)
        items.append({'producto': p, 'puntaje': round(score, 6), 'explicacion': texto[0].upper() + texto[1:] + '.'})
    items.sort(key=lambda i: (-i['puntaje'], i['producto']['id']))
    if not items:
        return _generico(candidatos, limite, 'No hay productos con señal positiva.', 'Exploración general.')
    motivo = None if cf else 'Sin selecciones, el híbrido usa solo la parte de contenido.'
    return {'metodo': 'hibrido', 'motivo_alternativa': motivo, 'resultados': items[:limite]}


def recomendar(productos, disciplinas, tipos, seleccionados, limite=10, metodo='contenido', modelo=None):
    mapa = {p['id']: p for p in productos}
    seleccionados = list(dict.fromkeys(seleccionados))
    candidatos = [p for p in productos if p['id'] not in seleccionados]
    if metodo == 'popularidad':
        return _popularidad(candidatos, modelo, limite)
    if metodo == 'colaborativo':
        return _colaborativo(candidatos, mapa, seleccionados, modelo, limite)
    if metodo == 'hibrido':
        return _hibrido(candidatos, mapa, disciplinas, tipos, seleccionados, modelo, limite)
    return _contenido(candidatos, mapa, disciplinas, tipos, seleccionados, limite, modelo)
