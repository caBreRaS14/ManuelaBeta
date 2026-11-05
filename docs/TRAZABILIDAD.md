# Matriz de trazabilidad · estado del incremento 0.1

**Alcance vigente Gearly 2.0:** [ALCANCE_PROTOTIPO.md](ALCANCE_PROTOTIPO.md). El recorrido de contenido/genérico se mantiene local con SQLite. PostgreSQL, nube, chatbot generativo, colaborativo e híbrido quedan para etapas posteriores y no son requisitos de esta demostración. La matriz siguiente conserva los estados iniciales; la verificación posterior del navegador y del rediseño está registrada en [PRUEBAS_EJECUTADAS.md](PRUEBAS_EJECUTADAS.md).

**Los estados “comprobado” se refieren únicamente a ejecución técnica documentada, nunca a evaluación de tesis.**

| Código documento | Funcionalidad | Estado inicial |
|---|---|---|
| RF01 | Consultar catálogo y filtrar/buscar | Implementado y comprobado mediante test de API; interfaz sin comprobación de navegador |
| RF02 | Capturar vocabulario de intereses y tipos | Implementado y comprobado mediante test de API; interfaz sin comprobación de navegador |
| RF03 | Omitir, editar o retirar perfil | Implementado y comprobado mediante test de API; interfaz sin comprobación de navegador |
| RF04 | Selecciones de 0 a 5, únicas | Implementado y comprobado mediante test de API; interfaz sin comprobación de navegador |
| RF05 | Generar recomendaciones y manejar 0 señales | Implementado y comprobado CONT/genérico; POP/CF/HIB pendientes |
| RF06 | Método y explicación auténticos | Implementado y comprobado mediante test de API; interfaz sin comprobación de navegador |
| RF07 | Registrar listas y versiones | Implementado y comprobado mediante test de API; interfaz sin comprobación de navegador |
| RF08 | Juicios H03 sin alterar modelo | Pendiente (evaluación humana) |
| RF09 | Operador y aprobación de catálogo | Pendiente (carga local inicial, sin rol operador) |
| RF10 | Preparación offline y métricas reproducibles | Pendiente (solo pruebas técnicas) |
| RF11 | Consentimiento y retiro de investigación | Pendiente (eliminar preferencias no es retirar consentimiento) |
| RF12 | Aviso académico y sin transacciones | Implementado, verificación visual pendiente |
| RNF01 | Privacidad / acceso entre participantes | Parcial: sesión y CSRF; prueba 401/403 básica aprobada, seguridad integral pendiente |
| RNF02 | Integridad y duplicados | Implementado y comprobado mediante test técnico |
| RNF03 | Reproducibilidad del ranking | Implementado y comprobado mediante test técnico |
| RNF04 | Rendimiento p95 a 5.000 productos | Pendiente |
| RNF05 | Teclado y diseño 360 px / WCAG | Parcial, auditoría pendiente |
| RNF06 | Mantenibilidad | Arquitectura modular; verificación completa pendiente |
| RNF07 | Recuperación RPO/RTO | Pendiente |
| RNF08 | Separación datos de prueba | No hay corpus experimental integrado; control formal pendiente |

Actualizar los estados únicamente después de ejecutar pruebas específicas. Las pruebas se ejecutan con `cd backend; .\\.venv\\Scripts\\python.exe -m pytest -v`.
