import React, { useState, useEffect, useCallback } from 'react';

const AGENTS = [
  { id: 'A1', fullId: 'A1_RECEPCION', name: 'Recepción', icon: '📥', color: 'indigo', description: 'Clasificación y extracción de documentos' },
  { id: 'A2', fullId: 'A2_ANALISIS', name: 'Análisis', icon: '🔍', color: 'purple', description: 'Análisis fiscal y deducibilidad' },
  { id: 'A3', fullId: 'A3_NORMATIVO', name: 'Normativo', icon: '📜', color: 'violet', description: 'Normativa fiscal mexicana' },
  { id: 'A4', fullId: 'A4_CONTABLE', name: 'Contable', icon: '📊', color: 'green', description: 'Verificación contable NIF' },
  { id: 'A5', fullId: 'A5_OPERATIVO', name: 'Operativo', icon: '⚙️', color: 'yellow', description: 'Capacidad y materialidad' },
  { id: 'A6', fullId: 'A6_FINANCIERO', name: 'Financiero', icon: '💰', color: 'emerald', description: 'Análisis financiero' },
  { id: 'A7', fullId: 'A7_LEGAL', name: 'Legal', icon: '⚖️', color: 'red', description: 'Contratos y cláusulas' },
  { id: 'A8', fullId: 'A8_REDTEAM', name: 'Red Team', icon: '🛡️', color: 'orange', description: 'Simulación auditoría SAT' },
  { id: 'A9', fullId: 'A9_SINTESIS', name: 'Síntesis', icon: '📝', color: 'cyan', description: 'Dictamen final' },
  { id: 'A10', fullId: 'A10_ARCHIVO', name: 'Archivo', icon: '📁', color: 'gray', description: 'Archivo documental' },
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
        const response = await fetch('/api/agents/available');
        if (response.ok) {
          const data = await response.json();
          const fetchedAgents = data.agents || [];
          if (fetchedAgents.length > 0) {
            const mergedAgents = fetchedAgents.map(apiAgent => {
              const staticAgent = AGENTS.find(a => a.fullId === apiAgent.agent_id);
              return {
                id: apiAgent.agent_id.split('_')[0],
                fullId: apiAgent.agent_id,
                name: staticAgent?.name || apiAgent.agent_id.split('_')[1],
                icon: apiAgent.icon || staticAgent?.icon || '🤖',
                description: apiAgent.description || staticAgent?.description || '',
                color: staticAgent?.color || 'gray',
              };
            });
            setApiAgents(mergedAgents);
          }
        }
      } catch (error) {
        console.error('Error fetching agents:', error);
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
