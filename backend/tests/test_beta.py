import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.recommender import recomendar

DATOS = Path(__file__).resolve().parents[2] / 'data'
CAT = json.loads((DATOS / 'catalogo_beta.json').read_text(encoding='utf-8'))
MODELO = json.loads((DATOS / 'modelo_beta.json').read_text(encoding='utf-8'))
IDS = [p['id'] for p in CAT]


def sel_con_vecinos():
    return next(i for i in IDS if len(MODELO['vecinos'].get(i, [])) >= 5)


def test_catalogo_beta_valido():
    assert len(CAT) == len(set(IDS)) > 1000
    assert {p['disciplina'] for p in CAT} == {'running', 'ciclismo', 'entrenamiento'}
    assert set(MODELO['popularidad']) == set(IDS)


def test_contenido_v2_usa_categorias_y_titulo():
    attrs = MODELO['atributos']
    assert set(attrs) == set(IDS)
    s = next(i for i in IDS if len(attrs[i]['c']) >= 2)
    r = recomendar(CAT, [], [], [s], metodo='contenido', modelo=MODELO)
    assert r['metodo'] == 'contenido' and s not in [x['producto']['id'] for x in r['resultados']]
    top = r['resultados'][0]
    comparte = (set(attrs[top['producto']['id']]['c']) & set(attrs[s]['c'])) | (set(attrs[top['producto']['id']]['w']) & set(attrs[s]['w']))
    assert comparte, 'el mejor resultado debe compartir categoría o palabras con la selección'
    assert top['explicacion'].startswith('Similar a tus selecciones')
    # sin `atributos` se usa la representación binaria disciplina/tipo (v1) y sigue funcionando
    v1 = recomendar(CAT, ['ciclismo'], [], [], metodo='contenido', modelo={k: v for k, v in MODELO.items() if k != 'atributos'})
    assert v1['metodo'] == 'contenido' and v1['resultados'][0]['producto']['disciplina'] == 'ciclismo'
    assert [x['puntaje'] for x in r['resultados']] == sorted((x['puntaje'] for x in r['resultados']), reverse=True)


def test_popularidad_ordena_y_excluye():
    s = IDS[0]
    r = recomendar(CAT, [], [], [s], metodo='popularidad', modelo=MODELO)
    ids = [x['producto']['id'] for x in r['resultados']]
    assert r['metodo'] == 'popularidad' and s not in ids
    pops = [MODELO['popularidad'][i] for i in ids]
    assert pops == sorted(pops, reverse=True)


def test_colaborativo_usa_vecinos_y_sin_seleccion_cae_a_generico():
    s = sel_con_vecinos()
    r = recomendar(CAT, [], [], [s], metodo='colaborativo', modelo=MODELO)
    vecinos = {j for j, _ in MODELO['vecinos'][s]}
    assert r['metodo'] == 'colaborativo' and s not in [x['producto']['id'] for x in r['resultados']]
    assert all(x['producto']['id'] in vecinos for x in r['resultados'])
    vacio = recomendar(CAT, ['ciclismo'], [], [], metodo='colaborativo', modelo=MODELO)
    assert vacio['metodo'] == 'generico' and vacio['motivo_alternativa']


def test_hibrido_combina_y_es_determinista():
    s = sel_con_vecinos()
    a = recomendar(CAT, ['ciclismo'], ['accesorios'], [s], metodo='hibrido', modelo=MODELO)
    b = recomendar(CAT, ['ciclismo'], ['accesorios'], [s], metodo='hibrido', modelo=MODELO)
    assert a['metodo'] == 'hibrido' and a['resultados'] == b['resultados']
    assert s not in [x['producto']['id'] for x in a['resultados']]
    assert all(0 < x['puntaje'] <= 1 for x in a['resultados'])
    solo_contenido = recomendar(CAT, ['ciclismo'], [], [], metodo='hibrido', modelo=MODELO)
    assert solo_contenido['metodo'] == 'hibrido' and solo_contenido['motivo_alternativa']
    assert recomendar(CAT, [], [], [], metodo='hibrido', modelo=MODELO)['metodo'] == 'generico'


def test_api_beta_comparar_a_ciegas_y_exportar(tmp_path, monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app import main
    eng = create_engine('sqlite:///' + str(tmp_path / 'beta.db'), connect_args={'check_same_thread': False})
    monkeypatch.setattr(main, 'engine', eng)
    monkeypatch.setattr(main, 'SessionLocal', sessionmaker(bind=eng, expire_on_commit=False))
    monkeypatch.setenv('GEARLY_CATALOGO', 'beta')
    monkeypatch.setenv('ADMIN_KEY', 'clave-de-prueba')
    main.startup()
    s = sel_con_vecinos()
    with TestClient(main.app) as c:
        assert c.get('/productos').json()['total'] == len(CAT)
        assert c.get('/vocabulario').json()['tipos'] == [t for t in main.TIPOS if any(p['tipo'] == t for p in CAT)]
        token = c.post('/sesiones').json()['csrf']
        h = {'X-Gearly-CSRF': token}
        p = c.put('/perfil', json={'disciplinas': ['ciclismo'], 'tipos': [], 'version': 0}, headers=h).json()
        p = c.put('/selecciones', json={'ids': [s], 'version': p['version']}, headers=h).json()
        # sugerencias inmediatas: parecidos a lo que acaba de marcar, sin repetir lo ya elegido
        otra = IDS[5]
        sim = c.get('/similares', params={'de': s, 'excluir': f'{s},{otra}', 'limite': 6}).json()
        ids_sim = [x['producto']['id'] for x in sim['resultados']]
        assert sim['de'] == [s] and 1 <= len(ids_sim) <= 6 and s not in ids_sim and otra not in ids_sim
        assert all(x['explicacion'] for x in sim['resultados'])
        assert c.get('/similares', params={'de': 'NOEXISTE'}).status_code == 422
        assert c.get('/similares', params={'de': s, 'limite': 99}).status_code == 422
        assert c.get('/recomendaciones', params={'metodo': 'inventado'}).status_code == 422
        assert c.get('/recomendaciones', params={'metodo': 'hibrido'}).json()['metodo'] == 'hibrido'
        assert c.get('/recomendaciones/comparar').status_code == 422  # mínimo 3 selecciones
        assert c.put('/selecciones', json={'ids': IDS[:11], 'version': p['version']}, headers=h).status_code == 422  # máximo 10
        voc = c.get('/vocabulario').json()
        assert (voc['min_selecciones'], voc['max_selecciones']) == (3, 10)
        p = c.put('/selecciones', json={'ids': [s] + [j for j, _ in MODELO['vecinos'][s][:2]], 'version': p['version']}, headers=h).json()
        assert len(p['ids']) == 3
        pop = c.get('/productos', params={'orden': 'popular', 'limite': 5, 'disciplina': 'ciclismo,running'}).json()['productos']
        pops = [MODELO['popularidad'][x['id']] for x in pop]
        assert pops == sorted(pops, reverse=True) and {x['disciplina'] for x in pop} <= {'ciclismo', 'running'}
        r = c.get('/recomendaciones/comparar').json()
        assert [x['etiqueta'] for x in r['listas']] == ['A', 'B', 'C'] and r['codigo'].startswith('G-')
        assert all('metodo' not in x for x in r['listas'])  # el cliente no ve qué método es cada lista
        assert c.get('/recomendaciones/comparar', params={'metodos': 'popularidad,popularidad'}).status_code == 422
        # vista de desarrollo: con la clave revela el método y NO queda registrada como dato de participantes
        n_antes = c.get('/admin/exportar', params={'clave': 'clave-de-prueba'}).json()['total']
        assert c.get('/recomendaciones/comparar', params={'clave': 'mala'}).status_code == 403
        dev = c.get('/recomendaciones/comparar', params={'clave': 'clave-de-prueba'}).json()['listas']
        assert {x['metodo'] for x in dev} == {'popularidad', 'contenido', 'hibrido'} and all(x['resultados'][0]['explicacion'] for x in dev)
        assert c.get('/admin/exportar', params={'clave': 'clave-de-prueba'}).json()['total'] == n_antes
        assert c.get('/admin/exportar').status_code == 403
        filas = c.get('/admin/exportar', params={'clave': 'clave-de-prueba'}).json()['filas']
        assert {f['metodo_solicitado'] for f in filas} == {'popularidad', 'contenido', 'hibrido'}
        assert {f['codigo'] for f in filas} == {r['codigo']}
        codigo = c.get('/perfil').json()['codigo']
        assert codigo == r['codigo']
        assert 'Max-Age=604800' in c.post('/sesiones').headers['set-cookie']  # sesión de 7 días
    with TestClient(main.app) as otro:  # otro dispositivo, sin cookies
        assert otro.get('/perfil').status_code == 401
        assert otro.post('/sesiones/retomar', json={'codigo': 'G-00000000'}).status_code == 404
        assert otro.post('/sesiones/retomar', json={'codigo': 'g-ñandú'}).status_code == 404
        assert otro.post('/sesiones/retomar', json={'codigo': f' {codigo.lower()} '}).status_code == 200
        assert otro.get('/perfil').json()['codigo'] == codigo
    monkeypatch.delenv('ADMIN_KEY')
    with TestClient(main.app) as c:
        assert c.get('/admin/exportar', params={'clave': 'x'}).status_code == 404
