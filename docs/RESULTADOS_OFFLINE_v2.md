# Resultados del experimento offline, v2 · 4 de noviembre de 2026

Sustituye como resultado vigente a [RESULTADOS_OFFLINE_v1.md](RESULTADOS_OFFLINE_v1.md), que se conserva íntegro. Reproducible con `python -I scripts/experimento_offline.py <carpeta_con_los_CSV>` (≈ 140 s, semilla `20261104`). Cifras completas en `evidencias/resultados_offline.json` (la corrida v1 está en `evidencias/resultados_offline_v1_contenido_basico.json`). Catálogo `BETA-01`, modelo `POP-CONT2-CF-HIB-BETA-02`.

## Cambio de protocolo (registro)
- **Fecha:** 4 de noviembre de 2026.
- **Motivo:** en la corrida v1 el contenido (representación binaria disciplina/tipo, sección 4.1.5 del documento) rindió igual que el azar (NDCG@10 0,0025 frente a 0,0025). Una línea base así de débil hace poco exigente la comparación HIB − CONT.
- **Cambio:** se añade **CONT v2**, un contenido TF-IDF que combina tres grupos con peso igual (disciplina/tipo, ruta de categorías de Amazon, palabras del título y marca). Los pesos se fijaron antes de evaluar y **no se ajustaron con los resultados**. El híbrido usa ahora CONT v2.
- **Qué se conserva:** CONT-v1 se evalúa en la misma corrida. El análisis principal sigue siendo k = 3, K = 10, HIB − CONT con IC 95 % bootstrap, ahora con CONT v2.
- **Salvedad:** la decisión se tomó después de ver el resultado v1. Es un grado de libertad del investigador y debe informarse como tal.

## Resultados en `test` (n = 767 usuarios, mismos que en v1)
NDCG@10 (azar = 10 productos al azar, promedio de 30 repeticiones):

| k | Azar | POP | CONT-v1 | CONT (v2) | CF | HIB |
|---|---|---|---|---|---|---|
| 1 | 0,0023 | 0,0052 | 0,0010 | 0,0133 | 0,0176 | 0,0163 |
| **3** | 0,0025 | 0,0052 | 0,0025 | 0,0182 | 0,0258 | **0,0262** |
| 5 | 0,0025 | 0,0055 | 0,0014 | 0,0165 | 0,0201 | 0,0234 |

Escenario principal (k = 3), métricas secundarias:

| | Precision@10 | Recall@10 | Cobertura del catálogo |
|---|---|---|---|
| POP | 0,0016 | 0,0124 | 0,5 % |
| CONT-v1 | 0,0005 | 0,0042 | 4,2 % |
| CONT (v2) | 0,0042 | 0,0342 | 66,3 % |
| CF | 0,0063 | 0,0489 | 63,7 % |
| HIB | 0,0063 | 0,0504 | 65,2 % |

Diferencias de NDCG@10, media e IC 95 %:

| Comparación | k = 1 | k = 3 | k = 5 |
|---|---|---|---|
| **HIB − CONT (v2)** | +0,0030 [−0,0044, +0,0109] | **+0,0080 [−0,0009, +0,0170]** | +0,0069 [−0,0006, +0,0150] |
| CF − CONT (v2) | +0,0043 [−0,0038, +0,0127] | +0,0076 [−0,0023, +0,0175] | +0,0036 [−0,0049, +0,0124] |
| POP − CONT (v2) | −0,0081 [−0,0155, −0,0014] | −0,0131 [−0,0210, −0,0056] | −0,0109 [−0,0185, −0,0041] |
| CONT (v2) − CONT-v1 | +0,0123 [+0,0061, +0,0194] | +0,0157 [+0,0085, +0,0233] | +0,0151 [+0,0090, +0,0220] |
| HIB − CONT-v1 | +0,0153 [+0,0089, +0,0227] | +0,0237 [+0,0150, +0,0328] | +0,0220 [+0,0149, +0,0298] |

Otras (k = 3): HIB − POP +0,0210 [+0,0128, +0,0301] · **HIB − CF +0,0003 [−0,0026, +0,0036]**.

Ajuste exploratorio en `valid` (n = 962, k = 3, NDCG@10): híbrido con peso del contenido 0,25 → 0,0222 · 0,50 → 0,0205 · 0,75 → 0,0195; CONT v2 solo 0,0151; CONT-v1 solo 0,0008. En `test` se usó 0,5, fijado de antemano.

Listas genéricas (alternativa sin señal): 0 % en todos los métodos.

## Lectura
1. **La hipótesis de trabajo ya no se sostiene con claridad.** Frente al contenido v1, el híbrido ganaba por +0,0237 (IC sin cero). Frente a un contenido razonable, la diferencia es +0,0080 y su IC incluye el cero, también en k = 1 y k = 5. Con 767 usuarios no se puede afirmar que el híbrido supere al contenido. El documento ya prevé este desenlace: no se presume que la solución más compleja gane.
2. **La ventaja anterior era en gran parte un efecto de la línea base débil.** La mejora del contenido (v2 − v1: +0,0157 en k = 3) es del mismo tamaño que la ventaja que antes se atribuía al híbrido.
3. **Contenido, colaborativo e híbrido superan con claridad al azar y a la popularidad.** Popularidad queda por debajo del contenido v2 (diferencia significativa en los tres escenarios).
4. **CF e híbrido son prácticamente iguales** (+0,0003, IC que incluye el cero). El híbrido, tal como está, no aporta sobre el colaborativo solo.
5. **Nominalmente** CF e HIB lideran en k = 3 y k = 5, y CONT queda por detrás, pero las diferencias no son distinguibles del ruido a este tamaño de muestra.
6. **Peso del híbrido:** en el ajuste, dar menos peso al contenido rindió algo mejor (0,25), pero las diferencias son pequeñas y no se aplicaron a `test`.
7. **Cobertura:** contenido, CF e híbrido recomiendan más de la mitad del catálogo; la popularidad, solo el 0,5 %.

## Límites
- 767 usuarios y 1,32 relevantes por usuario: las diferencias son pequeñas (NDCG ≈ 0,02) y la estimación es ruidosa. Un tamaño de muestra mayor podría resolver los intervalos que hoy incluyen el cero.
- CONT v2 usa metadatos de Amazon (categorías, título, marca), en inglés. Su ventaja depende de la calidad de esos metadatos.
- Catálogo de 2.200 productos clasificados por palabras clave; casi no hay calzado ni ropa de running.
- Las señales son interacciones históricas (cualquier calificación), no preferencias declaradas. **Este experimento no evalúa el formulario ni la usabilidad.**
- Datos de Amazon (EE. UU.); no representan consumidores colombianos.
- Una sola corrida por versión; sin corrección por comparaciones múltiples; el cambio de protocolo se decidió tras ver v1.
