// Recursos locales revisados; la presentación no modifica los atributos del catálogo.
export const productImages:Record<string,string> = Object.fromEntries(
 ['run','bike','fit'].flatMap(prefix => Array.from({length:6},(_,i)=>`${prefix}-0${i+1}`))
 .map(id=>[id,`/images/productos/${id}.webp`])
);
export const photographicProducts = new Set(['run-01','run-06','bike-01','bike-05','fit-01','fit-03']);
export const disciplines = [
 {id:'running',name:'Running',copy:'Cada paso cuenta',image:'/images/categorias/running.webp'},
 {id:'ciclismo',name:'Ciclismo',copy:'Movimiento sin límites',image:'/images/categorias/ciclismo.webp'},
 {id:'entrenamiento',name:'Entrenamiento',copy:'Supera tu propia marca',image:'/images/categorias/entrenamiento.webp'},
];
