import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';

// SYNCED WITH: backend/config/agents_registry.py (18 agents total)
// This is the fallback static list when API is unavailable
const AGENTS = [
  // === AGENTES PRINCIPALES (7) ===
  { id: 'A1', fullId: 'A1_SPONSOR', name: 'María Rodríguez', icon: '🎯', color: 'indigo', description: 'Sponsor / Evaluador Estratégico - Evalúa razón de negocios y BEE', type: 'principal' },
  { id: 'A2', fullId: 'A2_PMO', name: 'Carlos Mendoza', icon: '📋', color: 'blue', description: 'Orquestador del Proceso F0-F9 - Controla flujo y candados', type: 'principal' },
  { id: 'A3', fullId: 'A3_FISCAL', name: 'Laura Sánchez', icon: '⚖️', color: 'purple', description: 'Especialista en Cumplimiento Fiscal - 4 pilares, VBC Fiscal', type: 'principal' },
  { id: 'A4', fullId: 'A4_LEGAL', name: 'Ana García', icon: '📜', color: 'red', description: 'Especialista en Contratos y Trazabilidad - SOW, VBC Legal', type: 'principal' },
  { id: 'A5', fullId: 'A5_FINANZAS', name: 'Roberto Sánchez', icon: '💰', color: 'emerald', description: 'Director Financiero - Proporción económica, 3-way match', type: 'principal' },
  { id: 'A6', fullId: 'A6_PROVEEDOR', name: 'Due Diligence', icon: '🔍', color: 'yellow', description: 'Validador de Proveedores - Entregables y evidencias', type: 'principal' },
  { id: 'A7', fullId: 'A7_DEFENSA', name: 'Laura Vázquez', icon: '🛡️', color: 'orange', description: 'Directora de Defense File - Expediente y defendibilidad', type: 'principal' },
  // === AGENTES ESPECIALIZADOS (3) ===
  { id: 'A8', fullId: 'A8_AUDITOR', name: 'Diego Ramírez', icon: '📊', color: 'cyan', description: 'Auditor Documental - Estructura y completitud', type: 'especializado' },
  { id: 'KB', fullId: 'KB_CURATOR', name: 'Dra. Elena Vázquez', icon: '📚', color: 'violet', description: 'Curadora de Conocimiento - RAG normativa', type: 'especializado' },
  { id: 'DA', fullId: 'DEVILS_ADVOCATE', name: 'Abogado del Diablo', icon: '😈', color: 'gray', description: 'Control Interno - Cuestionamiento sistemático', type: 'especializado' },
  // === SUBAGENTES FISCALES (3) - Reportan a A3_FISCAL ===
  { id: 'S1', fullId: 'S1_TIPIFICACION', name: 'Patricia López', icon: '🏷️', color: 'pink', description: 'Clasificador de Tipología - Asigna tipo de servicio', type: 'subagente', parent: 'A3_FISCAL' },
  { id: 'S2', fullId: 'S2_MATERIALIDAD', name: 'Fernando Ruiz', icon: '📎', color: 'teal', description: 'Especialista en Materialidad - Art. 69-B CFF', type: 'subagente', parent: 'A3_FISCAL' },
  { id: 'S3', fullId: 'S3_RIESGOS', name: 'Gabriela Vega', icon: '⚠️', color: 'red', description: 'Detector de Riesgos - EFOS, precios de transferencia', type: 'subagente', parent: 'A3_FISCAL' },
  // === SUBAGENTES PMO (5) - Reportan a A2_PMO ===
  { id: 'SA', fullId: 'S_ANALIZADOR', name: 'Subagente Analizador', icon: '🔬', color: 'blue', description: 'Análisis de Datos - Extrae datos de documentos', type: 'subagente', parent: 'A2_PMO' },
  { id: 'SC', fullId: 'S_CLASIFICADOR', name: 'Subagente Clasificador', icon: '📁', color: 'blue', description: 'Clasificación por Severidad - Issues por tipo', type: 'subagente', parent: 'A2_PMO' },
  { id: 'SR', fullId: 'S_RESUMIDOR', name: 'Subagente Resumidor', icon: '📝', color: 'blue', description: 'Compresión y Resumen - Resúmenes ejecutivos', type: 'subagente', parent: 'A2_PMO' },
  { id: 'SV', fullId: 'S_VERIFICADOR', name: 'Subagente Verificador', icon: '✅', color: 'green', description: 'Control de Calidad - Completitud y calidad', type: 'subagente', parent: 'A2_PMO' },
  { id: 'SRD', fullId: 'S_REDACTOR', name: 'Subagente Redactor', icon: '✍️', color: 'blue', description: 'Redacción de Documentos - Documentos formales', type: 'subagente', parent: 'A2_PMO' },
];

const AgentCard = ({ agent, active, completed, onClick }) => {
  const baseStyles = "relative p-4 rounded-xl border-2 cursor-pointer transition-all duration-300 hover:shadow-lg";
  
  let statusStyles = "border-gray-200 bg-white hover:border-gray-300";
  if (active) {
    statusStyles = "border-blue-500 bg-blue-50 scale-105 shadow-lg";
  } else if (completed) {
    statusStyles = "border-green-500 bg-green-50";
  }

  return (
    <button
      onClick={() => onClick(agent)}
      className={`${baseStyles} ${statusStyles}`}
    >
      <div className="text-3xl mb-2">{agent.icon}</div>
      <div className="font-semibold text-gray-900 text-sm">{agent.name}</div>
      <div className="text-xs text-gray-500 mt-1">{agent.id}</div>
      
      {active && (
        <div className="absolute -top-1 -right-1 w-4 h-4">
          <span className="absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75 animate-ping"></span>
          <span className="relative inline-flex rounded-full h-4 w-4 bg-blue-500"></span>
        </div>
      )}
      
      {completed && (
        <div className="absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
          <span className="text-white text-xs font-bold">✓</span>
        </div>
      )}
    </button>
  );
};

const AgentDetail = ({ agent, onClose }) => {
  if (!agent) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-4xl">{agent.icon}</span>
            <div>
              <h3 className="text-xl font-bold text-gray-900">{agent.name}</h3>
              <p className="text-sm text-gray-500">{agent.fullId}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>
        
        <p className="text-gray-600 mb-4">{agent.description}</p>
        
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <h4 className="font-semibold text-gray-900 mb-2">Funciones principales:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Análisis especializado</li>
            <li>• Validación de documentos</li>
            <li>• Generación de reportes</li>
            <li>• Scoring de compliance</li>
          </ul>
        </div>
        
        <button
          onClick={onClose}
          className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  );
};

export default function AgentPanel({ 
  activeAgents = [], 
  completedAgents = [],
  onAgentSelect,
  showProgress = true,
  selectable = true,
}) {
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [detailAgent, setDetailAgent] = useState(null);
  const [apiAgents, setApiAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        // Use api service (includes auth headers) - data from unified registry
        const data = await api.get('/api/agents/available');
        const fetchedAgents = data.agents || [];
        if (fetchedAgents.length > 0) {
          const mergedAgents = fetchedAgents.map(apiAgent => {
            // Match by agent_id from unified registry
            const staticAgent = AGENTS.find(a => a.fullId === apiAgent.agent_id);
            return {
              id: apiAgent.agent_id.split('_')[0] || apiAgent.agent_id,
              fullId: apiAgent.agent_id,
              name: apiAgent.name || staticAgent?.name || apiAgent.agent_id,
              icon: apiAgent.icon || staticAgent?.icon || '🤖',
              description: apiAgent.description || staticAgent?.description || '',
              color: apiAgent.color || staticAgent?.color || 'gray',
              type: apiAgent.type || staticAgent?.type || 'principal',
              role: apiAgent.role || staticAgent?.description || '',
              parent: apiAgent.parent_agent || staticAgent?.parent || null,
            };
          });
          setApiAgents(mergedAgents);
        }
      } catch (error) {
        console.error('Error fetching agents from registry:', error);
        // Fallback to static AGENTS list is automatic (displayAgents logic)
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();
  }, []);

  const toggleAgent = useCallback((agent) => {
    if (!selectable) {
      setDetailAgent(agent);
      return;
    }
    
    setSelectedAgents(prev => {
      const isSelected = prev.includes(agent.fullId);
      const newSelection = isSelected 
        ? prev.filter(id => id !== agent.fullId)
        : [...prev, agent.fullId];
      
      if (onAgentSelect) {
        onAgentSelect(newSelection);
      }
      
      return newSelection;
    });
  }, [selectable, onAgentSelect]);

  const isActive = (agentId) => activeAgents.includes(agentId) || activeAgents.includes(agentId.split('_')[0]);
  const isCompleted = (agentId) => completedAgents.includes(agentId) || completedAgents.includes(agentId.split('_')[0]);

  const displayAgents = apiAgents.length > 0 ? apiAgents : AGENTS;
  const progressPercent = (completedAgents.length / displayAgents.length) * 100;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">🤖 Panel de Agentes</h2>
          <p className="text-sm text-gray-500 mt-1">
            {selectable 
              ? `${selectedAgents.length} agentes seleccionados`
              : `${completedAgents.length}/${displayAgents.length} agentes completados`
            }
          </p>
        </div>
        
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-gray-300"></span>
            Inactivo
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            Activo
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            Completado
          </span>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        {displayAgents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            active={isActive(agent.fullId) || selectedAgents.includes(agent.fullId)}
            completed={isCompleted(agent.fullId)}
            onClick={toggleAgent}
          />
        ))}
      </div>

      {showProgress && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progreso del análisis</span>
            <span>{completedAgents.length}/{AGENTS.length} agentes</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {selectable && selectedAgents.length > 0 && (
        <div className="mt-4 p-4 bg-blue-50 rounded-xl">
          <h4 className="font-semibold text-blue-900 mb-2">Agentes seleccionados:</h4>
          <div className="flex flex-wrap gap-2">
            {selectedAgents.map(id => {
              const agent = displayAgents.find(a => a.fullId === id);
              return (
                <span 
                  key={id}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                >
                  {agent?.icon} {agent?.name}
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleAgent(agent);
                    }}
                    className="ml-1 text-blue-400 hover:text-blue-600"
                  >
                    ×
                  </button>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {loading && (
        <div className="mt-4 text-center text-gray-500 text-sm">
          Cargando información de agentes...
        </div>
      )}

      <AgentDetail agent={detailAgent} onClose={() => setDetailAgent(null)} />
    </div>
  );
}
