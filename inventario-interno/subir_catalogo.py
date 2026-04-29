"""
Pinturas Autos Torres — Subir inventario XLS a Supabase
Sube los productos del XLS a la tabla 'productos' de la web publica.
- Productos nuevos: visible=false (Alicia los activa desde el panel)
- Productos existentes: actualiza nombre, categoria, precio, stock
- Nunca toca: visible, foto_url (gestionados manualmente)

Uso: python subir_catalogo.py
"""

import sys
import json
import urllib.request
import urllib.error
import pandas as pd
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────
XLS_RUTAS = [
    Path(__file__).parent / "Inventario.XLS",
    Path(__file__).parent / "inventario.XLS",
    Path.home() / "Downloads" / "Inventario.XLS",
]

EDGE_URL   = "https://avysjexafpdhzeadnxmc.supabase.co/functions/v1/sincronizar-productos"
SYNC_TOKEN = "pinturas-torres-sync-2025"
BATCH_SIZE = 100

# ── DETECCIÓN DE MARCA (para nombre enriquecido) ──────────────────
MARCAS = [
    ("Sikkens",       ["SIKKENS", "AUTOWAVE", "AUTOCRYL"]),
    ("Novol",         ["NOVOL"]),
    ("Sagola",        ["SAGOLA"]),
    ("CRS",           ["CRS"]),
    ("Vermaat",       ["VERMAAT", "AEROMETAL"]),
    ("3M",            ["3M", "SCOTT BRITE", "PPS"]),
    ("Franchi & Kim", ["FRANCHI"]),
    ("Indasa",        ["INDASA", "RHYNO"]),
    ("Metabo",        ["METABO"]),
    ("Besa",          ["BESA"]),
    ("Dismoer",       ["DISMOER"]),
    ("Airum",         ["AIRUM"]),
    ("Kenda",         ["KENDA", "CROMAUTO"]),
    ("Iwata / Sata",  ["IWATA", "SATA"]),
]

# ── BASES COLORIMÉTRICAS: EXCLUIDAS DEL CATÁLOGO WEB ─────────────
# Son mezclas profesionales (Autowave, Autocryl, Cromaqua, etc.)
# que se usan por máquina — no se venden como producto final.
def es_base_colorimetrica(desc: str) -> bool:
    d = desc.upper().strip()
    if d.startswith("BASE "):
        return True
    if "AUTOWAVE MM " in d:
        return True
    return False

# ── DETECCIÓN DE CATEGORÍA WEB ────────────────────────────────────
# Solo 3 categorías públicas. Orden importa: primera coincidencia gana.
TIPO_A_CATEGORIA = [
    # pinturas: productos de acabado listos para usar (NO bases de mezcla)
    ("pinturas", ["PINTURA ", "SPRAY ", "BARNIZ ", "BARNIZ.", "CLEARCOAT",
                  "FONDO ", "FONDOS ", "IMPRIMACION", "WASH PRIMER", "WASHPRIMER",
                  "PRECARGA", "CONVERTIDOR DE OXIDO", "CONVERTIDOR OXIDO",
                  "ANTIGRAVILLA", "DISOLVENTE", "CATALIZADOR", "DILUYENTE",
                  "ENDURECEDOR", "REDUCTOR ", "ACTIVADOR ", "ACELERANTE",
                  "TEXTURADO ", "NEGRO MATE", "NEGRO SATINADO", "NEGRO TEXTURADO",
                  "ALUMINIO LLANTAS", "ACRITOP", "AUTOCLEAR", "THINNER"]),
    # herramientas: pistolas, lijadoras, maquinaria
    ("herramientas", ["PISTOLA ", "BOQUILLA ", "AEROGRAFO ", "LIJADORA",
                      "PULIDORA", "EXCENTRICA", "SOPLADORA", "COMPRESOR",
                      "ASPIRADOR", "DEPOSITO DE GRAVEDAD", "DEPOSITO GRAVEDAD",
                      "ADAPTADOR PPS", "ADAPTADOR PARA PPS", "VICTORIA RS"]),
    # accesorios: todo lo demás (lijas, cintas, EPI, herramientas manuales...)
]

def detectar_categoria(desc: str) -> str:
    d = desc.upper()
    for cat, palabras in TIPO_A_CATEGORIA:
        if any(p in d for p in palabras):
            return cat
    return "accesorios"

# ── LEER XLS ─────────────────────────────────────────────────────
def encontrar_xls() -> Path:
    for r in XLS_RUTAS:
        if r.exists():
            return r
    return None

def leer_xls(ruta: Path) -> pd.DataFrame:
    df_raw = pd.read_excel(ruta, header=None)
    header_row = None
    for i, row in df_raw.iterrows():
        if any("digo" in str(v).lower() for v in row if pd.notna(v)):
            header_row = i
            break
    if header_row is None:
        raise ValueError("No se encontro la fila de cabeceras")

    df = pd.read_excel(ruta, header=header_row)

    col_map = {}
    for col in df.columns:
        c = str(col).lower()
        if "digo" in c:            col_map[col] = "codigo"
        elif "escri" in c:         col_map[col] = "nombre"
        elif "costo" in c:         col_map[col] = "_costo"
        elif "venta" in c:         col_map[col] = "precio"
        elif "stock" in c:         col_map[col] = "stock"
    df = df.rename(columns=col_map)

    keep = [c for c in ["codigo", "nombre", "precio", "stock"] if c in df.columns]
    df = df[keep].copy()

    df = df.dropna(subset=["nombre"])
    df["nombre"]  = df["nombre"].astype(str).str.strip()
    df = df[df["nombre"].str.len() > 1]
    df["codigo"]  = df["codigo"].fillna("").astype(str).str.strip()
    df["stock"]   = pd.to_numeric(df.get("stock", 0),  errors="coerce").fillna(0).astype(int)
    df["precio"]  = pd.to_numeric(df.get("precio", 0), errors="coerce").fillna(0).round(2)
    df["categoria"] = df["nombre"].apply(detectar_categoria)

    return df

# ── LLAMAR EDGE FUNCTION ─────────────────────────────────────────
def subir_batch(productos: list) -> dict:
    payload = json.dumps({"productos": productos}).encode("utf-8")
    req = urllib.request.Request(
        EDGE_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-sync-token": SYNC_TOKEN,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body[:200]}"}
    except Exception as e:
        return {"error": str(e)}

# ── MAIN ─────────────────────────────────────────────────────────
def main():
    print("=" * 52)
    print("  Subir inventario XLS al catalogo web")
    print("=" * 52)

    ruta = encontrar_xls()
    if not ruta:
        print("\nERROR: No se encontro Inventario.XLS")
        input("Pulsa Enter para salir...")
        sys.exit(1)

    print(f"\nLeyendo: {ruta.name}")
    try:
        df = leer_xls(ruta)
    except Exception as e:
        print(f"ERROR al leer XLS: {e}")
        input("Pulsa Enter para salir...")
        sys.exit(1)

    # Excluir bases colorimétricas ANTES de subir al catálogo
    mask_base = df["nombre"].apply(es_base_colorimetrica)
    df_bases   = df[mask_base]
    df         = df[~mask_base].copy()

    print(f"  {len(df_bases):3d} bases colorimétricas EXCLUIDAS (no van al catálogo)")
    print(f"  {len(df):3d} productos listos para subir")
    print()

    # Resumen por categoria
    for cat, cnt in df["categoria"].value_counts().items():
        print(f"  {cat:15} {cnt} productos")
    print()

    resp = input("Subir al catalogo web? (s/n): ").strip().lower()
    if resp != "s":
        print("Cancelado.")
        input("Pulsa Enter para salir...")
        return

    # Convertir a lista de dicts para la Edge Function
    productos = []
    for _, row in df.iterrows():
        p = {
            "codigo":    row["codigo"] or f"XLS-{len(productos):04d}",
            "nombre":    row["nombre"],
            "categoria": row["categoria"],
            "stock":     int(row["stock"]),
        }
        if row["precio"] > 0:
            p["precio"] = float(row["precio"])
        productos.append(p)

    # Subir en batches
    total_ok = 0
    total_err = 0
    batches = [productos[i:i+BATCH_SIZE] for i in range(0, len(productos), BATCH_SIZE)]
    print(f"Subiendo en {len(batches)} tandas de {BATCH_SIZE}...")
    print()

    for i, batch in enumerate(batches, 1):
        print(f"  Tanda {i}/{len(batches)} ({len(batch)} productos)...", end=" ")
        result = subir_batch(batch)
        if "error" in result:
            print(f"ERROR: {result['error']}")
            total_err += len(batch)
        else:
            ok = result.get("insertados", result.get("upserted", len(batch)))
            print(f"OK ({ok})")
            total_ok += len(batch)

    print()
    print(f"Resultado: {total_ok} productos subidos, {total_err} errores")
    print()
    if total_err == 0:
        print("Todo subido correctamente.")
        print("Los productos estan con visible=false.")
        print("Activar los que quieras mostrar desde el panel admin.")
    print()
    input("Pulsa Enter para cerrar...")

if __name__ == "__main__":
    main()
