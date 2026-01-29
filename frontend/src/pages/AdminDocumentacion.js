import React, { useState, useEffect } from 'react';
import api from '../services/api';

const BookOpenIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
  </svg>
);

const BotIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2"/>
    <circle cx="12" cy="5" r="2"/>
    <path d="M12 7v4"/>
    <line x1="8" y1="16" x2="8" y2="16"/>
    <line x1="16" y1="16" x2="16" y2="16"/>
  </svg>
);

const ChartIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10"/>
    <line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6" y1="20" x2="6" y2="14"/>
  </svg>
);

const LockIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
);

const ShieldIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    <path d="M9 12l2 2 4-4"/>
  </svg>
);

const MoonIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
);

const SunIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5"/>
    <line x1="12" y1="1" x2="12" y2="3"/>
    <line x1="12" y1="21" x2="12" y2="23"/>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
    <line x1="1" y1="12" x2="3" y2="12"/>
    <line x1="21" y1="12" x2="23" y2="12"/>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
  </svg>
);

const ChevronDownIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 12 15 18 9"/>
  </svg>
);

const ChevronUpIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="18 15 12 9 6 15"/>
  </svg>
);

const DownloadIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);

const PlusIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"/>
    <line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);

const RefreshIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
);

const AlertTriangleIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
    <line x1="12" y1="9" x2="12" y2="13"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
);

const LayersIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 2 7 12 12 22 7 12 2"/>
    <polyline points="2 17 12 22 22 17"/>
    <polyline points="2 12 12 17 22 12"/>
  </svg>
);

const ClockIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
);

const TargetIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <circle cx="12" cy="12" r="6"/>
    <circle cx="12" cy="12" r="2"/>
  </svg>
);

function KPICard({ title, value, subtitle, icon: Icon, gradient, delay = "0", valueColor }) {
  return (
    <div 
      className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl p-6 shadow-lg shadow-slate-200/50 dark:shadow-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 animate-fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
          <p className={`text-3xl font-bold mt-1 ${valueColor || 'text-slate-800 dark:text-slate-100'}`}>{value}</p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{subtitle}</p>
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}

function AgentCard({ agent, onDownloadMarkdown }) {
  const [expanded, setExpanded] = useState(false);
  
  const typeColors = {
    principal: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    subagent: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
  };
  
  return (
    <div className={`bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl rounded-xl border ${agent.can_block ? 'border-red-300 dark:border-red-700' : 'border-slate-200/50 dark:border-slate-700/50'} overflow-hidden transition-all duration-300`}>
      <div 
        className="p-4 cursor-pointer flex items-center justify-between hover:bg-slate-50/50 dark:hover:bg-slate-700/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${agent.type === 'principal' ? 'from-blue-500 to-indigo-600' : 'from-purple-500 to-violet-600'} flex items-center justify-center`}>
            <BotIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-slate-800 dark:text-slate-100">{agent.agent_id}</h3>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${typeColors[agent.type] || typeColors.principal}`}>
                {agent.type === 'principal' ? 'Principal' : 'Subagente'}
              </span>
              {agent.can_block && (
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 flex items-center gap-1">
                  <AlertTriangleIcon className="w-3 h-3" />
                  Bloqueante
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">{agent.role}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDownloadMarkdown(agent.agent_id);
            }}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            title="Descargar documentación"
          >
            <DownloadIcon className="w-4 h-4 text-slate-500 dark:text-slate-400" />
          </button>
          {expanded ? (
            <ChevronUpIcon className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDownIcon className="w-5 h-5 text-slate-400" />
          )}
        </div>
      </div>
      
      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-200/50 dark:border-slate-700/50 pt-4 animate-fade-in">
          <p className="text-sm text-slate-600 dark:text-slate-300 mb-4">{agent.description}</p>
          
          {agent.phases && agent.phases.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Fases</h4>
              <div className="flex flex-wrap gap-2">
                {agent.phases.map((phase, idx) => (
                  <span key={idx} className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-xs text-slate-600 dark:text-slate-300">
                    {phase}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {agent.capabilities && agent.capabilities.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Capacidades</h4>
              <div className="space-y-2">
                {agent.capabilities.map((cap, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <div className={`w-2 h-2 rounded-full mt-1.5 ${cap.can_block ? 'bg-red-500' : 'bg-green-500'}`}></div>
                    <div>
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{cap.name}</span>
                      {cap.description && (
                        <p className="text-xs text-slate-500 dark:text-slate-400">{cap.description}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {agent.controls && agent.controls.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Controles</h4>
              <div className="space-y-2">
                {agent.controls.map((control, idx) => (
                  <div key={idx} className="p-2 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <LockIcon className="w-3 h-3 text-amber-500" />
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{control.name}</span>
                      <span className="text-xs text-slate-400">({control.phase})</span>
                    </div>
                    {control.condition && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 ml-5">{control.condition}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PhaseCard({ phase, index }) {
  return (
    <div className={`relative flex items-start gap-4 ${index < 9 ? 'pb-8' : ''}`}>
      {index < 9 && (
        <div className="absolute left-5 top-10 w-0.5 h-full bg-gradient-to-b from-slate-300 to-transparent dark:from-slate-600"></div>
      )}
      
      <div className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center ${
        phase.is_hard_lock 
          ? 'bg-gradient-to-br from-red-500 to-rose-600 shadow-lg shadow-red-500/30' 
          : 'bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/30'
      }`}>
        {phase.is_hard_lock ? (
          <LockIcon className="w-5 h-5 text-white" />
        ) : (
          <span className="text-white font-bold text-sm">{phase.phase_id}</span>
        )}
      </div>
      
      <div className="flex-1 bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl rounded-xl p-4 border border-slate-200/50 dark:border-slate-700/50">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">{phase.phase_id}: {phase.name}</h3>
          {phase.is_hard_lock && (
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300">
              Candado Duro
            </span>
          )}
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-300 mb-2">{phase.description}</p>
        {phase.lock_condition && (
          <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <p className="text-xs text-red-700 dark:text-red-300 flex items-center gap-1">
              <LockIcon className="w-3 h-3" />
              {phase.lock_condition}
            </p>
          </div>
        )}
        {phase.required_agents && phase.required_agents.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {phase.required_agents.map((agent, idx) => (
              <span key={idx} className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-xs text-slate-600 dark:text-slate-300">
                {agent}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function PillarCard({ pillar }) {
  const gradients = [
    'from-blue-500 to-indigo-600',
    'from-green-500 to-emerald-600',
    'from-purple-500 to-violet-600',
    'from-amber-500 to-orange-600'
  ];
  
  return (
    <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl rounded-xl p-6 border border-slate-200/50 dark:border-slate-700/50">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradients[Math.floor(Math.random() * gradients.length)]} flex items-center justify-center shadow-lg`}>
          <TargetIcon className="w-6 h-6 text-white" />
        </div>
        <div className="text-right">
          <span className="text-3xl font-bold text-slate-800 dark:text-slate-100">{pillar.max_points}</span>
          <p className="text-xs text-slate-500 dark:text-slate-400">puntos</p>
        </div>
      </div>
      <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">{pillar.name}</h3>
      <p className="text-sm text-slate-600 dark:text-slate-300">{pillar.description}</p>
      {pillar.criteria && pillar.criteria.length > 0 && (
        <div className="mt-4">
          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Criterios</h4>
          <ul className="space-y-1">
            {pillar.criteria.map((criterion, idx) => (
              <li key={idx} className="text-xs text-slate-600 dark:text-slate-300 flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5"></span>
                {criterion}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function SnapshotCard({ snapshot }) {
  return (
    <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl rounded-xl p-4 border border-slate-200/50 dark:border-slate-700/50">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-500 to-slate-700 flex items-center justify-center">
            <LayersIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800 dark:text-slate-100">v{snapshot.version}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">{snapshot.snapshot_id}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
            <ClockIcon className="w-3 h-3" />
            {new Date(snapshot.created_at).toLocaleDateString('es-MX')}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-slate-600 dark:text-slate-300">
          <strong>{snapshot.agent_count}</strong> agentes
        </span>
        <span className="text-slate-600 dark:text-slate-300">
          <strong>{snapshot.phase_count}</strong> fases
        </span>
        <span className="text-slate-600 dark:text-slate-300">
          <strong>{snapshot.pillar_count}</strong> pilares
        </span>
      </div>
      <p className="text-xs text-slate-400 dark:text-slate-500 mt-2">Por: {snapshot.created_by}</p>
    </div>
  );
}

function AdminDocumentacion() {
  const [overview, setOverview] = useState(null);
  const [inventory, setInventory] = useState(null);
  const [phases, setPhases] = useState([]);
  const [pillars, setPillars] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('agents');
  const [agentFilter, setAgentFilter] = useState('all');
  const [creatingSnapshot, setCreatingSnapshot] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('durezza-dark-mode');
      return saved === 'true';
    }
    return false;
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('durezza-dark-mode', darkMode);
  }, [darkMode]);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [overviewRes, inventoryRes, phasesRes, pillarsRes, snapshotsRes] = await Promise.all([
        api.get('/api/docs/overview'),
        api.get('/api/docs/inventory'),
        api.get('/api/docs/phases'),
        api.get('/api/docs/pillars'),
        api.get('/api/docs/snapshots')
      ]);

      setOverview(overviewRes);
      setInventory(inventoryRes);
      setPhases(phasesRes);
      setPillars(pillarsRes);
      setSnapshots(snapshotsRes);
    } catch (err) {
      console.error('Error loading documentation:', err);
      setError(err.response?.data?.detail || err.message || 'Error al cargar la documentación');
    }
    setLoading(false);
  }

  async function handleCreateSnapshot() {
    setCreatingSnapshot(true);
    try {
      await api.post('/api/docs/snapshot');
      await loadData();
    } catch (err) {
      console.error('Error creating snapshot:', err);
      setError('Error al crear snapshot');
    }
    setCreatingSnapshot(false);
  }

  async function handleDownloadMarkdown(agentId) {
    try {
      const response = await api.get(`/api/docs/agents/${agentId}/markdown`);
      const blob = new Blob([response.markdown], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${agentId}_documentation.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading markdown:', err);
    }
  }

  const filteredAgents = inventory?.agents?.filter(agent => {
    if (agentFilter === 'all') return true;
    if (agentFilter === 'principal') return agent.type === 'principal';
    if (agentFilter === 'subagent') return agent.type === 'subagent';
    if (agentFilter === 'blocking') return agent.can_block;
    return true;
  }) || [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center transition-colors duration-300">
        <div className="text-center animate-fade-in">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-200 dark:border-blue-800 rounded-full animate-spin border-t-blue-600 dark:border-t-blue-400 mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <BookOpenIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <p className="mt-6 text-slate-600 dark:text-slate-300 font-medium">Cargando Hub de Documentación...</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'agents', label: 'Inventario de Agentes', icon: BotIcon },
    { id: 'phases', label: 'Fases POE', icon: ChartIcon },
    { id: 'pillars', label: 'Pilares de Evaluación', icon: ShieldIcon },
    { id: 'snapshots', label: 'Snapshots', icon: LayersIcon }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-50 to-blue-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 transition-colors duration-300">
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900"></div>
        <div className="absolute inset-0 opacity-30">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="mesh" width="40" height="40" patternUnits="userSpaceOnUse">
                <circle cx="20" cy="20" r="1" fill="rgba(255,255,255,0.3)"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#mesh)"/>
          </svg>
        </div>
        <div className="absolute inset-0 backdrop-blur-[1px]"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="animate-fade-in-up">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br from-blue-400 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                  <BookOpenIcon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Hub de Documentación</h1>
                    <span className="px-2 py-0.5 bg-white/20 backdrop-blur-md rounded text-xs font-semibold text-white">REVISAR.IA</span>
                  </div>
                  <p className="text-blue-200 text-sm sm:text-base">Documentación automatizada del sistema multi-agente</p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={loadData}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 text-white transition-all duration-300 hover:scale-105 active:scale-95"
              >
                <RefreshIcon className="w-5 h-5" />
                <span className="text-sm font-medium hidden sm:inline">Actualizar</span>
              </button>
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 text-white transition-all duration-300 hover:scale-105 active:scale-95"
              >
                {darkMode ? (
                  <>
                    <SunIcon className="w-5 h-5" />
                    <span className="text-sm font-medium hidden sm:inline">Modo Claro</span>
                  </>
                ) : (
                  <>
                    <MoonIcon className="w-5 h-5" />
                    <span className="text-sm font-medium hidden sm:inline">Modo Oscuro</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
            <p className="text-red-700 dark:text-red-300 flex items-center gap-2">
              <AlertTriangleIcon className="w-5 h-5" />
              {error}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8">
          <KPICard 
            title="Total Agentes"
            value={overview?.total_agents || 11}
            subtitle="Principales + Subagentes"
            icon={BotIcon}
            gradient="from-blue-500 to-cyan-500"
            delay="0"
          />
          <KPICard 
            title="Fases POE"
            value={overview?.total_phases || 10}
            subtitle="F0 - F9"
            icon={ChartIcon}
            gradient="from-violet-500 to-purple-500"
            delay="100"
          />
          <KPICard 
            title="Pilares"
            value={overview?.total_pillars || 4}
            subtitle="100 puntos totales"
            icon={ShieldIcon}
            gradient="from-emerald-500 to-green-500"
            delay="200"
          />
          <KPICard 
            title="Candados Duros"
            value={overview?.hard_locks?.length || 3}
            subtitle={overview?.hard_locks?.join(', ') || 'F2, F6, F8'}
            icon={LockIcon}
            gradient="from-rose-500 to-red-500"
            delay="300"
            valueColor="text-rose-600 dark:text-rose-400"
          />
        </div>

        <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl rounded-2xl shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 overflow-hidden">
          <div className="border-b border-slate-200/50 dark:border-slate-700/50">
            <div className="flex overflow-x-auto">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-6 py-4 font-medium text-sm whitespace-nowrap transition-all duration-200 border-b-2 ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50/50 dark:bg-blue-900/20'
                        : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="p-6">
            {activeTab === 'agents' && (
              <div>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                  <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
                    Inventario de Agentes ({filteredAgents.length})
                  </h2>
                  <div className="flex items-center gap-2">
                    <select
                      value={agentFilter}
                      onChange={(e) => setAgentFilter(e.target.value)}
                      className="px-3 py-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">Todos los agentes</option>
                      <option value="principal">Solo principales</option>
                      <option value="subagent">Solo subagentes</option>
                      <option value="blocking">Solo bloqueantes</option>
                    </select>
                  </div>
                </div>
                
                <div className="grid gap-4">
                  {filteredAgents.map((agent) => (
                    <AgentCard 
                      key={agent.agent_id} 
                      agent={agent} 
                      onDownloadMarkdown={handleDownloadMarkdown}
                    />
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'phases' && (
              <div>
                <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-6">
                  Fases del Procedimiento Operativo Estándar (POE)
                </h2>
                <div className="space-y-0">
                  {phases.map((phase, index) => (
                    <PhaseCard key={phase.phase_id} phase={phase} index={index} />
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'pillars' && (
              <div>
                <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-6">
                  Pilares de Evaluación (100 puntos totales)
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {pillars.map((pillar) => (
                    <PillarCard key={pillar.pillar_id} pillar={pillar} />
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'snapshots' && (
              <div>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                  <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
                    Historial de Snapshots
                  </h2>
                  <button
                    onClick={handleCreateSnapshot}
                    disabled={creatingSnapshot}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {creatingSnapshot ? (
                      <>
                        <RefreshIcon className="w-4 h-4 animate-spin" />
                        Generando...
                      </>
                    ) : (
                      <>
                        <PlusIcon className="w-4 h-4" />
                        Generar Snapshot
                      </>
                    )}
                  </button>
                </div>
                
                {snapshots.length === 0 ? (
                  <div className="text-center py-12">
                    <LayersIcon className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-500 dark:text-slate-400">No hay snapshots disponibles</p>
                    <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">Genera el primer snapshot para documentar el estado actual del sistema</p>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {snapshots.map((snapshot) => (
                      <SnapshotCard key={snapshot.snapshot_id} snapshot={snapshot} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default AdminDocumentacion;
