import React, { useState, useEffect, useCallback } from 'react';

const api = {
  get: async (url) => {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`/api${url}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      }
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },
  post: async (url, data = {}) => {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`/api${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
};

const STATUS_CONFIG = {
  ok: { emoji: '✅', color: '#10B981', label: 'OK', bgClass: 'bg-emerald-500/20', borderClass: 'border-emerald-500/30', textClass: 'text-emerald-400' },
  warning: { emoji: '⚠️', color: '#F59E0B', label: 'Warning', bgClass: 'bg-amber-500/20', borderClass: 'border-amber-500/30', textClass: 'text-amber-400' },
  error: { emoji: '❌', color: '#EF4444', label: 'Error', bgClass: 'bg-red-500/20', borderClass: 'border-red-500/30', textClass: 'text-red-400' },
  critical: { emoji: '🔴', color: '#EF4444', label: 'Critical', bgClass: 'bg-red-600/20', borderClass: 'border-red-600/30', textClass: 'text-red-500' }
};

const SEVERITY_CONFIG = {
  low: { color: '#10B981', bgClass: 'bg-emerald-500/20', textClass: 'text-emerald-400' },
  medium: { color: '#F59E0B', bgClass: 'bg-amber-500/20', textClass: 'text-amber-400' },
  high: { color: '#EF4444', bgClass: 'bg-red-500/20', textClass: 'text-red-400' },
  critical: { color: '#DC2626', bgClass: 'bg-red-600/20', textClass: 'text-red-500' }
};

const getStatusConfig = (status) => {
  const key = (status || 'ok').toLowerCase();
  return STATUS_CONFIG[key] || STATUS_CONFIG.ok;
};

const getSeverityConfig = (severity) => {
  const key = (severity || 'low').toLowerCase();
  return SEVERITY_CONFIG[key] || SEVERITY_CONFIG.low;
};

const getSystemStatusFromHealth = (saludSistema) => {
  const health = saludSistema || 0;
  if (health >= 80) {
    return { bg: 'bg-emerald-500', pulse: 'bg-emerald-400', label: 'Saludable' };
  } else if (health >= 50) {
    return { bg: 'bg-amber-500', pulse: 'bg-amber-400', label: 'Advertencia' };
  } else if (health > 0) {
    return { bg: 'bg-red-500', pulse: 'bg-red-400', label: 'Crítico' };
  } else {
    return { bg: 'bg-slate-500', pulse: 'bg-slate-400', label: 'Sin datos' };
  }
};

const SystemHealth = () => {
  const [guardianStatus, setGuardianStatus] = useState(null);
  const [healthChecks, setHealthChecks] = useState([]);
  const [bugs, setBugs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [runningCheck, setRunningCheck] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, checksRes, bugsRes] = await Promise.all([
        api.get('/guardian/status').catch(() => ({ status: 'unknown', is_running: false })),
        api.get('/guardian/health-checks').catch(() => ({ checks: [] })),
        api.get('/guardian/bugs').catch(() => ({ bugs: [] }))
      ]);
      
      setGuardianStatus(statusRes);
      setHealthChecks(checksRes.checks || checksRes.health_checks || []);
      setBugs(bugsRes.bugs || []);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError('Error al cargar datos del guardian');
      console.error('Guardian fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleStartGuardian = async () => {
    setActionLoading(true);
    try {
      await api.post('/guardian/start');
      await fetchData();
    } catch (err) {
      setError('Error al iniciar el guardian');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopGuardian = async () => {
    setActionLoading(true);
    try {
      await api.post('/guardian/stop');
      await fetchData();
    } catch (err) {
      setError('Error al detener el guardian');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunCheck = async (checkId) => {
    setRunningCheck(checkId);
    try {
      await api.post(`/guardian/health-checks/${checkId}/run`);
      await fetchData();
    } catch (err) {
      setError(`Error al ejecutar prueba ${checkId}`);
    } finally {
      setRunningCheck(null);
    }
  };

  const isRunning = guardianStatus?.guardian_running || guardianStatus?.is_running || guardianStatus?.running || false;
  const systemStatus = getSystemStatusFromHealth(guardianStatus?.salud_sistema);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-emerald-500/30 rounded-full animate-spin border-t-emerald-500 mx-auto"></div>
          <p className="mt-6 text-slate-400 font-medium">Cargando estado del sistema...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <span className="text-3xl">🛡️</span>
              Sistema de Agentes Guardianes
            </h1>
            <p className="text-slate-400 mt-1">Monitoreo de salud y diagnóstico del sistema</p>
          </div>
          {lastUpdate && (
            <div className="text-sm text-slate-500">
              Última actualización: {lastUpdate.toLocaleTimeString('es-MX')}
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-500/10 backdrop-blur-xl border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
            <span className="text-xl">❌</span>
            <span className="text-red-400">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-300"
            >
              ✕
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-white">Estado General</h2>
              <div className="relative">
                <div className={`w-4 h-4 rounded-full ${systemStatus.bg}`}></div>
                <div className={`absolute inset-0 w-4 h-4 rounded-full ${systemStatus.pulse} animate-ping opacity-75`}></div>
              </div>
            </div>

            <div className="text-center mb-6">
              <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full ${systemStatus.bg}/20 mb-4`}>
                <div className={`w-16 h-16 rounded-full ${systemStatus.bg} flex items-center justify-center`}>
                  <span className="text-3xl">
                    {systemStatus.label === 'Saludable' ? '✅' : systemStatus.label === 'Advertencia' ? '⚠️' : '🔴'}
                  </span>
                </div>
              </div>
              <p className="text-xl font-bold text-white">{systemStatus.label}</p>
              <p className="text-slate-400 text-sm mt-1">
                Guardian: {isRunning ? 'Activo' : 'Detenido'}
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleStartGuardian}
                disabled={actionLoading || isRunning}
                className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all flex items-center justify-center gap-2 ${
                  isRunning
                    ? 'bg-slate-700/50 text-slate-500 cursor-not-allowed'
                    : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30'
                }`}
              >
                {actionLoading ? (
                  <div className="w-5 h-5 border-2 border-emerald-400/30 rounded-full animate-spin border-t-emerald-400"></div>
                ) : (
                  <>
                    <span>▶️</span>
                    Iniciar
                  </>
                )}
              </button>
              <button
                onClick={handleStopGuardian}
                disabled={actionLoading || !isRunning}
                className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all flex items-center justify-center gap-2 ${
                  !isRunning
                    ? 'bg-slate-700/50 text-slate-500 cursor-not-allowed'
                    : 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30'
                }`}
              >
                {actionLoading ? (
                  <div className="w-5 h-5 border-2 border-red-400/30 rounded-full animate-spin border-t-red-400"></div>
                ) : (
                  <>
                    <span>⏹️</span>
                    Detener
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="lg:col-span-2 bg-white/5 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <span>🔍</span>
                Pruebas de Salud
              </h2>
              <span className="text-sm text-slate-400">{healthChecks.length} pruebas</span>
            </div>

            <div className="space-y-3 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
              {healthChecks.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <span className="text-4xl block mb-2">📋</span>
                  No hay pruebas de salud configuradas
                </div>
              ) : (
                healthChecks.map((check) => {
                  const statusConfig = getStatusConfig(check.status);
                  return (
                    <div
                      key={check.id || check.name}
                      className={`p-4 rounded-xl border ${statusConfig.bgClass} ${statusConfig.borderClass} flex items-center justify-between group`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{statusConfig.emoji}</span>
                        <div>
                          <p className="font-medium text-white">{check.name || check.id}</p>
                          <p className="text-sm text-slate-400">{check.description || 'Sin descripción'}</p>
                          {check.last_run && (
                            <p className="text-xs text-slate-500 mt-1">
                              Última ejecución: {new Date(check.last_run).toLocaleString('es-MX')}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusConfig.bgClass} ${statusConfig.textClass}`}>
                          {statusConfig.label}
                        </span>
                        <button
                          onClick={() => handleRunCheck(check.id)}
                          disabled={runningCheck === check.id}
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-2 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300"
                          title="Ejecutar prueba"
                        >
                          {runningCheck === check.id ? (
                            <div className="w-4 h-4 border-2 border-slate-400/30 rounded-full animate-spin border-t-slate-400"></div>
                          ) : (
                            <span>▶️</span>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <span>🐛</span>
              Bugs Detectados
            </h2>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              bugs.length === 0 
                ? 'bg-emerald-500/20 text-emerald-400' 
                : 'bg-red-500/20 text-red-400'
            }`}>
              {bugs.length} bugs
            </span>
          </div>

          {bugs.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <span className="text-5xl block mb-3">✅</span>
              <p className="text-lg font-medium text-slate-400">No hay bugs detectados</p>
              <p className="text-sm">El sistema está funcionando correctamente</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {bugs.map((bug, index) => {
                const severityConfig = getSeverityConfig(bug.severity);
                return (
                  <div
                    key={bug.id || index}
                    className={`p-4 rounded-xl border ${severityConfig.bgClass} border-slate-700/50 hover:border-slate-600/50 transition-colors`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityConfig.bgClass} ${severityConfig.textClass}`}>
                        {(bug.severity || 'unknown').toUpperCase()}
                      </span>
                      <span className="text-xs text-slate-500">
                        {bug.detected_at ? new Date(bug.detected_at).toLocaleDateString('es-MX') : 'Reciente'}
                      </span>
                    </div>
                    <h3 className="font-medium text-white mb-1">{bug.title || bug.name || 'Bug sin título'}</h3>
                    <p className="text-sm text-slate-400 line-clamp-2">{bug.description || 'Sin descripción'}</p>
                    {bug.component && (
                      <p className="text-xs text-slate-500 mt-2">
                        Componente: {bug.component}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white/5 backdrop-blur-xl rounded-xl border border-slate-700/50 p-4 text-center">
            <p className="text-2xl font-bold text-emerald-400">
              {healthChecks.filter(c => (c.status || '').toLowerCase() === 'ok').length}
            </p>
            <p className="text-sm text-slate-400">Pruebas OK</p>
          </div>
          <div className="bg-white/5 backdrop-blur-xl rounded-xl border border-slate-700/50 p-4 text-center">
            <p className="text-2xl font-bold text-amber-400">
              {healthChecks.filter(c => (c.status || '').toLowerCase() === 'warning').length}
            </p>
            <p className="text-sm text-slate-400">Advertencias</p>
          </div>
          <div className="bg-white/5 backdrop-blur-xl rounded-xl border border-slate-700/50 p-4 text-center">
            <p className="text-2xl font-bold text-red-400">
              {healthChecks.filter(c => ['error', 'critical'].includes((c.status || '').toLowerCase())).length}
            </p>
            <p className="text-sm text-slate-400">Errores</p>
          </div>
          <div className="bg-white/5 backdrop-blur-xl rounded-xl border border-slate-700/50 p-4 text-center">
            <p className="text-2xl font-bold text-red-500">{bugs.length}</p>
            <p className="text-sm text-slate-400">Bugs</p>
          </div>
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
};

export default SystemHealth;
