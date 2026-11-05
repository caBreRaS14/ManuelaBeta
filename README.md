# Gearly · prototipo académico funcional

Interfaz **Gearly 2.0 — Move beyond.**: portada editorial, fotografías locales, disciplinas, preferencias guiadas y recomendaciones reales. Consulta [el registro del rediseño](docs/REDISENO_GEARLY_2.md), [el inventario de imágenes](docs/INVENTARIO_IMAGENES.json) y las capturas `evidencias/gearly-2-*.png`. La ejecución local y los contratos de API se mantienen.

**Universidad Manuela Beltrán · Ingeniería de Software · Versión 0.1 (2 de noviembre de 2026)**

Prototipo para usuarios nuevos: catálogo deportivo, búsqueda/filtros, captura voluntaria de intereses y hasta cinco productos, cálculo de recomendaciones de contenido y exploración genérica. No es una tienda ni procesa compras. El catálogo es ficticio.

## Requisitos Windows

- Windows 10/11, VS Code, Python **3.12.x**, Node.js **22 LTS** y npm.
- No se requiere cuenta en servicios pagos.
- SQLite viene integrado con Python: no instales un servidor de base de datos, Docker ni PostgreSQL para esta demostración.

## Alcance actual y arranque diario

Este incremento es un **prototipo académico funcional e interactivo**. Incluye los 18 productos JSON, búsqueda/filtros, preferencias opcionales, cero a cinco selecciones, similitud coseno real, explicaciones, modificación/retirada y exploración genérica. Conserva el diseño editorial y las imágenes originales.

Después de instalar las dependencias una sola vez, en VS Code abre **Terminal > Ejecutar tarea > Gearly: iniciar prototipo local**. Se abren dos terminales y se usa explícitamente SQLite en `backend/gearly.db`, incluso si otra configuración local apunta a una base externa. Cuando ambos servidores estén listos, abre **http://127.0.0.1:5173**. Para detenerlos usa Ctrl+C en las dos terminales o **Terminal > Finalizar tarea**.

Si el puerto 5173 está ocupado, la tarea lo indicará sin cambiar silenciosamente la dirección: reutiliza el servidor existente si corresponde a este proyecto o detén ese servidor antes de iniciar de nuevo.

PostgreSQL, nube, chatbot generativo, filtrado colaborativo y recomendación híbrida quedan **fuera de esta etapa**. No son requisitos para ejecutar o aprobar el recorrido. La compatibilidad previa de conexión con PostgreSQL se conserva; no se incorpora trabajo adicional sobre ella. Consulta [el alcance y etapas futuras](docs/ALCANCE_PROTOTIPO.md).

## Instalación paso a paso (PowerShell)

1. Descomprime el ZIP. En VS Code elige **Archivo > Abrir carpeta** y selecciona `Gearly`.
2. Abre una terminal **Terminal > Nueva terminal** en la carpeta principal.
3. Inicia el backend:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
$env:DATABASE_URL = 'sqlite:///./gearly.db'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Mantén esta terminal abierta. La API debe responder en **http://127.0.0.1:8000/salud** y su documentación en **http://127.0.0.1:8000/docs**.

4. Abre **otra** terminal en VS Code (desde la carpeta `Gearly`) e inicia la interfaz:

```powershell
cd frontend
npm install
npm run dev
```

5. En el navegador abre **http://127.0.0.1:5173**. Si tienes un error de cookies entre localhost y 127.0.0.1, usa exactamente la dirección 127.0.0.1 indicada.

**Nota:** Vite ofrece las llamadas `/api` como proxy al backend; ambos procesos deben estar encendidos. La primera vez el servidor crea automáticamente las tablas y carga `data/catalogo_demo.json` si la tabla de productos está vacía. Esa es la **carga reproducible** del catálogo. No se insertan cuentas, reseñas ni interacciones de otros usuarios.

## Persistencia de la demostración

El catálogo JSON se carga si la tabla de productos está vacía. Los perfiles, selecciones y listas se guardan en `backend/gearly.db`. Recargar la página conserva las preferencias guardadas de la sesión del navegador; los cambios sin guardar todavía son un borrador. Un perfil vacío genera resultados genéricos calculados por el backend, identificados como no personalizados. No hay listas personalizadas fijas en React.

Los archivos de compatibilidad PostgreSQL existentes, incluido `docker-compose.yml`, se conservan para futuras etapas y no se usan en este recorrido. La dependencia Python `psycopg` incluida previamente es un controlador, no un servidor de base de datos.

## Uso

1. En **Catálogo**, busca o filtra por disciplina y tipo. Marca artículos como “Me interesa” (máximo cinco).
2. Desde el corazón del encabezado o **Descubrir para mí**, abre **Diseña tu experiencia** y elige running/ciclismo/entrenamiento y tipos de productos. Las selecciones son opcionales.
3. Pulsa **DESCUBRIR MIS RECOMENDACIONES**. La API guarda el perfil y devuelve una lista calculada por similitud coseno, incluso si elegiste cero artículos y solo declaraste intereses.
4. Consulta **Para ti**: cada tarjeta explica coincidencias. Los productos seleccionados quedan excluidos.
5. Pulsa **Ajustar preferencias**, modifica y vuelve a generar. **Retirar todas mis preferencias** borra las elecciones activas.
6. Con el perfil vacío, pulsa generar: la interfaz identifica la salida **genérica**, ordenada por identificador estable, no por popularidad.

## Cómo funciona el cálculo

Cada producto tiene dos atributos observables: disciplina y tipo. Se codifica en un vector binario de 8 posiciones, normalizado a norma 1. Se forma un bloque con preferencias declaradas y otro con la media de artículos seleccionados; cuando existen ambos, se suman con el mismo peso y se normalizan. Para cada candidato no seleccionado se calcula el producto punto entre vectores normalizados (coseno). El orden es descendente por puntuación, con desempate por ID. Se muestran hasta 10 coincidencias positivas. Cuando no existe ningún vector o no hay candidatos compatibles, se declara salida genérica ordenada por ID. **No se han calculado estadísticas de popularidad; POP del experimento académico permanece pendiente.**

## Pruebas técnicas

En una tercera terminal:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

Estas pruebas comprueban selección duplicada, límite de cinco, intereses, actualización, retirada, ausencia de señales, exclusión y un recorrido vía API. No equivalen a pruebas de usabilidad ni a evaluación offline de NDCG.

## Problemas frecuentes

- `py -3.12` no funciona: instala Python 3.12 y revisa `py -0p`.
- `npm` no se reconoce: instala Node.js 22 LTS, cierra y vuelve a abrir VS Code.
- `ModuleNotFoundError`: usa el ejecutable `.venv\\Scripts\\python.exe` e instala `requirements.txt` dentro de `backend`.
- `ECONNREFUSED` o catálogo no carga: verifica que Uvicorn está en el puerto 8000 y Vite en 5173.
- Puerto ocupado: cierra el proceso que usa el puerto. El proxy está fijado en 8000 y el frontend en 5173.
- `401`: el navegador crea sesión automáticamente al abrir. Recarga la página.
- `403`: revisa cookies y usa siempre `127.0.0.1:5173`. Recarga para regenerar sesión/CSRF si hace falta.
- `409`: otra pestaña cambió el perfil; recarga antes de volver a guardar.
- Si una configuración antigua intenta conectar a PostgreSQL, usa la tarea **Gearly: iniciar prototipo local** o fija `$env:DATABASE_URL = 'sqlite:///./gearly.db'` antes de iniciar Uvicorn. No hace falta instalar otra base de datos.
- Para reiniciar datos de SQLite: **detén Uvicorn**, elimina `backend/gearly.db` (esto destruye preferencias de demostración) y vuelve a iniciar.

## Arquitectura, procedencia y límites

- `frontend/`: React 19 + TypeScript + Vite, estilos responsivos, íconos Lucide (licencia ISC), fotografías y recursos conceptuales locales WebP aportados para el rediseño.
- `backend/app/main.py`: API FastAPI, persistencia SQLAlchemy, cookies de sesión aleatorias HttpOnly y validación CSRF para cambios.
- `backend/app/recommender.py`: cálculo determinista de contenido.
- `data/catalogo_demo.json`: **18 productos ficticios redactados para este proyecto**; no se tomaron de tiendas, no hay precios, ventas, imágenes comerciales ni reseñas.
- No se distribuye Amazon Reviews 2023. Su inspección, condiciones de uso y protocolo experimental quedan pendientes.
- No hay autenticación institucional, control de roles de operador, evaluaciones H03, retiradas de investigación, migraciones, HTTPS ni controles de despliegue. La sesión es solo para demostración local (no publicar como servicio público).
- Las listas generadas guardan versiones de modelo/catálogo/perfil, pero no son registros de un experimento humano autorizado.

Consulta `docs/GUIA_DEMOSTRACION.md`, `docs/TRAZABILIDAD.md` y `docs/DECISIONES.md`. No se alteró el documento de tesis original.
