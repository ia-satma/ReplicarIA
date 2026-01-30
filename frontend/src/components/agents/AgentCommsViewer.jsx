import React, { useState, useEffect, useRef } from 'react';

/**
 * Agent info with colors and icons for the communication viewer
 */
const AGENT_CONFIG = {
  A1: { icon: '🎯', name: 'Estrategia', color: '#6366f1', bgColor: '#eef2ff' },
  A2: { icon: '📋', name: 'PMO (Orquestador)', color: '#3b82f6', bgColor: '#eff6ff' },
  A3: { icon: '💼', name: 'Fiscal', color: '#f59e0b', bgColor: '#fef3c7' },
  A4: { icon: '⚖️', name: 'Legal', color: '#8b5cf6', bgColor: '#f5f3ff' },
  A5: { icon: '💰', name: 'Finanzas', color: '#10b981', bgColor: '#d1fae5' },
  A6: { icon: '🏢', name: 'Proveedor', color: '#06b6d4', bgColor: '#cffafe' },
  A7: { icon: '🛡️', name: 'Defensa', color: '#ef4444', bgColor: '#fee2e2' },
};

const STATUS_CONFIG = {
  pendiente: { label: 'Pendiente', color: '#f59e0b', icon: '⏳' },
  en_revision: { label: 'En Revisión', color: '#3b82f6', icon: '🔍' },
  aprobado: { label: 'Aprobado', color: '#10b981', icon: '✅' },
  rechazado: { label: 'Rechazado', color: '#ef4444', icon: '❌' },
  requiere_cambios: { label: 'Requiere Cambios', color: '#f97316', icon: '📝' },
};

/**
 * Single communication message card - styled like an email
 */
const CommunicationCard = ({ comm, isLatest }) => {
  const fromAgent = AGENT_CONFIG[comm.from_agent] || AGENT_CONFIG.A2;
  const toAgent = AGENT_CONFIG[comm.to_agent] || AGENT_CONFIG.A4;
  const status = STATUS_CONFIG[comm.status] || STATUS_CONFIG.pendiente;
  const [expanded, setExpanded] = useState(isLatest);

  return (
    <div
      className={`relative mb-4 rounded-xl overflow-hidden transition-all duration-300 ${
        isLatest ? 'ring-2 ring-blue-400 shadow-lg' : 'shadow-md hover:shadow-lg'
      }`}
      style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        borderLeft: `4px solid ${fromAgent.color}`
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          {/* From Agent Avatar */}
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center text-2xl shadow-inner"
            style={{ backgroundColor: fromAgent.bgColor }}
          >
            {fromAgent.icon}
          </div>

          {/* Arrow */}
          <div className="text-gray-400 text-xl animate-pulse">→</div>

          {/* To Agent Avatar */}
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center text-2xl shadow-inner"
            style={{ backgroundColor: toAgent.bgColor }}
          >
            {toAgent.icon}
          </div>

          {/* Names */}
          <div className="ml-2">
            <div className="text-white font-medium text-sm">
              {fromAgent.name} <span className="text-gray-400">→</span> {toAgent.name}
            </div>
            <div className="text-gray-400 text-xs">
              {new Date(comm.timestamp).toLocaleString('es-MX', {
                dateStyle: 'short',
                timeStyle: 'short'
              })}
            </div>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-2">
          <span
            className="px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1"
            style={{
              backgroundColor: `${status.color}20`,
              color: status.color,
              border: `1px solid ${status.color}40`
            }}
          >
            <span>{status.icon}</span>
            {status.label}
          </span>
          <span className="text-gray-400 text-sm">
            {expanded ? '▼' : '▶'}
          </span>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-4 pb-4 animate-fadeIn">
          {/* Subject Line */}
          <div className="bg-slate-800/50 rounded-lg p-3 mb-3">
            <div className="text-gray-400 text-xs mb-1">Asunto:</div>
            <div className="text-white font-medium">{comm.subject}</div>
          </div>

          {/* Email Body */}
          <div className="bg-slate-900/50 rounded-lg p-4">
            <div className="text-gray-400 text-xs mb-2">Contenido:</div>
            <pre className="text-gray-200 text-sm whitespace-pre-wrap font-sans leading-relaxed">
              {comm.content}
            </pre>
          </div>

          {/* Metadata */}
          {comm.metadata && Object.keys(comm.metadata).length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {comm.metadata.previous_feedback && (
                <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-1 rounded">
                  Con feedback previo
                </span>
              )}
              {comm.metadata.articles_cited && (
                <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">
                  {comm.metadata.articles_cited.length} artículos citados
                </span>
              )}
            </div>
          )}

          {/* Iteration Badge */}
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-gray-500">Iteración:</span>
            <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full">
              #{comm.iteration}
            </span>
          </div>
        </div>
      )}

      {/* Unread indicator */}
      {!comm.read && (
        <div className="absolute top-4 right-4 w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
      )}
    </div>
  );
};

/**
 * Workflow Progress Indicator
 */
const WorkflowProgress = ({ workflow }) => {
  const stages = [
    { key: 'pmo_to_legal', label: 'PMO → Legal', icon: '📋→⚖️' },
    { key: 'legal_review', label: 'Revisión Legal', icon: '⚖️' },
    { key: 'legal_to_pmo', label: 'Legal → PMO', icon: '⚖️→📋' },
    { key: 'pmo_to_provider', label: 'PMO → Proveedor', icon: '📋→🏢' },
    { key: 'provider_changes', label: 'Cambios Proveedor', icon: '🏢' },
    { key: 'completed', label: 'Completado', icon: '✅' },
  ];

  const currentIndex = stages.findIndex(s => s.key === workflow?.current_stage);

  return (
    <div className="bg-slate-800/50 rounded-xl p-4 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-semibold">Progreso del Workflow</h3>
        <span className={`text-xs px-2 py-1 rounded ${
          workflow?.status === 'completado' ? 'bg-green-500/20 text-green-400' :
          workflow?.status === 'error' ? 'bg-red-500/20 text-red-400' :
          'bg-blue-500/20 text-blue-400'
        }`}>
          {workflow?.status || 'No iniciado'}
        </span>
      </div>

      <div className="flex items-center gap-1 overflow-x-auto pb-2">
        {stages.map((stage, index) => (
          <React.Fragment key={stage.key}>
            <div
              className={`flex flex-col items-center min-w-[80px] p-2 rounded-lg transition-all ${
                index < currentIndex ? 'bg-green-500/20' :
                index === currentIndex ? 'bg-blue-500/30 ring-2 ring-blue-400' :
                'bg-slate-700/50'
              }`}
            >
              <span className="text-2xl mb-1">{stage.icon}</span>
              <span className={`text-xs text-center ${
                index <= currentIndex ? 'text-white' : 'text-gray-500'
              }`}>
                {stage.label}
              </span>
            </div>
            {index < stages.length - 1 && (
              <div className={`w-6 h-0.5 ${
                index < currentIndex ? 'bg-green-500' : 'bg-slate-600'
              }`} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

/**
 * Main AgentCommsViewer Component
 * Shows real-time communication between agents for a project
 */
const AgentCommsViewer = ({ projectId, autoRefresh = true, refreshInterval = 5000 }) => {
  const [communications, setCommunications] = useState([]);
  const [workflow, setWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);
  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  // Fetch communications
  const fetchCommunications = async () => {
    if (!projectId) return;

    try {
      const response = await fetch(`${API_URL}/api/agent-comms/communications/${projectId}`);
      if (response.ok) {
        const data = await response.json();
        setCommunications(data.communications || []);
      }
    } catch (err) {
      console.error('Error fetching communications:', err);
      setError('Error cargando comunicaciones');
    }
  };

  // Fetch workflow status
  const fetchWorkflow = async () => {
    if (!projectId) return;

    try {
      const response = await fetch(`${API_URL}/api/agent-comms/workflow-status/${projectId}`);
      if (response.ok) {
        const data = await response.json();
        setWorkflow(data);
      }
    } catch (err) {
      console.error('Error fetching workflow:', err);
    }
  };

  // Initial fetch
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await Promise.all([fetchCommunications(), fetchWorkflow()]);
      setLoading(false);
    };
    load();
  }, [projectId]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || !projectId) return;

    const interval = setInterval(() => {
      fetchCommunications();
      fetchWorkflow();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, projectId, refreshInterval]);

  // Auto-scroll to latest message
  useEffect(() => {
    if (containerRef.current && communications.length > 0) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [communications.length]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-slate-900 rounded-xl">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Cargando comunicaciones...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-center">
        <span className="text-4xl mb-2 block">⚠️</span>
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-6 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
            <span className="text-2xl">📬</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Comunicaciones Inter-Agentes</h2>
            <p className="text-gray-400 text-sm">Proyecto: {projectId}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {autoRefresh && (
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Actualizando
            </span>
          )}
          <span className="text-gray-500 text-sm">
            {communications.length} mensaje{communications.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Workflow Progress */}
      {workflow && <WorkflowProgress workflow={workflow} />}

      {/* Communications Timeline */}
      <div
        ref={containerRef}
        className="max-h-[500px] overflow-y-auto pr-2 custom-scrollbar"
      >
        {communications.length === 0 ? (
          <div className="text-center py-12">
            <span className="text-6xl mb-4 block opacity-50">📭</span>
            <p className="text-gray-400 text-lg">No hay comunicaciones aún</p>
            <p className="text-gray-500 text-sm mt-2">
              Las comunicaciones aparecerán aquí cuando los agentes empiecen a trabajar
            </p>
          </div>
        ) : (
          communications.map((comm, index) => (
            <CommunicationCard
              key={comm.id}
              comm={comm}
              isLatest={index === communications.length - 1}
            />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-center justify-between">
        <div className="flex gap-4">
          {Object.entries(AGENT_CONFIG).slice(0, 4).map(([key, agent]) => (
            <div key={key} className="flex items-center gap-1">
              <span
                className="w-6 h-6 rounded-full flex items-center justify-center text-sm"
                style={{ backgroundColor: agent.bgColor }}
              >
                {agent.icon}
              </span>
              <span className="text-gray-400 text-xs hidden sm:inline">{agent.name}</span>
            </div>
          ))}
        </div>

        <button
          onClick={() => { fetchCommunications(); fetchWorkflow(); }}
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
        >
          <span>↻</span> Actualizar
        </button>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #1e293b;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #475569;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #64748b;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default AgentCommsViewer;
