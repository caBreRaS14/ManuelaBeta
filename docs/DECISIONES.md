# Decisiones y diferencias frente al documento

**Fuente principal:** Gearly_Avance_Institucional (1).docx, versión 2 de noviembre de 2026, capítulos III–IV y anexos.

- **ADR01 (alcance vigente Gearly 2.0):** React/TypeScript + FastAPI y SQLite local, con carga inicial de `data/catalogo_demo.json`. El prototipo no requiere PostgreSQL, Docker ni servicios externos. La compatibilidad previa de `DATABASE_URL` se conserva, pero PostgreSQL pertenece a una etapa posterior y no bloquea esta entrega.
- **ADR02:** backend modular monolítico. No se crean microservicios ni pasarelas de compra.
- **Método CONT:** representación binaria disciplina/tipo, coseno y pesos iguales de los bloques de preferencias e ítems, como se describe en 4.1.5. Sin vecinos colaborativos ni hibridación.
- **Contradicción del plan:** el documento llama “popularidad” al fallback incluso sin perfil, pero el catálogo ficticio no tiene usuarios de entrenamiento ni popularidad observable. Una lista ordenada por ID se rotula explícitamente **exploración genérica**, no POP científico.
- **Dataset:** Amazon Reviews 2023 / Sports and Outdoors es el candidato de la tesis, no el conjunto de esta demostración. No se descargó ni redistribuyó aquí. La revisión de permisos y las particiones temporales siguen pendientes.
- **Alcance F01:** preferencias y selección se guardan en una sesión aleatoria local sin datos identificatorios. Los controles completos de códigos de participante, consentimiento, operador e investigación propuestos en 4.1.6–4.1.7 no se presentan como implementados.
- **Sesiones:** cookie HttpOnly y token CSRF para mutaciones, pero sin identidad institucional ni expiración verificada en pruebas específicas. No debe exponerse en Internet.
- **Registro:** la tabla `listas` almacena resultados y versión del perfil, del modelo y del catálogo. No se crean resultados offline ni respuestas humanas.
- **Catálogo:** productos demostrativos propios con etiquetas revisables; no representan Amazon ni tiendas colombianas.
- **Visuales:** diseño editorial morado/verde, íconos Lucide bajo licencia ISC y fotografías/recursos conceptuales originales aportados en `frontend/public/images`. Se mantiene el rediseño existente.

- **Etapas futuras, fuera del incremento actual:** PostgreSQL, servicios en la nube, chatbot generativo, filtrado colaborativo y recomendación híbrida. No se implementan, entrenan ni evalúan aquí. POP medido, corpus experimental autorizado, evaluación offline/humana y controles de investigación mantienen sus estados pendientes. Las listas genéricas actuales son un orden neutro por ID, no una simulación de un modelo futuro.

- **ADR-beta-01 · Contenido v2 (4 de noviembre de 2026):** el método CONT de 4.1.5 (binario disciplina/tipo) se conserva como **CONT-v1** y se añade **CONT v2** (TF-IDF con disciplina/tipo, ruta de categorías, palabras del título y marca; tres grupos con peso igual, fijados antes de evaluar). Motivo: CONT-v1 rindió igual que el azar en el experimento offline (ver `docs/RESULTADOS_OFFLINE_v1.md`). La aplicación y el híbrido usan CONT v2 (modelo `POP-CONT2-CF-HIB-BETA-02`). El cambio de protocolo y su salvedad (decisión posterior a ver v1) están en `docs/RESULTADOS_OFFLINE_v2.md`. Si no hay `atributos` en el modelo (catálogo demo), el sistema usa CONT-v1.
