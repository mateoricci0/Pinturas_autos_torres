import { createClient } from 'jsr:@supabase/supabase-js@2';

const SECRET_TOKEN = 'pinturas-torres-sync-2025';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'content-type, x-sync-token',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

function jsonResp(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS },
  });
}

function normCategoria(val: string): string {
  const k = val.toUpperCase().trim();
  if (k.includes('PINTURA') || k.includes('BARNIZ') || k.includes('LACA')) return 'pinturas';
  if (k.includes('HERRAMIENTA') || k.includes('MAQUINARIA') || k.includes('PISTOLA') || k.includes('PULIDORA')) return 'herramientas';
  return 'accesorios';
}

function limpiarPrecio(val: unknown): number | null {
  if (val === null || val === undefined || val === '') return null;
  if (typeof val === 'number') return isFinite(val) && val >= 0 ? Math.round(val * 100) / 100 : null;
  let s = String(val).replace(/[^0-9.,]/g, '');
  if (s.includes(',') && !s.includes('.')) s = s.replace(',', '.');
  else if (s.includes(',') && s.includes('.')) s = s.replace('.', '').replace(',', '.');
  const n = parseFloat(s);
  return isNaN(n) || n < 0 ? null : Math.round(n * 100) / 100;
}

function limpiarStock(val: unknown): number {
  if (val === null || val === undefined) return 0;
  if (typeof val === 'number') return Math.max(0, Math.trunc(val));
  const n = parseInt(String(val));
  return isNaN(n) || n < 0 ? 0 : n;
}

Deno.serve(async (req: Request) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: CORS });
  }

  if (req.method !== 'POST') {
    return jsonResp({ error: 'Metodo no permitido' }, 405);
  }

  const token = req.headers.get('x-sync-token');
  if (token !== SECRET_TOKEN) {
    return jsonResp({ error: 'No autorizado' }, 401);
  }

  let body: { productos?: unknown[] };
  try {
    body = await req.json();
  } catch {
    return jsonResp({ error: 'JSON invalido' }, 400);
  }

  if (!Array.isArray(body.productos) || body.productos.length === 0) {
    return jsonResp({ error: 'Sin productos' }, 400);
  }

  const limpios: Record<string, unknown>[] = [];
  const omitidos: string[] = [];

  for (const p of body.productos as Record<string, unknown>[]) {
    const codigo = String(p.codigo ?? '').trim().slice(0, 100);
    if (!codigo) { omitidos.push('sin codigo'); continue; }

    const nombre    = String(p.nombre ?? codigo).trim().slice(0, 200);
    const categoria = normCategoria(String(p.categoria ?? ''));
    const precio    = limpiarPrecio(p.precio);
    const stock     = limpiarStock(p.stock);
    const visible   = typeof p.visible === 'boolean' ? p.visible : false;

    limpios.push({
      codigo, nombre, categoria, precio, stock, visible,
      actualizado_at: new Date().toISOString(),
    });
  }

  if (limpios.length === 0) {
    return jsonResp({ error: 'Sin productos validos', omitidos }, 400);
  }

  const sb = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
    { auth: { persistSession: false } }
  );

  let procesados = 0;
  for (let i = 0; i < limpios.length; i += 100) {
    const lote = limpios.slice(i, i + 100);
    const { error } = await sb.from('productos').upsert(lote, { onConflict: 'codigo' });
    if (error) return jsonResp({ error: `Lote ${i}: ${error.message}` }, 500);
    procesados += lote.length;
  }

  return jsonResp({ ok: true, procesados, omitidos: omitidos.length });
});
