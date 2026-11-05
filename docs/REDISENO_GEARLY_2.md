# Gearly 2.0 — Move beyond.

Implementación local del 4 de noviembre de 2026. Se conserva el backend, el catálogo de 18 productos y el motor CONT-DEMO-01. No se añadieron precios, compras, reseñas ni resultados científicos.

**Aclaración de alcance posterior:** [ALCANCE_PROTOTIPO.md](ALCANCE_PROTOTIPO.md) es la referencia vigente para esta etapa académica local. PostgreSQL, nube, chatbot generativo, colaborativo e híbrido se reservan a etapas posteriores; no son requisitos pendientes del rediseño. El README y las tareas de VS Code priorizan SQLite y la demostración al profesor. El registro de pruebas incluye el recorrido ampliado con cero/cinco artículos y persistencia tras recarga.

## Interfaz y componentes

- `frontend/src/main.tsx`: encabezado editorial, logotipo tipográfico con Lucide, navegación con estado activo, menú móvil con `aria-expanded`, portada, Deportes, Cómo funciona, catálogo, preferencias y Para ti. La navegación sigue siendo estado React, como en el prototipo original; no existen rutas URL independientes.
- `ProductImage`: recurso por ID, texto alternativo, carga diferida y sustituto textual ante una imagen no disponible.
- `Categories`: tres fotografías originales, navegación que limpia búsqueda/tipo y aplica la disciplina real.
- `How`: recorrido de cuatro etapas y acceso al formulario.
- Preferencias: cuatro pasos, deportes fotográficos, tipos válidos, miniaturas, contador anunciado, selección voluntaria de cero a cinco artículos, retirada y guardado.
- Para ti: fondo morado, tarjetas claras, explicaciones originales de la API, recalcular, modificar selecciones, retirar preferencias y explorar sin personalización. Esta última acción retira el perfil activo mediante DELETE y obtiene una lista genérica real.
- `frontend/src/style.css`: variables de paleta, Outfit + DM Sans, composiciones editoriales, filtros adaptables, foco visible, enlace para saltar al contenido y respeto de `prefers-reduced-motion`.
- `frontend/src/assets.ts`: correspondencia visual de los 18 IDs y clasificación de recursos fotográficos/conceptuales.
- `frontend/src/vite-env.d.ts`: tipos del entorno Vite.
- `frontend/index.html`: título, descripción y color del navegador corregidos en UTF-8.

El inicio de sesión solo crea una sesión nueva al recibir 401. Los demás errores se muestran sin ocultarlos creando otra sesión. Cookies, CSRF y control de versión continúan usando los contratos existentes.

## Recursos gráficos

Inventario completo reproducible: `node scripts/inventory-images.mjs`. El resultado está en `docs/INVENTARIO_IMAGENES.json`: formato, dimensiones, proporción, peso y atributos del producto cuando corresponde.

Se inspeccionaron 43 archivos WebP: 605.228 bytes en total. No había manifiesto previo. Se usan:

| Recurso | Uso |
| --- | --- |
| `hero/hero-principal.webp` (912 × 309) | Portada de escritorio completa; recorte derecho en móvil y titular HTML separado |
| `hero/hero-secundario.webp` (617 × 309) | Campaña de personalización |
| `categorias/running.webp` (509 × 232) | Disciplina y preferencia running |
| `categorias/ciclismo.webp` (502 × 232) | Disciplina y preferencia ciclismo |
| `categorias/entrenamiento.webp` (510 × 232) | Disciplina y preferencia entrenamiento |
| `decoracion/ondas.webp` (359 × 188) | Detalle de movimiento en Cómo funciona |
| `productos/{id}.webp` (720 × 720) | Catálogo, selecciones y recomendaciones de cada ID real |

Seis productos tienen fotografía demostrativa: run-01, run-06, bike-01, bike-05, fit-01 y fit-03. Los doce restantes ya contenían láminas conceptuales: se conservan y se identifican como recursos provisionales. No se cambió ningún deporte o tipo para acomodar una imagen. Los demás recursos quedan inventariados como alternativas disponibles y no se insertan artificialmente en la interfaz.

Las imágenes mantienen proporciones. Los productos usan `contain`; la portada móvil recorta hacia la atleta para dejar fuera el texto incrustado y ofrecer el titular en HTML. En escritorio se conserva la campaña completa y el encabezado equivalente está disponible para lectores de pantalla.

## Validación ejecutada

Estado inicial: build aprobado al ejecutarlo fuera del sandbox, donde esbuild sí puede leer la configuración; pytest: 4 aprobadas. El primer intento de build dentro del sandbox falló por permisos, no por código.

Estado final:

- `npm run build`: TypeScript y Vite aprobados.
- `backend/.venv/Scripts/python.exe -m pytest -q`: cuatro pruebas aprobadas. Cubren algoritmo determinista, exclusión, selecciones sin intereses y recorrido de API con validación de duplicados, límite cinco, CSRF, conflictos de versión y retirada.
- Chrome real automatizado mediante protocolo de depuración: inicio; 18 productos; búsqueda de casco; filtro running con seis productos; intereses running/calzado; selección de run-01; generación real; exclusión de run-01; modificación y regeneración; retirada; alternativa genérica; abrir/cerrar menú móvil; navegación por disciplina; ausencia de desbordamiento en inicio y catálogo a 360 px; imágenes visibles sin fallos y ausencia de excepciones JavaScript.
- Capturas revisadas de escritorio 1440 px y móvil 360 px, en `evidencias/gearly-2-*.png`. Resultado legible por máquina: `evidencias/browser-qa.json`.

Scripts nuevos: `scripts/browser-qa.mjs` (requiere Chrome con depuración en 9222, interfaz en 5173 y API en 8000) y `scripts/inventory-images.mjs` (sin dependencias adicionales). El perfil temporal de Chrome está excluido mediante `.gitignore`.

## Ejecución y límites

Se mantienen los comandos del README: Uvicorn en 8000 y `npm run dev` en frontend; abrir `http://127.0.0.1:5173`.

No se publicó el prototipo. No se ejecutó PostgreSQL ni una evaluación científica o de usabilidad. La inspección automática de desbordamiento cubre inicio y catálogo a 360 px; tablets, otras anchuras, navegación con lector de pantalla y todos los modos de error requieren una revisión manual adicional. Las fuentes usan Google Fonts con alternativas locales. Las tres advertencias de deprecación originales del backend siguen presentes (FastAPI `on_event` y Starlette/AnyIO). Las láminas conceptuales pueden sustituirse más adelante por fotografías exactas manteniendo los mismos IDs.
