"""Descarga los datos crudos de Amazon Reviews 2023 (Sports and Outdoors) que necesitan los demás scripts.

Uso:
    python -I scripts/descargar_datos.py <carpeta_de_destino>

Deja en la carpeta (que debe estar FUERA del repositorio):
    Sports_and_Outdoors.{train,valid,test}.csv   ~200 MB. Interacciones 5-core con partición temporal.
    meta_filtrado.jsonl                          ~57 MB. Metadatos de los productos que aparecen en esas interacciones.

Para lo segundo se lee en streaming el archivo de metadatos de ~4,1 GB (no se guarda en disco, pero SÍ se
transfieren 4,1 GB) y se conservan solo los productos con interacciones. Tarda según la conexión.

Fuente: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023 (McAuley Lab). Revisa sus condiciones de uso.
Sólo biblioteca estándar. Si un archivo ya existe, se omite (borra el archivo para volver a descargarlo).
"""
import csv
import json
import shutil
import sys
import urllib.request
from pathlib import Path

BASE = 'https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main'
CSVS = {s: f'{BASE}/benchmark/5core/timestamp/Sports_and_Outdoors.{s}.csv' for s in ('train', 'valid', 'test')}
META = f'{BASE}/raw/meta_categories/meta_Sports_and_Outdoors.jsonl'
CAMPOS = ('parent_asin', 'title', 'main_category', 'categories', 'average_rating', 'rating_number', 'price', 'store')


def descargar_csv(carpeta):
    for nombre, url in CSVS.items():
        destino = carpeta / f'Sports_and_Outdoors.{nombre}.csv'
        if destino.exists():
            print(f'  ya existe: {destino.name}')
            continue
        print(f'  descargando {destino.name} ...', flush=True)
        with urllib.request.urlopen(url, timeout=120) as r, open(destino, 'wb') as f:
            shutil.copyfileobj(r, f)


def filtrar_metadatos(carpeta):
    destino = carpeta / 'meta_filtrado.jsonl'
    if destino.exists():
        print(f'  ya existe: {destino.name}')
        return
    asins = set()
    for s in CSVS:
        with open(carpeta / f'Sports_and_Outdoors.{s}.csv', encoding='utf-8') as f:
            lector = csv.reader(f)
            next(lector)
            asins.update(fila[1] for fila in lector)
    print(f'  productos con interacciones: {len(asins)}. Leyendo ~4,1 GB de metadatos en streaming ...', flush=True)
    leidas = guardadas = 0
    parcial = destino.with_suffix('.parcial')
    with urllib.request.urlopen(META, timeout=120) as r, open(parcial, 'w', encoding='utf-8') as out:
        for linea in r:
            leidas += 1
            if leidas % 200000 == 0:
                print(f'    leídas {leidas}, guardadas {guardadas}', flush=True)
            try:
                o = json.loads(linea)
            except ValueError:
                continue
            if o.get('parent_asin') in asins:
                out.write(json.dumps({k: o.get(k) for k in CAMPOS}, ensure_ascii=False) + '\n')
                guardadas += 1
    parcial.replace(destino)  # solo queda el archivo final si la lectura terminó completa
    print(f'  listo: {guardadas} productos guardados de {leidas} leídos')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    carpeta = Path(sys.argv[1])
    carpeta.mkdir(parents=True, exist_ok=True)
    print('1/2 CSV de interacciones')
    descargar_csv(carpeta)
    print('2/2 Metadatos filtrados')
    filtrar_metadatos(carpeta)
    print('\nSiguiente:  python -I scripts/preparar_datos.py', carpeta)


if __name__ == '__main__':
    main()
