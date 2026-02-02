import React, { useState } from 'react';

// === PREMIUM AGENT CONFIGURATION (18 AGENTS) ===
// Organized by "Clusters" for better visual flow
const AGENTS_CONFIG = [
  // --- CLUSTER 1: STRATEGIC CORE (La "Mesa Directiva") ---
  { id: 'A1', name: 'Sponsor / Estrategia', emoji: '🎯', color: '#34d399', group: 'Strategic', role: 'Define objetivos y evalúa riesgo global' },
  { id: 'A2', name: 'PMO / Orquestador', emoji: '📋', color: '#6366f1', group: 'Strategic', role: 'Coordina el flujo F0-F9' },
  { id: 'A5', name: 'Director Financiero', emoji: '💰', color: '#ec4899', group: 'Strategic', role: 'Aprueba presupuestos y ROI' },

  // --- CLUSTER 2: FISCAL & LEGAL (El "Cerebro Técnico") ---
  { id: 'A3', name: 'Fiscal (Tax)', emoji: '⚖️', color: '#a855f7', group: 'Fiscal', role: 'Cumplimiento Código Fiscal' },
  { id: 'S1', name: 'Tipificación', emoji: '🏷️', color: '#c084fc', group: 'Fiscal', role: 'Sub-agente: Clasifica operación' },
  { id: 'S2', name: 'Materialidad', emoji: '📎', color: '#d8b4fe', group: 'Fiscal', role: 'Sub-agente: Revisa pruebas' },
  { id: 'S3', name: 'Riesgos', emoji: '⚠️', color: '#f3e8ff', group: 'Fiscal', role: 'Sub-agente: Detecta anomalías' },
  { id: 'A4', name: 'Legal / Contratos', emoji: '📜', color: '#f97316', group: 'Fiscal', role: 'Validez contractual' },
  { id: 'A7', name: 'Defense File', emoji: '🛡️', color: '#f43f5e', group: 'Fiscal', role: 'Integra expediente de defensa' },

  // --- CLUSTER 3: OPERATIONAL & AUDIT (Los "Ojos y Manos") ---
  { id: 'A6', name: 'Due Diligence', emoji: '🔍', color: '#06b6d4', group: 'Operational', role: 'Valida proveedores (69-B)' },
  { id: 'A8', name: 'Red Team', emoji: '😈', color: '#eab308', group: 'Operational', role: 'Auditoría agresiva (Simulación SAT)' },
  { id: 'KB', name: 'Curator', emoji: '📚', color: '#22c55e', group: 'Operational', role: 'Gestión de Conocimiento' },
  { id: 'A9', name: 'Síntesis', emoji: '📝', color: '#84cc16', group: 'Operational', role: 'Resumen Ejecutivo' },
  { id: 'A10', name: 'Archivo', emoji: '📁', color: '#10b981', group: 'Operational', role: 'Resguardo Final' },

  // --- CLUSTER 4: ANALYTICS SUB-AGENTS (PMO Support) ---
  { id: 'SA', name: 'Analizador', emoji: '🔬', color: '#94a3b8', group: 'Support', role: 'Análisis de datos crudos' },
  { id: 'SC', name: 'Clasificador', emoji: '📁', color: '#cbd5e1', group: 'Support', role: 'Priorización de tareas' },
  { id: 'SR', name: 'Resumidor', emoji: '📝', color: '#e2e8f0', group: 'Support', role: 'Compresión de textos' },
  { id: 'SV', name: 'Verificador', emoji: '✅', color: '#f1f5f9', group: 'Support', role: 'QA Final' },
];

/**
 * AgentNode Component - Premium "Glass" Style
 */
const AgentNode = ({ agent, status, onAgentClick, isSelected }) => {
  const isInactive = status === 'idle';

  return (
    <div
      onClick={() => onAgentClick && onAgentClick(agent)}
      className={`
        relative group cursor-pointer transition-all duration-300 ease-out-expo
        flex flex-col items-center justify-center p-3
        rounded-2xl border backdrop-blur-md
        ${isSelected
          ? 'ring-2 ring-primary ring-offset-2 ring-offset-white scale-105 z-10'
          : 'hover:scale-105 hover:bg-white/40 z-0'
        }
        ${status === 'active'
          ? 'bg-blue-50/80 border-blue-200 shadow-lg shadow-blue-500/20'
          : status === 'completed'
            ? 'bg-green-50/80 border-green-200 shadow-sm'
            : status === 'error'
              ? 'bg-red-50/80 border-red-200'
              : 'bg-white/40 border-white/20 hover:border-white/60'
        }
      `}
      style={{
        width: '100px',
        height: '110px',
        opacity: isInactive ? 0.7 : 1
      }}
    >
      {/* Active Ping Animation */}
      {status === 'active' && (
        <span className="absolute -top-1 -right-1 flex h-4 w-4">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-4 w-4 bg-blue-500"></span>
        </span>
      )}

      {/* Completed Checkmark */}
      {status === 'completed' && (
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-sm">
          ✓
        </span>
      )}

      {/* Emoji Icon */}
      <div
        className={`text-4xl mb-2 transition-transform duration-300 ${status === 'active' ? 'scale-110 animate-pulse' : 'group-hover:scale-110'}`}
        style={{ filter: isInactive ? 'grayscale(0.8)' : 'none' }}
      >
        {agent.emoji}
      </div>

      {/* Agent ID & Name */}
      <div className="text-center w-full">
        <div className={`text-xs font-bold tracking-tight ${status === 'active' ? 'text-blue-700' : 'text-gray-700'}`}>
          {agent.id}
        </div>
        <div className="text-[10px] leading-tight text-gray-500 font-medium truncate w-full px-1">
          {agent.name}
        </div>
      </div>

      {/* Status Bar Indicator */}
      <div className="absolute bottom-0 left-0 right-0 h-1 rounded-b-2xl overflow-hidden">
        <div
          className="h-full transition-all duration-500"
          style={{
            width: status !== 'idle' ? '100%' : '0%',
            backgroundColor: agent.color
          }}
        />
      </div>
    </div>
  );
};

/**
 * Group Container - Visual Grouping for Clusters
 */
const AgentGroup = ({ title, agents, activeAgents, completedAgents, onAgentClick, selectedAgent }) => (
  <div className="bg-white/30 rounded-3xl p-4 border border-white/40 shadow-sm backdrop-blur-sm flex flex-col gap-3">
    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider px-2">{title}</h3>
    <div className="flex flex-wrap gap-3 justify-center">
      {agents.map(agent => (
        <AgentNode
          key={agent.id}
          agent={agent}
          status={
            completedAgents.includes(agent.id) ? 'completed'
              : activeAgents.includes(agent.id) ? 'active'
                : 'idle'
          }
          onAgentClick={onAgentClick}
          isSelected={selectedAgent?.id === agent.id}
        />
      ))}
    </div>
  </div>
);

/**
 * Main Visualization Component
 */
const AgentFlowVisualization = ({
  activeAgents = [],
  completedAgents = [],
  onAgentClick = null,
  showDetails = true,
}) => {
  const [selectedAgent, setSelectedAgent] = useState(null);

  const handleAgentClick = (agent) => {
    setSelectedAgent(agent);
    if (onAgentClick) onAgentClick(agent);
  };

  // Group Agents
  const strategicAgents = AGENTS_CONFIG.filter(a => a.group === 'Strategic');
  const fiscalAgents = AGENTS_CONFIG.filter(a => a.group === 'Fiscal');
  const operationalAgents = AGENTS_CONFIG.filter(a => a.group === 'Operational');
  const supportAgents = AGENTS_CONFIG.filter(a => a.group === 'Support');

  const totalAgents = AGENTS_CONFIG.length;
  // Fallback safe logic for division by zero
  const progressPercentage = totalAgents > 0 ? (completedAgents.length / totalAgents) * 100 : 0;

  return (
    <div className="w-full h-full flex flex-col gap-6 relative overflow-hidden bg-gray-50/50 rounded-3xl p-2">

      {/* Background Decorative Blobs */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-purple-200/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 pointer-events-none"></div>

      {/* Header & Progress */}
      <div className="flex items-center justify-between px-4 pt-2 z-10">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Neural Network</h2>
          <p className="text-sm text-gray-500 font-medium">{completedAgents.length} / {totalAgents} Agentes Activados</p>
        </div>

        {/* Apple-style Progress Bar */}
        <div className="w-48 bg-gray-100 rounded-full h-2 overflow-hidden shadow-inner">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-700 ease-out-quart"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Scrollable Canvas for Agent Clusters */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 z-10 custom-scrollbar">
        <div className="space-y-6 max-w-5xl mx-auto">

          {/* Top Row: Strategy */}
          <div className="flex justify-center">
            <AgentGroup
              title="Mesa Directiva (Estrategia)"
              agents={strategicAgents}
              activeAgents={activeAgents}
              completedAgents={completedAgents}
              onAgentClick={handleAgentClick}
              selectedAgent={selectedAgent}
            />
          </div>

          {/* Middle Row: Fiscal & Legal (Main Engine) */}
          <div className="flex justify-center">
            <AgentGroup
              title="Núcleo Fiscal y Legal"
              agents={fiscalAgents}
              activeAgents={activeAgents}
              completedAgents={completedAgents}
              onAgentClick={handleAgentClick}
              selectedAgent={selectedAgent}
            />
          </div>

          {/* Bottom Row: Operations & Support Split */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <AgentGroup
              title="Operaciones y Auditoría"
              agents={operationalAgents}
              activeAgents={activeAgents}
              completedAgents={completedAgents}
              onAgentClick={handleAgentClick}
              selectedAgent={selectedAgent}
            />
            <AgentGroup
              title="Soporte y Análisis de Datos"
              agents={supportAgents}
              activeAgents={activeAgents}
              completedAgents={completedAgents}
              onAgentClick={handleAgentClick}
              selectedAgent={selectedAgent}
            />
          </div>
        </div>
      </div>

      {/* Floating Detail Panel (Premium Glass Modal effect) */}
      {showDetails && selectedAgent && (
        <div className="absolute top-4 right-4 w-72 bg-white/90 backdrop-blur-xl border border-white/50 shadow-apple-lg rounded-2xl p-5 z-20 animate-scale-in">
          <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-2xl bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-100`}>
              <span className="text-3xl">{selectedAgent.emoji}</span>
            </div>
            <button
              onClick={() => setSelectedAgent(null)}
              className="text-gray-400 hover:text-gray-600 w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
            >
              ✕
            </button>
          </div>

          <h3 className="text-xl font-bold text-gray-900">{selectedAgent.name}</h3>
          <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider text-white" style={{ backgroundColor: selectedAgent.color }}>
            {selectedAgent.id}
          </span>

          <div className="mt-4 space-y-3">
            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase">Rol</label>
              <p className="text-sm text-gray-700 font-medium leading-snug">{selectedAgent.role}</p>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase">Estado</label>
              <div className="mt-1">
                {completedAgents.includes(selectedAgent.id)
                  ? <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-lg">✅ Completado</span>
                  : activeAgents.includes(selectedAgent.id)
                    ? <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-lg animate-pulse">⚡ Procesando...</span>
                    : <span className="text-xs font-bold text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">💤 Inactivo</span>
                }
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentFlowVisualization;
