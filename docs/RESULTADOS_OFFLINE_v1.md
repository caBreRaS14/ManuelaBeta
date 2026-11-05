# Resultados del experimento offline · 4 de noviembre de 2026

> **Nota:** resultado histórico de la primera corrida (contenido binario). El resultado vigente, con contenido v2 y el registro del cambio de protocolo, está en [RESULTADOS_OFFLINE_v2.md](RESULTADOS_OFFLINE_v2.md).

Reproducible con `python -I scripts/experimento_offline.py <carpeta_con_los_CSV>` (≈ 90 s, semilla `20261104`). Cifras completas en `evidencias/resultados_offline.json`. Catálogo `BETA-01`, modelo `POP-CONT-CF-HIB-BETA-01`.

## Qué se midió
Recuperación de interacciones **posteriores** de un usuario a partir de **k señales previas** (1, 3 o 5), con el mismo `recomendar()` que sirve la aplicación.

- **Datos:** Amazon Reviews 2023, *Sports and Outdoors*, benchmark 5-core con partición temporal (train < valid < test). El modelo (popularidad y vecinos) se calculó **solo con `train`**.
- **Señales:** las k interacciones más recientes del usuario con productos del catálogo, anteriores al periodo evaluado. No se reconstruyeron intereses declarados.
- **Relevantes:** interacciones del usuario en el periodo evaluado con productos del catálogo (media: 1,32 por usuario).
- **Usuarios:** los elegibles (≥ 5 interacciones previas en el catálogo y ≥ 1 relevante): **767 en prueba** y 962 en ajuste. No hubo muestreo. Mismo conjunto para k = 1, 3 y 5.
- **Ajuste vs. prueba:** el peso del híbrido se exploró solo en `valid`; en `test` se usó el valor de la aplicación (0,5), fijado antes de ver resultados.
- **Análisis principal (fijado de antemano):** k = 3, K = 10, diferencia media de NDCG@10 entre HIB y CONT, con IC 95 % por bootstrap (2.000 remuestreos, sobre usuarios). Lo demás es secundario.
- **Alternativa genérica:** no se descartó ninguna lista; la frecuencia de listas genéricas fue **0 %** en todos los métodos.

## Resultados en `test` (n = 767)

NDCG@10 (azar = 10 productos al azar, promedio de 30 repeticiones):

| k | Azar | POP | CONT | CF | HIB |
|---|---|---|---|---|---|
| 1 | 0,0023 | 0,0052 | 0,0010 | 0,0176 | 0,0180 |
| **3** | 0,0025 | 0,0052 | 0,0025 | 0,0258 | **0,0262** |
| 5 | 0,0025 | 0,0055 | 0,0014 | 0,0201 | 0,0201 |

Escenario principal (k = 3), métricas secundarias:

| | Precision@10 | Recall@10 | Cobertura del catálogo |
|---|---|---|---|
| POP | 0,0016 | 0,0124 | 0,5 % |
| CONT | 0,0005 | 0,0042 | 4,2 % |
| CF | 0,0063 | 0,0489 | 63,7 % |
| HIB | 0,0061 | 0,0499 | 62,7 % |

Diferencias de NDCG@10 (media e IC 95 %):

| Comparación | k = 1 | k = 3 | k = 5 |
|---|---|---|---|
| **HIB − CONT** | +0,0170 [+0,0100, +0,0248] | **+0,0237 [+0,0150, +0,0329]** | +0,0187 [+0,0121, +0,0258] |
| CF − CONT | +0,0166 [+0,0099, +0,0241] | +0,0233 [+0,0146, +0,0326] | +0,0187 [+0,0122, +0,0257] |
| POP − CONT | +0,0041 [+0,0008, +0,0073] | +0,0026 [−0,0018, +0,0067] | +0,0041 [+0,0007, +0,0076] |
| HIB − POP (k = 3) | | +0,0210 [+0,0125, +0,0301] | |
| **HIB − CF (k = 3)** | | **+0,0004 [−0,0018, +0,0024]** | |

Ajuste exploratorio en `valid` (n = 962, k = 3, NDCG@10 del híbrido según el peso del contenido): 0,25 → 0,0214 · 0,50 → 0,0202 · 0,75 → 0,0170. Contenido solo: 0,0008.

## Lectura
1. **La hipótesis de trabajo se cumple en este escenario:** la diferencia HIB − CONT en k = 3 es positiva y su IC no incluye el cero.
2. **Pero la ventaja viene del componente colaborativo, no de combinar.** HIB no se distingue de CF (+0,0004, IC que incluye el cero).
3. **El contenido no supera al azar.** CONT (0,0025 en k = 3) es igual a la línea base aleatoria (0,0025). La causa más probable es que su representación solo usa disciplina y tipo (unas 12 combinaciones), con empates masivos que se resuelven por orden de identificador. Por eso la comparación HIB − CONT es poco exigente: **la línea base de contenido es muy débil.** Esto no demuestra que el contenido no sirva, sino que esta implementación aporta casi nada.
4. **Popularidad** rinde cerca del doble que el azar, pero recomienda siempre los mismos productos (cobertura 0,5 %).
5. **En el ajuste, un peso menor para el contenido rindió mejor,** coherente con el punto 3. No se aplicó a `test` porque el peso estaba fijado de antemano.
6. **Más señales no mejoró de forma monótona** (k = 1: 0,0180 · k = 3: 0,0262 · k = 5: 0,0201). No se investigó la causa; no se debe atribuir a una razón concreta sin analizarla.

## Límites
- 767 usuarios y 1,32 relevantes por usuario en promedio: las diferencias absolutas son pequeñas (NDCG ≈ 0,02) y la estimación es ruidosa.
- El catálogo (2.200 productos) y la clasificación en disciplina y tipo se hicieron por palabras clave; puede haber errores. Los zapatos y la ropa de running casi no están en el corpus.
- Las señales son interacciones históricas (cualquier calificación), no preferencias declaradas en el formulario. **Este experimento no evalúa el formulario ni la usabilidad.**
- Datos de Amazon (EE. UU.); no representan consumidores colombianos.
- Una sola ejecución; no se corrigieron comparaciones múltiples.
- Cambiar la representación de contenido después de ver estos resultados exigiría registrarlo como cambio de protocolo, con fecha y motivo, y conservar este resultado.
