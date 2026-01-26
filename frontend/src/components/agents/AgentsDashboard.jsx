import React, { useState, useEffect, useCallback } from 'react';
import AgentFlowVisualization from './AgentFlowVisualization';
import AgentChat from './AgentChat';

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

  /**
   * Fetch stats from API on component mount
   */
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/agents/stats');
        if (response.ok) {
          const data = await response.json();
          setStats({
            total_analisis: data.totalAnalyses || data.total_analisis || 0,
            score_promedio: data.avgScore || data.score_promedio || 0,
            latencia_ms: data.avgLatency || data.latencia_ms || 0,
            tasa_exito: data.successRate || data.tasa_exito || 0,
          });
        }
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
        const response = await fetch('/api/agents/deliberations/recent');
        if (response.ok) {
          const data = await response.json();
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
        }
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
   * Demonstrates the agent processing flow
   */
  const handleSimularAnalisis = useCallback(async () => {
    setIsSimulating(true);
    setActiveAgents([]);
    setCompletedAgents([]);
    setShowChat(true);

    const agentIds = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7'];

    for (let i = 0; i < agentIds.length; i++) {
      // Activate current agent
      setActiveAgents([agentIds[i]]);

      // Simulate processing time
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Mark as completed
      setCompletedAgents((prev) => [...prev, agentIds[i]]);
      setActiveAgents([]);
    }

    setIsSimulating(false);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard de Agentes</h1>
          <p className="text-gray-600 mt-1">Monitoreo en tiempo real del sistema de inteligencia artificial</p>
        </div>
        <button
          onClick={handleSimularAnalisis}
          disabled={isSimulating}
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium shadow-sm disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isSimulating ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              Simulando...
            </>
          ) : (
            'Simular Análisis'
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

        {/* Right Column - Recent Deliberations */}
        <div className="col-span-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col h-full overflow-hidden">
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
              onClick={handleSimularAnalisis}
              disabled={isSimulating}
              className="inline-block px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Comenzar Análisis Simulado
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentsDashboard;
