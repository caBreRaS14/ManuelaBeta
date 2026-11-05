import {useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {ArrowLeft,ArrowRight,Check,Heart,RotateCcw,Search,Sparkles,X} from 'lucide-react';
import './style.css';
import './flow.css';
import {productImages,disciplines} from './assets';

type Producto={id:string;nombre:string;disciplina:string;tipo:string;descripcion:string;color:string;icono:string};
type Perfil={disciplinas:string[];tipos:string[];ids:string[];version:number;codigo?:string};
type Recomendacion={producto:Producto;puntaje:number|null;explicacion:string};
type Lista={lista_id:string;metodo:string;motivo_alternativa:string|null;resultados:Recomendacion[]};
type ListaDev={etiqueta:string;metodo?:string;metodo_resultante?:string;aviso:string|null;resultados:{producto:Producto;explicacion?:string}[]};
type Comparacion={codigo:string;listas:ListaDev[]};
type Vocab={tipos:string[];min_selecciones:number;max_selecciones:number};
type Sugerencias={de:Producto;items:{producto:Producto;explicacion:string}[]};
// 0 inicio · 1 deportes · 2 tipo de producto · 3 tus gustos · 4 recomendaciones · 5 comparación (solo desarrollo)
type Paso=0|1|2|3|4|5;

const vacio:Perfil={disciplinas:[],tipos:[],ids:[],version:0};
const nombres:Record<string,string>={running:'Running',ciclismo:'Ciclismo',entrenamiento:'Entrenamiento',calzado:'Calzado',ropa:'Ropa',accesorios:'Accesorios',proteccion:'Protección',equipamiento:'Equipamiento'};
const iconosTipo:Record<string,string>={calzado:'👟',ropa:'👕',accesorios:'🎒',proteccion:'🛡️',equipamiento:'🔧'};
const ayudaTipo:Record<string,string>={calzado:'Zapatillas y zapatos',ropa:'Prendas deportivas',accesorios:'Luces, bolsos, hidratación…',proteccion:'Cascos y protectores',equipamiento:'Equipos, partes y herramientas'};
const pasos:{n:Paso;titulo:string}[]=[{n:1,titulo:'Deportes'},{n:2,titulo:'Tipo de producto'},{n:3,titulo:'Tus gustos'},{n:4,titulo:'Recomendaciones'}];
// Vista solo para desarrolladores: se activa abriendo la app con #dev (o #dev=CLAVE si el servidor tiene ADMIN_KEY). Los usuarios no la ven.
const DEV_CLAVE=(()=>{const m=/(?:^|[#&])dev(?:=([^&]*))?/.exec(location.hash);return m?decodeURIComponent(m[1]||''):null})();
const nombreMetodo:Record<string,string>={popularidad:'Popularidad (POP)',contenido:'Contenido (CONT)',colaborativo:'Colaborativo (CF)',hibrido:'Híbrido (HIB)'};

class ApiError extends Error {constructor(public status:number,message:string){super(message)}}
let csrf='';
function cookie(name:string){return decodeURIComponent(document.cookie.split('; ').find(x=>x.startsWith(name+'='))?.split('=').slice(1).join('=')||'')}
async function api<T>(url:string,method='GET',body?:unknown):Promise<T>{
 const r=await fetch('/api'+url,{method,credentials:'include',headers:{...(method!=='GET'?{'Content-Type':'application/json','X-Gearly-CSRF':csrf||cookie('gearly_csrf')}:{})},...(body!==undefined?{body:JSON.stringify(body)}:{})});
 if(!r.ok){let d:unknown;try{d=await r.json()}catch{};throw new ApiError(r.status,typeof d==='object'&&d!==null&&'detail' in d?String((d as {detail:unknown}).detail):`Error ${r.status}`)}
 return r.json() as Promise<T>;
}
const mismos=(a:string[],b:string[])=>JSON.stringify([...a].sort())===JSON.stringify([...b].sort());

function ProductImage({p}:{p:Producto}){
 const [failed,setFailed]=useState(false);
 const cat=disciplines.find(x=>x.id===p.disciplina);
 return productImages[p.id]&&!failed
  ?<img src={productImages[p.id]} width="720" height="720" loading="lazy" alt={p.nombre} onError={()=>setFailed(true)}/>
  :<div className="category-art" style={{background:`linear-gradient(145deg,${p.color} 0%,#ffffff 140%)`}} role="img" aria-label={`Imagen genérica de la categoría ${cat?.name}`}><span aria-hidden="true">{({running:'🏃',ciclismo:'🚴',entrenamiento:'🏋️'} as Record<string,string>)[p.disciplina]||p.icono}</span></div>;
}

function Tarjeta({p,liked,onToggle,disabled,why}:{p:Producto;liked?:boolean;onToggle?:()=>void;disabled?:boolean;why?:string}){
 return <article className={'g-card'+(liked?' liked':'')}>
  <div className="g-card-art"><ProductImage p={p}/></div>
  <div className="g-card-body">
   <div className="g-tags"><span>{nombres[p.disciplina]}</span><span>{nombres[p.tipo]}</span></div>
   <h3>{p.nombre}</h3>
   <p className="g-path">{p.descripcion}</p>
   {why&&<p className="g-why"><Sparkles size={14}/><span>{why}</span></p>}
   {onToggle&&<button className={'g-like'+(liked?' on':'')} onClick={onToggle} disabled={disabled} aria-pressed={liked}>{liked?<><Check size={16}/> Te gusta</>:<><Heart size={16}/> Me gusta</>}</button>}
  </div>
 </article>;
}

function App(){
 const [paso,setPaso]=useState<Paso>(0);
 const [codigoIn,setCodigoIn]=useState('');
 const [perfil,setPerfil]=useState<Perfil>(vacio);
 const [d,setD]=useState<string[]>([]),[t,setT]=useState<string[]>([]),[ids,setIds]=useState<string[]>([]);
 const [vocab,setVocab]=useState<Vocab>({tipos:['ropa','accesorios','proteccion','equipamiento'],min_selecciones:3,max_selecciones:10});
 const [conocidos,setConocidos]=useState<Record<string,Producto>>({});
 const [items,setItems]=useState<Producto[]>([]),[total,setTotal]=useState(0),[pagina,setPagina]=useState(1),[cargando,setCargando]=useState(false),[buscado,setBuscado]=useState(false);
 const [query,setQuery]=useState(''),[fd,setFd]=useState<string[]>([]),[ft,setFt]=useState<string[]>([]);
 const [lista,setLista]=useState<Lista|null>(null),[comp,setComp]=useState<Comparacion|null>(null);
 const [sug,setSug]=useState<Sugerencias|null>(null),[sugCargando,setSugCargando]=useState(false),[sugerir,setSugerir]=useState(true);
 const [loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(''),[copiado,setCopiado]=useState(false);
 const lastClave=useRef(''),lastKey=useRef(''),reqId=useRef(0),sugId=useRef(0);
 const {min_selecciones:min,max_selecciones:max}=vocab;
 const agregar=(ps:Producto[])=>setConocidos(prev=>({...prev,...Object.fromEntries(ps.map(x=>[x.id,x]))}));
 const hydrate=(p:Perfil)=>{setPerfil(p);setD(p.disciplinas);setT(p.tipos);setIds(p.ids)};
 const cambiado=!mismos(d,perfil.disciplinas)||!mismos(t,perfil.tipos)||!mismos(ids,perfil.ids);
 const puedeAvanzar=ids.length>=min;

 useEffect(()=>{(async()=>{try{
   setVocab(await api<Vocab>('/vocabulario'));
   try{hydrate(await api<Perfil>('/perfil'))}catch(e){if(!(e instanceof ApiError)||e.status!==401)throw e;const s=await api<{csrf:string}>('/sesiones','POST');csrf=s.csrf;hydrate(await api<Perfil>('/perfil'))}
  }catch(e){setError(e instanceof Error?e.message:String(e))}finally{setLoading(false)}})()},[]);

 useEffect(()=>{window.scrollTo({top:0,behavior:'instant'});setSug(null)},[paso]);

 // El panel de sugerencias se cierra con Escape y bloquea el scroll de la página mientras está abierto.
 useEffect(()=>{
  if(!sug)return;
  const onKey=(e:KeyboardEvent)=>{if(e.key==='Escape')setSug(null)};
  window.addEventListener('keydown',onKey);
  const prev=document.body.style.overflow;document.body.style.overflow='hidden';
  return()=>{window.removeEventListener('keydown',onKey);document.body.style.overflow=prev};
 },[sug!==null]);

 // Nombres de los productos ya elegidos (por ejemplo, tras recargar la página).
 useEffect(()=>{const faltan=ids.filter(id=>!conocidos[id]);if(!faltan.length)return;api<{productos:Producto[]}>('/productos?limite=50&ids='+faltan.join(',')).then(c=>agregar(c.productos)).catch(()=>{})},[ids.join(',')]);

 // Catálogo del paso 3: paginado y filtrado en el servidor, ordenado por popularidad.
 const claveFiltros=`${query}|${fd.join(',')}|${ft.join(',')}`;
 useEffect(()=>{
  if(paso!==3)return;
  if(lastClave.current!==claveFiltros&&pagina!==1){setPagina(1);return}
  const key=claveFiltros+'#'+pagina;
  if(lastKey.current===key)return;
  const h=setTimeout(async()=>{
   const id=++reqId.current;setCargando(true);
   try{
    const qs=new URLSearchParams({pagina:String(pagina),limite:'24',orden:'popular'});
    if(query)qs.set('q',query);if(fd.length)qs.set('disciplina',fd.join(','));if(ft.length)qs.set('tipo',ft.join(','));
    const c=await api<{total:number;productos:Producto[]}>('/productos?'+qs.toString());
    if(id!==reqId.current)return;
    lastKey.current=key;lastClave.current=claveFiltros;
    setBuscado(true);setTotal(c.total);setItems(prev=>pagina===1?c.productos:[...prev,...c.productos]);agregar(c.productos);
   }catch(e){if(id===reqId.current)setError(e instanceof Error?e.message:String(e))}finally{if(id===reqId.current)setCargando(false)}
  },pagina===1?200:0);
  return()=>clearTimeout(h);
 },[paso,claveFiltros,pagina]);

 function invalidar(){setLista(null);setComp(null)}
 function alternar(valor:string,arr:string[],setter:(v:string[])=>void){setter(arr.includes(valor)?arr.filter(x=>x!==valor):[...arr,valor]);invalidar()}

 // Al marcar "Me gusta" se abre un panel con productos parecidos; si marca uno de ellos, el panel se actualiza con ese.
 async function abrirSugerencias(p:Producto,elegidos:string[]){
  const id=++sugId.current;setSug({de:p,items:[]});setSugCargando(true);
  try{
   const r=await api<{resultados:{producto:Producto;explicacion:string}[]}>(`/similares?de=${encodeURIComponent(p.id)}&excluir=${encodeURIComponent(elegidos.join(','))}&limite=6`);
   if(id!==sugId.current)return;
   agregar(r.resultados.map(x=>x.producto));setSug({de:p,items:r.resultados});
  }catch{if(id===sugId.current)setSug(null)}finally{if(id===sugId.current)setSugCargando(false)}
 }
 function alternarLike(p:Producto){
  setError('');
  if(ids.includes(p.id)){setIds(prev=>prev.filter(x=>x!==p.id));invalidar();return}
  if(ids.length>=max){setError(`Puedes elegir máximo ${max} productos. Quita uno para añadir otro.`);return}
  agregar([p]);setIds(prev=>prev.includes(p.id)?prev:[...prev,p.id]);invalidar();
  if(sugerir&&ids.length+1<max)abrirSugerencias(p,[...ids,p.id]);else setSug(null);
 }

 async function accion(work:()=>Promise<void>){setBusy(true);setError('');try{await work()}catch(e){setError(e instanceof Error?e.message:String(e))}finally{setBusy(false)}}
 async function guardar(){
  let p=perfil;
  if(!mismos(d,p.disciplinas)||!mismos(t,p.tipos))p=await api<Perfil>('/perfil','PUT',{disciplinas:d,tipos:t,version:p.version});
  if(!mismos(ids,p.ids))p=await api<Perfil>('/selecciones','PUT',{ids,version:p.version});
  hydrate(p);
 }
 const verRecomendaciones=()=>accion(async()=>{await guardar();setLista(await api<Lista>('/recomendaciones?metodo=hibrido'));setPaso(4)});
 const compararListas=()=>accion(async()=>{await guardar();setComp(await api<Comparacion>('/recomendaciones/comparar?clave='+encodeURIComponent(DEV_CLAVE??'')));setPaso(5)});
 const reiniciar=()=>accion(async()=>{hydrate(await api<Perfil>('/perfil','DELETE'));invalidar();setFd([]);setFt([]);setQuery('');setPaso(1)});
 const retomar=()=>accion(async()=>{
  const s=await api<{csrf:string}>('/sesiones/retomar','POST',{codigo:codigoIn});csrf=s.csrf;
  const p=await api<Perfil>('/perfil');hydrate(p);invalidar();setCodigoIn('');setFd(p.disciplinas);setFt(p.tipos);setQuery('');
  if(p.ids.length>=min){setLista(await api<Lista>('/recomendaciones?metodo=hibrido'));setPaso(4)}else setPaso(p.disciplinas.length?3:1);
 });
 function irAGustos(o:{todo?:boolean;sinTipos?:boolean}){
  if(o.todo||o.sinTipos){setT([]);invalidar()}
  setFd(o.todo?[]:d);setFt(o.todo||o.sinTipos?[]:t);setQuery('');setPaso(3);
 }
 function irPaso(n:Paso){
  if(n===paso)return;
  if(n<4){setPaso(n);return}
  if(!puedeAvanzar){setError(`Elige al menos ${min} productos que te gusten para continuar.`);return}
  lista&&!cambiado?setPaso(4):verRecomendaciones();
 }
 async function copiar(codigo:string){try{await navigator.clipboard.writeText(codigo);setCopiado(true);setTimeout(()=>setCopiado(false),2000)}catch{setError('No se pudo copiar. Selecciona el código y cópialo manualmente.')}}

 const seleccionados=ids.map(id=>conocidos[id]).filter(Boolean);
 const falta=min-ids.length;

 return <div className="app">
  <a className="skip-link" href="#contenido">Ir al contenido</a>
  <div className="announcement">GEARLY BETA ACADÉMICA <span>MOVE BEYOND.</span></div>
  <header className="header"><div className="header-inner g-header">
   <button className="brand" aria-label="Gearly, volver al inicio" onClick={()=>setPaso(0)}>GEARLY<Sparkles aria-hidden="true" size={23}/></button>
   {paso>0&&<nav className="g-stepper" aria-label="Progreso">
    <ol>{pasos.map(s=>{const bloqueado=s.n===4&&!puedeAvanzar;return <li key={s.n}>
     <button className={'g-step'+(paso===s.n?' current':'')+(paso>s.n?' done':'')} aria-current={paso===s.n?'step':undefined} disabled={busy||bloqueado} onClick={()=>irPaso(s.n)}>
      <span className="g-num">{paso>s.n?<Check size={14}/>:s.n}</span><span className="g-label">{s.titulo}</span>
     </button></li>})}</ol>
   </nav>}
  </div></header>
  {paso>0&&perfil.codigo&&<div className="g-codebar"><span>Tu código de sesión: <b>{perfil.codigo}</b></span><button className="g-link" onClick={()=>copiar(perfil.codigo!)}>{copiado?'¡Copiado!':'Copiar'}</button><small>Guárdalo: con él puedes retomar tu perfil durante 7 días, incluso desde otro dispositivo.</small></div>}
  <div id="contenido" tabIndex={-1}/>
  {error&&<div className="notification error" role="alert"><span>{error}</span><button aria-label="Cerrar error" onClick={()=>setError('')}><X size={16}/></button></div>}

  {loading?<main className="container center"><div className="spinner"/>Cargando...</main>:<>

  {paso===0&&<main className="container g-page g-landing">
   <section className="g-intro">
    <span className="eyebrow">BETA ACADÉMICA · UNIVERSIDAD MANUELA BELTRÁN</span>
    <h1>Descubre productos deportivos que <em>encajan contigo.</em></h1>
    <p>Gearly es un prototipo que recomienda productos deportivos a personas que llegan por primera vez, sin historial previo. Hace parte de un trabajo de grado de Ingeniería de Software.</p>
   </section>
   <div className="g-cards">
    <section className="g-box"><h2>¿Para qué es esta beta?</h2><p>Queremos probar si, con solo decir qué deportes te interesan y marcar unos pocos productos que te gustan, Gearly puede recomendarte cosas útiles, y si el recorrido es fácil de seguir. <b>Tu experiencia nos ayuda a mejorarlo.</b></p></section>
    <section className="g-box"><h2>¿Qué vas a hacer?</h2><ol className="g-list"><li><b>1</b>Elige los deportes que te interesan.</li><li><b>2</b>Dinos qué tipo de producto buscas.</li><li><b>3</b>Marca entre {min} y {max} productos que te gusten.</li><li><b>4</b>Mira tus recomendaciones y por qué aparecen.</li></ol><p className="g-small">Toma unos 3 minutos.</p></section>
    <section className="g-box"><h2>Antes de empezar</h2><ul className="g-bullets"><li><b>Es una beta:</b> puede haber errores y la primera carga puede tardar un poco.</li><li><b>No es una tienda:</b> no se vende nada. Los productos vienen de datos públicos de Amazon Reviews 2023, con nombres en inglés e imágenes ilustrativas.</li><li><b>Es anónima:</b> no pedimos nombre ni correo. Guardamos tus elecciones y un código de sesión.</li><li><b>Puedes volver:</b> con tu código retomas tu perfil durante 7 días.</li></ul></section>
   </div>
   <div className="g-actions"><button className="btn primary" onClick={()=>setPaso(1)}>COMENZAR <ArrowRight size={17}/></button><span className="g-small">Al comenzar aceptas participar en esta prueba académica.</span></div>
   <section className="g-resume"><h2>¿Ya participaste?</h2><p>Escribe tu código de sesión para retomar tu perfil.</p>
    <form onSubmit={e=>{e.preventDefault();if(codigoIn.trim())retomar()}}><input aria-label="Código de sesión" placeholder="G-1A2B3C4D" value={codigoIn} onChange={e=>setCodigoIn(e.target.value)} autoComplete="off" spellCheck={false}/><button className="btn secondary" type="submit" disabled={busy||!codigoIn.trim()}>{busy?'Buscando...':'Retomar'}</button></form></section>
  </main>}

  {paso===1&&<main className="container g-page">
   <section className="g-intro">
    <span className="eyebrow">PASO 1 DE 4</span>
    <h1>¿Qué deportes <em>te mueven?</em></h1>
    <p>Elige uno o varios. Con esto te mostraremos productos de esos deportes.</p>
   </section>
   <div className="g-sports" role="group" aria-label="Deportes">{disciplines.map(x=>{const on=d.includes(x.id);return <button key={x.id} className={'g-sport'+(on?' on':'')} aria-pressed={on} onClick={()=>alternar(x.id,d,setD)}>
    <img src={x.image} alt="" width="510" height="232"/><span className="g-sport-copy"><b>{x.name}</b><small>{x.copy}</small></span><span className="g-check">{on&&<Check size={18}/>}</span>
   </button>})}</div>
   <div className="g-actions">
    <button className="btn secondary" onClick={()=>setPaso(0)}><ArrowLeft size={16}/> Inicio</button>
    <button className="btn primary" disabled={!d.length} onClick={()=>setPaso(2)}>CONTINUAR <ArrowRight size={17}/></button>
    <button className="g-link" onClick={()=>irAGustos({todo:true})}>Prefiero ver todo el catálogo</button>
   </div>
   {!d.length&&<p className="g-hint">Elige al menos un deporte para continuar.</p>}
   <p className="g-consent">Esta es una prueba académica anónima: no pedimos nombre, correo ni datos de compra. Al continuar aceptas participar.</p>
  </main>}

  {paso===2&&<main className="container g-page">
   <section className="g-intro">
    <span className="eyebrow">PASO 2 DE 4</span>
    <h1>¿Qué tipo de producto <em>buscas?</em></h1>
    <p>Elige uno o varios, o sáltate este paso si te da igual.</p>
   </section>
   <div className="g-types" role="group" aria-label="Tipos de producto">{vocab.tipos.map(x=>{const on=t.includes(x);return <button key={x} className={'g-type'+(on?' on':'')} aria-pressed={on} onClick={()=>alternar(x,t,setT)}>
    <span className="g-type-icon" aria-hidden="true">{iconosTipo[x]}</span><span className="g-type-copy"><b>{nombres[x]}</b><small>{ayudaTipo[x]}</small></span><span className="g-check">{on&&<Check size={18}/>}</span>
   </button>})}</div>
   <div className="g-actions">
    <button className="btn secondary" onClick={()=>setPaso(1)}><ArrowLeft size={16}/> Deportes</button>
    {t.length>0?<button className="btn primary" onClick={()=>irAGustos({})}>CONTINUAR <ArrowRight size={17}/></button>
     :<button className="btn primary" onClick={()=>irAGustos({sinTipos:true})}>ME DA IGUAL, CONTINUAR <ArrowRight size={17}/></button>}
   </div>
  </main>}

  {paso===3&&<main className="container g-page g-with-dock">
   <section className="g-intro">
    <span className="eyebrow">PASO 3 DE 4</span>
    <h1>Marca lo que <em>te gusta.</em></h1>
    <p>Elige entre <b>{min} y {max} productos</b> que te llamen la atención. Al marcar uno te mostraremos otros parecidos. Entre más elijas, mejores serán tus recomendaciones.</p>
   </section>
   <div className="g-filters">
    <div className="search"><Search size={19}/><input aria-label="Buscar productos" placeholder="Buscar (los nombres están en inglés): mat, bike light, helmet..." value={query} onChange={e=>setQuery(e.target.value)}/></div>
    <div className="g-chips" role="group" aria-label="Filtrar por deporte">{disciplines.map(x=><button key={x.id} className={'g-chip'+(fd.includes(x.id)?' on':'')} aria-pressed={fd.includes(x.id)} onClick={()=>setFd(fd.includes(x.id)?fd.filter(y=>y!==x.id):[...fd,x.id])}>{x.name}</button>)}</div>
    <div className="g-chips" role="group" aria-label="Filtrar por tipo">{vocab.tipos.map(x=><button key={x} className={'g-chip small'+(ft.includes(x)?' on':'')} aria-pressed={ft.includes(x)} onClick={()=>setFt(ft.includes(x)?ft.filter(y=>y!==x):[...ft,x])}>{nombres[x]}</button>)}</div>
   </div>
   <p className="g-count"><b>{total}</b> productos · los más populares primero{(fd.length>0||ft.length>0||query)&&<button className="g-link" onClick={()=>{setFd([]);setFt([]);setQuery('')}}>Quitar filtros</button>}</p>
   {items.length?<div className="g-grid">{items.map(p=><Tarjeta key={p.id} p={p} liked={ids.includes(p.id)} onToggle={()=>alternarLike(p)} disabled={busy}/>)}</div>:<div className="empty">{cargando||!buscado?'Buscando...':'No encontramos coincidencias. Prueba quitar algún filtro.'}</div>}
   {items.length<total&&<div className="g-more"><button className="btn secondary" disabled={cargando} onClick={()=>setPagina(pagina+1)}>{cargando?'Cargando...':`Ver más productos (${items.length} de ${total})`}</button></div>}
   <div className="g-dock" role="region" aria-label="Tus elecciones">
    <div className="g-dock-main">
     <div className="g-meter" role="progressbar" aria-valuemin={0} aria-valuemax={max} aria-valuenow={ids.length} aria-label="Productos elegidos">{Array.from({length:max},(_,i)=><i key={i} className={(i<ids.length?'full ':'')+(i<min?'req':'')}/>)}</div>
     <p><b>{ids.length} de {max}</b> · {falta>0?`elige ${falta} más para continuar`:ids.length<max?'¡listo! puedes añadir más para afinar tus recomendaciones':'llegaste al máximo'}</p>
     {seleccionados.length>0&&<ul className="g-picked">{seleccionados.map(p=><li key={p.id}><span title={p.nombre}>{p.nombre}</span><button aria-label={`Quitar ${p.nombre}`} onClick={()=>alternarLike(p)}><X size={13}/></button></li>)}</ul>}
    </div>
    <div className="g-dock-actions">
     <button className="btn secondary" onClick={()=>setPaso(2)} disabled={busy}><ArrowLeft size={16}/> Tipo</button>
     <button className="btn primary" disabled={!puedeAvanzar||busy} onClick={verRecomendaciones}>{busy?'CALCULANDO...':'VER MIS RECOMENDACIONES'} <ArrowRight size={17}/></button>
    </div>
   </div>

   {sug&&<div className="g-modal-back" onMouseDown={e=>{if(e.target===e.currentTarget)setSug(null)}}>
    <div className="g-modal" role="dialog" aria-modal="true" aria-labelledby="sug-titulo">
     <button className="g-modal-close" aria-label="Cerrar sugerencias" onClick={()=>setSug(null)}><X size={18}/></button>
     <p className="g-modal-eyebrow"><Heart size={14}/> Te gustó</p>
     <h2 id="sug-titulo">{sug.de.nombre}</h2>
     <p className="g-modal-sub">¿Alguno de estos se parece a lo que buscas? Marca los que te gusten, o sigue explorando.</p>
     {sugCargando?<div className="g-modal-loading"><div className="spinner"/>Buscando parecidos...</div>
      :sug.items.length?<div className="g-modal-grid">{sug.items.map(x=><Tarjeta key={x.producto.id} p={x.producto} why={x.explicacion} liked={ids.includes(x.producto.id)} onToggle={()=>alternarLike(x.producto)} disabled={busy}/>)}</div>
      :<p className="g-note">No encontramos productos parecidos. Sigue explorando el catálogo.</p>}
     <div className="g-modal-foot">
      <span className="g-modal-count"><b>{ids.length} de {max}</b> elegidos{falta>0?` · faltan ${falta}`:''}</span>
      <label className="g-check-label"><input type="checkbox" checked={sugerir} onChange={e=>setSugerir(e.target.checked)}/> Mostrar parecidos cuando elija un producto</label>
      <button className="btn primary" onClick={()=>setSug(null)}>SEGUIR EXPLORANDO</button>
     </div>
    </div>
   </div>}
  </main>}

  {paso===4&&lista&&<main className="container g-page">
   <section className="g-intro">
    <span className="eyebrow">PASO 4 DE 4</span>
    <h1>Elegido <em>para ti.</em></h1>
    <p>Basado en {d.length?<>tus intereses (<b>{d.map(x=>nombres[x]).join(', ')}</b>) y en </>:null}los <b>{ids.length} productos</b> que marcaste. Cada sugerencia dice por qué aparece.</p>
    {seleccionados.length>0&&<ul className="g-picked static">{seleccionados.map(p=><li key={p.id}><span title={p.nombre}>{p.nombre}</span></li>)}</ul>}
   </section>
   {lista.motivo_alternativa&&<p className="g-note">{lista.motivo_alternativa}</p>}
   {lista.resultados.length?<div className="g-grid">{lista.resultados.map(r=><Tarjeta key={r.producto.id} p={r.producto} why={r.explicacion}/>)}</div>:<div className="empty">No quedaron productos para recomendar. Cambia tus gustos e inténtalo de nuevo.</div>}
   <div className="g-actions between">
    <button className="btn secondary" disabled={busy} onClick={()=>setPaso(3)}><ArrowLeft size={16}/> Cambiar mis gustos</button>
    <button className="g-link" disabled={busy} onClick={reiniciar}><RotateCcw size={15}/> Empezar de nuevo con otros intereses</button>
    {DEV_CLAVE!==null&&<button className="g-link dev" disabled={busy} onClick={compararListas}>[dev] Comparar estrategias</button>}
   </div>
  </main>}

  {paso===5&&comp&&DEV_CLAVE!==null&&<main className="container g-page">
   <section className="g-intro">
    <span className="eyebrow">SOLO DESARROLLO · NO LO VEN LOS USUARIOS</span>
    <h1>Comparar <em>estrategias.</em></h1>
    <p>Mismo perfil (<b>{comp.codigo}</b>, {ids.length} productos marcados) con cada método, lado a lado. Esta vista no se guarda como dato de participantes.</p>
   </section>
   <div className="compare-grid">{comp.listas.map(l=><section key={l.etiqueta} className="compare-list" aria-label={nombreMetodo[l.metodo||'']||l.etiqueta}>
    <h2><span>{l.etiqueta}</span> {nombreMetodo[l.metodo||'']||`Lista ${l.etiqueta}`}</h2>
    {l.aviso&&<p className="compare-note">{l.aviso}</p>}
    <ol>{l.resultados.map(r=><li key={r.producto.id}><b>{r.producto.nombre}</b><small>{nombres[r.producto.disciplina]} · {nombres[r.producto.tipo]}</small>{r.explicacion&&<span><Sparkles size={13}/> {r.explicacion}</span>}</li>)}</ol>
   </section>)}</div>
   <div className="g-actions"><button className="btn secondary" disabled={busy} onClick={()=>setPaso(4)}><ArrowLeft size={16}/> Volver a mis recomendaciones</button></div>
  </main>}
  </>}

  <footer><div className="container footer-inner"><div><b>GEARLY<Sparkles size={22}/></b><p>MOVE BEYOND.</p></div><p>Gearly es un prototipo académico. Los productos provienen de datos públicos de Amazon Reviews 2023 y no representan una tienda comercial: no hay compras ni inventario.</p><small>Universidad Manuela Beltrán · 2026<br/>Beta académica</small></div></footer>
 </div>;
}
createRoot(document.getElementById('root')!).render(<App/>);
