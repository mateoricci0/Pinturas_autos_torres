import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight request
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

    // Preparar el prompt
    const systemPrompt = `Eres un experto en pintura de carrocería, automoción y herramientas.
Tu trabajo es clasificar productos. Recibirás un JSON con una lista.
Debes devolver UNICAMENTE un JSON válido que sea un objeto con la propiedad "productos", la cual contiene un array de objetos. 

Reglas para MARCA:
- Extrae la marca si está implícita (ej: SIKKENS, SAGOLA, 3M, METABO, DISMOER, BESA, NOVOL, INDASA, AIWARITA, MIRKA, IWATA, NORTON, MAXMEYER, etc).
- Si no está claro, pon "Sin marca".

Reglas para TIPO (Usa SOLO estos 4):
- "Pinturas" (imprimaciones, aparejos, masillas, esmaltes, catalizadores, diluyentes, disolventes, bases)
- "Barnices" (lacas y barnices transparentes)
- "Herramientas" (pistolas, máquinas, pulidoras, básculas)
- "Accesorios" (lijas, cintas, vasos de mezcla, pulimentos, boinas, monos, epis, sprays vacíos, anexos)

Formato estricto de respuesta:
{
  "productos": [
    {"id": "el_mismo_id_recibido", "marca": "Marca", "tipo": "Tipo"}
  ]
}`;

    // Limitar cantidad por request para no saturar la API
    const batch = productos.slice(0, 50);

    const promptUser = "Aquí tienes la lista de productos:\n\n" + JSON.stringify(batch);

    const res = await fetch('https://api.deepseek.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: promptUser }
        ],
        temperature: 0.1,
        response_format: { type: "json_object" }
      })
    });

    const aiData = await res.json();
    
    if (aiData.error) {
      throw new Error(aiData.error.message || 'Error de la API de DeepSeek');
    }

    let resultado;
    try {
      const content = aiData.choices[0].message.content;
      resultado = JSON.parse(content);
    } catch (e) {
      throw new Error("La IA no devolvió un JSON válido.");
    }

    return new Response(JSON.stringify({ resultados: resultado.productos }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500,
    });
  }
})
