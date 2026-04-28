"""
Pinturas Autos Torres — Procesador de Inventario
Lee el XLS exportado de TPVsol y genera inventario.html

Uso: python procesar_inventario.py
O doble clic en generar.bat
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────

XLS_RUTAS = [
    Path(__file__).parent / "Inventario.XLS",
    Path(__file__).parent / "inventario.XLS",
    Path(__file__).parent / "Inventario.xls",
    Path.home() / "Downloads" / "Inventario.XLS",
    Path.home() / "Downloads" / "inventario.XLS",
]

SALIDA_HTML = Path(__file__).parent / "inventario.html"

SB_URL = "https://avysjexafpdhzeadnxmc.supabase.co"
SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF2eXNqZXhhZnBkaHplYWRueG1jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY5MzQzMTAsImV4cCI6MjA5MjUxMDMxMH0.cCB8tjDlBhhazXrFtI4hjiG5I6Gbax_Z-Q7FiznVvCk"

# ──────────────────────────────────────────────
# DETECCIÓN DE MARCA
# ──────────────────────────────────────────────

MARCAS = [
    ("Sikkens",       ["SIKKENS", "AUTOWAVE", "AUTOCRYL", "AUTOSURFACER"]),
    ("Novol",         ["NOVOL"]),
    ("Sagola",        ["SAGOLA", "FURA 2"]),
    ("CRS",           ["CRS"]),
    ("Vermaat",       ["VERMAAT", "AEROMETAL"]),
    ("3M",            ["3M", "SCOTT BRITE", "SCOTCH-BRITE", "SCOTCHBRITE", "PPS"]),
    ("Franchi & Kim", ["FRANCHI", "FRANCHI&KIM", "FRANCHI & KIM"]),
    ("Indasa",        ["INDASA", "RHYNO"]),
    ("Metabo",        ["METABO"]),
    ("Besa",          ["BESA"]),
    ("Dismoer",       ["DISMOER"]),
    ("Airum",         ["AIRUM"]),
    ("Felton",        ["FELTON"]),
    ("Bryll",         ["BRYLL"]),
    ("Kenda",         ["KENDA", "CROMAUTO"]),
    ("Iwata / Sata",  ["IWATA", "SATA"]),
]

def detectar_marca(desc: str) -> str:
    d = desc.upper()
    for nombre, palabras in MARCAS:
        for p in palabras:
            if p in d:
                return nombre
    return "Sin marca"

# ──────────────────────────────────────────────
# DETECCIÓN DE TIPO
# ──────────────────────────────────────────────

TIPOS = [
    ("Lija / Abrasivo",          ["LIJA", "DISCO VELCRO", "DISCO ABRAS", "VELCRO ABRAS",
                                   "PLIEGO SCOTT", "ESPONJA LIJAR", "ESPONJA DE LIJ", "GARLOPA"]),
    ("Masilla",                  ["MASILLA", "UNISOFT", "POLIESTER"]),
    ("Pintura / Base",           ["PINTURA", "BASE AGUA", "BASE SOLV", "AUTOWAVE", "AUTOCRYL",
                                   "CROMAUTO", "BASE BICAPA", "BASE DE AGUA", "BASE WATERBASED"]),
    ("Spray",                    ["SPRAY"]),
    ("Barniz",                   ["BARNIZ", "LACA ", "CLEARCOAT"]),
    ("Fondo / Imprimacion",      ["FONDO", "IMPRIMACION", "IMPRIMACI", "WASH PRIMER",
                                   "PRECARGA", "CONVERTIDOR DE OXIDO", "ANTIOXIDANTE",
                                   "FOSFATANTE", "INHIBIDOR"]),
    ("Disolvente / Catalizador", ["DISOLVENTE", "CATALIZADOR", "DILUYENTE",
                                   "ENDURECEDOR", "REDUCTOR", "ACTIVADOR"]),
    ("Pistola / Aerografia",     ["PISTOLA", "BOQUILLA", "RACOR", "AGUJA ", "TAPA AGUJA",
                                   "AEROGRAFO", "AEROGRAFIA", "DEPOSITO DE GRAVEDAD",
                                   "DEPOSITO GRAVEDAD", "DEPOSITOS DE GRAVEDAD",
                                   "RETENEDOR DE FILTROS", "ADAPTADOR PPS", "ADAPTADOR PARA AEROG",
                                   "GRAVEDAD "]),
    ("Lijadora / Pulidora",      ["LIJADORA", "PULIDORA", "EXCENTRICA", "SOPLADORA"]),
    ("Compresor / Aire",         ["COMPRESOR", "MANGUERA", "REGULADOR DE PRESION",
                                   "FILTRO SEPARADOR", "CONDENSADOR ", "ENCHUFE LATON",
                                   "ESCOBILLAS"]),
    ("Cinta / Enmascarado",      ["CINTA", "ENMASCARAR", "PAPEL ENCM", "FILM CON",
                                   "FILM POLIET", "VELCRO ADHESIVO"]),
    ("Mascarilla / EPI",         ["MASCARILLA", "MASCARILLAS", "GUANTE", "MONO ",
                                   "MONOS ", "GAFAS", "PROTEC", "FILTRO PARTICULAS"]),
    ("Herramienta",              ["CUTTER", "ESPATULA", "PINCEL", "BROCHA", "RODILLO",
                                   "LLAVE", "MANGO VARILLA", "RECAMBIO VELOUR", "PINCELES",
                                   "REGLA MEDIR"]),
    ("Pulimento / Abrillantado", ["PULIMENTO", "ABRILLANTADOR", "AUTOGLOSS", "POLISH"]),
    ("Limpieza",                 ["DESENGRASANTE", "LIMPIADOR", "LIMPIEZA", "SILICON OFF",
                                   "KIT LIMPIEZA"]),
    ("Adhesivo / Sellado",       ["ADHESIVO", "SELLADOR", "SIKAFLEX", "PEGAMENTO",
                                   "BOQUILLAS PEGAMENTO"]),
    ("Envase / Recipiente",      ["ENVASE DE PLASTICO", "ENVASE PLAST", "RECIPIENTE"]),
]

def detectar_tipo(desc: str) -> str:
    d = desc.upper()
    for nombre, palabras in TIPOS:
        for p in palabras:
            if p in d:
                return nombre
    return "Sin clasificar"

# ──────────────────────────────────────────────
# LECTURA DEL XLS
# ──────────────────────────────────────────────

def encontrar_xls() -> Path:
    for ruta in XLS_RUTAS:
        if ruta.exists():
            return ruta
    return None

def leer_inventario(ruta: Path) -> "pd.DataFrame":
    print(f"Leyendo: {ruta}")
    df = pd.read_excel(ruta, header=None)

    header_row = None
    for i, row in df.iterrows():
        vals = [str(v).lower() for v in row if pd.notna(v)]
        if any("digo" in v for v in vals):
            header_row = i
            break

    if header_row is None:
        print("ERROR: No se encontro la fila de cabeceras en el XLS")
        sys.exit(1)

    df = pd.read_excel(ruta, header=header_row)

    col_map = {}
    for col in df.columns:
        c = str(col).lower()
        if "digo" in c:
            col_map[col] = "codigo"
        elif "escri" in c:
            col_map[col] = "descripcion"
        elif "costo" in c or "coste" in c:
            col_map[col] = "_costo"
        elif "venta" in c:
            col_map[col] = "precio_venta"
        elif "stock" in c:
            col_map[col] = "stock"

    df = df.rename(columns=col_map)

    cols_keep = [c for c in ["codigo", "descripcion", "precio_venta", "stock"] if c in df.columns]
    df = df[cols_keep].copy()

    df = df.dropna(subset=["descripcion"])
    df["descripcion"] = df["descripcion"].astype(str).str.strip()
    df = df[df["descripcion"].str.len() > 1]

    df["codigo"] = df["codigo"].fillna("").astype(str).str.strip()
    df["stock"] = pd.to_numeric(df.get("stock", 0), errors="coerce").fillna(0).astype(int)
    df["precio_venta"] = pd.to_numeric(df.get("precio_venta", 0), errors="coerce").fillna(0).round(2)

    df["marca"] = df["descripcion"].apply(detectar_marca)
    df["tipo"] = df["descripcion"].apply(detectar_tipo)

    return df

# ──────────────────────────────────────────────
# GENERACIÓN DEL HTML
# ──────────────────────────────────────────────

def generar_html(df: "pd.DataFrame", ruta_xls: str) -> str:
    productos = df.to_dict(orient="records")
    for p in productos:
        p.pop("_costo", None)

    marcas_base = sorted(df["marca"].unique().tolist())
    tipos_base  = sorted(df["tipo"].unique().tolist())

    data_json   = json.dumps(productos, ensure_ascii=False)
    marcas_json = json.dumps(marcas_base, ensure_ascii=False)
    tipos_json  = json.dumps(tipos_base, ensure_ascii=False)
    total       = len(productos)
    sb_url      = SB_URL
    sb_key      = SB_KEY

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"es\">\n"
        "<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "<title>Inventario Interno — Pinturas Autos Torres</title>\n"
        "<link href=\"https://fonts.googleapis.com/css2?family=Unbounded:wght@700;900&family=Inter:wght@400;500;600&display=swap\" rel=\"stylesheet\">\n"
        "<style>\n"
        "*{box-sizing:border-box;margin:0;padding:0}\n"
        ":root{\n"
        "  --mg:#B5006A;--mg2:#D4007A;--mg3:#F7E0EE;\n"
        "  --black:#0D0D0D;--white:#fff;--gray:#F3F3F3;--dg:#666;\n"
        "  --head:'Unbounded',sans-serif;--body:'Inter',sans-serif;\n"
        "}\n"
        "body{font-family:var(--body);background:#FAFAFA;color:var(--black);min-height:100vh}\n"
        ".top{background:var(--mg);padding:.85rem 1.5rem;display:flex;align-items:center;gap:1rem;\n"
        "  border-bottom:3px solid var(--black);position:sticky;top:0;z-index:20;flex-wrap:wrap}\n"
        ".top-logo{font-family:var(--head);font-size:10px;font-weight:900;color:var(--white);letter-spacing:-0.01em;flex:1;min-width:0}\n"
        ".top-logo b{background:var(--white);color:var(--mg);padding:2px 7px;margin-right:5px}\n"
        ".top-right{display:flex;gap:8px;align-items:center;flex-wrap:wrap}\n"
        ".top-badge{background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);\n"
        "  color:var(--white);font-size:11px;padding:4px 10px;border-radius:20px;white-space:nowrap}\n"
        ".autosave{display:flex;align-items:center;gap:6px;font-size:11px;color:rgba(255,255,255,0.85)}\n"
        ".autosave-dot{width:8px;height:8px;border-radius:50%;background:#4CAF50;flex-shrink:0;\n"
        "  box-shadow:0 0 6px rgba(76,175,80,0.8);transition:background .3s}\n"
        ".autosave-dot.saving{background:#FFB300;animation:pulse .6s infinite alternate}\n"
        ".autosave-dot.offline{background:#FFB300;box-shadow:0 0 6px rgba(255,179,0,0.8)}\n"
        "@keyframes pulse{from{opacity:1}to{opacity:.3}}\n"
        ".filtros{background:var(--white);border-bottom:2px solid var(--black);\n"
        "  padding:1rem 1.5rem;display:flex;flex-wrap:wrap;gap:.75rem;align-items:flex-end}\n"
        ".f-group{display:flex;flex-direction:column;gap:4px;min-width:160px}\n"
        ".f-group label{font-size:10px;font-weight:600;text-transform:uppercase;\n"
        "  letter-spacing:.08em;color:var(--dg)}\n"
        "select,input[type=text]{\n"
        "  font-family:var(--body);font-size:13px;\n"
        "  border:1.5px solid #ddd;border-radius:6px;padding:8px 10px;\n"
        "  background:var(--white);color:var(--black);outline:none;transition:border-color .15s;\n"
        "}\n"
        "select:focus,input[type=text]:focus{border-color:var(--mg)}\n"
        ".f-actions{display:flex;gap:8px;align-items:flex-end;margin-left:auto}\n"
        ".btn{font-family:var(--head);font-size:9px;font-weight:700;letter-spacing:.06em;\n"
        "  text-transform:uppercase;padding:9px 16px;border-radius:5px;border:none;\n"
        "  cursor:pointer;transition:background .15s}\n"
        ".btn-out{background:var(--white);color:var(--black);border:2px solid #ddd}\n"
        ".btn-out:hover{border-color:var(--mg);color:var(--mg)}\n"
        ".stats-bar{padding:.6rem 1.5rem;background:var(--gray);border-bottom:1px solid #e0e0e0;\n"
        "  display:flex;gap:1.5rem;font-size:12px;color:var(--dg);flex-wrap:wrap}\n"
        ".stats-bar b{color:var(--black)}\n"
        ".tabla-wrap{overflow-x:auto;padding:0 1.5rem 2rem}\n"
        "table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:13px}\n"
        "thead th{\n"
        "  font-family:var(--head);font-size:8px;font-weight:700;letter-spacing:.1em;\n"
        "  text-transform:uppercase;color:var(--dg);\n"
        "  padding:10px 12px;text-align:left;border-bottom:2px solid var(--black);\n"
        "  position:sticky;top:0;background:var(--white);z-index:5;white-space:nowrap;\n"
        "}\n"
        "tbody tr{border-bottom:1px solid #eee;transition:background .1s}\n"
        "tbody tr:hover{background:var(--mg3)}\n"
        "td{padding:9px 12px;vertical-align:middle}\n"
        "td.codigo{font-family:monospace;font-size:11px;color:var(--dg);white-space:nowrap}\n"
        "td.descripcion{max-width:320px;line-height:1.4}\n"
        "td.precio{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}\n"
        "td.stock{text-align:center;font-weight:600}\n"
        ".badge{\n"
        "  display:inline-flex;align-items:center;gap:4px;\n"
        "  font-size:10px;font-weight:500;padding:3px 9px;border-radius:12px;\n"
        "  white-space:nowrap;cursor:pointer;transition:filter .15s;user-select:none;\n"
        "}\n"
        ".badge:hover{filter:brightness(0.9)}\n"
        ".badge-marca{background:#E8F4FD;color:#1A6FA8}\n"
        ".badge-tipo{background:#F0F7EE;color:#2D7A3A}\n"
        ".badge-sin{background:#F5F5F5;color:#999}\n"
        ".badge-editado{outline:2px solid var(--mg);outline-offset:1px}\n"
        ".badge-pencil{font-size:9px;opacity:.6}\n"
        ".stock-0{color:#C0392B;font-weight:700}\n"
        ".stock-low{color:#E67E22;font-weight:700}\n"
        ".stock-ok{color:#27AE60}\n"
        ".popover{\n"
        "  position:fixed;z-index:100;\n"
        "  background:var(--white);border:2px solid var(--black);border-radius:10px;\n"
        "  padding:14px 16px;width:270px;box-shadow:4px 4px 0 var(--black);\n"
        "  display:none;\n"
        "}\n"
        ".popover.visible{display:block}\n"
        ".popover-title{font-family:var(--head);font-size:9px;font-weight:700;\n"
        "  letter-spacing:.08em;text-transform:uppercase;color:var(--dg);margin-bottom:8px}\n"
        ".popover-desc{font-size:11px;color:#444;margin-bottom:10px;\n"
        "  border-left:3px solid var(--mg);padding-left:8px;line-height:1.4;\n"
        "  max-height:50px;overflow:hidden}\n"
        ".popover select{width:100%;margin-bottom:8px;font-size:13px}\n"
        ".popover-custom{display:flex;gap:6px;margin-bottom:10px}\n"
        ".popover-custom input{flex:1;font-size:12px;padding:6px 8px}\n"
        ".popover-custom input::placeholder{color:#bbb}\n"
        ".popover-btns{display:flex;gap:6px}\n"
        ".pop-ok{flex:1;background:var(--mg);color:var(--white);border:none;\n"
        "  border-radius:5px;padding:8px;font-family:var(--head);font-size:8px;\n"
        "  font-weight:700;letter-spacing:.06em;text-transform:uppercase;cursor:pointer}\n"
        ".pop-ok:hover{background:var(--mg2)}\n"
        ".pop-cancel{background:var(--white);color:var(--black);border:2px solid #ddd;\n"
        "  border-radius:5px;padding:8px 12px;font-family:var(--head);font-size:8px;\n"
        "  font-weight:700;letter-spacing:.06em;text-transform:uppercase;cursor:pointer}\n"
        ".pop-cancel:hover{border-color:var(--black)}\n"
        ".toast{\n"
        "  position:fixed;bottom:24px;left:50%;transform:translateX(-50%);\n"
        "  background:var(--black);color:var(--white);\n"
        "  font-size:13px;padding:10px 20px;border-radius:8px;\n"
        "  opacity:0;transition:opacity .3s;pointer-events:none;z-index:200;white-space:nowrap;\n"
        "}\n"
        ".toast.show{opacity:1}\n"
        ".empty{text-align:center;padding:4rem 2rem;color:var(--dg)}\n"
        "@media(max-width:640px){\n"
        "  .filtros{flex-direction:column}\n"
        "  .f-group{min-width:100%}\n"
        "  .f-actions{margin-left:0;width:100%;flex-direction:column}\n"
        "  .btn{width:100%;text-align:center}\n"
        "  table{font-size:12px}\n"
        "  thead th{font-size:7px;padding:8px}\n"
        "  td{padding:7px 8px}\n"
        "  td.descripcion{max-width:140px}\n"
        "  .popover{width:calc(100vw - 32px);left:16px!important}\n"
        "}\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "\n"
        "<div class=\"top\">\n"
        "  <div class=\"top-logo\"><b>PAT</b>Inventario Interno</div>\n"
        "  <div class=\"top-right\">\n"
        f"    <div class=\"top-badge\">{total} productos &middot; {ruta_xls}</div>\n"
        "    <div class=\"autosave\">\n"
        "      <div class=\"autosave-dot\" id=\"autosave-dot\"></div>\n"
        "      <span id=\"autosave-txt\">Conectando...</span>\n"
        "    </div>\n"
        "  </div>\n"
        "</div>\n"
        "\n"
        "<div class=\"filtros\">\n"
        "  <div class=\"f-group\">\n"
        "    <label>Marca</label>\n"
        "    <select id=\"sel-marca\"><option value=\"\">Todas las marcas</option></select>\n"
        "  </div>\n"
        "  <div class=\"f-group\">\n"
        "    <label>Tipo</label>\n"
        "    <select id=\"sel-tipo\"><option value=\"\">Todos los tipos</option></select>\n"
        "  </div>\n"
        "  <div class=\"f-group\">\n"
        "    <label>Buscar</label>\n"
        "    <input type=\"text\" id=\"buscar\" placeholder=\"Código o descripción…\">\n"
        "  </div>\n"
        "  <div class=\"f-group\">\n"
        "    <label>Ordenar por</label>\n"
        "    <select id=\"sel-orden\">\n"
        "      <option value=\"descripcion\">Descripción A-Z</option>\n"
        "      <option value=\"stock-asc\">Stock ↑ (menor primero)</option>\n"
        "      <option value=\"stock-desc\">Stock ↓ (mayor primero)</option>\n"
        "      <option value=\"precio-desc\">Precio ↓</option>\n"
        "      <option value=\"precio-asc\">Precio ↑</option>\n"
        "      <option value=\"marca\">Marca A-Z</option>\n"
        "      <option value=\"editados\">Editados primero</option>\n"
        "    </select>\n"
        "  </div>\n"
        "  <div class=\"f-actions\">\n"
        "    <button class=\"btn btn-out\" onclick=\"limpiarFiltros()\">Limpiar</button>\n"
        "  </div>\n"
        "</div>\n"
        "\n"
        "<div class=\"stats-bar\" id=\"stats-bar\">Cargando…</div>\n"
        "\n"
        "<div class=\"tabla-wrap\">\n"
        "  <table>\n"
        "    <thead><tr>\n"
        "      <th>Código</th>\n"
        "      <th>Descripción</th>\n"
        "      <th title=\"Haz clic en el badge para editar\">Marca ✏</th>\n"
        "      <th title=\"Haz clic en el badge para editar\">Tipo ✏</th>\n"
        "      <th onclick=\"ordenarPor('stock-asc')\" style=\"cursor:pointer\">Stock ↕</th>\n"
        "      <th onclick=\"ordenarPor('precio-desc')\" style=\"cursor:pointer\">P. Venta ↕</th>\n"
        "    </tr></thead>\n"
        "    <tbody id=\"tabla-body\"></tbody>\n"
        "  </table>\n"
        "  <div class=\"empty\" id=\"empty-msg\" style=\"display:none\">\n"
        "    <div style=\"font-size:2.5rem;margin-bottom:.75rem\">\U0001f50d</div>\n"
        "    <div>No hay productos con estos filtros.</div>\n"
        "  </div>\n"
        "</div>\n"
        "\n"
        "<div class=\"popover\" id=\"popover\">\n"
        "  <div class=\"popover-title\" id=\"pop-title\"></div>\n"
        "  <div class=\"popover-desc\" id=\"pop-desc\"></div>\n"
        "  <select id=\"pop-select\"></select>\n"
        "  <div class=\"popover-custom\">\n"
        "    <input type=\"text\" id=\"pop-custom\" placeholder=\"O escribe una nueva…\">\n"
        "  </div>\n"
        "  <div class=\"popover-btns\">\n"
        "    <button class=\"pop-cancel\" onclick=\"cerrarPopover()\">Cancelar</button>\n"
        "    <button class=\"pop-ok\" onclick=\"confirmarEdicion()\">Guardar</button>\n"
        "  </div>\n"
        "</div>\n"
        "\n"
        "<div class=\"toast\" id=\"toast\"></div>\n"
        "\n"
        "<script src=\"https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js\"></script>\n"
        "<script>\n"
        f"const SB_URL  = '{sb_url}';\n"
        f"const SB_KEY  = '{sb_key}';\n"
        "const sb      = supabase.createClient(SB_URL, SB_KEY);\n"
        "const TABLA   = 'inventario_correcciones';\n"
        "const LS_KEY  = 'pat_correcciones_v1';\n"
        "\n"
        f"const TODOS_ORIG  = {data_json};\n"
        f"const MARCAS_BASE = {marcas_json};\n"
        f"const TIPOS_BASE  = {tipos_json};\n"
        "\n"
        "let correcciones = {};\n"
        "let TODOS = [];\n"
        "\n"
        "function claveProducto(p) {\n"
        "  const c = (p.codigo || '').trim();\n"
        "  if (c && c !== '—') return c;\n"
        "  return 'desc_' + btoa(encodeURIComponent(p.descripcion.slice(0,60))).slice(0,20);\n"
        "}\n"
        "\n"
        "function aplicarCorreccionesADatos() {\n"
        "  TODOS = TODOS_ORIG.map((p, i) => {\n"
        "    const key = claveProducto(p);\n"
        "    const c   = correcciones[key] || {};\n"
        "    return { ...p, _idx: i, _key: key, marca: c.marca ?? p.marca, tipo: c.tipo ?? p.tipo };\n"
        "  });\n"
        "}\n"
        "\n"
        "async function cargarCorrecciones() {\n"
        "  setIndicador('cargando');\n"
        "  try {\n"
        "    const { data, error } = await sb.from(TABLA).select('codigo,marca,tipo');\n"
        "    if (error) throw error;\n"
        "    correcciones = {};\n"
        "    (data || []).forEach(row => {\n"
        "      correcciones[row.codigo] = { marca: row.marca, tipo: row.tipo };\n"
        "    });\n"
        "    localStorage.setItem(LS_KEY, JSON.stringify(correcciones));\n"
        "    setIndicador('ok');\n"
        "  } catch(err) {\n"
        "    console.warn('Sin conexion con Supabase:', err.message);\n"
        "    try { correcciones = JSON.parse(localStorage.getItem(LS_KEY) || '{}'); } catch(e) {}\n"
        "    setIndicador('offline');\n"
        "  }\n"
        "  aplicarCorreccionesADatos();\n"
        "  poblarSelects();\n"
        "  aplicarFiltros();\n"
        "}\n"
        "\n"
        "async function guardarCorreccion(key, marca, tipo) {\n"
        "  setIndicador('guardando');\n"
        "  try {\n"
        "    const { error } = await sb.from(TABLA).upsert(\n"
        "      { codigo: key, marca, tipo, actualizado_at: new Date().toISOString() },\n"
        "      { onConflict: 'codigo' }\n"
        "    );\n"
        "    if (error) throw error;\n"
        "    localStorage.setItem(LS_KEY, JSON.stringify(correcciones));\n"
        "    setIndicador('ok');\n"
        "  } catch(err) {\n"
        "    localStorage.setItem(LS_KEY, JSON.stringify(correcciones));\n"
        "    setIndicador('offline');\n"
        "    mostrarToast('Sin internet — guardado solo en este dispositivo');\n"
        "  }\n"
        "}\n"
        "\n"
        "let indicadorEstado = 'ok';\n"
        "function setIndicador(estado) {\n"
        "  indicadorEstado = estado;\n"
        "  const dot = document.getElementById('autosave-dot');\n"
        "  const txt = document.getElementById('autosave-txt');\n"
        "  const n   = Object.keys(correcciones).length;\n"
        "  dot.className = 'autosave-dot';\n"
        "  dot.style.background = '';\n"
        "  dot.style.boxShadow  = '';\n"
        "  if (estado === 'cargando' || estado === 'guardando') {\n"
        "    dot.classList.add('saving');\n"
        "    txt.textContent = estado === 'cargando' ? 'Cargando...' : 'Guardando...';\n"
        "  } else if (estado === 'ok') {\n"
        "    dot.style.background = '#4CAF50';\n"
        "    dot.style.boxShadow  = '0 0 6px rgba(76,175,80,0.8)';\n"
        "    txt.textContent = n > 0\n"
        "      ? n + ' cambio' + (n===1?'':'s') + ' guardado' + (n===1?'':'s')\n"
        "      : 'Sincronizado';\n"
        "  } else {\n"
        "    dot.classList.add('offline');\n"
        "    txt.textContent = 'Sin conexión — guardado local';\n"
        "  }\n"
        "}\n"
        "\n"
        "function todasMarcas() {\n"
        "  return [...new Set([...MARCAS_BASE, ...TODOS.map(p=>p.marca)])].sort();\n"
        "}\n"
        "function todosTipos() {\n"
        "  return [...new Set([...TIPOS_BASE, ...TODOS.map(p=>p.tipo)])].sort();\n"
        "}\n"
        "\n"
        "const selMarca = document.getElementById('sel-marca');\n"
        "const selTipo  = document.getElementById('sel-tipo');\n"
        "\n"
        "function poblarSelects() {\n"
        "  const mAct = selMarca.value, tAct = selTipo.value;\n"
        "  selMarca.innerHTML = '<option value=\"\">Todas las marcas</option>';\n"
        "  selTipo.innerHTML  = '<option value=\"\">Todos los tipos</option>';\n"
        "  todasMarcas().forEach(m => {\n"
        "    const o = document.createElement('option');\n"
        "    o.value = m; o.textContent = m;\n"
        "    if (m === mAct) o.selected = true;\n"
        "    selMarca.appendChild(o);\n"
        "  });\n"
        "  todosTipos().forEach(t => {\n"
        "    const o = document.createElement('option');\n"
        "    o.value = t; o.textContent = t;\n"
        "    if (t === tAct) o.selected = true;\n"
        "    selTipo.appendChild(o);\n"
        "  });\n"
        "}\n"
        "\n"
        "let ordenActual = 'descripcion';\n"
        "\n"
        "function ordenarPor(ord) {\n"
        "  document.getElementById('sel-orden').value = ord;\n"
        "  ordenActual = ord;\n"
        "  aplicarFiltros();\n"
        "}\n"
        "\n"
        "function limpiarFiltros() {\n"
        "  selMarca.value = ''; selTipo.value = '';\n"
        "  document.getElementById('buscar').value = '';\n"
        "  document.getElementById('sel-orden').value = 'descripcion';\n"
        "  ordenActual = 'descripcion';\n"
        "  aplicarFiltros();\n"
        "}\n"
        "\n"
        "function aplicarFiltros() {\n"
        "  const marca = selMarca.value;\n"
        "  const tipo  = selTipo.value;\n"
        "  const busq  = document.getElementById('buscar').value.toLowerCase().trim();\n"
        "  ordenActual = document.getElementById('sel-orden').value;\n"
        "\n"
        "  let lista = TODOS.filter(p => {\n"
        "    if (marca && p.marca !== marca) return false;\n"
        "    if (tipo  && p.tipo  !== tipo)  return false;\n"
        "    if (busq && !(p.descripcion+' '+p.codigo).toLowerCase().includes(busq)) return false;\n"
        "    return true;\n"
        "  });\n"
        "\n"
        "  lista.sort((a, b) => {\n"
        "    const aE = !!correcciones[a._key], bE = !!correcciones[b._key];\n"
        "    switch(ordenActual) {\n"
        "      case 'stock-asc':   return a.stock - b.stock;\n"
        "      case 'stock-desc':  return b.stock - a.stock;\n"
        "      case 'precio-desc': return b.precio_venta - a.precio_venta;\n"
        "      case 'precio-asc':  return a.precio_venta - b.precio_venta;\n"
        "      case 'marca':       return a.marca.localeCompare(b.marca);\n"
        "      case 'editados':    return (bE-aE)||a.descripcion.localeCompare(b.descripcion);\n"
        "      default:            return a.descripcion.localeCompare(b.descripcion);\n"
        "    }\n"
        "  });\n"
        "\n"
        "  renderTabla(lista);\n"
        "  actualizarStats(lista, marca, tipo);\n"
        "}\n"
        "\n"
        "function stockClass(s) { return s===0?'stock-0':s<=2?'stock-low':'stock-ok'; }\n"
        "function badgeClass(val, campo) {\n"
        "  if (val==='Sin marca'||val==='Sin clasificar') return 'badge-sin';\n"
        "  return campo==='marca'?'badge-marca':'badge-tipo';\n"
        "}\n"
        "\n"
        "function renderTabla(lista) {\n"
        "  const body  = document.getElementById('tabla-body');\n"
        "  const empty = document.getElementById('empty-msg');\n"
        "  if (!lista.length) { body.innerHTML=''; empty.style.display='block'; return; }\n"
        "  empty.style.display = 'none';\n"
        "  body.innerHTML = lista.map(p => {\n"
        "    const precioStr = p.precio_venta > 0\n"
        "      ? p.precio_venta.toLocaleString('es-ES',{minimumFractionDigits:2,maximumFractionDigits:2})+' €'\n"
        "      : '—';\n"
        "    const corr  = correcciones[p._key] || {};\n"
        "    const mEdit = !!corr.marca, tEdit = !!corr.tipo;\n"
        "    const lapiz = '<span class=\"badge-pencil\">✏</span>';\n"
        "    const bMarca = `<span class=\"badge ${badgeClass(p.marca,'marca')}${mEdit?' badge-editado':''}\"\n"
        "      onclick=\"abrirPopover(event,${p._idx},'marca')\" title=\"Clic para cambiar la marca\">\n"
        "      ${p.marca} ${mEdit?lapiz:''}</span>`;\n"
        "    const bTipo = `<span class=\"badge ${badgeClass(p.tipo,'tipo')}${tEdit?' badge-editado':''}\"\n"
        "      onclick=\"abrirPopover(event,${p._idx},'tipo')\" title=\"Clic para cambiar el tipo\">\n"
        "      ${p.tipo} ${tEdit?lapiz:''}</span>`;\n"
        "    return `<tr>\n"
        "      <td class=\"codigo\">${p.codigo||'—'}</td>\n"
        "      <td class=\"descripcion\">${p.descripcion}</td>\n"
        "      <td>${bMarca}</td>\n"
        "      <td>${bTipo}</td>\n"
        "      <td class=\"stock\"><span class=\"${stockClass(p.stock)}\">${p.stock}</span></td>\n"
        "      <td class=\"precio\">${precioStr}</td>\n"
        "    </tr>`;\n"
        "  }).join('');\n"
        "}\n"
        "\n"
        "function actualizarStats(lista, marca, tipo) {\n"
        "  const sinStock  = lista.filter(p=>p.stock===0).length;\n"
        "  const stockBajo = lista.filter(p=>p.stock>0&&p.stock<=2).length;\n"
        "  const nEdit     = Object.keys(correcciones).length;\n"
        f"  document.getElementById('stats-bar').innerHTML = `\n"
        "    Mostrando <b>${lista.length}</b> de <b>" + str(total) + r"""</b> productos
    &nbsp;&middot;&nbsp; Sin stock: <b style="color:#C0392B">${sinStock}</b>
    &nbsp;&middot;&nbsp; Stock bajo (&le;2): <b style="color:#E67E22">${stockBajo}</b>
    ${nEdit>0?`&nbsp;&middot;&nbsp; Editados: <b style="color:var(--mg)">${nEdit}</b>`:''}
    ${marca?`&nbsp;&middot;&nbsp; Marca: <b>${marca}</b>`:''}
    ${tipo ?`&nbsp;&middot;&nbsp; Tipo: <b>${tipo}</b>` :''}
  `;
}

let popIdx = null, popCampo = null;

function abrirPopover(e, idx, campo) {
  e.stopPropagation();
  popIdx = idx; popCampo = campo;
  const p = TODOS[idx];
  const pop = document.getElementById('popover');
  document.getElementById('pop-title').textContent =
    campo==='marca' ? 'Cambiar marca' : 'Cambiar tipo';
  document.getElementById('pop-desc').textContent = p.descripcion;
  document.getElementById('pop-custom').value = '';
  const sel = document.getElementById('pop-select');
  sel.innerHTML = '';
  (campo==='marca' ? todasMarcas() : todosTipos()).forEach(v => {
    const o = document.createElement('option');
    o.value = v; o.textContent = v;
    if (v === p[campo]) o.selected = true;
    sel.appendChild(o);
  });
  const margin=12, pw=270, ph=230;
  let top=e.clientY+margin, left=e.clientX-10;
  if (left+pw > window.innerWidth-margin)  left = window.innerWidth-pw-margin;
  if (top+ph  > window.innerHeight-margin) top  = e.clientY-ph-margin;
  pop.style.top=top+'px'; pop.style.left=left+'px';
  pop.classList.add('visible');
  document.getElementById('pop-custom').focus();
}

function cerrarPopover() {
  document.getElementById('popover').classList.remove('visible');
  popIdx = null; popCampo = null;
}

async function confirmarEdicion() {
  if (popIdx === null) return;
  const custom   = document.getElementById('pop-custom').value.trim();
  const nuevoVal = custom || document.getElementById('pop-select').value;
  const p   = TODOS[popIdx];
  const key = p._key;

  if (!correcciones[key]) correcciones[key] = {};
  correcciones[key][popCampo] = nuevoVal;
  TODOS[popIdx][popCampo] = nuevoVal;

  poblarSelects();
  aplicarFiltros();
  cerrarPopover();
  mostrarToast('Guardado: "' + nuevoVal + '"');

  await guardarCorreccion(key, correcciones[key].marca ?? null, correcciones[key].tipo ?? null);
}

document.addEventListener('click', e => {
  const pop = document.getElementById('popover');
  if (pop.classList.contains('visible') && !pop.contains(e.target)) cerrarPopover();
});
document.getElementById('pop-custom').addEventListener('keydown', e => {
  if (e.key==='Enter') confirmarEdicion();
  if (e.key==='Escape') cerrarPopover();
});

let toastT;
function mostrarToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(toastT);
  toastT = setTimeout(()=>t.classList.remove('show'), 2500);
}

selMarca.addEventListener('change', aplicarFiltros);
selTipo.addEventListener('change', aplicarFiltros);
document.getElementById('sel-orden').addEventListener('change', aplicarFiltros);
let debT;
document.getElementById('buscar').addEventListener('input', ()=>{
  clearTimeout(debT); debT=setTimeout(aplicarFiltros,200);
});

cargarCorrecciones();
</script>
</body>
</html>
"""
    )

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  Pinturas Autos Torres - Inventario Interno")
    print("=" * 50)

    ruta_xls = encontrar_xls()
    if not ruta_xls:
        print()
        print("ERROR: No se encontro el archivo Inventario.XLS")
        print()
        print("Coloca el archivo XLS exportado de TPVsol en:")
        print(f"  {Path(__file__).parent / 'Inventario.XLS'}")
        print()
        input("Pulsa Enter para salir...")
        sys.exit(1)

    try:
        df = leer_inventario(ruta_xls)
    except Exception as e:
        print(f"\nERROR al leer el XLS: {e}")
        input("Pulsa Enter para salir...")
        sys.exit(1)

    print(f"  * {len(df)} productos cargados")
    sin_marca = (df["marca"] == "Sin marca").sum()
    sin_tipo  = (df["tipo"] == "Sin clasificar").sum()
    print(f"  * Marcas detectadas:  {len(df['marca'].unique())} | Sin detectar: {sin_marca}")
    print(f"  * Tipos detectados:   {len(df['tipo'].unique())} | Sin clasificar: {sin_tipo}")

    print("\nGenerando HTML...")
    html = generar_html(df, ruta_xls.name)
    SALIDA_HTML.write_text(html, encoding="utf-8")

    print(f"  * Guardado en: {SALIDA_HTML}")
    print()
    print("Listo! Abre el archivo inventario.html en el navegador.")
    print()

    import webbrowser
    webbrowser.open(SALIDA_HTML.as_uri())

    input("Pulsa Enter para cerrar...")

if __name__ == "__main__":
    main()
