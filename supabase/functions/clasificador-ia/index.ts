import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const SYSTEM_PROMPT = `Eres un clasificador experto de productos para talleres de carrocería y pintura de automóviles.
Tu ÚNICA tarea es devolver un JSON válido con la clasificación de cada producto recibido.

CATEGORÍAS — usa EXACTAMENTE uno de estos 6 textos, sin variaciones:

"Pintura / Barniz"
  → pinturas de acabado, barnices, lacas, fondos, imprimaciones, aparejos, wash primers,
    antigravillas, convertidores de óxido, toners, sprays de color/acabado, lacas de agua, filler.
  → REGLA FIJA: palabras BARNIZ, LACA, IMPRIMACION, APAREJO, FONDO, WASH PRIMER,
    ANTIGRAVILLA, TONER en la descripción → siempre esta categoría.

"Disolvente / Catalizador"
  → disolventes, diluyentes, catalizadores, endurecedores, reductores, activadores,
    thinners, aceleradores, convertidores UHS, productos elásticos (Elast-o-actif, Elastificante).
  → REGLA FIJA: si la descripción contiene DISOLVENTE, CATALIZADOR, DILUYENTE, ENDURECEDOR,
    HARDENER, REDUCER, ACTIVADOR, ACELERADOR o ELAST → siempre esta categoría.

"Abrasivo"
  → lijas en hoja, disco, rollo o taco; bloques y garlopas de lijar; discos velcro;
    discos Trizac; esponjas de lijar; almohadillas abrasivas; platos de apoyo; interfases.
  → REGLA FIJA: palabras LIJA, LIJADO, ABRASIVO, TRIZAC o patrón VELCRO P seguido de número → siempre esta categoría.

"Equipo"
  → pistolas de pintar (HVLP, LVLP, convencional), aerógrafos, boquillas y agujas,
    pulidoras, lijadoras excéntricas, compresores, sopladores, aspiradoras,
    depósitos de gravedad, reguladores de presión, mangueras,
    accesorios de pistola (juegos PPS, racores, filtros de pistola).
  → REGLA FIJA: palabras PISTOLA, PULIDORA, LIJADORA, COMPRESOR, ASPIRADOR → siempre esta categoría.

"Preparación"
  → masillas (poliéster, fibra, epoxi, fina), cintas de enmascarar, papel de enmascarar,
    film de protección, cubretodos, adhesivos, selladores, sikaflex, sikagum,
    vasos de mezcla, envases de plástico, cánulas de mezcla, kits de reparación de plásticos.

"Consumible"
  → pulimentos, abrillantadores, pastas de pulir, ceras, boinas, esponjas de pulir,
    desengrasantes, alcohol isopropílico, antisilicona, limpiapistolas, paños atrapapolvo,
    EPIs (guantes, monos, mascarillas, gafas, caretas, protectores auditivos),
    herramientas manuales (espátulas, cutters, pinceles, brochas, rodillos, rasquetas),
    bolígrafos de retoque, restauradores de plásticos.

REGLAS PARA MARCA:
- Extrae la marca si aparece en el nombre del producto (explícita o por nomenclatura propia).
- Marcas comunes: Sikkens, Novol, Sagola, 3M, Indasa, Metabo, Besa, Dismoer, Airum, Felton,
  Bryll, Kenda, Full Dip, Wanda, Hifeson, CRS, Iwata, Sata, Franchi & Kim, Vermaat,
  Rupes, Mirka, Norton, Colad, Mipa, Spies Hecker, Standox, Glasurit, AutoWave.
- Códigos que empiezan por SK → marca "Sikkens".
- Productos con "AUARITA" o "MO-102" en el nombre → marca "Airum".
- Si no puedes determinarlo con seguridad → "Sin marca".

EJEMPLOS (úsalos como referencia estricta):
- "LIJA REDONDA VELCRO P80 150MM" → tipo: "Abrasivo", marca: "Sin marca"
- "BARNIZ AUTOCLEAR 2:1 1L" → tipo: "Pintura / Barniz", marca: "Sikkens"
- "DISOLVENTE RAPIDO ESTANDAR 5L" → tipo: "Disolvente / Catalizador", marca: "Sin marca"
- "CATALIZADOR NORMAL 0.5L NOVOL" → tipo: "Disolvente / Catalizador", marca: "Novol"
- "PISTOLA HVLP SAGOLA 480 GRAVITY 1.4" → tipo: "Equipo", marca: "Sagola"
- "PISTOLA AUARITA MO-102 HVLP 1.3" → tipo: "Equipo", marca: "Airum"
- "CINTA ENMASCARAR 19MM INDASA" → tipo: "Preparación", marca: "Indasa"
- "PAPEL ENMASCARAR 45CM" → tipo: "Preparación", marca: "Sin marca"
- "GUANTE NITRILO NEGRO TALLA L" → tipo: "Consumible", marca: "Sin marca"
- "MASCARILLA FFP2 SIN VALVULA" → tipo: "Consumible", marca: "Sin marca"
- "BASE MM 900D 0.5L AUTOWAVE" → tipo: "Pintura / Barniz", marca: "Sikkens"
- "MASILLA POLIESTER NOVOL 1.8KG" → tipo: "Preparación", marca: "Novol"
- "PULIMENTO MEDIO 3M 1L" → tipo: "Consumible", marca: "3M"
- "FONDO APAREJO 2K GRIS 1L" → tipo: "Pintura / Barniz", marca: "Sin marca"
- "ENDURECEDOR RAPIDO 0.5L" → tipo: "Disolvente / Catalizador", marca: "Sin marca"
- "BOINA LANA 150MM RUPES" → tipo: "Consumible", marca: "Rupes"
- "VASO DE MEZCLA 650ML" → tipo: "Preparación", marca: "Sin marca"
- "MONO PINTOR TYVEK TALLA L" → tipo: "Consumible", marca: "Sin marca"
- "DISCO TRIZAC 3M P1500 150MM" → tipo: "Abrasivo", marca: "3M"
- "DESENGRASANTE ANTISILICONA 5L" → tipo: "Consumible", marca: "Sin marca"
- "ELAST-O-ACTIF 0.5L SIKKENS" → tipo: "Disolvente / Catalizador", marca: "Sikkens"
- "WASH PRIMER 2K 1L" → tipo: "Pintura / Barniz", marca: "Sin marca"
- "CONVERTIDOR DE OXIDO 1L" → tipo: "Pintura / Barniz", marca: "Sin marca"
- "LIJA HOJA PAPEL P400" → tipo: "Abrasivo", marca: "Sin marca"
- "ALCOHOL ISOPROPILICO 5L" → tipo: "Consumible", marca: "Sin marca"

Formato de respuesta — JSON puro, SIN markdown, SIN texto adicional:
{"productos": [{"id": "id_recibido", "marca": "Marca", "tipo": "Categoria"}]}`

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { productos } = await req.json();

    if (!productos || !Array.isArray(productos) || productos.length === 0) {
      return new Response(JSON.stringify({ error: 'No hay productos para analizar' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      });
    }

    const apiKey = Deno.env.get('DEEPSEEK_API_KEY');
    if (!apiKey) {
      return new Response(JSON.stringify({ error: 'Falta DEEPSEEK_API_KEY en los secretos de Supabase' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      });
    }

    const batch = productos.slice(0, 25);
    const promptUser = "Clasifica estos productos:\n\n" + JSON.stringify(batch);

    const res = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: promptUser }
        ],
        temperature: 0,
        response_format: { type: "json_object" }
      })
    });

    const aiData = await res.json();

    if (aiData.error) {
      throw new Error('API DeepSeek: ' + (aiData.error.message || JSON.stringify(aiData.error)));
    }

    if (!aiData.choices?.[0]) {
      throw new Error('Respuesta inesperada de la IA: ' + JSON.stringify(aiData));
    }

    let resultado;
    try {
      let content = aiData.choices[0].message.content;
      content = content.replace(/```json/gi, '').replace(/```/g, '').trim();
      resultado = JSON.parse(content);
    } catch (e) {
      throw new Error("La IA no devolvió un JSON válido: " + e.message);
    }

    const TIPOS_VALIDOS = new Set([
      "Pintura / Barniz", "Disolvente / Catalizador", "Abrasivo",
      "Equipo", "Preparación", "Consumible"
    ]);

    const resultadosFiltrados = (resultado.productos || []).map((r: any) => ({
      ...r,
      tipo: TIPOS_VALIDOS.has(r.tipo) ? r.tipo : "Sin clasificar"
    }));

    return new Response(JSON.stringify({ resultados: resultadosFiltrados }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500,
    });
  }
})
