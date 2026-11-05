import {readdir,readFile,writeFile,stat} from 'node:fs/promises';
const root='frontend/public/images';
const rows=[];
for(const folder of await readdir(root))for(const name of await readdir(`${root}/${folder}`)){
 const path=`${root}/${folder}/${name}`, b=await readFile(path),kind=b.toString('ascii',12,16);
 let width,height;
 if(kind==='VP8X'){width=1+b.readUIntLE(24,3);height=1+b.readUIntLE(27,3)}
 else if(kind==='VP8 '){width=b.readUInt16LE(26)&16383;height=b.readUInt16LE(28)&16383}
 else throw Error(`Formato sin inspeccionar: ${path}`);
 rows.push({path:`/images/${folder}/${name}`,format:'WebP',width,height,ratio:Number((width/height).toFixed(3)),bytes:(await stat(path)).size});
}
const photos=new Set(['run-01','run-06','bike-01','bike-05','fit-01','fit-03']);
const catalog=JSON.parse(await readFile('data/catalogo_demo.json','utf8'));
for(const p of catalog){const row=rows.find(r=>r.path===`/images/productos/${p.id}.webp`);if(!row)throw Error(`Falta imagen de ${p.id}`);Object.assign(row,{productId:p.id,name:p.nombre,discipline:p.disciplina,type:p.tipo,provisional:!photos.has(p.id)})}
await writeFile('docs/INVENTARIO_IMAGENES.json',JSON.stringify(rows,null,2)+'\n');
console.log(`${rows.length} WebP inspeccionados; ${catalog.length} productos con recurso correspondiente; ${rows.reduce((s,r)=>s+r.bytes,0)} bytes.`);
