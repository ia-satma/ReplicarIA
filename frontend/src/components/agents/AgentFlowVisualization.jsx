import React, { useState } from 'react';

// Agent configuration with all 10 agents
const AGENTS_CONFIG = [
  { id: 'A1', name: 'Recepción', emoji: '📥', color: '#6366f1' },
  { id: 'A2', name: 'Análisis', emoji: '🔍', color: '#8b5cf6' },
  { id: 'A3', name: 'Normativo', emoji: '📜', color: '#a855f7' },
  { id: 'A4', name: 'Contable', emoji: '📊', color: '#d946ef' },
  { id: 'A5', name: 'Operativo', emoji: '⚙️', color: '#ec4899' },
  { id: 'A6', name: 'Financiero', emoji: '💰', color: '#f43f5e' },
  { id: 'A7', name: 'Legal', emoji: '⚖️', color: '#f97316' },
  { id: 'A8', name: 'Red Team', emoji: '🛡️', color: '#eab308' },
  { id: 'A9', name: 'Síntesis', emoji: '📝', color: '#84cc16' },
  { id: 'A10', name: 'Archivo', emoji: '📁', color: '#22c55e' },
];

/**
 * AgentNode Sub-component
 * Displays individual agent nodes with status indicators and animations
 */
const AgentNode = ({ agent, status, onAgentClick, isSelected }) => {
  const getNodeClasses = () => {
    const baseClasses = 'relative w-28 h-28 rounded-lg border-2 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 hover:scale-110 hover:shadow-xl';
    
    switch (status) {
      case 'active':
        return `${baseClasses} border-blue-500 bg-blue-50 animate-pulse`;
      case 'completed':
        return `${baseClasses} border-green-500 bg-green-50`;
      case 'error':
        return `${baseClasses} border-red-500 bg-red-50`;
      case 'idle':
      default:
        return `${baseClasses} border-gray-300 bg-gray-100`;
    }
  };

  const getTextColor = () => {
    switch (status) {
      case 'active':
        return 'text-blue-700';
      case 'completed':
        return 'text-green-700';
      case 'error':
        return 'text-red-700';
      case 'idle':
      default:
        return 'text-gray-700';
    }
  };

  const ringClasses = isSelected ? 'ring-2 ring-offset-2 ring-indigo-500' : '';

  return (
    <div
      onClick={() => onAgentClick && onAgentClick(agent)}
      className={`${getNodeClasses()} ${ringClasses}`}
    >
      {/* Ping animation for active state */}
      {status === 'active' && (
        <div className="absolute top-2 right-2 w-3 h-3">
          <div className="absolute inset-0 bg-blue-500 rounded-full animate-ping"></div>
          <div className="absolute inset-0 bg-blue-500 rounded-full opacity-75"></div>
        </div>
      )}

      {/* Checkmark badge for completed state */}
      {status === 'completed' && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center shadow-md">
          <span className="text-white text-sm font-bold">✓</span>
        </div>
      )}

      {/* Error indicator */}
      {status === 'error' && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center shadow-md">
          <span className="text-white text-sm font-bold">!</span>
        </div>
      )}

      {/* Agent emoji */}
      <div className="text-4xl mb-2">{agent.emoji}</div>

      {/* Agent ID */}
      <div className={`text-sm font-bold ${getTextColor()}`}>{agent.id}</div>

      {/* Agent name (smaller) */}
      <div className={`text-xs mt-1 ${getTextColor()} font-medium`}>{agent.name}</div>
    </div>
  );
};

/**
 * AgentFlowVisualization Component
 * Main component displaying a 5x2 grid of agents with status tracking and details panel
 */
const AgentFlowVisualization = ({
  activeAgents = [],
  completedAgents = [],
  onAgentClick = null,
  showDetails = true,
}) => {
  const [selectedAgent, setSelectedAgent] = useState(null);

  /**
   * Determine agent status based on active and completed arrays
   */
  const getAgentStatus = (agentId) => {
    if (completedAgents.includes(agentId)) return 'completed';
    if (activeAgents.includes(agentId)) return 'active';
    return 'idle';
  };

  /**
   * Handle agent click - update selection and call parent callback
   */
  const handleAgentClick = (agent) => {
    setSelectedAgent(agent);
    if (onAgentClick) {
      onAgentClick(agent);
    }
  };

  // Calculate progress percentage
  const progressPercentage = (completedAgents.length / 10) * 100;

  return (
    <div className="w-full h-full bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-8 flex flex-col gap-6">
      {/* Header Section */}
      <div className="space-y-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Flujo de Agentes</h2>
          <p className="text-sm text-gray-600 mt-1">Seguimiento del estado de procesamiento de todos los agentes</p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-6 bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-100 rounded border-2 border-gray-300"></div>
            <span className="text-sm font-medium text-gray-700">Inactivo</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-50 rounded border-2 border-blue-500 animate-pulse"></div>
            <span className="text-sm font-medium text-gray-700">Procesando</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-50 rounded border-2 border-green-500"></div>
            <span className="text-sm font-medium text-gray-700">Completado</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-50 rounded border-2 border-red-500"></div>
            <span className="text-sm font-medium text-gray-700">Error</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">Progreso general</span>
            <span className="text-sm font-semibold text-gray-900">
              {completedAgents.length} / {AGENTS_CONFIG.length}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Grid of Agents - 5x2 layout */}
        <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 p-6 overflow-auto">
          <div className="grid grid-cols-5 gap-6 w-fit">
            {AGENTS_CONFIG.map((agent) => (
              <AgentNode
                key={agent.id}
                agent={agent}
                status={getAgentStatus(agent.id)}
                onAgentClick={handleAgentClick}
                isSelected={selectedAgent?.id === agent.id}
              />
            ))}
          </div>
        </div>

        {/* Details Panel */}
        {showDetails && selectedAgent && (
          <div className="w-80 bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col overflow-hidden">
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">{selectedAgent.id}</h3>
                <p className="text-sm font-medium text-indigo-600 mt-1">{selectedAgent.name}</p>
              </div>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors text-xl font-semibold"
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 space-y-6 overflow-y-auto">
              {/* Emoji */}
              <div className="flex justify-center">
                <div className="text-6xl">{selectedAgent.emoji}</div>
              </div>

              {/* Status Badge */}
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase block mb-2">
                  Estado actual
                </label>
                <div>
                  {(() => {
                    const status = getAgentStatus(selectedAgent.id);
                    const statusConfig = {
                      completed: { label: 'Completado', bg: 'bg-green-500', text: 'text-white' },
                      active: { label: 'Procesando', bg: 'bg-blue-500', text: 'text-white' },
                      error: { label: 'Error', bg: 'bg-red-500', text: 'text-white' },
                      idle: { label: 'Inactivo', bg: 'bg-gray-400', text: 'text-white' },
                    };
                    const config = statusConfig[status] || statusConfig.idle;
                    return (
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${config.bg} ${config.text}`}>
                        {config.label}
                      </span>
                    );
                  })()}
                </div>
              </div>

              {/* Color Identifier */}
              <div className="pt-4 border-t border-gray-200">
                <label className="text-xs font-semibold text-gray-500 uppercase block mb-2">
                  Color identificador
                </label>
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded border-2 border-gray-300 shadow-sm"
                    style={{ backgroundColor: selectedAgent.color }}
                  ></div>
                  <div className="flex flex-col">
                    <code className="text-sm font-mono text-gray-700 font-semibold">{selectedAgent.color}</code>
                    <span className="text-xs text-gray-500 mt-1">Hex Color</span>
                  </div>
                </div>
              </div>

              {/* Additional Info */}
              <div className="pt-4 border-t border-gray-200">
                <label className="text-xs font-semibold text-gray-500 uppercase block mb-2">
                  Información
                </label>
                <div className="space-y-2 text-sm text-gray-700">
                  <p>
                    <span className="font-semibold">ID:</span> {selectedAgent.id}
                  </p>
                  <p>
                    <span className="font-semibold">Nombre:</span> {selectedAgent.name}
                  </p>
                  <p>
                    <span className="font-semibold">Orden:</span> Posición {AGENTS_CONFIG.findIndex((a) => a.id === selectedAgent.id) + 1} de 10
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentFlowVisualization;
