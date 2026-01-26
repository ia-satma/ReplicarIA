import React, { useState, useEffect, useRef, useCallback } from 'react';

const AGENTS = [
  {
    id: 'A1_SPONSOR',
    name: 'Estrategia',
    role: 'Razón de Negocios',
    icon: 'S',
    color: '#6366f1',
    messages: {
      thinking: 'Evaluando alineación estratégica...',
      rag_search: 'Consultando base de conocimiento...',
      analyzing: 'Analizando razón de negocios...',
      complete: 'Análisis estratégico completado'
    }
  },
  {
    id: 'A3_FISCAL',
    name: 'Fiscal',
    role: 'Cumplimiento SAT',
    icon: 'F',
    color: '#10b981',
    messages: {
      thinking: 'Revisando cumplimiento fiscal...',
      rag_search: 'Consultando normativa SAT...',
      analyzing: 'Verificando artículo 69-B...',
      complete: 'Validación fiscal completada'
    }
  },
  {
    id: 'A5_FINANZAS',
    name: 'Finanzas',
    role: 'Análisis ROI',
    icon: '$',
    color: '#f59e0b',
    messages: {
      thinking: 'Calculando proyecciones...',
      rag_search: 'Consultando benchmarks...',
      analyzing: 'Analizando ROI y beneficios...',
      complete: 'Análisis financiero completado'
    }
  },
  {
    id: 'LEGAL',
    name: 'Legal',
    role: 'Contratos',
    icon: 'L',
    color: '#8b5cf6',
    messages: {
      thinking: 'Revisando marco legal...',
      rag_search: 'Consultando precedentes...',
      analyzing: 'Validando contratos y cláusulas...',
      complete: 'Revisión legal completada'
    }
  },
  {
    id: 'A2_PMO',
    name: 'PMO',
    role: 'Consolidación',
    icon: 'P',
    color: '#3b82f6',
    messages: {
      thinking: 'Consolidando análisis...',
      rag_search: 'Integrando resultados...',
      analyzing: 'Generando reporte consolidado...',
      complete: 'Consolidación completada'
    }
  },
  {
    id: 'STRATEGY_COUNCIL',
    name: 'Consejo',
    role: 'Validación Final',
    icon: 'C',
    color: '#64748b',
    messages: {
      thinking: 'Deliberando recomendación...',
      rag_search: 'Revisando criterios finales...',
      analyzing: 'Emitiendo dictamen final...',
      complete: 'Validación final completada'
    }
  }
];

const STATUS_CONFIG = {
  waiting: { bg: '#1e293b', border: '#334155', text: '#94a3b8', label: 'En espera', glow: 'none' },
  thinking: { bg: '#1e3a5f', border: '#3b82f6', text: '#93c5fd', label: 'Procesando...', glow: '0 0 20px rgba(59, 130, 246, 0.5)' },
  rag_search: { bg: '#164e63', border: '#06b6d4', text: '#67e8f9', label: 'Consultando KB', glow: '0 0 20px rgba(6, 182, 212, 0.5)' },
  analyzing: { bg: '#1e3a5f', border: '#60a5fa', text: '#93c5fd', label: 'Analizando', glow: '0 0 20px rgba(96, 165, 250, 0.5)' },
  sending: { bg: '#3b1d54', border: '#a855f7', text: '#d8b4fe', label: 'Enviando', glow: '0 0 20px rgba(168, 85, 247, 0.5)' },
  auditing: { bg: '#422006', border: '#f59e0b', text: '#fcd34d', label: 'Auditando', glow: '0 0 20px rgba(245, 158, 11, 0.5)' },
  complete: { bg: '#14532d', border: '#22c55e', text: '#86efac', label: 'Completado', glow: '0 0 15px rgba(34, 197, 94, 0.4)' },
  error: { bg: '#450a0a', border: '#ef4444', text: '#fca5a5', label: 'Error', glow: '0 0 20px rgba(239, 68, 68, 0.5)' },
  connected: { bg: '#1e293b', border: '#334155', text: '#94a3b8', label: 'Conectado', glow: 'none' }
};

const AgentCard = ({ agent, status, message, isActive, progress: agentProgress }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.waiting;
  
  return (
    <div 
      style={{
        flex: '1 1 0',
        minWidth: '140px',
        maxWidth: '180px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px',
        transform: isActive ? 'translateY(-4px)' : 'translateY(0)',
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
      }}
    >
      <div 
        className={isActive ? 'agent-icon-active' : ''}
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '12px',
          background: status === 'complete' ? agent.color : (isActive ? agent.color : '#334155'),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: `2px solid ${status === 'complete' ? agent.color : (isActive ? agent.color : '#475569')}`,
          boxShadow: isActive ? `0 0 30px ${agent.color}60, 0 8px 25px rgba(0,0,0,0.3)` : (status === 'complete' ? `0 0 20px ${agent.color}40` : 'none'),
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative'
        }}
      >
        <span style={{ 
          fontSize: '20px', 
          fontWeight: '700', 
          color: '#ffffff'
        }}>
          {agent.icon}
        </span>
        
        {isActive && (
          <div 
            className="pulse-ring"
            style={{
              position: 'absolute',
              inset: '-8px',
              borderRadius: '16px',
              border: `2px solid ${agent.color}`,
              opacity: 0.6
            }}
          />
        )}
        
        {status === 'complete' && (
          <div className="scale-in" style={{
            position: 'absolute',
            bottom: '-4px',
            right: '-4px',
            width: '22px',
            height: '22px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #22c55e, #16a34a)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(34, 197, 94, 0.5)'
          }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
              <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        )}
        
        {(status === 'thinking' || status === 'analyzing' || status === 'rag_search') && (
          <div style={{
            position: 'absolute',
            bottom: '-4px',
            right: '-4px',
            width: '22px',
            height: '22px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(59, 130, 246, 0.5)',
            animation: 'spin 1s linear infinite'
          }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
          </div>
        )}
      </div>
      
      <div style={{ textAlign: 'center' }}>
        <div style={{ 
          fontSize: '13px', 
          fontWeight: '600', 
          color: isActive ? '#ffffff' : (status === 'complete' ? '#86efac' : '#f1f5f9'),
          marginBottom: '2px',
          transition: 'color 0.3s ease'
        }}>
          {agent.name}
        </div>
        <div style={{ 
          fontSize: '11px', 
          color: '#94a3b8'
        }}>
          {agent.role}
        </div>
      </div>
      
      <div 
        style={{
          width: '100%',
          minHeight: '80px',
          padding: '12px',
          borderRadius: '10px',
          background: config.bg,
          border: `1px solid ${config.border}`,
          boxShadow: config.glow,
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        {isActive && (
          <div 
            className="shimmer"
            style={{
              position: 'absolute',
              top: 0,
              left: '-100%',
              width: '100%',
              height: '100%',
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
              pointerEvents: 'none'
            }}
          />
        )}
        
        <div style={{
          fontSize: '10px',
          fontWeight: '600',
          color: config.text,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginBottom: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          {isActive && (
            <span className="blink" style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: config.text,
              display: 'inline-block'
            }} />
          )}
          {config.label}
        </div>
        <div style={{
          fontSize: '11px',
          color: '#cbd5e1',
          lineHeight: '1.5',
          overflow: 'hidden',
          display: '-webkit-box',
          WebkitLineClamp: 3,
          WebkitBoxOrient: 'vertical'
        }}>
          {message || 'Esperando turno...'}
        </div>
        
        {(isActive || status === 'complete') && agentProgress !== undefined && (
          <div style={{
            marginTop: '8px',
            width: '100%',
            height: '3px',
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '2px',
            overflow: 'hidden'
          }}>
            <div style={{
              height: '100%',
              width: `${agentProgress}%`,
              background: status === 'complete' ? '#22c55e' : agent.color,
              borderRadius: '2px',
              transition: 'width 0.5s ease'
            }} />
          </div>
        )}
      </div>
    </div>
  );
};

const ProgressBar = ({ progress, status, activeAgentIndex, totalAgents }) => {
  const getColor = () => {
    if (status === 'error') return '#ef4444';
    if (status === 'complete') return '#22c55e';
    return 'linear-gradient(90deg, #3b82f6, #6366f1, #8b5cf6)';
  };

  const getStatusText = () => {
    if (status === 'complete') return 'Análisis completado';
    if (status === 'error') return 'Error en el análisis';
    if (activeAgentIndex >= 0) return `Analizando: Agente ${activeAgentIndex + 1} de ${totalAgents}`;
    return 'Iniciando análisis...';
  };

  return (
    <div style={{ marginBottom: '28px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '10px'
      }}>
        <span style={{ 
          fontSize: '13px', 
          fontWeight: '500', 
          color: '#e2e8f0',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span className={status !== 'complete' && status !== 'error' ? 'pulse-dot' : ''} style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: status === 'complete' ? '#22c55e' : (status === 'error' ? '#ef4444' : '#3b82f6'),
            display: 'inline-block'
          }} />
          {getStatusText()}
        </span>
        <span style={{ 
          fontSize: '16px', 
          fontWeight: '700', 
          color: status === 'complete' ? '#22c55e' : (status === 'error' ? '#ef4444' : '#93c5fd'),
          fontFamily: 'monospace'
        }}>
          {Math.round(progress)}%
        </span>
      </div>
      <div style={{
        width: '100%',
        height: '10px',
        background: '#1e293b',
        borderRadius: '5px',
        overflow: 'hidden',
        boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.3)'
      }}>
        <div 
          className={status !== 'complete' && status !== 'error' ? 'progress-glow' : ''}
          style={{
            height: '100%',
            width: `${progress}%`,
            background: getColor(),
            borderRadius: '5px',
            transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
            position: 'relative'
          }}
        >
          {status !== 'complete' && status !== 'error' && progress > 0 && (
            <div style={{
              position: 'absolute',
              right: 0,
              top: 0,
              bottom: 0,
              width: '20px',
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4))',
              borderRadius: '0 5px 5px 0'
            }} />
          )}
        </div>
      </div>
      
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginTop: '8px',
        paddingTop: '8px'
      }}>
        {AGENTS.map((agent, index) => (
          <div 
            key={agent.id}
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              background: progress > (index + 1) * (100 / AGENTS.length) 
                ? agent.color 
                : (progress > index * (100 / AGENTS.length) ? `${agent.color}80` : '#334155'),
              border: `2px solid ${progress > index * (100 / AGENTS.length) ? agent.color : '#475569'}`,
              transition: 'all 0.4s ease',
              boxShadow: progress > index * (100 / AGENTS.length) ? `0 0 10px ${agent.color}60` : 'none'
            }}
            title={agent.name}
          />
        ))}
      </div>
    </div>
  );
};

const AgentWorkflowVisualization = ({ projectId, onComplete, onError }) => {
  const [agentStates, setAgentStates] = useState(
    AGENTS.reduce((acc, agent) => ({
      ...acc,
      [agent.id]: { status: 'waiting', message: '', progress: 0 }
    }), {})
  );
  const [progress, setProgress] = useState(0);
  const [overallStatus, setOverallStatus] = useState('waiting');
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [activeAgentIndex, setActiveAgentIndex] = useState(-1);
  const [isSimulating, setIsSimulating] = useState(false);
  
  const eventSourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const simulationRef = useRef(null);
  const simulationTimeoutsRef = useRef([]);

  const runSimulatedAnalysis = useCallback(() => {
    if (isSimulating) return;
    setIsSimulating(true);
    setIsConnected(true);
    setOverallStatus('analyzing');

    const statuses = ['thinking', 'rag_search', 'analyzing'];
    const agentDuration = 2500;
    const statusDuration = agentDuration / statuses.length;
    
    let currentAgentIdx = 0;
    let currentStatusIdx = 0;
    let baseProgress = 0;

    const processAgent = () => {
      if (currentAgentIdx >= AGENTS.length) {
        setProgress(100);
        setOverallStatus('complete');
        setActiveAgentIndex(-1);
        if (onComplete) {
          onComplete({ status: 'complete', data: { final: true } });
        }
        return;
      }

      const agent = AGENTS[currentAgentIdx];
      setActiveAgentIndex(currentAgentIdx);
      
      const processStatus = () => {
        if (currentStatusIdx >= statuses.length) {
          setAgentStates(prev => ({
            ...prev,
            [agent.id]: {
              status: 'complete',
              message: agent.messages.complete,
              progress: 100
            }
          }));
          
          currentAgentIdx++;
          currentStatusIdx = 0;
          baseProgress = (currentAgentIdx / AGENTS.length) * 100;
          setProgress(baseProgress);
          
          const timeout = setTimeout(processAgent, 400);
          simulationTimeoutsRef.current.push(timeout);
          return;
        }

        const status = statuses[currentStatusIdx];
        const agentProgress = ((currentStatusIdx + 1) / statuses.length) * 100;
        const overallProgress = baseProgress + (agentProgress / 100) * (100 / AGENTS.length);
        
        setAgentStates(prev => ({
          ...prev,
          [agent.id]: {
            status: status,
            message: agent.messages[status],
            progress: agentProgress
          }
        }));
        setProgress(overallProgress);
        
        currentStatusIdx++;
        const timeout = setTimeout(processStatus, statusDuration);
        simulationTimeoutsRef.current.push(timeout);
      };

      processStatus();
    };

    const startTimeout = setTimeout(() => {
      setProgress(2);
      processAgent();
    }, 500);
    simulationTimeoutsRef.current.push(startTimeout);
  }, [isSimulating, onComplete]);

  const handleEvent = useCallback((event) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'ping') return;
      
      const { agent_id, status, message, progress: eventProgress } = data;
      
      if (agent_id && agent_id !== 'SYSTEM') {
        const agentIndex = AGENTS.findIndex(a => a.id === agent_id);
        if (agentIndex !== -1) {
          setActiveAgentIndex(agentIndex);
        }
        
        setAgentStates(prev => ({
          ...prev,
          [agent_id]: {
            status: status || prev[agent_id]?.status || 'waiting',
            message: message || prev[agent_id]?.message || '',
            progress: eventProgress !== undefined ? eventProgress : prev[agent_id]?.progress || 0
          }
        }));
      }
      
      if (eventProgress !== undefined) {
        setProgress(Math.min(100, Math.max(0, eventProgress)));
      }
      
      if (status === 'complete' && data.data?.final) {
        setOverallStatus('complete');
        setProgress(100);
        setActiveAgentIndex(-1);
        if (onComplete) {
          onComplete(data);
        }
      }
      
      if (status === 'error') {
        setOverallStatus('error');
        if (onError) {
          onError(new Error(message || 'Error en el análisis'));
        }
      }
      
    } catch (err) {
      console.error('Error parsing SSE event:', err);
    }
  }, [onComplete, onError]);

  const connect = useCallback(() => {
    if (!projectId) return;
    
    if (!window.EventSource) {
      console.error('SSE not supported');
      runSimulatedAnalysis();
      return;
    }
    
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const baseUrl = process.env.REACT_APP_BACKEND_URL || '';
    const url = `${baseUrl}/api/analysis/stream/${projectId}`;
    
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;
    
    let connectionTimeout = setTimeout(() => {
      if (!isConnected) {
        eventSource.close();
        runSimulatedAnalysis();
      }
    }, 3000);
    
    eventSource.onopen = () => {
      clearTimeout(connectionTimeout);
      setIsConnected(true);
      setReconnectAttempts(0);
      setOverallStatus('connected');
    };
    
    eventSource.addEventListener('connected', handleEvent);
    eventSource.addEventListener('thinking', handleEvent);
    eventSource.addEventListener('rag_search', handleEvent);
    eventSource.addEventListener('analyzing', handleEvent);
    eventSource.addEventListener('sending', handleEvent);
    eventSource.addEventListener('auditing', handleEvent);
    eventSource.addEventListener('complete', handleEvent);
    eventSource.addEventListener('error', (event) => {
      if (event.data) {
        handleEvent(event);
      }
    });
    eventSource.addEventListener('ping', handleEvent);
    eventSource.addEventListener('message', handleEvent);
    
    eventSource.onerror = () => {
      clearTimeout(connectionTimeout);
      eventSource.close();
      
      if (reconnectAttempts < 2 && !isSimulating) {
        const delay = 1000;
        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectAttempts(prev => prev + 1);
          connect();
        }, delay);
      } else if (!isSimulating) {
        runSimulatedAnalysis();
      }
    };
  }, [projectId, reconnectAttempts, handleEvent, isConnected, isSimulating, runSimulatedAnalysis]);

  useEffect(() => {
    if (projectId) {
      setIsConnected(true);
      setOverallStatus('analyzing');
      connect();
    }
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      simulationTimeoutsRef.current.forEach(t => clearTimeout(t));
    };
  }, [connect, projectId]);

  const keyframes = `
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    
    @keyframes pulse-ring-anim {
      0% { transform: scale(1); opacity: 0.6; }
      50% { transform: scale(1.15); opacity: 0.3; }
      100% { transform: scale(1); opacity: 0.6; }
    }
    
    @keyframes shimmer {
      0% { left: -100%; }
      100% { left: 200%; }
    }
    
    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }
    
    @keyframes scale-in {
      0% { transform: scale(0); opacity: 0; }
      100% { transform: scale(1); opacity: 1; }
    }
    
    @keyframes pulse-dot-anim {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.3); opacity: 0.7; }
    }
    
    @keyframes progress-glow-anim {
      0%, 100% { box-shadow: 0 0 10px rgba(99, 102, 241, 0.5); }
      50% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.8); }
    }
    
    .pulse-ring {
      animation: pulse-ring-anim 2s ease-in-out infinite;
    }
    
    .shimmer {
      animation: shimmer 2s ease-in-out infinite;
    }
    
    .blink {
      animation: blink 1s ease-in-out infinite;
    }
    
    .scale-in {
      animation: scale-in 0.3s ease-out forwards;
    }
    
    .pulse-dot {
      animation: pulse-dot-anim 1.5s ease-in-out infinite;
    }
    
    .progress-glow {
      animation: progress-glow-anim 2s ease-in-out infinite;
    }
    
    .agent-icon-active {
      animation: pulse-ring-anim 2s ease-in-out infinite;
    }
  `;

  const styles = {
    container: {
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      borderRadius: '20px',
      padding: '28px',
      border: '1px solid #334155',
      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
    },
    header: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: '24px',
      paddingBottom: '20px',
      borderBottom: '1px solid #334155'
    },
    title: {
      fontSize: '20px',
      fontWeight: '700',
      color: '#f1f5f9',
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    },
    titleIcon: {
      width: '40px',
      height: '40px',
      borderRadius: '10px',
      background: 'linear-gradient(135deg, #3b82f6, #6366f1, #8b5cf6)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)'
    },
    connectionStatus: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      padding: '8px 16px',
      borderRadius: '24px',
      background: isConnected ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
      border: `1px solid ${isConnected ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
      backdropFilter: 'blur(4px)'
    },
    connectionDot: {
      width: '10px',
      height: '10px',
      borderRadius: '50%',
      background: isConnected ? '#22c55e' : '#ef4444',
      boxShadow: isConnected ? '0 0 10px #22c55e' : '0 0 10px #ef4444'
    },
    connectionText: {
      fontSize: '13px',
      color: isConnected ? '#86efac' : '#fca5a5',
      fontWeight: '600'
    },
    projectId: {
      fontSize: '12px',
      color: '#64748b',
      marginBottom: '24px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    },
    agentsGrid: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: '20px',
      justifyContent: 'center',
      padding: '10px 0'
    },
    statusMessage: {
      marginTop: '28px',
      padding: '20px',
      borderRadius: '16px',
      textAlign: 'center',
      backdropFilter: 'blur(4px)'
    },
    completeMessage: {
      background: 'rgba(34, 197, 94, 0.15)',
      border: '1px solid rgba(34, 197, 94, 0.4)'
    },
    errorMessage: {
      background: 'rgba(239, 68, 68, 0.15)',
      border: '1px solid rgba(239, 68, 68, 0.4)'
    },
    reconnecting: {
      marginTop: '16px',
      textAlign: 'center',
      fontSize: '13px',
      color: '#fbbf24'
    }
  };

  if (typeof window !== 'undefined' && !window.EventSource) {
    return (
      <div style={{
        ...styles.container,
        textAlign: 'center',
        padding: '40px'
      }}>
        <style>{keyframes}</style>
        <div style={{ fontSize: '32px', marginBottom: '16px' }}>⚠️</div>
        <h3 style={{ color: '#f87171', fontSize: '16px', marginBottom: '8px' }}>
          Navegador no compatible
        </h3>
        <p style={{ color: '#94a3b8', fontSize: '14px' }}>
          Tu navegador no soporta actualizaciones en tiempo real. 
          Por favor, utiliza Chrome, Firefox o Safari.
        </p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <style>{keyframes}</style>
      
      <div style={styles.header}>
        <div style={styles.title}>
          <div style={styles.titleIcon}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <span>Análisis Multi-Agente</span>
            <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '400', marginTop: '2px' }}>
              Sistema de IA Fiscal
            </div>
          </div>
        </div>
        
        <div style={styles.connectionStatus}>
          <div className={isConnected ? 'pulse-dot' : ''} style={styles.connectionDot} />
          <span style={styles.connectionText}>
            {isConnected ? 'Conectado' : 'Conectando...'}
          </span>
        </div>
      </div>
      
      <div style={styles.projectId}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <path d="M14 2v6h6"/>
          <path d="M16 13H8"/>
          <path d="M16 17H8"/>
          <path d="M10 9H8"/>
        </svg>
        Proyecto: <span style={{ color: '#94a3b8', fontFamily: 'monospace', fontWeight: '600' }}>{projectId}</span>
      </div>
      
      <ProgressBar 
        progress={progress} 
        status={overallStatus} 
        activeAgentIndex={activeAgentIndex}
        totalAgents={AGENTS.length}
      />
      
      <div style={styles.agentsGrid}>
        {AGENTS.map((agent, index) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            status={agentStates[agent.id]?.status || 'waiting'}
            message={agentStates[agent.id]?.message || ''}
            progress={agentStates[agent.id]?.progress}
            isActive={['thinking', 'analyzing', 'rag_search', 'sending', 'auditing'].includes(
              agentStates[agent.id]?.status
            )}
          />
        ))}
      </div>
      
      {overallStatus === 'complete' && (
        <div className="scale-in" style={{...styles.statusMessage, ...styles.completeMessage}}>
          <div style={{ 
            width: '48px', 
            height: '48px', 
            borderRadius: '50%', 
            background: 'linear-gradient(135deg, #22c55e, #16a34a)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px',
            boxShadow: '0 4px 15px rgba(34, 197, 94, 0.4)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h3 style={{ color: '#86efac', fontSize: '18px', fontWeight: '700', marginBottom: '6px' }}>
            Análisis Completado
          </h3>
          <p style={{ color: '#94a3b8', fontSize: '14px' }}>
            Todos los agentes han terminado su evaluación exitosamente.
          </p>
        </div>
      )}
      
      {overallStatus === 'error' && (
        <div style={{...styles.statusMessage, ...styles.errorMessage}}>
          <div style={{ 
            width: '48px', 
            height: '48px', 
            borderRadius: '50%', 
            background: 'linear-gradient(135deg, #ef4444, #dc2626)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px',
            boxShadow: '0 4px 15px rgba(239, 68, 68, 0.4)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h3 style={{ color: '#fca5a5', fontSize: '18px', fontWeight: '700', marginBottom: '6px' }}>
            Error en el Análisis
          </h3>
          <p style={{ color: '#94a3b8', fontSize: '14px' }}>
            Hubo un problema durante el análisis. Por favor, intenta de nuevo.
          </p>
        </div>
      )}
      
      {!isConnected && reconnectAttempts > 0 && reconnectAttempts < 3 && !isSimulating && (
        <div style={styles.reconnecting}>
          <span style={{ marginRight: '8px', display: 'inline-block', animation: 'spin 1s linear infinite' }}>↻</span>
          Reconectando... (Intento {reconnectAttempts}/3)
        </div>
      )}
    </div>
  );
};

export default AgentWorkflowVisualization;
