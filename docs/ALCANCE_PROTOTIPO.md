# Alcance vigente — Gearly 2.0

Gearly 2.0 es un prototipo académico local, funcional e interactivo para demostrar preferencias explícitas de usuarios nuevos. No se exige una aplicación comercial terminada ni infraestructura externa.

## Incluido

1. Portada editorial deportiva en morados y verdes, con imágenes originales integradas.
2. Catálogo de 18 productos demostrativos cargados inicialmente desde `data/catalogo_demo.json`.
3. Búsqueda y filtros de disciplina/tipo sobre el catálogo real recibido de FastAPI.
4. Intereses deportivos y tipos opcionales.
5. Entre cero y cinco artículos únicos, con posibilidad de retirar cada selección.
6. Recomendaciones reales mediante similitud coseno en `backend/app/recommender.py`, excluyendo los artículos seleccionados.
7. Explicaciones recibidas del backend y coherentes con atributos e intereses.
8. Guardar, modificar y eliminar preferencias; regenerar con el perfil vigente.
9. Exploración genérica explícitamente no personalizada, ordenada por ID; no se presenta como popularidad ni como una recomendación personalizada simulada.
10. Persistencia SQLite local, sesión por cookies, CSRF y control de versión existentes.

Para personalizar no es obligatorio seleccionar artículos: bastan disciplinas o tipos. Sin ninguna señal, la API declara la alternativa genérica. Las preferencias guardadas sobreviven a recargas durante la sesión del navegador; las elecciones sin guardar son borradores.

## Etapas futuras, no requisitos del prototipo

| Función | Estado y alcance |
| --- | --- |
| PostgreSQL | Compatibilidad de conexión previa conservada; migración, despliegue y validación pendientes. No se instala ni usa en el recorrido local. |
| Nube | No desplegada; fuera de esta entrega. |
| Chatbot generativo | No implementado; fuera de esta entrega. |
| Filtrado colaborativo | No implementado ni entrenado. Requiere datos y protocolo de evaluación. |
| Recomendación híbrida | No implementada ni evaluada. |
| Popularidad medida | Pendiente; el orden genérico por ID no la sustituye. |
| Corpus experimental y métricas offline | Pendientes de preparación, permisos y evaluación reproducible. |
| Evaluación humana y controles de investigación | Pendientes. Retirar preferencias del prototipo no equivale a retirar consentimiento de investigación. |

Se conservan las funcionalidades implementadas y las evidencias históricas. Las limitaciones de accesibilidad, usabilidad, rendimiento y despliegue permanecen identificadas, sin impedir la demostración local ni presentarse como resultados científicos.

## Ejecución en Windows y VS Code

Instalación inicial según README (Python, entorno virtual y dependencias; Node y `npm install`). No se necesita activar el entorno virtual: se usa su ejecutable directamente.

Para cada demostración: **Terminal > Ejecutar tarea > Gearly: iniciar prototipo local**. Esperar a que Uvicorn y Vite estén listos; abrir `http://127.0.0.1:5173`. La tarea utiliza SQLite y los puertos 8000/5173 sin modificar el archivo `.env` del usuario. Detener ambas tareas al terminar.

Para demostrar el modelo al profesor, seguir [GUIA_DEMOSTRACION.md](GUIA_DEMOSTRACION.md). Resultados técnicos en [PRUEBAS_EJECUTADAS.md](PRUEBAS_EJECUTADAS.md). Ningún documento de tesis ni conclusión científica se altera para aparentar implementaciones futuras.
