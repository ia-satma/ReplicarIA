import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronDown, ChevronUp } from 'lucide-react';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const AGENT_COLORS = {
  'A1': '#6366f1',
  'A2': '#8b5cf6',
  'A3': '#a855f7',
  'A4': '#d946ef',
  'A5': '#ec4899',
  'A6': '#f43f5e',
  'A7': '#ef4444',
  'A8': '#f97316',
  'A9': '#eab308',
  'A10': '#22c55e'
};

const AGENT_NAMES = {
  'A1': 'A1 Sponsor',
  'A2': 'A2 PMO',
  'A3': 'A3 Fiscal',
  'A4': 'A4 Legal',
  'A5': 'A5 Finanzas',
  'A6': 'A6 Proveedor',
  'A7': 'A7 Defensa',
  'A8': 'A8 Auditor',
  'A9': 'A9 Especialista',
  'A10': 'A10 Evaluador'
};

const SAMPLE_DELIBERATIONS = [
  {
    id: '1',
    fase: 1,
    agente_id: 'A1',
    tipo: 'analysis',
    resumen: 'Análisis estratégico inicial del proyecto',
    decision: { aprobado: true, score: 85 },
    created_at: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: '2',
    fase: 2,
    agente_id: 'A3',
    tipo: 'analysis',
    resumen: 'Revisión de cumplimiento fiscal',
    decision: { aprobado: true, score: 78 },
    created_at: new Date(Date.now() - 64800000).toISOString()
  },
  {
    id: '3',
    fase: 3,
    agente_id: 'A5',
    tipo: 'analysis',
    resumen: 'Evaluación de viabilidad financiera',
    decision: { aprobado: true, score: 92 },
    created_at: new Date(Date.now() - 43200000).toISOString()
  },
  {
    id: '4',
    fase: 4,
    agente_id: 'A4',
    tipo: 'analysis',
    resumen: 'Validación legal y contractual',
    decision: { aprobado: false, score: 55 },
    created_at: new Date(Date.now() - 21600000).toISOString()
  }
];

const normalizeDeliberation = (d) => ({
  id: d.id,
  agente_id: d.agente_id || d.agent_id || 'A1',
  fase: d.fase || d.phase || 1,
  resumen: d.resumen || d.summary || d.content || '',
  decision: d.decision || { aprobado: false, score: 0 },
  created_at: d.created_at || d.createdAt || new Date().toISOString(),
  tipo: d.tipo || d.type || 'analysis'
});

const DeliberationTimeline = ({ projectId }) => {
  const [deliberations, setDeliberations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedItems, setExpandedItems] = useState(new Set());
  const [usingSampleData, setUsingSampleData] = useState(false);

  useEffect(() => {
    loadDeliberations();
  }, [projectId]);

  const loadDeliberations = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/projects/${projectId}/deliberations`);
      
      if (response.data.deliberations && response.data.deliberations.length > 0) {
        setDeliberations(response.data.deliberations.map(normalizeDeliberation));
        setUsingSampleData(false);
      } else {
        setDeliberations(SAMPLE_DELIBERATIONS.map(normalizeDeliberation));
        setUsingSampleData(true);
      }
    } catch (err) {
      console.error('Error loading deliberations:', err);
      setDeliberations(SAMPLE_DELIBERATIONS.map(normalizeDeliberation));
      setUsingSampleData(true);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = (id) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const formatDate = (isoString) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString('es-MX', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  const getAgentColor = (agentId) => {
    return AGENT_COLORS[agentId] || '#6366f1';
  };

  const getAgentName = (agentId) => {
    return AGENT_NAMES[agentId] || agentId;
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScorePercentage = (decision) => {
    if (!decision) return 0;
    if (typeof decision === 'string') {
      try {
        decision = JSON.parse(decision);
      } catch {
        return 0;
      }
    }
    return decision.score || 0;
  };

  const getApprovalStatus = (decision) => {
    if (!decision) return { approved: false, label: 'Pendiente' };
    if (typeof decision === 'string') {
      try {
        decision = JSON.parse(decision);
      } catch {
        return { approved: false, label: 'Pendiente' };
      }
    }
    const approved = decision.aprobado || decision.approved;
    return {
      approved,
      label: approved ? 'Aprobado' : 'Rechazado'
    };
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 space-y-4">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Historial de Deliberaciones
        </h2>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse"></div>
            <div className="h-3 bg-gray-100 rounded w-1/2 animate-pulse"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!deliberations || deliberations.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 text-center">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Historial de Deliberaciones
        </h2>
        <p className="text-gray-500">No hay deliberaciones aún</p>
      </div>
    );
  }

  const sortedDeliberations = [...deliberations].sort((a, b) => {
    const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
    const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
    return dateA - dateB;
  });

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Historial de Deliberaciones
        </h2>
        {usingSampleData && (
          <div className="text-xs bg-amber-50 text-amber-700 px-3 py-1 rounded-full">
            Datos de ejemplo
          </div>
        )}
      </div>

      <div className="space-y-0 relative">
        {sortedDeliberations.map((deliberation, index) => {
          const isExpanded = expandedItems.has(deliberation.id);
          const agentColor = getAgentColor(deliberation.agente_id);
          const agentName = getAgentName(deliberation.agente_id);
          const status = getApprovalStatus(deliberation.decision);
          const score = getScorePercentage(deliberation.decision);
          const scoreColor = getScoreColor(score);

          return (
            <div key={deliberation.id} className="relative pb-6">
              {/* Timeline connector line */}
              {index < sortedDeliberations.length - 1 && (
                <div
                  className="absolute left-6 top-16 bottom-0 w-0.5 bg-gray-200"
                  style={{ height: 'calc(100% + 24px)' }}
                />
              )}

              {/* Timeline dot and content */}
              <div className="flex gap-4">
                {/* Timeline dot */}
                <div className="flex flex-col items-center pt-1">
                  <div
                    className="w-12 h-12 rounded-full flex items-center justify-center text-white font-semibold text-sm ring-4 ring-white shadow-md"
                    style={{ backgroundColor: agentColor }}
                  >
                    {deliberation.agente_id}
                  </div>
                </div>

                {/* Content card */}
                <div className="flex-1 pt-1">
                  <button
                    onClick={() => toggleExpanded(deliberation.id)}
                    className="w-full text-left hover:bg-gray-50 transition-colors p-3 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        {/* Header: Phase and Agent */}
                        <div className="flex items-center gap-2 mb-2">
                          <span className="inline-block px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-semibold rounded">
                            F{deliberation.fase}
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {agentName}
                          </span>
                          <span
                            className={`inline-block px-2 py-1 text-xs font-semibold rounded ${
                              status.approved
                                ? 'bg-green-100 text-green-700'
                                : 'bg-red-100 text-red-700'
                            }`}
                          >
                            {status.label}
                          </span>
                        </div>

                        {/* Summary */}
                        <p className="text-sm text-gray-700 mb-3">
                          {deliberation.resumen}
                        </p>

                        {/* Score progress bar */}
                        <div className="mb-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-gray-500">Puntuación</span>
                            <span className="text-xs font-semibold text-gray-700">
                              {score}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-all ${scoreColor}`}
                              style={{ width: `${Math.min(score, 100)}%` }}
                            />
                          </div>
                        </div>

                        {/* Timestamp */}
                        <p className="text-xs text-gray-500">
                          {formatDate(deliberation.created_at)}
                        </p>
                      </div>

                      {/* Expand icon */}
                      <div className="ml-3 flex-shrink-0">
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </div>
                  </button>

                  {/* Expanded details */}
                  {isExpanded && (
                    <div className="mt-2 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                      <h4 className="text-sm font-semibold text-gray-900 mb-3">
                        Detalles Completos
                      </h4>
                      <div className="bg-white p-3 rounded border border-gray-200 text-xs overflow-auto max-h-96">
                        <pre className="text-gray-600 whitespace-pre-wrap break-words">
                          {JSON.stringify(deliberation, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DeliberationTimeline;
