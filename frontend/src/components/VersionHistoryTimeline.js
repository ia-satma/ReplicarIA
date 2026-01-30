import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const VersionHistoryTimeline = ({ projectId, currentProjectId }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedVersion, setExpandedVersion] = useState(null);

  useEffect(() => {
    const fetchVersions = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`/api/projects/${projectId}/versions`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Error al cargar historial');
        }
        
        const data = await response.json();
        setVersions(data.versions || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchVersions();
    }
  }, [projectId]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDecisionColor = (decision) => {
    switch (decision) {
      case 'approve':
      case 'approved':
        return 'bg-green-500';
      case 'request_adjustment':
      case 'requires_adjustment':
        return 'bg-amber-500';
      case 'reject':
      case 'rejected':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getDecisionLabel = (decision) => {
    switch (decision) {
      case 'approve':
      case 'approved':
        return 'Aprobado';
      case 'request_adjustment':
      case 'requires_adjustment':
        return 'Ajustes';
      case 'reject':
      case 'rejected':
        return 'Rechazado';
      default:
        return 'Pendiente';
    }
  };

  const getAgentName = (agentId) => {
    const names = {
      'A1_SPONSOR': 'Estrategia',
      'A3_FISCAL': 'Fiscal',
      'A5_FINANZAS': 'Finanzas',
      'LEGAL': 'Legal',
      'A2_PMO': 'PMO',
      'STRATEGY_COUNCIL': 'Consejo'
    };
    return names[agentId] || agentId;
  };

  const getComplianceColor = (score) => {
    if (score >= 75) return 'text-green-600 bg-green-100';
    if (score >= 50) return 'text-amber-600 bg-amber-100';
    return 'text-red-600 bg-red-100';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-100 p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-gray-500">Cargando historial...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl border border-gray-100 p-6">
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    );
  }

  if (versions.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Historial de Versiones</h3>
            <p className="text-sm text-gray-500">No hay versiones registradas aún</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-bold text-gray-900">Historial de Versiones</h3>
          <p className="text-sm text-gray-500">{versions.length} versiones del proyecto</p>
        </div>
      </div>

      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
        
        <div className="space-y-4">
          {versions.map((version, index) => {
            const isCurrentVersion = version.project_id === currentProjectId;
            const isExpanded = expandedVersion === version.project_id;
            const versionNumber = `v${version.version || index + 1}.0`;
            
            return (
              <div key={version.project_id} className="relative pl-10">
                <div className={`absolute left-2 w-5 h-5 rounded-full border-2 ${
                  isCurrentVersion 
                    ? 'bg-indigo-500 border-indigo-500' 
                    : version.final_decision === 'approved' 
                      ? 'bg-green-500 border-green-500'
                      : version.final_decision === 'rejected'
                        ? 'bg-red-500 border-red-500'
                        : 'bg-white border-gray-300'
                }`}>
                  {isCurrentVersion && (
                    <div className="absolute inset-0 rounded-full animate-ping bg-indigo-400 opacity-50"></div>
                  )}
                </div>
                
                <div 
                  className={`border rounded-xl p-4 transition-all cursor-pointer ${
                    isCurrentVersion 
                      ? 'border-indigo-300 bg-indigo-50/50 shadow-sm' 
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                  }`}
                  onClick={() => setExpandedVersion(isExpanded ? null : version.project_id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 rounded-lg text-sm font-bold ${
                        isCurrentVersion ? 'bg-indigo-500 text-white' : 'bg-gray-100 text-gray-700'
                      }`}>
                        {versionNumber}
                      </span>
                      
                      {isCurrentVersion && (
                        <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full">
                          Actual
                        </span>
                      )}
                      
                      {version.is_adjustment && (
                        <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">
                          Ajuste
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded-lg text-sm font-semibold ${getComplianceColor(version.compliance_score)}`}>
                        {version.compliance_score}%
                      </span>
                      
                      <svg 
                        className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">{formatDate(version.created_at)}</p>
                  
                  <div className="flex items-center gap-1">
                    {version.agent_states && version.agent_states.map((agent, idx) => (
                      <div 
                        key={idx}
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${getDecisionColor(agent.decision)}`}
                        title={`${getAgentName(agent.agent_id)}: ${getDecisionLabel(agent.decision)}`}
                      >
                        {getAgentName(agent.agent_id).charAt(0)}
                      </div>
                    ))}
                    {(!version.agent_states || version.agent_states.length === 0) && (
                      <span className="text-xs text-gray-400">Sin deliberaciones</span>
                    )}
                  </div>
                  
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-semibold text-gray-700 mb-3">Estado de Agentes</h4>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {version.agent_states && version.agent_states.map((agent, idx) => (
                          <div 
                            key={idx}
                            className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg"
                          >
                            <div className={`w-3 h-3 rounded-full ${getDecisionColor(agent.decision)}`}></div>
                            <div>
                              <p className="text-xs font-medium text-gray-700">{getAgentName(agent.agent_id)}</p>
                              <p className="text-xs text-gray-500">{getDecisionLabel(agent.decision)}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      {version.adjustment_notes && (
                        <div className="mt-3 p-3 bg-amber-50 rounded-lg">
                          <p className="text-xs font-medium text-amber-800 mb-1">Notas de ajuste:</p>
                          <p className="text-xs text-amber-700">{version.adjustment_notes}</p>
                        </div>
                      )}
                      
                      {!isCurrentVersion && version.project_id && (
                        <Link
                          to={`/project/${version.project_id}`}
                          className="mt-3 inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                        >
                          Ver esta versión
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </Link>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default VersionHistoryTimeline;
