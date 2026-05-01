import { createClient } from 'jsr:@supabase/supabase-js@2';

// JWT verified automatically by Supabase (verify_jwt: true in config)
// No static token needed — only authenticated users can call this function.

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'content-type, authorization',
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
  if (k.includes('HERRAMIENTA') || k.includes('PISTOLA') || k.includes('PULIDORA') || k.includes('LIJADORA')) return 'herramientas';
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
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
  if (req.method !== 'POST') return jsonResp({ error: 'Metodo no permitido' }, 405);

  let body: { productos?: unknown[] };
  try { body = await req.json(); }
  catch { return jsonResp({ error: 'JSON invalido' }, 400); }

  if (!Array.isArray(body.productos) || body.productos.length === 0)
    return jsonResp({ error: 'Sin productos' }, 400);

  const limpios: Record<string, unknown>[] = [];
  const omitidos: string[] = [];

  for (const p of body.productos as Record<string, unknown>[]) {
    const codigo = String(p.codigo ?? '').trim().slice(0, 100);
    if (!codigo) { omitidos.push('sin codigo'); continue; }
    limpios.push({
      codigo,
      nombre:    String(p.nombre ?? codigo).trim().slice(0, 200),
      categoria: normCategoria(String(p.categoria ?? '')),
      precio:    limpiarPrecio(p.precio),
      stock:     limpiarStock(p.stock),
      visible:   typeof p.visible === 'boolean' ? p.visible : false,
      actualizado_at: new Date().toISOString(),
    });
  }

  if (limpios.length === 0) return jsonResp({ error: 'Sin productos validos', omitidos }, 400);

  const sb = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
    { auth: { persistSession: false } }
  );

  let procesados = 0;
  for (let i = 0; i < limpios.length; i += 100) {
    const { error } = await sb.from('productos').upsert(limpios.slice(i, i + 100), { onConflict: 'codigo' });
    if (error) return jsonResp({ error: `Lote ${i}: ${error.message}` }, 500);
    procesados += lote.length;
  }

  return jsonResp({ ok: true, procesados, omitidos: omitidos.length });
});
