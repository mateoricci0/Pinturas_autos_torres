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
    antigravillas, convertidores de óxido, bases colorimétricas, toners, sprays de color/acabado.
  → REGLA FIJA: si la descripción empieza por "BASE " → siempre esta categoría.

"Disolvente / Catalizador"
  → disolventes, diluyentes, catalizadores, endurecedores, reductores, activadores,
    thinners, accelerators, convertidores UHS, productos elásticos (Elast-o-actif).
  → REGLA FIJA: si contiene DISOLVENTE, CATALIZADOR, DILUYENTE, ENDURECEDOR, HARDENER, REDUCER → siempre esta categoría.

"Abrasivo"
  → lijas en hoja, disco, rollo o taco; bloques y garlopas de lijar; discos velcro;
    discos Trizac; esponjas de lijar; almohadillas; platos de apoyo; interfases.

"Equipo"
  → pistolas de pintar, aerógrafos, boquillas, pulidoras, lijadoras excéntricas,
    compresores, sopladores, aspiradoras, depósitos de gravedad, reguladores de presión,
    mangueras, accesorios de pistola (agujas, juegos PPS, racores).

"Preparación"
  → masillas (poliéster, fibra, epoxi), cintas de enmascarar, papel de enmascarar,
    film de protección, cubretodos, adhesivos, selladores, sikaflex, vasos de mezcla,
    envases de plástico, cánulas, kits de reparación de plásticos.

"Consumible"
  → pulimentos, abrillantadores, pastas de pulir, ceras, boinas, esponjas de pulir,
    desengrasantes, antisilicona, limpiapistolass, paños atrapapolvo,
    EPIs (guantes, monos, mascarillas, gafas, caretas),
    herramientas manuales (espátulas, cutters, pinceles, brochas, rodillos),
    bolígrafos de retoque, restauradores de plásticos.

REGLAS PARA MARCA:
- Extrae la marca si aparece en el nombre del producto (explícita o implícita por nomenclatura).
- Marcas comunes: Sikkens, Novol, Sagola, 3M, Indasa, Metabo, Besa, Dismoer, Airum, Felton,
  Bryll, Kenda, Full Dip, Wanda, Hifeson, CRS, Iwata, Sata, Franchi & Kim, Vermaat, Rupes, Mirka, Norton.
- Códigos que empiezan por SK → marca "Sikkens".
- Si no puedes determinarlo con seguridad → "Sin marca".

EJEMPLOS (usa como referencia):
- "LIJA REDONDA VELCRO P80 150MM" → tipo: "Abrasivo", marca: "Sin marca"
- "BARNIZ AUTOCLEAR 2:1 1L" → tipo: "Pintura / Barniz", marca: "Sikkens"
- "DISOLVENTE RAPIDO ESTANDAR 5L" → tipo: "Disolvente / Catalizador", marca: "Sin marca"
- "CATALIZADOR NORMAL 0.5L NOVOL" → tipo: "Disolvente / Catalizador", marca: "Novol"
- "PISTOLA HVLP SAGOLA 480 GRAVITY 1.4" → tipo: "Equipo", marca: "Sagola"
- "CINTA ENMASCARAR 19MM INDASA" → tipo: "Preparación", marca: "Indasa"
- "GUANTE NITRILO NEGRO TALLA L" → tipo: "Consumible", marca: "Sin marca"
- "BASE MM 900D 0.5L AUTOWAVE" → tipo: "Pintura / Barniz", marca: "Sikkens"
- "MASILLA POLIESTER NOVOL 1.8KG" → tipo: "Preparación", marca: "Novol"
- "PULIMENTO MEDIO 3M 1L" → tipo: "Consumible", marca: "3M"
- "FONDO APAREJO 2K GRIS 1L" → tipo: "Pintura / Barniz", marca: "Sin marca"
- "ENDURECEDOR RAPIDO 0.5L" → tipo: "Disolvente / Catalizador", marca: "Sin marca"
- "BOINA LANA 150MM RUPES" → tipo: "Consumible", marca: "Rupes"
- "VASO DE MEZCLA 650ML" → tipo: "Preparación", marca: "Sin marca"
- "MONO PINTOR TYVEK TALLA L" → tipo: "Consumible", marca: "Sin marca"

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

    // Validar que los tipos devueltos son de las 6 categorías permitidas
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
