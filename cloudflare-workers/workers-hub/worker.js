/**
 * WORKERS HUB - Orquestador Central de Microfunciones
 *
 * Este Worker actúa como el "cerebro" que coordina todos los Workers especializados
 * y los conecta con la plataforma ReplicarIA.
 *
 * Funciones:
 * - Registry de Workers disponibles
 * - Enrutamiento de tareas al Worker correcto
 * - Cola de tareas asíncronas
 * - Comunicación bidireccional con ReplicarIA
 * - Health checks de todos los Workers
 *
 * Última actualización: 2026-02-04
 */

// Registry de Workers especializados
const WORKERS_REGISTRY = {
  // Investigación y análisis
  'oraculo-estrategico': {
    url: 'https://oraculo-estrategico.workers.dev',
    capabilities: ['investigacion', 'due_diligence', 'pestel', 'porter', 'esg', 'materialidad'],
    agentes: ['A6_PROVEEDOR', 'S2_MATERIALIDAD', 'A3_FISCAL', 'A1_SPONSOR'],
    timeout: 300000
  },

  // Lectura y procesamiento de documentos
  'lector-documentos': {
    url: 'https://lector-documentos.workers.dev',
    capabilities: ['ocr', 'extraccion_texto', 'analisis_pdf', 'analisis_imagen'],
    agentes: ['A8_AUDITOR', 'S_ANALIZADOR', 'A7_DEFENSA'],
    timeout: 120000
  },

  // Redacción de comunicaciones
  'redactor-comunicaciones': {
    url: 'https://redactor-comunicaciones.workers.dev',
    capabilities: ['redaccion_email', 'notificaciones', 'reportes', 'resumen'],
    agentes: ['A2_PMO', 'S_REDACTOR', 'S_RESUMIDOR'],
    timeout: 60000
  },

  // Validación SAT y compliance
  'validador-sat': {
    url: 'https://validador-sat.workers.dev',
    capabilities: ['lista_69b', 'cfdi', 'opinion_cumplimiento', 'rfc'],
    agentes: ['A3_FISCAL', 'S3_RIESGOS'],
    timeout: 30000
  },

  // Scraping especializado
  'scraper-web': {
    url: 'https://scraper-web.workers.dev',
    capabilities: ['scraping', 'monitoreo_web', 'extraccion_datos'],
    agentes: ['A6_PROVEEDOR', 'KB_CURATOR'],
    timeout: 120000
  }
};

export default {
  async fetch(request, env) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Empresa-ID, X-Agent-ID',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    try {
      // =====================================================================
      // ENDPOINTS DE GESTIÓN
      // =====================================================================

      // Health check del Hub
      if (url.pathname === '/health') {
        return jsonResponse({
          status: 'ok',
          hub_version: '1.0.0',
          workers_registered: Object.keys(WORKERS_REGISTRY).length
        }, corsHeaders);
      }

      // Lista de Workers registrados
      if (url.pathname === '/workers') {
        return jsonResponse({
          workers: Object.entries(WORKERS_REGISTRY).map(([id, config]) => ({
            id,
            capabilities: config.capabilities,
            agentes: config.agentes,
            status: 'registered'
          }))
        }, corsHeaders);
      }

      // Health check de todos los Workers
      if (url.pathname === '/workers/health') {
        const healthChecks = await checkAllWorkersHealth(env);
        return jsonResponse({ workers: healthChecks }, corsHeaders);
      }

      // =====================================================================
      // ENDPOINT PRINCIPAL: EJECUTAR TAREA
      // =====================================================================

      if (url.pathname === '/execute' && request.method === 'POST') {
        const body = await request.json();
        const { tarea, parametros, agente_id, empresa_id, callback_url } = body;

        // Validar tarea
        if (!tarea) {
          return jsonResponse({ error: 'Tarea requerida' }, corsHeaders, 400);
        }

        // Encontrar Worker que pueda manejar la tarea
        const worker = findWorkerForTask(tarea);
        if (!worker) {
          return jsonResponse({
            error: `No hay Worker disponible para la tarea: ${tarea}`,
            tareas_disponibles: getAllCapabilities()
          }, corsHeaders, 404);
        }

        // Ejecutar tarea
        const resultado = await executeTask(worker, tarea, parametros, env);

        // Si hay callback_url, notificar a ReplicarIA
        if (callback_url && resultado.success) {
          await notifyReplicarIA(callback_url, {
            tarea,
            resultado,
            agente_id,
            empresa_id,
            timestamp: new Date().toISOString()
          }, env);
        }

        return jsonResponse(resultado, corsHeaders);
      }

      // =====================================================================
      // ENDPOINT: EJECUTAR PIPELINE (múltiples tareas en secuencia)
      // =====================================================================

      if (url.pathname === '/pipeline' && request.method === 'POST') {
        const body = await request.json();
        const { pasos, empresa_id, agente_id, callback_url } = body;

        if (!pasos || !Array.isArray(pasos)) {
          return jsonResponse({ error: 'Se requiere array de pasos' }, corsHeaders, 400);
        }

        const resultados = [];
        let contexto = {};

        for (const paso of pasos) {
          const worker = findWorkerForTask(paso.tarea);
          if (!worker) {
            resultados.push({
              paso: paso.tarea,
              success: false,
              error: `Worker no encontrado para: ${paso.tarea}`
            });
            continue;
          }

          // Merge de parámetros con contexto del paso anterior
          const parametros = {
            ...paso.parametros,
            contexto_previo: contexto
          };

          const resultado = await executeTask(worker, paso.tarea, parametros, env);
          resultados.push({
            paso: paso.tarea,
            ...resultado
          });

          // Actualizar contexto para siguiente paso
          if (resultado.success) {
            contexto = { ...contexto, [paso.tarea]: resultado };
          }
        }

        const pipelineResult = {
          success: resultados.every(r => r.success),
          pasos_completados: resultados.filter(r => r.success).length,
          total_pasos: pasos.length,
          resultados,
          contexto_final: contexto
        };

        // Callback si existe
        if (callback_url) {
          await notifyReplicarIA(callback_url, {
            tipo: 'pipeline',
            resultado: pipelineResult,
            agente_id,
            empresa_id
          }, env);
        }

        return jsonResponse(pipelineResult, corsHeaders);
      }

      // =====================================================================
      // ENDPOINT: WEBHOOK DESDE REPLICARIA
      // =====================================================================

      if (url.pathname === '/webhook/replicaria' && request.method === 'POST') {
        const body = await request.json();
        const { evento, datos, proyecto_id, empresa_id } = body;

        console.log(`Webhook recibido: ${evento} - Proyecto: ${proyecto_id}`);

        // Procesar según tipo de evento
        let resultado;
        switch (evento) {
          case 'nuevo_proveedor':
            resultado = await handleNuevoProveedor(datos, env);
            break;
          case 'fase_cambio':
            resultado = await handleFaseCambio(datos, env);
            break;
          case 'documento_subido':
            resultado = await handleDocumentoSubido(datos, env);
            break;
          case 'solicitar_investigacion':
            resultado = await handleSolicitarInvestigacion(datos, env);
            break;
          default:
            resultado = { processed: false, message: `Evento no manejado: ${evento}` };
        }

        return jsonResponse({
          evento,
          proyecto_id,
          resultado,
          timestamp: new Date().toISOString()
        }, corsHeaders);
      }

      // =====================================================================
      // ENDPOINT: PROXY DIRECTO A WORKER ESPECÍFICO
      // =====================================================================

      if (url.pathname.startsWith('/proxy/')) {
        const workerId = url.pathname.split('/')[2];
        const workerConfig = WORKERS_REGISTRY[workerId];

        if (!workerConfig) {
          return jsonResponse({ error: `Worker no encontrado: ${workerId}` }, corsHeaders, 404);
        }

        // Reenviar request al Worker específico
        const targetUrl = workerConfig.url + url.pathname.replace(`/proxy/${workerId}`, '');
        const proxyResponse = await fetch(targetUrl, {
          method: request.method,
          headers: request.headers,
          body: request.method !== 'GET' ? await request.text() : undefined
        });

        const proxyData = await proxyResponse.json();
        return jsonResponse(proxyData, corsHeaders, proxyResponse.status);
      }

      // UI de administración
      if (url.pathname === '/' || url.pathname === '/admin') {
        return new Response(getAdminUI(), {
          headers: { ...corsHeaders, 'Content-Type': 'text/html; charset=utf-8' }
        });
      }

      return jsonResponse({ error: 'Endpoint no encontrado' }, corsHeaders, 404);

    } catch (error) {
      console.error('Error en Workers Hub:', error);
      return jsonResponse({
        error: error.message,
        stack: error.stack
      }, corsHeaders, 500);
    }
  }
};

// ============================================================================
// FUNCIONES AUXILIARES
// ============================================================================

function jsonResponse(data, corsHeaders, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

function findWorkerForTask(tarea) {
  for (const [id, config] of Object.entries(WORKERS_REGISTRY)) {
    if (config.capabilities.includes(tarea)) {
      return { id, ...config };
    }
  }
  return null;
}

function getAllCapabilities() {
  const capabilities = new Set();
  for (const config of Object.values(WORKERS_REGISTRY)) {
    config.capabilities.forEach(c => capabilities.add(c));
  }
  return Array.from(capabilities);
}

async function executeTask(worker, tarea, parametros, env) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), worker.timeout);

    const response = await fetch(`${worker.url}/api/${tarea}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Hub-Request': 'true'
      },
      body: JSON.stringify(parametros),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Worker respondió con status: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      worker_id: worker.id,
      tarea,
      ...data
    };

  } catch (error) {
    return {
      success: false,
      worker_id: worker.id,
      tarea,
      error: error.name === 'AbortError' ? 'Timeout' : error.message
    };
  }
}

async function checkAllWorkersHealth(env) {
  const checks = [];

  for (const [id, config] of Object.entries(WORKERS_REGISTRY)) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${config.url}/health`, {
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      checks.push({
        id,
        status: response.ok ? 'healthy' : 'unhealthy',
        response_time: null,
        capabilities: config.capabilities
      });
    } catch (error) {
      checks.push({
        id,
        status: 'unreachable',
        error: error.message,
        capabilities: config.capabilities
      });
    }
  }

  return checks;
}

async function notifyReplicarIA(callbackUrl, data, env) {
  try {
    await fetch(callbackUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Worker-Callback': 'true',
        'Authorization': `Bearer ${env.REPLICARIA_API_KEY || ''}`
      },
      body: JSON.stringify(data)
    });
  } catch (error) {
    console.error('Error notificando a ReplicarIA:', error);
  }
}

// ============================================================================
// HANDLERS DE EVENTOS
// ============================================================================

async function handleNuevoProveedor(datos, env) {
  const { empresa, rfc, sitio_web, monto, tipo_servicio } = datos;

  // Ejecutar due diligence automático
  const oraculoWorker = WORKERS_REGISTRY['oraculo-estrategico'];

  return await executeTask(oraculoWorker, 'due_diligence', {
    empresa,
    rfc,
    sitio_web,
    monto_operacion: monto,
    tipo_servicio
  }, env);
}

async function handleFaseCambio(datos, env) {
  const { fase_anterior, fase_nueva, proyecto_id } = datos;

  // Lógica según la fase
  if (fase_nueva === 'F5' || fase_nueva === 'F6') {
    // Documentar materialidad
    return { action: 'trigger_materialidad', proyecto_id };
  }

  return { processed: true, fase: fase_nueva };
}

async function handleDocumentoSubido(datos, env) {
  const { documento_url, tipo_documento, proyecto_id } = datos;

  // Procesar documento con lector
  const lectorWorker = WORKERS_REGISTRY['lector-documentos'];

  if (lectorWorker) {
    return await executeTask(lectorWorker, 'analisis_pdf', {
      url: documento_url,
      tipo: tipo_documento
    }, env);
  }

  return { processed: false, message: 'Lector de documentos no disponible' };
}

async function handleSolicitarInvestigacion(datos, env) {
  const { empresa, tipo_investigacion, parametros } = datos;

  const oraculoWorker = WORKERS_REGISTRY['oraculo-estrategico'];

  return await executeTask(oraculoWorker, tipo_investigacion || 'investigacion', {
    empresa,
    ...parametros
  }, env);
}

// ============================================================================
// UI DE ADMINISTRACIÓN
// ============================================================================

function getAdminUI() {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🔗 Workers Hub - ReplicarIA</title>
  <style>
    :root {
      --primary: #6366f1;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #ef4444;
      --bg: #0f172a;
      --card: #1e293b;
      --text: #f1f5f9;
      --muted: #94a3b8;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem;
    }
    .container { max-width: 1400px; margin: 0 auto; }
    h1 {
      font-size: 2rem;
      background: linear-gradient(135deg, #6366f1, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }
    .subtitle { color: var(--muted); margin-bottom: 2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1.5rem; }
    .card {
      background: var(--card);
      border-radius: 1rem;
      padding: 1.5rem;
      border: 1px solid #334155;
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1rem;
    }
    .card-title { font-size: 1.25rem; }
    .status {
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .status.healthy { background: var(--success); color: white; }
    .status.unhealthy { background: var(--danger); color: white; }
    .status.unknown { background: var(--warning); color: black; }
    .capabilities {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 1rem;
    }
    .capability {
      background: #334155;
      padding: 0.25rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.75rem;
      color: var(--muted);
    }
    .agentes { margin-top: 0.75rem; color: var(--muted); font-size: 0.875rem; }
    .btn {
      background: var(--primary);
      color: white;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 0.5rem;
      cursor: pointer;
      font-size: 0.875rem;
      margin-top: 1rem;
    }
    .btn:hover { opacity: 0.9; }
    .section-title {
      font-size: 1.5rem;
      margin: 2rem 0 1rem;
      color: var(--primary);
    }
    .endpoint {
      background: #0f172a;
      padding: 0.75rem;
      border-radius: 0.5rem;
      margin-bottom: 0.5rem;
      font-family: monospace;
      font-size: 0.875rem;
    }
    .method {
      background: var(--primary);
      color: white;
      padding: 0.125rem 0.5rem;
      border-radius: 0.25rem;
      margin-right: 0.5rem;
      font-size: 0.75rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🔗 Workers Hub</h1>
    <p class="subtitle">Orquestador Central de Microfunciones - ReplicarIA</p>

    <div class="grid" id="workersGrid"></div>

    <h2 class="section-title">📡 Endpoints Disponibles</h2>
    <div class="card">
      <div class="endpoint">
        <span class="method">GET</span> /workers - Lista de workers registrados
      </div>
      <div class="endpoint">
        <span class="method">GET</span> /workers/health - Health check de todos los workers
      </div>
      <div class="endpoint">
        <span class="method">POST</span> /execute - Ejecutar tarea individual
      </div>
      <div class="endpoint">
        <span class="method">POST</span> /pipeline - Ejecutar pipeline de tareas
      </div>
      <div class="endpoint">
        <span class="method">POST</span> /webhook/replicaria - Webhook desde ReplicarIA
      </div>
      <div class="endpoint">
        <span class="method">*</span> /proxy/{worker_id}/* - Proxy directo a worker
      </div>
    </div>

    <h2 class="section-title">📋 Ejemplo de Uso</h2>
    <div class="card">
      <pre style="background: #0f172a; padding: 1rem; border-radius: 0.5rem; overflow-x: auto;">
// Ejecutar tarea individual
fetch('/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tarea: 'investigacion',
    parametros: {
      empresa: 'Acme Corp',
      sitio_web: 'https://acme.mx'
    },
    agente_id: 'A6_PROVEEDOR',
    empresa_id: 'EMP-001',
    callback_url: 'https://api.revisar.ia/webhooks/worker'
  })
});

// Ejecutar pipeline
fetch('/pipeline', {
  method: 'POST',
  body: JSON.stringify({
    pasos: [
      { tarea: 'scraping', parametros: { url: '...' } },
      { tarea: 'investigacion', parametros: { empresa: '...' } },
      { tarea: 'materialidad', parametros: { monto: 100000 } }
    ],
    callback_url: '...'
  })
});
      </pre>
    </div>
  </div>

  <script>
    async function loadWorkers() {
      const response = await fetch('/workers');
      const data = await response.json();

      const grid = document.getElementById('workersGrid');
      grid.innerHTML = data.workers.map(w => \`
        <div class="card">
          <div class="card-header">
            <span class="card-title">\${w.id}</span>
            <span class="status unknown">Checking...</span>
          </div>
          <div class="capabilities">
            \${w.capabilities.map(c => \`<span class="capability">\${c}</span>\`).join('')}
          </div>
          <div class="agentes">Agentes: \${w.agentes.join(', ')}</div>
          <button class="btn" onclick="testWorker('\${w.id}')">Probar</button>
        </div>
      \`).join('');

      // Check health
      const healthResponse = await fetch('/workers/health');
      const healthData = await healthResponse.json();

      healthData.workers.forEach(h => {
        const card = [...document.querySelectorAll('.card-title')]
          .find(t => t.textContent === h.id)?.closest('.card');
        if (card) {
          const status = card.querySelector('.status');
          status.className = \`status \${h.status}\`;
          status.textContent = h.status;
        }
      });
    }

    async function testWorker(id) {
      alert(\`Probando worker: \${id}...\`);
    }

    loadWorkers();
  </script>
</body>
</html>`;
}
