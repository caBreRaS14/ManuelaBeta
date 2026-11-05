import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.recommender import recomendar
from app.main import app, startup

CAT=json.loads((Path(__file__).resolve().parents[2]/'data/catalogo_demo.json').read_text(encoding='utf-8'))

def test_generico_sin_senales():
    a=recomendar(CAT,[],[],[]);b=recomendar(CAT,[],[],[])
    assert a['metodo']=='generico'
    assert [x['producto']['id'] for x in a['resultados']]==[x['producto']['id'] for x in b['resultados']]

def test_contenido_y_exclusion():
    r=recomendar(CAT,['running'],['calzado'],['run-01'])
    assert r['metodo']=='contenido'
    assert 'run-01' not in [x['producto']['id'] for x in r['resultados']]
    assert r['resultados'][0]['producto']['disciplina']=='running'
    assert r['resultados'][0]['producto']['tipo']=='calzado'

def test_seleccion_sin_intereses():
    r=recomendar(CAT,[],[],['bike-01'])
    assert r['metodo']=='contenido' and 'bike-01' not in [x['producto']['id'] for x in r['resultados']]

def test_api_recorrido(tmp_path,monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app import main
    eng=create_engine('sqlite:///'+str(tmp_path/'test.db'),connect_args={'check_same_thread':False})
    monkeypatch.setattr(main,'engine',eng)
    monkeypatch.setattr(main,'SessionLocal',sessionmaker(bind=eng,expire_on_commit=False))
    main.startup()
    with TestClient(app) as c:
        catalog=c.get('/productos',params={'q':'casco'}).json()
        assert catalog['total']==1
        assert c.get('/perfil').status_code==401
        token=c.post('/sesiones').json()['csrf'];headers={'X-Gearly-CSRF':token}
        p=c.get('/perfil').json();assert p['version']==0
        assert c.get('/recomendaciones').json()['metodo']=='generico'
        p=c.put('/perfil',json={'disciplinas':['ciclismo'],'tipos':['proteccion'],'version':p['version']},headers=headers).json()
        assert p['disciplinas']==['ciclismo']
        assert c.put('/selecciones',json={'ids':['bike-01']*2,'version':p['version']},headers=headers).status_code==422
        assert c.put('/selecciones',json={'ids':[x['id'] for x in CAT[:11]],'version':p['version']},headers=headers).status_code==422
        p=c.put('/selecciones',json={'ids':['bike-01'],'version':p['version']},headers=headers).json()
        r=c.get('/recomendaciones').json();assert r['metodo']=='contenido' and all(x['producto']['id']!='bike-01' for x in r['resultados'])
        assert c.put('/perfil',json={'disciplinas':[],'tipos':[],'version':0},headers=headers).status_code==409
        p=c.put('/selecciones',json={'ids':[],'version':p['version']},headers=headers).json()
        assert c.get('/recomendaciones').json()['metodo']=='contenido' # conserva disciplinas
        p=c.delete('/perfil',headers=headers).json()
        assert p['ids']==[] and p['disciplinas']==[]
        assert c.get('/recomendaciones').json()['metodo']=='generico'
        assert c.put('/perfil',json={'disciplinas':['x'],'tipos':[],'version':p['version']},headers=headers).status_code==422
        assert c.put('/perfil',json={'disciplinas':[],'tipos':[],'version':p['version']}).status_code==403
