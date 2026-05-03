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
    antigravillas, convertidores de óxido, toners, texturados, tintes, zinc/galvanizado,
    clearcoat, filler, sprays de color o acabado (vinilos de color, llantas, anticaloricos de color).
  → REGLA FIJA: BARNIZ, LACA, IMPRIMACION, APAREJO, FONDO, WASH PRIMER, ANTIGRAVILLA,
    TONER, TEXTURADO, TINTE, CLEARCOAT, ZINC, GALVANIZADO, URKI-SPRAY, ACRITOP,
    SPETTRO, CONVERTIDOR DE OXIDO → siempre esta categoría.
  → REGLA FIJA: SPRAY seguido de cualquier color o acabado (NEGRO, BLANCO, GRIS, ROJO,
    AZUL, VERDE, AMARILLO, NARANJA, MARRON, VIOLETA, ROSA, PLATEADO, PLATA, ORO,
    DORADO, BRONCE, ALUMINIO, CROMO, PERLA, METALIZADO, FLUORESCENTE, CAMALEON,
    ANTICALORICO, LLANTAS, VINILO, ACRILICO, PREPARADOS, PRECARGA 2K) → esta categoría.
  → EXCEPCIÓN: SPRAY COLA, SPRAY DISOLVENTE, SPRAY QUITA PEGATINAS, SPRAY DECAPANTE,
    SPRAY CERA CAVIDADES, SPRAY REPARADOR FAROS → NO son esta categoría.

"Disolvente / Catalizador"
  → disolventes, diluyentes, catalizadores, endurecedores, reductores, activadores,
    thinners, aceleradores, productos elásticos (Elast-o-actif, Elastificante).
  → REGLA FIJA: DISOLVENTE, CATALIZADOR, DILUYENTE, ENDURECEDOR, HARDENER,
    REDUCER, ACTIVADOR, ACELERADOR, ELAST, THINNER → siempre esta categoría.

"Abrasivo"
  → lijas (hoja, disco, rollo), bloques y garlopas de lijar, discos velcro/fibra, Trizac/Trizact,
    esponjas de lijar, scotch brite, goma abrasiva, platos de apoyo/lijado,
    soportes velcro con vástago, interfases.
  → REGLA FIJA: LIJA, LIJADO, TRIZAC, TRIZACT, GARLOPA, SCOTCH BRITE, SCOT BRITE,
    GOMA ABRASIVA, DISCO FIBRA → siempre esta categoría.
  → REGLA FIJA: TACO LIJAR, TACO LIJA, TACO CORCHO, TACO MINI → esta categoría.
  → REGLA FIJA: PLATO DE APOYO, PLATO LIJADO, SOPORTE VELCRO, SOPORTE DISCO,
    VASTAGO PARA SOPORTE, VELCRO ADHESIVO → esta categoría.
  → REGLA FIJA: patrón VELCRO P seguido de número (ej. VELCRO P80) → esta categoría.
  → NOTA: "PASTA ABRASIVA PULIR" → Consumible, no Abrasivo.

"Equipo"
  → pistolas de pintar (HVLP, LVLP, VICTORIA model AEROMETAL), aerógrafos, boquillas/agujas,
    pulidoras, lijadoras excéntricas, compresores, sopladores/sopladoras, aspiradoras,
    reguladores de presión, filtros reguladores/separadores de agua, mangueras, racores,
    enchufes latón, válvulas, escobillas de carbón, soportes de pistola/tijera.
  → REGLA FIJA: PISTOLA, PULIDORA, LIJADORA, COMPRESOR, ASPIRADOR,
    SOPLADOR, SOPLADORA → siempre esta categoría.
  → REGLA FIJA: ENCHUFE LATON, VALVULA, RACOR, FILTRO REGULADOR,
    FILTRO SEPARADOR, ESCOBILLAS CARBON, SOPORTE TIJERA → esta categoría.
  → REGLA FIJA: VICTORIA seguido de modelo + AEROMETAL → esta categoría (pistolas de pintar).

"Preparación"
  → masillas (poliéster/fibra/epoxi/fina), cintas/papel de enmascarar, bobinas de enmascarado,
    papel con cinta, film de protección, cubretodos, selladores (a brocha, de lunas, junta
    parabrisas), sikaflex, sikagum, pegues de juntas, adhesivos de contacto, vasos de mezcla,
    tapas de vaso, cánulas de mezcla, filtros de pintura (micras), kits de reparación de
    plásticos, resinas, fibras.
  → REGLA FIJA: MASILLA POLIESTER, MASILLA FIBRA, MASILLA EPOXI, MASILLA FINA,
    CINTA ENMASCARAR, PAPEL ENMASCARAR, PAPEL CON CINTA, BOBINA, FILM, CUBRETODO,
    SIKAFLEX, SIKAGUM, PEGUE DE JUNTAS, VASO MEZCLA, VASO PINTURA,
    TAPA VASO, CANULA, FILTRO PINTURA → esta categoría.
  → REGLA FIJA: SELLADOR A BROCHA, SELLADOR DE LUNAS, SELLADOR JUNTA → esta categoría.
  → REGLA FIJA: SPRAY COLA DE CONTACTO → esta categoría.
  → NOTA: "MASILLA QUITA PULVERIZADOS" → Consumible, no Preparación.

"Consumible"
  → pulimentos, pastas de pulir, ceras, boinas/caperu­zas de lana, esponjas y discos de pulir
    (foam/espuma), desengrasantes, alcohol isopropílico, antisilicona, limpiapistolas, paños
    atrapapolvo, telas fálticas/gamuzas, EPIs (guantes, monos, mascarillas, gafas, caretas,
    protectores auditivos), herramientas manuales (espátulas, cutters/cuchillas, pinceles,
    brochas, rodillos, rasquetas, sacabollos manuales), hilo sacalunas, discos quitacintas,
    bolígrafos de retoque, restauradores de plásticos, spray quita pegatinas, spray decapante,
    spray cera, spray reparador faros, masilla quita pulverizados, ventosas de vacío,
    limpiametales, algodón mágico.
  → REGLA FIJA: PULIMENTO, PASTA ABRASIVA PULIR, CERA, BOINA, CAPERUZA LANA,
    DISCO ESPUMA, DISCO FOAM, DESENGRASANTE, ANTISILICONA, LIMPIAPISTOLAS,
    PAÑO, TELA FALTICA, HILO SACALUNAS, VENTOSA DE VACIO → siempre esta categoría.
  → REGLA FIJA: SPRAY QUITA PEGATINAS, SPRAY DECAPANTE, SPRAY CERA,
    SPRAY REPARADOR FAROS → esta categoría.

REGLAS PARA MARCA:
- Extrae la marca si aparece explícitamente en el nombre del producto.
- AEROMETAL → marca "Vermaat" (las pistolas VICTORIA son de Aerometal/Vermaat).
- Códigos que empiezan por SK o SIKAW → marca "Sikkens".
- "AUARITA" o "MO-102" en el nombre → marca "Airum".
- Marcas reconocibles: Sikkens, Novol, Sagola, 3M, Indasa, Metabo, Besa, Hifeson, Airum,
  Felton, Kenda, Full Dip, Wanda, CRS, Iwata, Sata, Vermaat, Rupes, Mirka, Norton,
  Colad, Mipa, Spies Hecker, Standox, Glasurit, AutoWave, Bossauto, Prosol, Seikar,
  Upol, Stark, Vallejo, Dismoer, Bryll, Nuair, Italco, Wufu, Beta.
- Si no puedes determinarlo con seguridad → "Sin marca".

EJEMPLOS (úsalos como referencia estricta):
- "LIJA REDONDA VELCRO P80 150MM" → tipo: "Abrasivo", marca: "Sin marca"
- "LIJA HOJA PAPEL P400" → tipo: "Abrasivo", marca: "Sin marca"
- "DISCO TRIZAC 3M P1500 150MM" → tipo: "Abrasivo", marca: "3M"
- "TRIZAC URAXTOP P3000 BOSSAUTO" → tipo: "Abrasivo", marca: "Bossauto"
- "TACO LIJAR NEGRO GOMA 126X68MM" → tipo: "Abrasivo", marca: "Sin marca"
- "TACO CORCHO 120X60X35" → tipo: "Abrasivo", marca: "Sin marca"
- "PLATO DE APOYO LIJADO 150MM" → tipo: "Abrasivo", marca: "Sin marca"
- "SOPORTE VELCRO CON VASTAGO 150MM" → tipo: "Abrasivo", marca: "Sin marca"
- "GARLOPA HIFESON 70X400" → tipo: "Abrasivo", marca: "Hifeson"
- "SCOT BRITE PLIEGO INDASA R/V/G" → tipo: "Abrasivo", marca: "Indasa"
- "BARNIZ AUTOCLEAR 2:1 1L" → tipo: "Pintura / Barniz", marca: "Sikkens"
- "BASE MM 900D 0.5L AUTOWAVE" → tipo: "Pintura / Barniz", marca: "AutoWave"
- "FONDO APAREJO 2K GRIS 1L" → tipo: "Pintura / Barniz", marca: "Sin marca"
- "WASH PRIMER 2K 1L" → tipo: "Pintura / Barniz", marca: "Sin marca"
- "TEXTURADO NEGRO RAL 9005 1L BESA" → tipo: "Pintura / Barniz", marca: "Besa"
- "TINTE NEGRO CRS 1L" → tipo: "Pintura / Barniz", marca: "CRS"
- "URKI-SPRAY RECARGABLE BASE AGUA 400ML BESA" → tipo: "Pintura / Barniz", marca: "Besa"
- "SPRAY NEGRO MATE KENDA 400ML RAL 9005" → tipo: "Pintura / Barniz", marca: "Kenda"
- "SPRAY BARNIZ BRILLO KENDA 400ML" → tipo: "Pintura / Barniz", marca: "Kenda"
- "SPRAY FONDO GRIS CRS 400ML" → tipo: "Pintura / Barniz", marca: "CRS"
- "SPRAY TEXTURADO NEGRO NOVOL 500ML" → tipo: "Pintura / Barniz", marca: "Novol"
- "SPRAY VINILO NEGRO FULL DIP 400ML" → tipo: "Pintura / Barniz", marca: "Full Dip"
- "SPRAY ZINC 400ML VERMAAT" → tipo: "Pintura / Barniz", marca: "Vermaat"
- "SPRAY WASHPRIMER 1K CF 400ML" → tipo: "Pintura / Barniz", marca: "Sin marca"
- "SPRAY CONVERTIDOR DE OXIDO 400ML PROSOL" → tipo: "Pintura / Barniz", marca: "Prosol"
- "SPRAY ANTIGRAVILLA NEGRO 500ML NOVOL" → tipo: "Pintura / Barniz", marca: "Novol"
- "SPRAY LLANTAS COLOR NEGRO 400ML" → tipo: "Pintura / Barniz", marca: "Sin marca"
- "SPRAY PRECARGA 2K 400ML FELTON" → tipo: "Pintura / Barniz", marca: "Felton"
- "SPRAY ANTICALORICO NEGRO METALIZADO 400ML FULL DIP" → tipo: "Pintura / Barniz", marca: "Full Dip"
- "DISOLVENTE RAPIDO ESTANDAR 5L" → tipo: "Disolvente / Catalizador", marca: "Sin marca"
- "THINNER AUTOCRYL PLUS LV HT 1L SIKKENS" → tipo: "Disolvente / Catalizador", marca: "Sikkens"
- "CATALIZADOR NORMAL 0.5L NOVOL" → tipo: "Disolvente / Catalizador", marca: "Novol"
- "ENDURECEDOR RAPIDO 0.5L" → tipo: "Disolvente / Catalizador", marca: "Sin marca"
- "ELAST-O-ACTIF 0.5L SIKKENS" → tipo: "Disolvente / Catalizador", marca: "Sikkens"
- "PISTOLA HVLP SAGOLA 480 GRAVITY 1.4" → tipo: "Equipo", marca: "Sagola"
- "PISTOLA AUARITA MO-102 HVLP 1.3" → tipo: "Equipo", marca: "Airum"
- "VICTORIA RS220 GP ECO&T PASO 1.4 AEROMETAL" → tipo: "Equipo", marca: "Vermaat"
- "SR 2185 LIJADORA ORBITAL METABO" → tipo: "Equipo", marca: "Metabo"
- "SOPLADOR DE BOLSILLO SAGOLA" → tipo: "Equipo", marca: "Sagola"
- "SOPLADORA SECADORA" → tipo: "Equipo", marca: "Sin marca"
- "ENCHUFE LATON 1/4 MACHO" → tipo: "Equipo", marca: "Sin marca"
- "FILTRO REGULADOR SEPARADOR 1/4" → tipo: "Equipo", marca: "Sin marca"
- "CINTA ENMASCARAR 19MM INDASA" → tipo: "Preparación", marca: "Indasa"
- "PAPEL ENMASCARAR 45CM" → tipo: "Preparación", marca: "Sin marca"
- "PAPEL CON CINTA 1.80M" → tipo: "Preparación", marca: "Sin marca"
- "VASO MEZCLA 0.400ML" → tipo: "Preparación", marca: "Sin marca"
- "SIKAFLEX SELLADOR DE LUNAS 256 300ML" → tipo: "Preparación", marca: "Sin marca"
- "FILTRO PINTURA 125 MICRAS" → tipo: "Preparación", marca: "Sin marca"
- "MASILLA POLIESTER NOVOL 1.8KG" → tipo: "Preparación", marca: "Novol"
- "SELLADOR A BROCHA CRS 1L" → tipo: "Preparación", marca: "CRS"
- "SELLADOR JUNTA PARABRISAS RESISTENTE AGUA 310ML" → tipo: "Preparación", marca: "Sin marca"
- "SPRAY COLA DE CONTACTO 400ML PROSOL" → tipo: "Preparación", marca: "Prosol"
- "GUANTE NITRILO NEGRO TALLA L" → tipo: "Consumible", marca: "Sin marca"
- "MASCARILLA FFP2 SIN VALVULA" → tipo: "Consumible", marca: "Sin marca"
- "MONO PINTOR TYVEK TALLA L" → tipo: "Consumible", marca: "Sin marca"
- "BOINA LANA 150MM RUPES" → tipo: "Consumible", marca: "Rupes"
- "CAPERUZA DE LANA 150MM" → tipo: "Consumible", marca: "Sin marca"
- "DISCO ESPUMA PULIR 150MM" → tipo: "Consumible", marca: "Sin marca"
- "PULIMENTO MEDIO 3M 1L" → tipo: "Consumible", marca: "3M"
- "VELVET PASTA ABRASIVA PULIR 200GR" → tipo: "Consumible", marca: "Sin marca"
- "DESENGRASANTE ANTISILICONA 5L" → tipo: "Consumible", marca: "Sin marca"
- "ALCOHOL ISOPROPILICO 5L" → tipo: "Consumible", marca: "Sin marca"
- "HILO SACALUNAS 20M" → tipo: "Consumible", marca: "Sin marca"
- "TELA FALTICA 50X50" → tipo: "Consumible", marca: "Sin marca"
- "SACABOLLOS MANUAL GRANDE" → tipo: "Consumible", marca: "Sin marca"
- "STARK ALGODON MAGICO 75GRS" → tipo: "Consumible", marca: "Stark"
- "MASILLA QUITA PULVERIZADOS" → tipo: "Consumible", marca: "Sin marca"
- "SPRAY QUITA PEGATINAS CAMP 200ML" → tipo: "Consumible", marca: "Sin marca"
- "VENTOSA DE VACIO INDIVIDUAL TOPTULL" → tipo: "Consumible", marca: "Sin marca"

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
