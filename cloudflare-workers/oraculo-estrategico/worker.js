/**
 * ORÁCULO ESTRATÉGICO - Cloudflare Worker
 * Sistema de Investigación Empresarial Profunda (14 Fases)
 *
 * Integra:
 * - Claude Sonnet para análisis profundo
 * - Perplexity sonar-pro para búsquedas web en tiempo real
 * - Firecrawl para scraping de sitios web
 *
 * Última actualización: 2026-02-04
 */

export default {
  async fetch(request, env) {
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok', version: '1.0.0' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Main investigation endpoint
    if (url.pathname === '/api/investigar' && request.method === 'POST') {
      try {
        const body = await request.json();
        const resultado = await investigarCompleto(body, env);
        return new Response(JSON.stringify(resultado), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Specific analysis endpoints
    if (url.pathname.startsWith('/api/analisis/') && request.method === 'POST') {
      const tipo = url.pathname.split('/').pop();
      try {
        const body = await request.json();
        const resultado = await ejecutarAnalisisEspecifico(tipo, body, env);
        return new Response(JSON.stringify(resultado), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // UI for testing
    if (url.pathname === '/' || url.pathname === '/ui') {
      return new Response(getUIHTML(), {
        headers: { ...corsHeaders, 'Content-Type': 'text/html; charset=utf-8' }
      });
    }

    return new Response('Not Found', { status: 404, headers: corsHeaders });
  }
};

// ============================================================================
// FUNCIÓN PRINCIPAL: INVESTIGACIÓN COMPLETA (14 FASES)
// ============================================================================

async function investigarCompleto(params, env) {
  const { empresa, sitio_web, sector, contexto, investigacion_completa } = params;

  if (!empresa) {
    return { success: false, error: 'Nombre de empresa requerido' };
  }

  console.log(`🔮 Iniciando investigación: ${empresa}`);

  const resultados = {
    empresa,
    sitio_web,
    sector,
    timestamp: new Date().toISOString(),
    scraping: null,
    claude: null,
    perplexity: {},
    consolidado: null
  };

  // FASE 1: Web Scraping
  if (sitio_web) {
    resultados.scraping = await ejecutarScraping(sitio_web, env);
  }

  // FASE 2-12: Investigaciones Perplexity (Multi-Query)
  const tiposInvestigacion = [
    'empresa', 'industria', 'economia', 'competidores', 'oportunidades',
    'pestel', 'porter', 'tendencias', 'esg', 'ecosistema', 'digital'
  ];

  for (const tipo of tiposInvestigacion) {
    const query = construirQueryPerplexity(tipo, empresa, sector, contexto);
    resultados.perplexity[tipo] = await buscarPerplexity(query, env);
  }

  // FASE 13: Análisis Claude
  resultados.claude = await analizarConClaude(
    empresa,
    sector,
    resultados.scraping,
    resultados.perplexity,
    contexto,
    env
  );

  // FASE 14: Consolidación
  resultados.consolidado = consolidarResultados(resultados);

  return {
    success: true,
    ...resultados
  };
}

// ============================================================================
// MÓDULO 1: WEB SCRAPING
// ============================================================================

async function ejecutarScraping(url, env) {
  if (!env.FIRECRAWL_API_KEY) {
    return { success: false, error: 'Firecrawl no configurado' };
  }

  try {
    const response = await fetch('https://api.firecrawl.dev/v1/scrape', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.FIRECRAWL_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url,
        formats: ['markdown'],
        onlyMainContent: true
      })
    });

    if (!response.ok) {
      throw new Error(`Firecrawl error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      url,
      contenido: data.data?.markdown || '',
      titulo: data.data?.metadata?.title || ''
    };
  } catch (error) {
    console.error('Error en scraping:', error);
    return { success: false, error: error.message };
  }
}

// ============================================================================
// MÓDULO 2: BÚSQUEDA PERPLEXITY (MULTI-QUERY)
// ============================================================================

function construirQueryPerplexity(tipo, empresa, sector, contexto) {
  const queries = {
    empresa: `Investiga EXHAUSTIVAMENTE la empresa "${empresa}" en México:
      - Historia y fundación
      - Estructura corporativa y directivos
      - Productos/servicios principales
      - Presencia de mercado y alcance geográfico
      - Certificaciones y reconocimientos
      - Noticias recientes
      Incluye SOLO información verificable con fuentes.`,

    industria: `Analiza la industria/sector "${sector || 'servicios profesionales'}" en México 2024-2026:
      - Tamaño de mercado y crecimiento
      - Principales jugadores
      - Tendencias actuales
      - Regulación relevante
      - Perspectivas de crecimiento`,

    economia: `Analiza el panorama económico para el sector ${sector || 'empresarial'} en México:
      - Indicadores macroeconómicos relevantes
      - Políticas gubernamentales que afectan el sector
      - Condiciones de financiamiento
      - Tendencias de inversión`,

    competidores: `Identifica y analiza los competidores de "${empresa}" en México:
      - Principales competidores directos
      - Diferenciadores de cada uno
      - Participación de mercado estimada
      - Fortalezas y debilidades comparativas`,

    oportunidades: `Basándote en "${empresa}" y el sector ${sector || 'empresarial'}:
      - Oportunidades de mercado identificadas
      - Nichos desatendidos
      - Tendencias aprovechables
      - Riesgos y amenazas del entorno`,

    pestel: `Realiza un análisis PESTEL completo para el sector ${sector || 'empresarial'} en México:
      POLÍTICO: Regulación, políticas públicas, estabilidad
      ECONÓMICO: Inflación, tipo de cambio, crecimiento PIB
      SOCIAL: Demografía, tendencias de consumo, cultura
      TECNOLÓGICO: Innovación, digitalización, adopción tech
      ECOLÓGICO: Regulación ambiental, sustentabilidad
      LEGAL: Marco normativo, compliance, litigios`,

    porter: `Analiza las 5 FUERZAS DE PORTER para ${sector || 'el sector'} en México:
      1. RIVALIDAD entre competidores actuales
      2. AMENAZA de nuevos entrantes
      3. PODER de negociación de proveedores
      4. PODER de negociación de clientes
      5. AMENAZA de productos sustitutos
      Incluye intensidad (Alta/Media/Baja) para cada fuerza.`,

    tendencias: `Identifica las MEGA-TENDENCIAS GLOBALES que impactarán a ${empresa} y su sector:
      - Transformación digital
      - Cambio climático y sustentabilidad
      - Demografía y cambio social
      - Geopolítica y comercio internacional
      - Innovación tecnológica
      Enfócate en impacto específico para México.`,

    esg: `Realiza un análisis ESG para evaluar a "${empresa}":
      ENVIRONMENTAL: Huella de carbono, gestión de residuos, energías renovables
      SOCIAL: Prácticas laborales, diversidad, impacto comunitario
      GOVERNANCE: Estructura directiva, transparencia, ética empresarial
      Identifica fortalezas, debilidades y áreas de mejora.`,

    ecosistema: `Mapea el ECOSISTEMA COMPLETO de la industria ${sector || 'empresarial'}:
      - Cadena de valor (proveedores, productores, distribuidores)
      - Stakeholders clave
      - Reguladores y entidades gubernamentales
      - Asociaciones y cámaras del sector
      - Infraestructura crítica`,

    digital: `Analiza la TRANSFORMACIÓN DIGITAL del sector ${sector || 'empresarial'}:
      - Nivel de adopción tecnológica
      - Herramientas y plataformas dominantes
      - Brechas digitales
      - Oportunidades de innovación
      - Casos de éxito en digitalización`
  };

  return queries[tipo] || queries.empresa;
}

async function buscarPerplexity(query, env) {
  if (!env.PERPLEXITY_API_KEY) {
    return { success: false, error: 'Perplexity no configurado' };
  }

  try {
    const response = await fetch('https://api.perplexity.ai/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.PERPLEXITY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'sonar-pro',
        messages: [
          {
            role: 'system',
            content: `Eres un analista de negocios experto en el mercado mexicano.
            Proporciona información VERIFICABLE con fuentes.
            Sé específico y usa datos actuales.
            Responde en español profesional.`
          },
          { role: 'user', content: query }
        ],
        max_tokens: 2000,
        temperature: 0.2
      })
    });

    if (!response.ok) {
      throw new Error(`Perplexity error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      contenido: data.choices?.[0]?.message?.content || '',
      citations: data.citations || []
    };
  } catch (error) {
    console.error('Error en Perplexity:', error);
    return { success: false, error: error.message };
  }
}

// ============================================================================
// MÓDULO 3: ANÁLISIS CLAUDE (14 FASES)
// ============================================================================

async function analizarConClaude(empresa, sector, scraping, perplexity, contexto, env) {
  if (!env.ANTHROPIC_API_KEY) {
    return { success: false, error: 'Claude no configurado' };
  }

  // Construir contexto completo para Claude
  let contextoCompleto = `## INVESTIGACIÓN DE: ${empresa}\n\n`;

  if (scraping?.success) {
    contextoCompleto += `### DATOS DEL SITIO WEB\n${scraping.contenido?.substring(0, 3000) || 'No disponible'}\n\n`;
  }

  // Agregar resultados de Perplexity
  for (const [tipo, resultado] of Object.entries(perplexity)) {
    if (resultado?.success) {
      contextoCompleto += `### ${tipo.toUpperCase()}\n${resultado.contenido?.substring(0, 2000) || ''}\n\n`;
    }
  }

  if (contexto) {
    contextoCompleto += `### CONTEXTO ADICIONAL\n${contexto}\n\n`;
  }

  const prompt = `Eres un analista estratégico senior especializado en el mercado mexicano.

INFORMACIÓN RECOPILADA:
${contextoCompleto}

GENERA UN ANÁLISIS ESTRATÉGICO COMPLETO que incluya:

## 1. RESUMEN EJECUTIVO
(2-3 párrafos con hallazgos clave)

## 2. PERFIL DE LA EMPRESA
- Datos verificados
- Capacidad operativa
- Presencia de mercado

## 3. ANÁLISIS DEL SECTOR
- Contexto competitivo
- Tendencias clave
- Regulación relevante

## 4. ANÁLISIS PESTEL
(Factor por factor con impacto)

## 5. FUERZAS DE PORTER
(5 fuerzas con intensidad)

## 6. ANÁLISIS ESG
(Ambiental, Social, Gobernanza)

## 7. EVALUACIÓN DE RIESGOS
- Riesgos identificados
- Nivel de cada riesgo (Alto/Medio/Bajo)
- Mitigaciones sugeridas

## 8. OPORTUNIDADES ESTRATÉGICAS
(Oportunidades concretas y accionables)

## 9. CONCLUSIONES Y RECOMENDACIONES
(Para due diligence y toma de decisiones)

## 10. DOCUMENTACIÓN DE MATERIALIDAD
(Para cumplimiento SAT Art. 69-B CFF si aplica)
- Razón de negocios
- Capacidad operativa del proveedor
- Consistencia con servicios declarados

Sé específico, usa datos verificados y proporciona análisis accionable.`;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 8000,
        messages: [{ role: 'user', content: prompt }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      analisis: data.content?.[0]?.text || ''
    };
  } catch (error) {
    console.error('Error en Claude:', error);
    return { success: false, error: error.message };
  }
}

// ============================================================================
// MÓDULO 4: CONSOLIDACIÓN DE RESULTADOS
// ============================================================================

function consolidarResultados(resultados) {
  const { empresa, scraping, claude, perplexity } = resultados;

  // Extraer secciones del análisis de Claude
  const analisisClaude = claude?.analisis || '';

  // Intentar extraer secciones específicas
  const secciones = {
    resumen_ejecutivo: extraerSeccion(analisisClaude, 'RESUMEN EJECUTIVO'),
    perfil_empresa: extraerSeccion(analisisClaude, 'PERFIL DE LA EMPRESA'),
    analisis_sector: extraerSeccion(analisisClaude, 'ANÁLISIS DEL SECTOR'),
    pestel: extraerSeccion(analisisClaude, 'ANÁLISIS PESTEL'),
    porter: extraerSeccion(analisisClaude, 'FUERZAS DE PORTER'),
    esg: extraerSeccion(analisisClaude, 'ANÁLISIS ESG'),
    riesgos: extraerSeccion(analisisClaude, 'EVALUACIÓN DE RIESGOS'),
    oportunidades: extraerSeccion(analisisClaude, 'OPORTUNIDADES ESTRATÉGICAS'),
    conclusiones: extraerSeccion(analisisClaude, 'CONCLUSIONES Y RECOMENDACIONES'),
    materialidad: extraerSeccion(analisisClaude, 'DOCUMENTACIÓN DE MATERIALIDAD')
  };

  // Calcular score de confianza
  let scoreConfianza = 0;
  if (scraping?.success) scoreConfianza += 20;
  if (claude?.success) scoreConfianza += 40;
  const perplexityExitosos = Object.values(perplexity).filter(p => p?.success).length;
  scoreConfianza += Math.min(40, perplexityExitosos * 4);

  return {
    empresa,
    ...secciones,
    analisis_completo: analisisClaude,
    score_confianza: scoreConfianza,
    fuentes: {
      web: scraping?.success ? 1 : 0,
      perplexity: perplexityExitosos,
      claude: claude?.success ? 1 : 0
    },
    timestamp: new Date().toISOString()
  };
}

function extraerSeccion(texto, nombreSeccion) {
  const regex = new RegExp(`##\\s*\\d*\\.?\\s*${nombreSeccion}[\\s\\S]*?(?=##|$)`, 'i');
  const match = texto.match(regex);
  return match ? match[0].replace(/^##\s*\d*\.?\s*[^\n]+\n/, '').trim() : '';
}

// ============================================================================
// ANÁLISIS ESPECÍFICOS
// ============================================================================

async function ejecutarAnalisisEspecifico(tipo, params, env) {
  const { empresa, sector, pais, sitio_web } = params;

  const query = construirQueryPerplexity(tipo, empresa, sector || '', '');
  const perplexityResult = await buscarPerplexity(query, env);

  // Análisis adicional con Claude si está disponible
  let claudeResult = null;
  if (env.ANTHROPIC_API_KEY && perplexityResult.success) {
    claudeResult = await analizarConClaude(
      empresa,
      sector,
      null,
      { [tipo]: perplexityResult },
      `Análisis específico de tipo: ${tipo}`,
      env
    );
  }

  return {
    success: true,
    tipo,
    empresa,
    sector,
    perplexity: perplexityResult,
    claude: claudeResult
  };
}

// ============================================================================
// UI HTML
// ============================================================================

function getUIHTML() {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🔮 Oráculo Estratégico</title>
  <style>
    :root {
      --primary: #6366f1;
      --primary-dark: #4f46e5;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #ef4444;
      --bg: #0f172a;
      --card: #1e293b;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    h1 {
      font-size: 2.5rem;
      background: linear-gradient(135deg, #6366f1, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }
    .subtitle { color: var(--text-muted); margin-bottom: 2rem; }
    .card {
      background: var(--card);
      border-radius: 1rem;
      padding: 1.5rem;
      margin-bottom: 1rem;
    }
    .form-group { margin-bottom: 1rem; }
    label {
      display: block;
      margin-bottom: 0.5rem;
      color: var(--text-muted);
      font-size: 0.875rem;
    }
    input, textarea {
      width: 100%;
      padding: 0.75rem;
      border: 1px solid #334155;
      border-radius: 0.5rem;
      background: #0f172a;
      color: var(--text);
      font-size: 1rem;
    }
    input:focus, textarea:focus {
      outline: none;
      border-color: var(--primary);
    }
    textarea { min-height: 80px; resize: vertical; }
    .btn {
      background: var(--primary);
      color: white;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 0.5rem;
      font-size: 1rem;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn:hover { background: var(--primary-dark); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .results { display: none; }
    .results.visible { display: block; }
    .section-title {
      font-size: 1.25rem;
      margin: 1.5rem 0 1rem;
      color: var(--primary);
    }
    .content { white-space: pre-wrap; line-height: 1.6; }
    .loading {
      display: none;
      text-align: center;
      padding: 2rem;
    }
    .loading.visible { display: block; }
    .spinner {
      border: 3px solid #334155;
      border-top: 3px solid var(--primary);
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 0 auto 1rem;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
    .stat {
      text-align: center;
      padding: 1rem;
      background: #0f172a;
      border-radius: 0.5rem;
    }
    .stat-value { font-size: 2rem; font-weight: bold; color: var(--primary); }
    .stat-label { color: var(--text-muted); font-size: 0.875rem; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🔮 Oráculo Estratégico</h1>
    <p class="subtitle">Investigación Empresarial Profunda - 14 Fases de Análisis</p>

    <div class="card">
      <form id="searchForm">
        <div class="grid">
          <div class="form-group">
            <label>Nombre de la Empresa *</label>
            <input type="text" id="empresa" placeholder="Ej: Acme Consulting S.A. de C.V." required>
          </div>
          <div class="form-group">
            <label>Sitio Web</label>
            <input type="url" id="sitioWeb" placeholder="https://ejemplo.com">
          </div>
        </div>
        <div class="grid">
          <div class="form-group">
            <label>Sector / Industria</label>
            <input type="text" id="sector" placeholder="Ej: Consultoría empresarial">
          </div>
        </div>
        <div class="form-group">
          <label>Contexto Adicional</label>
          <textarea id="contexto" placeholder="Información adicional para enfocar la investigación..."></textarea>
        </div>
        <button type="submit" class="btn" id="submitBtn">🔍 Investigar</button>
      </form>
    </div>

    <div class="loading" id="loading">
      <div class="spinner"></div>
      <p>Ejecutando investigación en 14 fases...</p>
      <p style="color: var(--text-muted); font-size: 0.875rem;">Esto puede tomar 2-5 minutos</p>
    </div>

    <div class="results" id="results">
      <div class="card">
        <h2 class="section-title">📊 Métricas de Investigación</h2>
        <div class="grid">
          <div class="stat">
            <div class="stat-value" id="scoreConfianza">-</div>
            <div class="stat-label">Score de Confianza</div>
          </div>
          <div class="stat">
            <div class="stat-value" id="fuentesWeb">-</div>
            <div class="stat-label">Fuentes Web</div>
          </div>
          <div class="stat">
            <div class="stat-value" id="fuentesPerplexity">-</div>
            <div class="stat-label">Búsquedas Perplexity</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2 class="section-title">📋 Resumen Ejecutivo</h2>
        <div class="content" id="resumenEjecutivo"></div>
      </div>

      <div class="card">
        <h2 class="section-title">🏢 Perfil de Empresa</h2>
        <div class="content" id="perfilEmpresa"></div>
      </div>

      <div class="card">
        <h2 class="section-title">📈 Análisis PESTEL</h2>
        <div class="content" id="pestel"></div>
      </div>

      <div class="card">
        <h2 class="section-title">⚔️ Fuerzas de Porter</h2>
        <div class="content" id="porter"></div>
      </div>

      <div class="card">
        <h2 class="section-title">🌱 Análisis ESG</h2>
        <div class="content" id="esg"></div>
      </div>

      <div class="card">
        <h2 class="section-title">⚠️ Riesgos Identificados</h2>
        <div class="content" id="riesgos"></div>
      </div>

      <div class="card">
        <h2 class="section-title">💡 Conclusiones</h2>
        <div class="content" id="conclusiones"></div>
      </div>
    </div>
  </div>

  <script>
    document.getElementById('searchForm').addEventListener('submit', async (e) => {
      e.preventDefault();

      const btn = document.getElementById('submitBtn');
      const loading = document.getElementById('loading');
      const results = document.getElementById('results');

      btn.disabled = true;
      loading.classList.add('visible');
      results.classList.remove('visible');

      try {
        const response = await fetch('/api/investigar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            empresa: document.getElementById('empresa').value,
            sitio_web: document.getElementById('sitioWeb').value,
            sector: document.getElementById('sector').value,
            contexto: document.getElementById('contexto').value,
            investigacion_completa: true
          })
        });

        const data = await response.json();

        if (data.success && data.consolidado) {
          const c = data.consolidado;
          document.getElementById('scoreConfianza').textContent = c.score_confianza + '%';
          document.getElementById('fuentesWeb').textContent = c.fuentes?.web || 0;
          document.getElementById('fuentesPerplexity').textContent = c.fuentes?.perplexity || 0;
          document.getElementById('resumenEjecutivo').textContent = c.resumen_ejecutivo || 'No disponible';
          document.getElementById('perfilEmpresa').textContent = c.perfil_empresa || 'No disponible';
          document.getElementById('pestel').textContent = c.pestel || 'No disponible';
          document.getElementById('porter').textContent = c.porter || 'No disponible';
          document.getElementById('esg').textContent = c.esg || 'No disponible';
          document.getElementById('riesgos').textContent = c.riesgos || 'No disponible';
          document.getElementById('conclusiones').textContent = c.conclusiones || 'No disponible';
          results.classList.add('visible');
        } else {
          alert('Error: ' + (data.error || 'Error desconocido'));
        }
      } catch (error) {
        alert('Error de conexión: ' + error.message);
      } finally {
        btn.disabled = false;
        loading.classList.remove('visible');
      }
    });
  </script>
</body>
</html>`;
}
