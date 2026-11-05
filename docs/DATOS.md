# Datos: qué está en git y qué no

## Para ejecutar la app en otro equipo no hace falta nada más
El repositorio ya trae lo necesario: `data/catalogo_beta.json` (catálogo) y `data/modelo_beta.json` (popularidad, vecinos colaborativos y atributos de contenido). Basta con instalar dependencias y arrancar (ver `README.md`). La base SQLite (`backend/gearly.db`) se crea sola, y `backend/.env` se copia de `backend/.env.example`.

## Lo que NO está en git (a propósito)
| Qué | Dónde estaba | Para qué sirve | Cómo recuperarlo |
|---|---|---|---|
| CSV de interacciones (~200 MB) y `meta_filtrado.jsonl` (~57 MB) | Carpeta aparte, fuera del repo | Solo para **regenerar** el catálogo/modelo o **repetir el experimento offline** | `python -I scripts/descargar_datos.py <carpeta>` |
| `node_modules`, `.venv`, `dist`, `*.db` | Local | Se reconstruyen | `npm install`, `py -3.12 -m venv .venv` + `pip install -r requirements.txt`, `npm run build` |
| `backend/.env` | Local | Configuración local | Copiar `backend/.env.example` |

## Regenerar y repetir el experimento
```powershell
python -I scripts/descargar_datos.py C:\ruta\fuera\del\repo\datos      # ~4,3 GB de transferencia, una sola vez
python -I scripts/preparar_datos.py C:\ruta\fuera\del\repo\datos       # genera data/catalogo_beta.json y data/modelo_beta.json
python -I scripts/experimento_offline.py C:\ruta\fuera\del\repo\datos  # ~140 s; escribe evidencias/resultados_offline.json
```
Fuente de los datos: Amazon Reviews 2023 (McAuley Lab, Hugging Face). Revisa sus condiciones de uso antes de redistribuirlos: por eso los crudos no se suben al repositorio.
