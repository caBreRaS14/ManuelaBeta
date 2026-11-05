# Guía para la demostración al profesor (5–8 minutos)

**Antes de grabar:** instala las dependencias según README si es el primer uso. En VS Code ejecuta **Terminal > Ejecutar tarea > Gearly: iniciar prototipo local**. Espera a que ambos servidores estén listos y abre `http://127.0.0.1:5173`. Se usa SQLite local; no se necesita PostgreSQL, Docker ni nube. El diseño editorial y las fotografías forman parte del prototipo.

| Paso | Qué hacer | Qué debe verse | Qué explicar |
|---|---|---|---|
| 1 | Mostrar Inicio | Portada Gearly y aviso académico | No es tienda comercial ni tiene pagos. |
| 2 | Abrir Catálogo, comprobar 18 productos y escribir `casco` | Un casco en resultados | Búsqueda local sobre el catálogo real recibido de la API. Borra la palabra. |
| 3 | Elegir filtro `Ciclismo` | Solo artículos de ciclismo | Filtros por atributos explícitos. |
| 4 | Abrir el corazón del encabezado | Diseña tu experiencia, formulario opcional | No es encuesta de investigación: captura preferencias F01. |
| 5 | Elegir `Running`, `Calzado`; marcar `Tenis de running ligeros` | Contador 1/5 | Hasta cinco señales, sin duplicados. |
| 6 | Pulsar `DESCUBRIR MIS RECOMENDACIONES` | Lista por contenido, razones | Coseno entre el perfil y los atributos del catálogo; excluye lo seleccionado. También funciona con cero artículos si hay intereses. |
| 7 | Volver y cambiar disciplina por `Ciclismo`, tipo por `Protección`; retirar selección y volver a generar | Productos de ciclismo/protección arriba | El ranking depende de las señales actuales. |
| 8 | En Para ti, pulsar `Explorar sin personalización` | Preferencias retiradas y etiqueta `EXPLORACIÓN GENÉRICA` | Orden neutro por ID, no popularidad. También se puede retirar desde el formulario y generar sin señales. |
| 9 | Abrir `http://127.0.0.1:8000/docs` | Documentación Swagger | React consume FastAPI real con SQLite local y catálogo inicial JSON. |
| 10 | Ejecutar `pytest -v` | Resultado auténtico de las pruebas | Pruebas técnicas, no resultados empíricos del trabajo de grado. |

## Capturas reales que debes guardar en `evidencias/`

1. `01_inicio.png`: vista inicial de Gearly con distintivo académico.
2. `02_catalogo_filtros.png`: búsqueda `casco` o filtro `Ciclismo`.
3. `03_preferencias.png`: running + calzado y un artículo seleccionado (1/5).
4. `04_recomendaciones_contenido.png`: primera lista y motivos, sin el seleccionado.
5. `05_recomendaciones_modificadas.png`: lista diferente tras cambiar preferencias.
6. `06_recomendacion_generica.png`: después de borrar todas las preferencias.
7. `07_api_docs.png`: Swagger /docs y endpoints.
8. `08_pruebas.png`: salida auténtica de pytest en terminal.

En Windows toma capturas con **Win + Shift + S**. Guarda cada una con el nombre indicado; nunca presentes dibujos o capturas de un diseño como ejecución real.

## Qué responder si preguntan por el híbrido

“El documento plantea comparar contenido, popularidad, colaborativo e híbrido sobre un subconjunto autorizado de Amazon Reviews 2023. Este incremento implementa primero el recorrido completo con contenido y exploración genérica. No hemos evaluado ni entrenado un híbrido con interacciones reales; esa fase se reporta como pendiente.”
