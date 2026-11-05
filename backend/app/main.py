import hashlib
import json
import os
import random
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, Cookie, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Text, select
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from .recommender import DISCIPLINAS, TIPOS, VERSION, CATALOGO_VERSION, METODOS, recomendar, explicar_parecido

load_dotenv()
DB_URL = os.getenv('DATABASE_URL','sqlite:///./gearly.db')
if DB_URL.startswith('postgres://'):DB_URL='postgresql+psycopg://'+DB_URL[len('postgres://'):]
elif DB_URL.startswith('postgresql://'):DB_URL='postgresql+psycopg://'+DB_URL[len('postgresql://'):]
RAIZ=Path(__file__).resolve().parents[2]
MAX_SELECCIONES=10
SESION_SEGUNDOS=int(os.getenv('SESSION_DAYS','7'))*86400
MIN_COMPARAR=3
ESTADO={'catalogo_version':CATALOGO_VERSION,'modelo_version':VERSION,'modelo':None,'tipos':list(TIPOS)}
engine = create_engine(DB_URL, connect_args={'check_same_thread':False} if DB_URL.startswith('sqlite') else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base=declarative_base()

class Producto(Base):
    __tablename__='productos'
    id=Column(String,primary_key=True)
    nombre=Column(String,nullable=False)
    disciplina=Column(String,nullable=False)
    tipo=Column(String,nullable=False)
    descripcion=Column(String,nullable=False)
    color=Column(String,nullable=False)
    icono=Column(String,nullable=False)

class Perfil(Base):
    __tablename__='perfiles'
    id=Column(String,primary_key=True)
    token=Column(String,unique=True,nullable=False)
    intereses=Column(Text,nullable=False,default='[]')
    tipos=Column(Text,nullable=False,default='[]')
    version=Column(Integer,nullable=False,default=0)
    creado=Column(DateTime(timezone=True),nullable=False)

class Seleccion(Base):
    __tablename__='selecciones'
    perfil_id=Column(String,ForeignKey('perfiles.id'),primary_key=True)
    producto_id=Column(String,ForeignKey('productos.id'),primary_key=True)

class Lista(Base):
    __tablename__='listas'
    id=Column(String,primary_key=True)
    perfil_id=Column(String,ForeignKey('perfiles.id'),nullable=False)
    perfil_version=Column(Integer,nullable=False)
    metodo=Column(String,nullable=False)
    catalogo_version=Column(String,nullable=False)
    modelo_version=Column(String,nullable=False)
    resultados_json=Column(Text,nullable=False)
    creado=Column(DateTime(timezone=True),nullable=False)

class Comparacion(Base):
    __tablename__='comparaciones'
    id=Column(String,primary_key=True)
    perfil_id=Column(String,ForeignKey('perfiles.id'),nullable=False)
    codigo=Column(String,nullable=False,index=True)
    perfil_version=Column(Integer,nullable=False)
    etiqueta=Column(String,nullable=False)
    metodo_solicitado=Column(String,nullable=False)
    metodo_resultante=Column(String,nullable=False)
    intereses=Column(Text,nullable=False)
    tipos=Column(Text,nullable=False)
    selecciones=Column(Text,nullable=False)
    resultados_ids=Column(Text,nullable=False)
    catalogo_version=Column(String,nullable=False)
    modelo_version=Column(String,nullable=False)
    creado=Column(DateTime(timezone=True),nullable=False)

app=FastAPI(title='Gearly · API académica',version='0.2.0')
app.add_middleware(CORSMiddleware,allow_origins=list({os.getenv('FRONTEND_ORIGIN','http://localhost:5173'),'http://127.0.0.1:5173','http://localhost:5173'}),allow_credentials=True,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Content-Type','X-Gearly-CSRF'])

def cargar_fuentes():
    """Catálogo beta (Amazon Reviews 2023, preparado offline) si existe; si no, el catálogo demo."""
    datos=RAIZ/'data'
    modo=os.getenv('GEARLY_CATALOGO','beta' if (datos/'catalogo_beta.json').exists() else 'demo')
    if modo=='beta':
        modelo=json.loads((datos/'modelo_beta.json').read_text(encoding='utf-8'))
        return json.loads((datos/'catalogo_beta.json').read_text(encoding='utf-8')),modelo['catalogo'],modelo['version'],modelo
    return json.loads((datos/'catalogo_demo.json').read_text(encoding='utf-8')),CATALOGO_VERSION,VERSION,None

@app.on_event('startup')
def startup():
    Base.metadata.create_all(engine)
    filas,cat_v,mod_v,modelo=cargar_fuentes()
    ESTADO.update(catalogo_version=cat_v,modelo_version=mod_v,modelo=modelo,tipos=[t for t in TIPOS if any(f['tipo']==t for f in filas)])
    with SessionLocal() as db:
        actuales={r[0] for r in db.query(Producto.id).all()}
        if actuales!={f['id'] for f in filas}:
            db.query(Seleccion).delete();db.query(Producto).delete()
            for row in filas:db.add(Producto(**row))
            db.commit()

def get_db():
    with SessionLocal() as db:yield db

def current(request:Request, db:Session=Depends(get_db)):
    token=request.cookies.get('gearly_sesion')
    perfil=db.query(Perfil).filter_by(token=token).first() if token else None
    if not perfil:raise HTTPException(401,'Inicia una sesión de demostración.')
    return perfil

def csrf(request:Request):
    token=request.cookies.get('gearly_csrf')
    if not token or not secrets.compare_digest(token,request.headers.get('X-Gearly-CSRF','')):
        raise HTTPException(403,'Token de protección inválido. Recarga la aplicación.')

class PerfilIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    disciplinas:list[str]=Field(default_factory=list)
    tipos:list[str]=Field(default_factory=list)
    version:int=Field(ge=0)

class SeleccionIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    ids:list[str]=Field(max_length=MAX_SELECCIONES)
    version:int=Field(ge=0)

def perfil_out(db,p):
    ids=[r.producto_id for r in db.query(Seleccion).filter_by(perfil_id=p.id).order_by(Seleccion.producto_id)]
    return {'disciplinas':json.loads(p.intereses),'tipos':json.loads(p.tipos),'ids':ids,'version':p.version,'codigo':codigo_sesion(p.id)}

def validar_etiquetas(valores, permitidos):
    if len(valores)!=len(set(valores)) or any(x not in permitidos for x in valores):raise HTTPException(422,'Etiquetas inválidas o repetidas.')

def validar_version(p,v):
    if p.version!=v:raise HTTPException(409,'El perfil cambió. Recarga los datos antes de guardar.')

@app.get('/salud')
def salud():return {'estado':'ok','catalogo':ESTADO['catalogo_version'],'modelo':ESTADO['modelo_version']}

def poner_cookies(response:Response,token:str):
    csrf_token=secrets.token_urlsafe(32)
    secure=os.getenv('SESSION_SECURE','false').lower()=='true'
    response.set_cookie('gearly_sesion',token,httponly=True,secure=secure,samesite='lax',max_age=SESION_SEGUNDOS)
    response.set_cookie('gearly_csrf',csrf_token,httponly=False,secure=secure,samesite='lax',max_age=SESION_SEGUNDOS)
    return csrf_token

@app.post('/sesiones')
def sesion(response:Response, db:Session=Depends(get_db)):
    token=secrets.token_urlsafe(32)
    p=Perfil(id=str(uuid.uuid4()),token=token,intereses='[]',tipos='[]',version=0,creado=datetime.now(timezone.utc))
    db.add(p);db.commit()
    return {'mensaje':'Sesión académica creada','csrf':poner_cookies(response,token)}

class RetomarIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    codigo:str=Field(min_length=3,max_length=24)

@app.post('/sesiones/retomar')
def retomar(data:RetomarIn,response:Response,db:Session=Depends(get_db)):
    """Recupera un perfil anónimo con su código de sesión (G-XXXXXXXX), por ejemplo desde otro dispositivo."""
    c=data.codigo.strip().upper()
    for p in (db.query(Perfil).all() if c.isascii() else []):
        if secrets.compare_digest(codigo_sesion(p.id),c):
            return {'mensaje':'Sesión retomada','csrf':poner_cookies(response,p.token)}
    raise HTTPException(404,'No encontramos ese código. Revisa que esté completo, por ejemplo G-1A2B3C4D.')

@app.get('/vocabulario')
def vocabulario():return {'disciplinas':list(DISCIPLINAS),'tipos':list(ESTADO['tipos']),'min_selecciones':MIN_COMPARAR,'max_selecciones':MAX_SELECCIONES}

@app.get('/productos')
def productos(q:str='',disciplina:str='',tipo:str='',ids:str='',orden:str='',pagina:int=Query(1,ge=1),limite:int=Query(18,ge=1,le=50),db:Session=Depends(get_db)):
    discs=[x for x in disciplina.split(',') if x];tps=[x for x in tipo.split(',') if x]
    if any(x not in DISCIPLINAS for x in discs):raise HTTPException(422,'Disciplina inválida')
    if any(x not in ESTADO['tipos'] for x in tps):raise HTTPException(422,'Tipo inválido')
    rows=db.query(Producto).order_by(Producto.id).all()
    items=[{k:getattr(p,k) for k in ('id','nombre','disciplina','tipo','descripcion','color','icono')} for p in rows]
    if ids:
        pedidos=ids.split(',')[:50];items=[p for p in items if p['id'] in pedidos]
    if q:items=[p for p in items if q.casefold() in (p['nombre']+' '+p['descripcion']).casefold()]
    if discs:items=[p for p in items if p['disciplina'] in discs]
    if tps:items=[p for p in items if p['tipo'] in tps]
    if orden=='popular' and ESTADO['modelo']:
        pop=ESTADO['modelo']['popularidad'];items.sort(key=lambda p:(-pop.get(p['id'],0),p['id']))
    return {'total':len(items),'pagina':pagina,'productos':items[(pagina-1)*limite:pagina*limite], 'catalogo_version':ESTADO['catalogo_version']}

@app.get('/perfil')
def obtener_perfil(p=Depends(current),db:Session=Depends(get_db)):return perfil_out(db,p)

@app.put('/perfil')
def guardar_perfil(data:PerfilIn,request:Request,p=Depends(current),db:Session=Depends(get_db)):
    csrf(request);validar_version(p,data.version)
    validar_etiquetas(data.disciplinas,DISCIPLINAS);validar_etiquetas(data.tipos,ESTADO['tipos'])
    p.intereses=json.dumps(data.disciplinas);p.tipos=json.dumps(data.tipos);p.version+=1
    db.commit();return perfil_out(db,p)

@app.delete('/perfil')
def borrar_perfil(request:Request,p=Depends(current),db:Session=Depends(get_db)):
    csrf(request);p.intereses='[]';p.tipos='[]';p.version+=1
    db.query(Seleccion).filter_by(perfil_id=p.id).delete();db.commit();return perfil_out(db,p)

@app.put('/selecciones')
def guardar_selecciones(data:SeleccionIn,request:Request,p=Depends(current),db:Session=Depends(get_db)):
    csrf(request);validar_version(p,data.version)
    if len(data.ids)!=len(set(data.ids)):raise HTTPException(422,'No puedes repetir productos.')
    disponibles={x.id for x in db.query(Producto).all()}
    if any(x not in disponibles for x in data.ids):raise HTTPException(422,'Producto desconocido.')
    db.query(Seleccion).filter_by(perfil_id=p.id).delete()
    for id in data.ids:db.add(Seleccion(perfil_id=p.id,producto_id=id))
    p.version+=1;db.commit();return perfil_out(db,p)

def catalogo_dict(db):
    return [{k:getattr(x,k) for k in ('id','nombre','disciplina','tipo','descripcion','color','icono')} for x in db.query(Producto).order_by(Producto.id).all()]

def etiquetas_ciegas(perfil_id,metodos):
    """Orden y letras A, B, C... fijos por sesión (reproducibles para el investigador); el cliente no ve el método."""
    orden=list(metodos);random.Random(hashlib.sha256(perfil_id.encode()).hexdigest()).shuffle(orden)
    return {m:chr(65+i) for i,m in enumerate(orden)}

def codigo_sesion(perfil_id):return 'G-'+hashlib.sha256(perfil_id.encode()).hexdigest()[:8].upper()

@app.get('/recomendaciones')
def recomendaciones(metodo:str='contenido',p=Depends(current),db:Session=Depends(get_db)):
    if metodo not in METODOS:raise HTTPException(422,'Método inválido')
    productos=catalogo_dict(db)
    estado=perfil_out(db,p)
    resultado=recomendar(productos,estado['disciplinas'],estado['tipos'],estado['ids'],metodo=metodo,modelo=ESTADO['modelo'])
    uid=str(uuid.uuid4())
    db.add(Lista(id=uid,perfil_id=p.id,perfil_version=p.version,metodo=resultado['metodo'],catalogo_version=ESTADO['catalogo_version'],modelo_version=f"{ESTADO['modelo_version']}:{metodo}",resultados_json=json.dumps(resultado['resultados'],ensure_ascii=False),creado=datetime.now(timezone.utc)))
    db.commit()
    return {'lista_id':uid,'perfil_version':p.version,'catalogo_version':ESTADO['catalogo_version'],'modelo_version':ESTADO['modelo_version'],'metodo':resultado['metodo'],'motivo_alternativa':resultado['motivo_alternativa'],'resultados':resultado['resultados']}

@app.get('/similares')
def similares(de:str,excluir:str='',limite:int=Query(6,ge=1,le=12),p=Depends(current),db:Session=Depends(get_db)):
    """Productos parecidos a los que el usuario acaba de marcar (`de`), sin repetir los ya elegidos (`excluir`). No guarda nada."""
    semillas=list(dict.fromkeys(x for x in de.split(',') if x))[:3]
    fuera={x for x in excluir.split(',') if x}-set(semillas)
    productos=catalogo_dict(db)
    if not semillas or any(s not in {x['id'] for x in productos} for s in semillas):raise HTTPException(422,'Producto desconocido.')
    r=recomendar([x for x in productos if x['id'] not in fuera],[],[],semillas,limite=limite,metodo='hibrido',modelo=ESTADO['modelo'])
    return {'de':semillas,'resultados':[{'producto':x['producto'],'explicacion':explicar_parecido(x['producto'],productos,semillas,ESTADO['modelo'])} for x in r['resultados']]}

@app.get('/recomendaciones/comparar')
def comparar(metodos:str='popularidad,contenido,hibrido',clave:str|None=None,p=Depends(current),db:Session=Depends(get_db)):
    """Herramienta para desarrolladores: lista las estrategias lado a lado. A ciegas por defecto; con `clave` (ADMIN_KEY, o
    cualquiera si no hay ADMIN_KEY configurada, como en local) revela el método, no se guarda y no cuenta como dato de participantes."""
    esperada=os.getenv('ADMIN_KEY','')
    revelar=clave is not None
    if revelar and esperada and not (clave.isascii() and secrets.compare_digest(clave,esperada)):raise HTTPException(403,'Clave inválida')
    pedidos=[m for m in metodos.split(',') if m]
    if not pedidos or len(set(pedidos))!=len(pedidos) or any(m not in METODOS for m in pedidos):raise HTTPException(422,'Métodos inválidos')
    estado=perfil_out(db,p)
    if len(estado['ids'])<MIN_COMPARAR:raise HTTPException(422,f'Elige al menos {MIN_COMPARAR} productos que te gusten para comparar listas.')
    productos=catalogo_dict(db);letras=etiquetas_ciegas(p.id,pedidos);codigo=codigo_sesion(p.id);ahora=datetime.now(timezone.utc)
    listas=[]
    for m in pedidos:
        r=recomendar(productos,estado['disciplinas'],estado['tipos'],estado['ids'],metodo=m,modelo=ESTADO['modelo'])
        if not revelar:db.add(Comparacion(id=str(uuid.uuid4()),perfil_id=p.id,codigo=codigo,perfil_version=p.version,etiqueta=letras[m],metodo_solicitado=m,metodo_resultante=r['metodo'],
            intereses=json.dumps(estado['disciplinas']),tipos=json.dumps(estado['tipos']),selecciones=json.dumps(estado['ids']),resultados_ids=json.dumps([x['producto']['id'] for x in r['resultados']]),
            catalogo_version=ESTADO['catalogo_version'],modelo_version=ESTADO['modelo_version'],creado=ahora))
        aviso='Esta lista usa un orden general porque tu perfil no aportó señal suficiente.' if r['metodo']=='generico' else None  # texto neutro: no delata la estrategia
        if revelar:listas.append({'etiqueta':letras[m],'metodo':m,'metodo_resultante':r['metodo'],'aviso':r['motivo_alternativa'],'resultados':r['resultados']})
        else:listas.append({'etiqueta':letras[m],'aviso':aviso,'resultados':[{'producto':x['producto']} for x in r['resultados']]})
    db.commit()
    listas.sort(key=lambda x:x['etiqueta'])
    return {'codigo':codigo,'perfil_version':p.version,'catalogo_version':ESTADO['catalogo_version'],'listas':listas}

@app.get('/admin/exportar')
def exportar(clave:str='',db:Session=Depends(get_db)):
    esperada=os.getenv('ADMIN_KEY','')
    if not esperada:raise HTTPException(404,'No disponible')
    if not secrets.compare_digest(clave,esperada):raise HTTPException(403,'Clave inválida')
    cols=('codigo','etiqueta','metodo_solicitado','metodo_resultante','perfil_version','intereses','tipos','selecciones','resultados_ids','catalogo_version','modelo_version','creado')
    filas=db.query(Comparacion).order_by(Comparacion.creado,Comparacion.codigo,Comparacion.etiqueta).all()
    return {'total':len(filas),'filas':[{c:(getattr(f,c).isoformat() if c=='creado' else getattr(f,c)) for c in cols} for f in filas]}

# Servicio único (Render): API bajo /api y frontend compilado en la raíz. En desarrollo se usa `app` con el proxy de Vite.
web=FastAPI(title='Gearly')
web.mount('/api',app)
_dist=RAIZ/'frontend'/'dist'
if _dist.exists():web.mount('/',StaticFiles(directory=_dist,html=True),name='frontend')
web.add_event_handler('startup',startup)
