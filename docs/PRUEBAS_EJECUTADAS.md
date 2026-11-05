# Registro de verificación · 2 de noviembre de 2026

## Confirmación del alcance académico local — 4 de noviembre de 2026

Se mantiene el backend y el algoritmo sin modificaciones. Se ejecutó Uvicorn con `DATABASE_URL=sqlite:///./gearly.db`, origen 127.0.0.1:5173 y cookies locales. Se reutilizó el frontend existente en 5173: el arranque con `--strictPort` detectó correctamente que el puerto ya estaba ocupado. No se inició PostgreSQL ni se usó nube.

- `npm.cmd run build`: aprobado, TypeScript y Vite (1.42 s).
- `.venv/Scripts/python.exe -m pytest -q`: **4 aprobadas**, tres advertencias de deprecación preexistentes (0.71 s).
- `node scripts/browser-qa.mjs`, Chrome real: portada; catálogo completo de 18 productos; búsqueda `casco`; filtros combinados Running/Calzado con dos productos; recomendaciones por contenido con cero selecciones; cinco selecciones únicas; sexto artículo rechazado; retirada individual; recomendaciones explicadas; exclusión de uno y cinco seleccionados; cambio efectivo de resultados al modificar intereses; recuperación de preferencias guardadas tras recarga; retirada y alternativa genérica real.
- Se conservaron las comprobaciones de menú móvil, categorías, ausencia de desbordamiento en inicio/catálogo a 360 px, imágenes visibles y ausencia de excepciones JavaScript.
- `evidencias/browser-qa.json` y cuatro capturas se regeneraron con el recorrido ampliado.
- `.vscode/tasks.json`: JSON válido con tres tareas; los comandos equivalentes del backend local y frontend se ejecutaron como se describe arriba. La selección de la tarea en la interfaz de VS Code no fue automatizada.
- Inventario: 43 WebP y los 18 IDs del catálogo comprobados, sin cambiar las imágenes.

Los modelos colaborativo/híbrido, chatbot, PostgreSQL y nube no son bloqueos ni tareas pendientes de este incremento: pertenecen a futuras etapas, según [ALCANCE_PROTOTIPO.md](ALCANCE_PROTOTIPO.md). No se ejecutó una evaluación científica, auditoría completa de accesibilidad o prueba de usabilidad.

## Actualización — rediseño Gearly 2.0, 4 de noviembre de 2026

Verificación ejecutada en Windows sobre el proyecto local:

- Estado inicial: `npm run build` aprobado fuera del sandbox; pytest, cuatro pruebas aprobadas.
- Estado final: `npm run build` aprobado (TypeScript + Vite); `.venv/Scripts/python.exe -m pytest -q`, cuatro pruebas aprobadas y tres advertencias de deprecación.
- Chrome real a 1440 px y 360 px: catálogo, búsqueda, filtro de disciplina, preferencias, selección, recomendaciones reales, exclusión, modificación/regeneración, retirada, alternativa genérica, menú móvil y navegación por categorías aprobados. Sin excepciones JavaScript; inicio y catálogo sin desbordamiento a 360 px.
- `node scripts/inventory-images.mjs`: 43 WebP inspeccionados; correspondencia comprobada para los 18 productos.
- Evidencias: `evidencias/browser-qa.json` y cuatro capturas `evidencias/gearly-2-*.png`.

Alcance y límites detallados en [REDISENO_GEARLY_2.md](REDISENO_GEARLY_2.md). El registro histórico siguiente se conserva como evidencia de su fecha original.

## Comandos realmente ejecutados en el entorno de construcción

`cd backend && PYTHONPATH=. pytest -q`

Resultado: **4 passed, 2 warnings in 0.70s**. Dos warnings deprecación `on_event` de FastAPI, no fallos.

1. `test_generico_sin_senales`: salida genérica y ranking determinista sin preferencias.
2. `test_contenido_y_exclusion`: coincidencia running/calzado y exclusión de artículo seleccionado.
3. `test_seleccion_sin_intereses`: uso de selección explícita sin intereses declarados.
4. `test_api_recorrido`: catálogo/búsqueda, acceso sin sesión 401, inicio de sesión, perfil, salida genérica, selección duplicada 422, seis selecciones 422, exclusión, versión obsoleta 409, retiro de selecciones, retiro de perfil, fallback genérico, etiqueta inválida 422 y petición sin CSRF 403.

**Entorno de ejecución:** Linux, Python 3.13, FastAPI 0.128.2 y SQLAlchemy 2.0.50 preinstalados. Las dependencias previstas para Windows están fijadas en `backend/requirements.txt`, pero no se pudo comprobar su instalación desde cero sin acceso al registro de paquetes.

## No verificado

La compilación frontend quedó **sin ejecutar exitosamente**: `npm install --no-audit --no-fund` agotó el tiempo porque este entorno no resuelve `registry.npmjs.org`. No se declara React compilado ni validado en navegador. No se capturaron pantallas reales. El código fuente frontend está incluido para instalación normal en Windows con acceso a npm. Tampoco se comprobó PostgreSQL, ni el despliegue bajo HTTPS, ni pruebas con personas, ni métricas experimentales, ni p95/recuperación/accesibilidad formal.

Para demostrarlo, primero instala dependencias y ejecuta `npm run build` en Windows. Si falla, conserva el error para revisar el código; el presente informe no atribuye éxito no observado.
