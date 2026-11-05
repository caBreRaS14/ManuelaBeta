# Despliegue de la beta en Render (plan gratuito)

Beta de pruebas de uso. Un solo servicio web (API + frontend compilado) y un Postgres gratuito.

## Qué esperar del plan gratuito
- El servicio se **duerme tras ~15 min sin tráfico**; el primer acceso tarda ~1 min. Ábrelo tú antes de cada sesión de pruebas.
- El Postgres gratuito **caduca a los ~30 días**.
- Los datos (catálogo y modelo, ~3 MB) viajan en el repositorio (`data/catalogo_beta.json`, `data/modelo_beta.json`); el servidor no entrena nada.

## Pasos
1. Sube la carpeta del proyecto a un repositorio de GitHub (`backend/`, `frontend/`, `data/`, `Dockerfile`, `render.yaml`). `.gitignore` ya excluye `node_modules`, `.venv`, `dist` y `*.db`.
2. En Render: **New → Blueprint**, conecta el repositorio. Lee `render.yaml` y crea `gearly` (web, Docker) y `gearly-db` (Postgres gratis).
3. Abre la URL `https://gearly-xxxx.onrender.com` y comprueba `/api/salud`.

Variables: `DATABASE_URL` (la entrega la base), `SESSION_SECURE=true`, `GEARLY_CATALOGO=beta`, `ADMIN_KEY` (generada; para la vista de desarrollo y la exportación).

## Experiencia del usuario (4 pasos, una pregunta por pantalla)
**Inicio** (explica qué es la beta) → **① Deportes** → **② Tipo de producto** (se puede omitir) → **③ Tus gustos** (marca entre 3 y 10 productos) → **④ Recomendaciones** (lista híbrida con la razón de cada producto). El mínimo de 3 y el máximo de 10 se aplican también en la API.

En el paso ③, al marcar «Me gusta» se abre un panel con 6 productos parecidos al que se acaba de elegir (`GET /api/similares`); si el usuario marca uno, el panel se actualiza con ese. Se puede cerrar, o desactivar con la casilla «Mostrar parecidos cuando elija un producto». El panel no guarda nada: solo ayuda a elegir.

El código de sesión (`G-XXXXXXXX`) se ve en una barra durante el flujo y sirve para **retomar el perfil**, incluso desde otro dispositivo (`POST /api/sesiones/retomar`). La sesión dura **7 días** (`SESSION_DAYS`).

## Para desarrolladores (los usuarios no lo ven)
- **Comparar estrategias:** abre la app con `#dev` al final de la URL (en Render, `#dev=TU_ADMIN_KEY`). En el paso 3 aparece el enlace «[dev] Comparar estrategias»: muestra popularidad, contenido e híbrido lado a lado con el mismo perfil, con su explicación. No se guarda como dato de participantes.
- **Registro de lo que vio cada participante:** cada lista de recomendaciones se guarda en la tabla `listas` (método, versión del modelo y del catálogo, resultados).
- **Exportar:** `https://TU-URL/api/admin/exportar?clave=ADMIN_KEY` devuelve las comparaciones registradas con el endpoint ciego (`/api/recomendaciones/comparar` sin `clave`), que la interfaz actual no usa.

## Local
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000   # API (con el proxy de Vite)
.\.venv\Scripts\python.exe -m uvicorn app.main:web --port 8000            # servicio único, tras `npm run build`
```

## Regenerar el catálogo y el modelo
`python -I scripts/preparar_datos.py <carpeta>` con los CSV 5-core de Sports and Outdoors y `meta_filtrado.jsonl`. El modelo usa solo la partición `train`. Resultados offline en `docs/RESULTADOS_OFFLINE_v2.md`.

## Límites conocidos de esta beta
- Los títulos son los de Amazon (en inglés). Las imágenes son genéricas por disciplina.
- El dataset no incluye calzado ni ropa de running relevantes, por eso el tipo «calzado» no está y running es la disciplina más débil (400 productos, muchos accesorios).
- La clasificación disciplina/tipo es por palabras clave sobre categorías y títulos; puede haber errores puntuales.
