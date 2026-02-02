import React, { useState, useEffect, useCallback, useRef } from 'react';
import AgentFlowVisualization from './AgentFlowVisualization';
import AgentChat from './AgentChat';
import api from '../../services/api';

/**
 * StatCard Component
 * Displays a metric with icon, value, and trend indicator
 */
const StatCard = ({ icon, label, value, trend, color }) => {
  const isPositive = trend >= 0;
  const trendColor = isPositive ? 'text-green-600' : 'text-red-600';
  const trendBgColor = isPositive ? 'bg-green-50' : 'bg-red-50';
  const arrow = isPositive ? '↑' : '↓';

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col hover:shadow-md transition-shadow">
      {/* Header with icon and trend */}
      <div className="flex items-start justify-between mb-4">
        <div className={`text-3xl rounded-lg p-3 ${color}`}>
          {icon}
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded ${trendBgColor}`}>
          <span className={`text-sm font-semibold ${trendColor}`}>
            {arrow} {Math.abs(trend)}%
          </span>
        </div>
      </div>

      {/* Label */}
      <p className="text-sm text-gray-600 mb-2 font-medium">{label}</p>

      {/* Value */}
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
};

/**
 * RecentDeliberation Component
 * Displays a recent deliberation with project info, score badge, and agents involved
 */
const RecentDeliberation = ({ deliberation }) => {
  const getScoreBadgeColor = (score) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getTimeAgo = (date) => {
    const now = new Date();
    const diffMs = now - new Date(date);
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Hace unos segundos';
    if (diffMins < 60) return `Hace ${diffMins}m`;
    if (diffHours < 24) return `Hace ${diffHours}h`;
    if (diffDays < 7) return `Hace ${diffDays}d`;
    return new Date(date).toLocaleDateString('es-MX');
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* Header with project name and score */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 text-sm">{deliberation.project_name}</h4>
          <p className="text-xs text-gray-500 mt-1">{getTimeAgo(deliberation.created_at)}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ml-2 ${getScoreBadgeColor(deliberation.score)}`}>
          {deliberation.score}%
        </span>
      </div>

      {/* Agents involved */}
      {deliberation.agents && deliberation.agents.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {deliberation.agents.map((agent) => (
            <span
              key={agent}
              className="inline-block px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded font-medium"
            >
              {agent}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Main AgentsDashboard Component
 * Complete dashboard with stats, agent flow visualization, recent deliberations, and chat interface
 */
const AgentsDashboard = ({ projectId = null }) => {
  // State Management
  const [stats, setStats] = useState({
    total_analisis: 0,
    score_promedio: 0,
    latencia_ms: 0,
    tasa_exito: 0,
  });
  const [deliberations, setDeliberations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeAgents, setActiveAgents] = useState([]);
  const [completedAgents, setCompletedAgents] = useState([]);
  const [showChat, setShowChat] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  // Ref for polling cleanup to prevent memory leaks
  const pollIntervalRef = useRef(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, []);

  // Simulation Modal State
  const [showSimulationModal, setShowSimulationModal] = useState(false);
  const [caseDescription, setCaseDescription] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedDemoCase, setSelectedDemoCase] = useState(null);

  // Pre-configured demo cases for sales pitches
  const demoCases = [
    {
      id: 'consulting',
      title: '📋 Servicios de Consultoría',
      description: 'Factura por $150,000 de servicios de consultoría fiscal. Proveedor: Consultores Profesionales SA de CV. RFC: CPR210315M52. CFDI timbrado, pago realizado por transferencia SPEI.'
    },
    {
      id: 'travel',
      title: '✈️ Gastos de Viaje',
      description: 'Reembolso de gastos de viaje de negocios por $45,000. Incluye: vuelos, hospedaje, alimentación y transporte terrestre. Viaje a Monterrey para reunión con cliente corporativo.'
    },
    {
      id: 'realestate',
      title: '🏢 Compra de Inmueble',
      description: 'Adquisición de oficina corporativa por $3,500,000. Escritura pública notariada, avalúo bancario, pago mediante crédito hipotecario y recursos propios.'
    },
    {
      id: 'tech',
      title: '💻 Licencias de Software',
      description: 'Compra de licencias Microsoft 365 Enterprise por $280,000 anuales. Proveedor autorizado, factura con complemento de pago, contrato de licenciamiento.'
    },
  ];

  /**
   * Fetch stats from API on component mount
   */
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.get('/api/agents/stats');
        setStats({
          total_analisis: data.totalAnalyses || data.total_analisis || 0,
          score_promedio: data.avgScore || data.score_promedio || 0,
          latencia_ms: data.avgLatency || data.latencia_ms || 0,
          tasa_exito: data.successRate || data.tasa_exito || 0,
        });
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };

    fetchStats();
  }, []);

  /**
   * Fetch recent deliberations on component mount
   */
  useEffect(() => {
    const fetchDeliberations = async () => {
      try {
        setLoading(true);
        const data = await api.get('/api/agents/deliberations/recent');
        const rawData = Array.isArray(data) ? data : data.deliberations || [];
        const normalizedData = rawData.map(d => ({
          project_name: d.projectName || d.project_name || 'Sin proyecto',
          created_at: d.timestamp || d.created_at || new Date().toISOString(),
          score: d.score || 0,
          agents: d.agentsInvolved || d.agents || [],
          summary: d.summary || d.resumen || '',
          id: d.id,
        }));
        setDeliberations(normalizedData);
      } catch (error) {
        console.error('Error fetching deliberations:', error);
        setDeliberations([]);
      } finally {
        setLoading(false);
      }
    };

    fetchDeliberations();
  }, []);

  /**
   * Simulate analysis with agent progress animation
   * Demonstrates the agent processing flow with all 10 agents
   */
  const [simulationMessages, setSimulationMessages] = useState([]);

  const handleSimularAnalisis = useCallback(async () => {
    // Determine which case to use (demo or custom)
    const activeCase = selectedDemoCase ? demoCases.find(c => c.id === selectedDemoCase) : null;
    const caseData = activeCase ? {
      case_id: activeCase.id,
      title: activeCase.title.replace(/^[^\s]+\s/, ''), // Remove emoji
      description: activeCase.description,
      amount: activeCase.description.match(/\$([\d,]+)/) ? parseFloat(activeCase.description.match(/\$([\d,]+)/)[1].replace(/,/g, '')) : 0,
    } : {
      case_id: 'custom',
      title: 'Análisis Personalizado',
      description: caseDescription || 'Análisis fiscal general',
      amount: 0
    };

    setIsSimulating(true);
    setActiveAgents([]);
    setCompletedAgents([]);
    setSimulationMessages([]);
    setShowChat(true);

    // Initial message
    setSimulationMessages([{
      id: 'case_intro',
      agentId: 'SISTEMA',
      agentName: 'Caso Recibido',
      emoji: '📋',
      status: 'completed',
      content: `Iniciando análisis con Inteligencia Artificial Real...\nCaso: ${caseData.title}`,
      processingTime: 0,
      timestamp: new Date(),
      isIntro: true
    }]);

    try {
      // 1. Trigger Real AI Deliberation using api service (includes auth headers)
      const response = await api.post('/api/deliberation/demo', caseData);
      const project_id = response.project_id;

      if (!project_id) throw new Error('No project_id returned from server');

      const processedAgents = new Set();

      // Clear any existing interval before creating new one
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }

      // 2. Poll for updates (store in ref for cleanup)
      pollIntervalRef.current = setInterval(async () => {
        try {
          // Check processing status using api service
          const statusData = await api.get(`/api/projects/processing-status/${project_id}`);

          if (statusData.success && statusData.data) {
            const { status, agent_statuses } = statusData.data;

            // Update active agents visualization
            if (agent_statuses) {
              const active = agent_statuses
                .filter(a => a.status === 'En proceso')
                .map(a => a.role);
              setActiveAgents(active);
            }

            // Check if completed or failed
            if (status === 'completed' || status === 'failed') {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
              setIsSimulating(false);

              if (status === 'completed') {
                // Refresh recent deliberations list
                try {
                  const recentData = await api.get('/api/agents/deliberations/recent');
                  const rawData = Array.isArray(recentData) ? recentData : recentData.deliberations || [];
                  const normalizedData = rawData.map(d => ({
                    project_name: d.projectName || d.project_name || 'Sin proyecto',
                    created_at: d.timestamp || d.created_at || new Date().toISOString(),
                    score: d.score || 0,
                    agents: d.agentsInvolved || d.agents || [],
                    summary: d.summary || d.resumen || '',
                    id: d.id,
                  }));
                  setDeliberations(normalizedData);
                } catch (refreshErr) {
                  console.error('Error refreshing deliberations:', refreshErr);
                }
              }
            }
          }

          // 3. Fetch Real Trail (Analysis Content)
          try {
            const trail = await api.get(`/api/deliberation/trail/${project_id}`);

            // Iterate through trail and add new messages
            if (Array.isArray(trail)) {
              trail.forEach((item) => {
                const msgId = `${item.agent_id}_${item.stage}`;

                if (!processedAgents.has(msgId)) {
                  processedAgents.add(msgId);

                  // Map backend agent ID to frontend display
                  // SYNCED WITH: backend/config/agents_registry.py (18 agents total)
                  const agentMap = {
                    // === AGENTES PRINCIPALES (7) ===
                    'A1_SPONSOR': { name: 'María Rodríguez', emoji: '🎯', id: 'A1', role: 'Sponsor / Evaluador Estratégico' },
                    'A2_PMO': { name: 'Carlos Mendoza', emoji: '📋', id: 'A2', role: 'Orquestador del Proceso F0-F9' },
                    'A3_FISCAL': { name: 'Laura Sánchez', emoji: '⚖️', id: 'A3', role: 'Especialista en Cumplimiento Fiscal' },
                    'A4_LEGAL': { name: 'Ana García', emoji: '📜', id: 'A4', role: 'Especialista en Contratos' },
                    'A5_FINANZAS': { name: 'Roberto Sánchez', emoji: '💰', id: 'A5', role: 'Director Financiero' },
                    'A6_PROVEEDOR': { name: 'Due Diligence', emoji: '🔍', id: 'A6', role: 'Validador de Proveedores' },
                    'A7_DEFENSA': { name: 'Laura Vázquez', emoji: '🛡️', id: 'A7', role: 'Directora de Defense File' },
                    // === AGENTES ESPECIALIZADOS (3) ===
                    'A8_AUDITOR': { name: 'Diego Ramírez', emoji: '📊', id: 'A8', role: 'Auditor Documental' },
                    'KB_CURATOR': { name: 'Dra. Elena Vázquez', emoji: '📚', id: 'KB', role: 'Curadora de Conocimiento' },
                    'DEVILS_ADVOCATE': { name: 'Abogado del Diablo', emoji: '😈', id: 'DA', role: 'Control Interno' },
                    // === SUBAGENTES FISCALES (3) - Reportan a A3_FISCAL ===
                    'S1_TIPIFICACION': { name: 'Patricia López', emoji: '🏷️', id: 'S1', role: 'Clasificador de Tipología' },
                    'S2_MATERIALIDAD': { name: 'Fernando Ruiz', emoji: '📎', id: 'S2', role: 'Especialista en Materialidad' },
                    'S3_RIESGOS': { name: 'Gabriela Vega', emoji: '⚠️', id: 'S3', role: 'Detector de Riesgos' },
                    // === SUBAGENTES PMO (5) - Reportan a A2_PMO ===
                    'S_ANALIZADOR': { name: 'Subagente Analizador', emoji: '🔬', id: 'SA', role: 'Análisis de Datos' },
                    'S_CLASIFICADOR': { name: 'Subagente Clasificador', emoji: '📁', id: 'SC', role: 'Clasificación por Severidad' },
                    'S_RESUMIDOR': { name: 'Subagente Resumidor', emoji: '📝', id: 'SR', role: 'Compresión y Resumen' },
                    'S_VERIFICADOR': { name: 'Subagente Verificador', emoji: '✅', id: 'SV', role: 'Control de Calidad' },
                    'S_REDACTOR': { name: 'Subagente Redactor', emoji: '✍️', id: 'SRD', role: 'Redacción de Documentos' },
                    // === ALIASES LEGACY (para compatibilidad con código antiguo) ===
                    'A1_RECEPCION': { name: 'María Rodríguez', emoji: '🎯', id: 'A1', role: 'Sponsor / Evaluador Estratégico' },
                    'A1_ESTRATEGIA': { name: 'María Rodríguez', emoji: '🎯', id: 'A1', role: 'Sponsor / Evaluador Estratégico' },
                    'A2_ANALISIS': { name: 'Laura Sánchez', emoji: '⚖️', id: 'A3', role: 'Especialista en Cumplimiento Fiscal' },
                    'A3_NORMATIVO': { name: 'Laura Sánchez', emoji: '⚖️', id: 'A3', role: 'Especialista en Cumplimiento Fiscal' },
                    'A4_CONTABLE': { name: 'Roberto Sánchez', emoji: '💰', id: 'A5', role: 'Director Financiero' },
                    'A5_OPERATIVO': { name: 'Due Diligence', emoji: '🔍', id: 'A6', role: 'Validador de Proveedores' },
                    'A6_FINANCIERO': { name: 'Roberto Sánchez', emoji: '💰', id: 'A5', role: 'Director Financiero' },
                    'A7_LEGAL': { name: 'Ana García', emoji: '📜', id: 'A4', role: 'Especialista en Contratos' },
                    'A8_REDTEAM': { name: 'Abogado del Diablo', emoji: '😈', id: 'DA', role: 'Control Interno' },
                    'A9_SINTESIS': { name: 'Laura Vázquez', emoji: '🛡️', id: 'A7', role: 'Directora de Defense File' },
                    'A10_ARCHIVO': { name: 'Dra. Elena Vázquez', emoji: '📚', id: 'KB', role: 'Curadora de Conocimiento' },
                    'LEGAL': { name: 'Ana García', emoji: '📜', id: 'A4', role: 'Especialista en Contratos' },
                  };

                  const agentInfo = agentMap[item.agent_id] || { name: item.agent_id, emoji: '🤖', id: item.agent_id };

                  setSimulationMessages(prev => [...prev, {
                    id: msgId,
                    agentId: agentInfo.id,
                    agentName: agentInfo.name,
                    emoji: agentInfo.emoji,
                    status: 'completed',
                    content: item.analysis || item.decision || "Análisis completado",
                    processingTime: 0,
                    timestamp: new Date(item.timestamp),
                    decision: item.decision
                  }]);

                  setCompletedAgents(prev => [...prev, agentInfo.id]);
                }
              });
            }
          } catch (trailErr) {
            // Trail might not exist yet, ignore
          }

        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 2000); // Poll every 2 seconds

    } catch (error) {
      console.error('Simulation error:', error);
      setSimulationMessages(prev => [...prev, {
        id: 'error',
        agentId: 'SISTEMA',
        agentName: 'Error',
        emoji: '❌',
        status: 'error',
        content: `Error al iniciar la simulación: ${error.message}`,
        timestamp: new Date()
      }]);
      setIsSimulating(false);
    }

  }, [caseDescription, selectedDemoCase, demoCases]);

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard de Agentes</h1>
          <p className="text-gray-600 mt-1">Monitoreo en tiempo real del sistema de inteligencia artificial</p>
        </div>
        <button
          onClick={() => setShowSimulationModal(true)}
          disabled={isSimulating}
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium shadow-sm disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isSimulating ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              Simulando...
            </>
          ) : (
            '🎯 Simular Análisis'
          )}
        </button>
      </div>

      {/* Stats Grid - Top Row with 4 Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          icon="📊"
          label="Total Análisis"
          value={stats.total_analisis || 0}
          trend={12}
          color="bg-blue-100"
        />
        <StatCard
          icon="⭐"
          label="Score Promedio"
          value={`${stats.score_promedio || 0}%`}
          trend={5}
          color="bg-purple-100"
        />
        <StatCard
          icon="⚡"
          label="Latencia"
          value={`${stats.latencia_ms || 0}ms`}
          trend={-3}
          color="bg-orange-100"
        />
        <StatCard
          icon="✅"
          label="Tasa de Éxito"
          value={`${stats.tasa_exito || 0}%`}
          trend={8}
          color="bg-green-100"
        />
      </div>

      {/* Main Content - Two Column Layout */}
      <div className="grid grid-cols-12 gap-6 min-h-[500px]">
        {/* Left Column - Agent Flow Visualization */}
        <div className="col-span-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden h-full">
            <div className="p-6 h-full overflow-auto">
              <AgentFlowVisualization
                activeAgents={activeAgents}
                completedAgents={completedAgents}
                showDetails={true}
              />
            </div>
          </div>
        </div>

        {/* Right Column - Simulation Log / Deliberations */}
        <div className="col-span-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col h-full overflow-hidden">
          {/* Show Simulation Log during simulation, otherwise show Deliberations */}
          {isSimulating || simulationMessages.length > 0 ? (
            <>
              <div className="flex items-center justify-between mb-4 flex-shrink-0">
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  {isSimulating && <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />}
                  🔴 Simulación en Vivo
                </h2>
                {!isSimulating && simulationMessages.length > 0 && (
                  <button
                    onClick={() => setSimulationMessages([])}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Limpiar
                  </button>
                )}
              </div>

              <div className="flex-1 overflow-y-auto space-y-3">
                {simulationMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`p-4 rounded-lg border transition-all ${msg.status === 'processing'
                      ? 'bg-indigo-50 border-indigo-200 animate-pulse'
                      : 'bg-gray-50 border-gray-200'
                      }`}
                  >
                    {/* Agent Header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{msg.emoji}</span>
                        <span className="font-semibold text-gray-900">{msg.agentId} {msg.agentName}</span>
                      </div>
                      {msg.status === 'completed' ? (
                        <span className="flex items-center gap-1 text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                          ✅ {(msg.processingTime / 1000).toFixed(1)}s
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-indigo-600 bg-indigo-100 px-2 py-1 rounded">
                          <span className="w-3 h-3 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                          Procesando...
                        </span>
                      )}
                    </div>

                    {/* Agent Message */}
                    {msg.content ? (
                      <p className="text-sm text-gray-700 leading-relaxed">
                        "{msg.content}"
                      </p>
                    ) : (
                      <div className="flex items-center gap-1">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    )}
                  </div>
                ))}

                {/* Auto-scroll anchor */}
                <div ref={(el) => el?.scrollIntoView({ behavior: 'smooth' })} />
              </div>
            </>
          ) : (
            <>
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex-shrink-0">Deliberaciones Recientes</h2>

              {loading ? (
                <div className="flex items-center justify-center flex-1">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-3 border-gray-300 border-t-indigo-600 rounded-full animate-spin"></div>
                    <span className="text-sm text-gray-600">Cargando deliberaciones...</span>
                  </div>
                </div>
              ) : deliberations.length === 0 ? (
                <div className="flex items-center justify-center flex-1">
                  <div className="text-center">
                    <div className="text-4xl mb-3">📋</div>
                    <p className="text-gray-600 font-medium">No hay deliberaciones recientes</p>
                    <p className="text-sm text-gray-500 mt-1">Comienza un análisis para ver resultados</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3 overflow-y-auto flex-1">
                  {deliberations.map((deliberation, index) => (
                    <RecentDeliberation key={index} deliberation={deliberation} />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Bottom - Agent Chat Interface */}
      {showChat ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="h-[600px] flex flex-col">
            <AgentChat projectId={projectId} />
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
          <div className="text-center">
            <div className="text-6xl mb-4">💬</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Inicia un análisis inteligente</h3>
            <p className="text-gray-600 max-w-md mx-auto mb-8">
              Haz clic en el botón "Simular Análisis" para ver a los agentes inteligentes procesando un caso completo y luego interactúa con ellos en tiempo real.
            </p>
            <button
              onClick={() => setShowSimulationModal(true)}
              disabled={isSimulating}
              className="inline-block px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              🎯 Comenzar Análisis Simulado
            </button>
          </div>
        </div>
      )}

      {/* Simulation Configuration Modal */}
      {showSimulationModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold">🎯 Configurar Simulación</h2>
                  <p className="text-indigo-100 mt-1">Elige un caso demo o describe tu propio escenario fiscal</p>
                </div>
                <button
                  onClick={() => {
                    setShowSimulationModal(false);
                    setCaseDescription('');
                    setSelectedDemoCase(null);
                    setUploadedFiles([]);
                  }}
                  className="text-white/80 hover:text-white p-2"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6 overflow-y-auto max-h-[60vh]">
              {/* Demo Cases Grid */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">💼 Casos Demo para Pitch de Venta</h3>
                <div className="grid grid-cols-2 gap-3">
                  {demoCases.map((demoCase) => (
                    <button
                      key={demoCase.id}
                      onClick={() => {
                        setSelectedDemoCase(demoCase.id);
                        setCaseDescription(demoCase.description);
                      }}
                      className={`p-4 rounded-xl border-2 text-left transition-all ${selectedDemoCase === demoCase.id
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                        }`}
                    >
                      <div className="font-medium text-gray-900">{demoCase.title}</div>
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">{demoCase.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Case Description */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">✏️ O describe tu propio caso</h3>
                <textarea
                  value={caseDescription}
                  onChange={(e) => {
                    setCaseDescription(e.target.value);
                    setSelectedDemoCase(null);
                  }}
                  placeholder="Describe el caso fiscal que quieres simular. Por ejemplo: 'Factura de servicios de consultoría por $100,000, proveedor nuevo sin historial previo...'"
                  className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none h-32"
                />
              </div>

              {/* File Upload Area */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">📎 Sube documentos (opcional)</h3>
                <div
                  className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-indigo-400 transition-colors cursor-pointer"
                  onClick={() => document.getElementById('fileUpload')?.click()}
                >
                  <input
                    id="fileUpload"
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.xml,.jpg,.png"
                    className="hidden"
                    onChange={(e) => {
                      const files = Array.from(e.target.files || []);
                      setUploadedFiles(prev => [...prev, ...files]);
                    }}
                  />
                  <div className="text-4xl mb-2">📄</div>
                  <p className="text-gray-600">Arrastra archivos aquí o haz clic para seleccionar</p>
                  <p className="text-xs text-gray-400 mt-1">PDF, XML, Word, Imágenes</p>
                </div>

                {/* Uploaded Files List */}
                {uploadedFiles.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {uploadedFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                        <span className="text-sm text-gray-700 truncate">{file.name}</span>
                        <button
                          onClick={() => setUploadedFiles(prev => prev.filter((_, i) => i !== idx))}
                          className="text-red-500 hover:text-red-700 p-1"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-6 bg-gray-50 border-t flex items-center justify-between">
              <p className="text-sm text-gray-500">
                {caseDescription ? '✓ Caso configurado' : 'Selecciona o describe un caso'}
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowSimulationModal(false);
                    setCaseDescription('');
                    setSelectedDemoCase(null);
                    setUploadedFiles([]);
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancelar
                </button>
                <button
                  onClick={() => {
                    setShowSimulationModal(false);
                    handleSimularAnalisis();
                  }}
                  disabled={!caseDescription.trim()}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  🚀 Iniciar Simulación
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentsDashboard;
