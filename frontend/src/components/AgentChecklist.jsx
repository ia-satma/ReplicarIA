import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

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

const AgentChecklist = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtroFaltantes, setFiltroFaltantes] = useState(false);

  useEffect(() => {
    loadAgentRequirements();
  }, []);

  const loadAgentRequirements = async () => {
    setLoading(true);
    try {
      const response = await api.get('/kb/agent-requirements');
      setData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error loading agent requirements:', err);
      setError('Error al cargar los requerimientos de agentes');
    } finally {
      setLoading(false);
    }
  };

  const handleGoToBiblioteca = () => {
    navigate('/biblioteca');
  };

  const getCompletitudColor = (completitud) => {
    if (completitud >= 100) return 'from-green-500 to-emerald-500';
    if (completitud >= 75) return 'from-blue-500 to-cyan-500';
    if (completitud >= 50) return 'from-amber-500 to-yellow-500';
    if (completitud >= 25) return 'from-orange-500 to-amber-500';
    return 'from-red-500 to-rose-500';
  };

  const filteredAgentes = data?.agentes?.filter(agente => 
    !filtroFaltantes || !agente.listo
  ) || [];

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Cargando requerimientos de agentes...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 text-xl mb-4">❌</div>
          <p className="text-slate-400">{error}</p>
          <button
            onClick={loadAgentRequirements}
            className="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const resumen = data?.resumen || {};

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                <span className="text-3xl">🤖</span>
                Checklist de Agentes
              </h1>
              <p className="text-slate-400 mt-1">
                Requerimientos documentales por agente de Revisar.IA
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filtroFaltantes}
                  onChange={(e) => setFiltroFaltantes(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-0"
                />
                Solo con documentos faltantes
              </label>
              
              <button
                onClick={handleGoToBiblioteca}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg transition-all flex items-center gap-2 text-sm font-medium"
              >
                <span>📚</span>
                Ir a Bibliotecaria
              </button>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
              <div className="text-3xl font-bold text-white">{resumen.completitud_general || 0}%</div>
              <div className="text-sm text-slate-400 mt-1">Completitud General</div>
              <div className="mt-2 w-full bg-slate-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full bg-gradient-to-r ${getCompletitudColor(resumen.completitud_general || 0)} transition-all`}
                  style={{ width: `${resumen.completitud_general || 0}%` }}
                />
              </div>
            </div>
            
            <div className="bg-green-900/30 rounded-xl p-4 border border-green-700/50">
              <div className="text-3xl font-bold text-green-400">{resumen.agentes_listos || 0}</div>
              <div className="text-sm text-green-300 mt-1">Agentes Listos</div>
            </div>
            
            <div className="bg-amber-900/30 rounded-xl p-4 border border-amber-700/50">
              <div className="text-3xl font-bold text-amber-400">{resumen.agentes_pendientes || 0}</div>
              <div className="text-sm text-amber-300 mt-1">Agentes Pendientes</div>
            </div>
            
            <div className="bg-blue-900/30 rounded-xl p-4 border border-blue-700/50">
              <div className="text-3xl font-bold text-blue-400">
                {resumen.total_documentos_disponibles || 0}/{resumen.total_documentos_requeridos || 0}
              </div>
              <div className="text-sm text-blue-300 mt-1">Documentos en Acervo</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredAgentes.map((agente) => (
            <div
              key={agente.agent_id}
              className="bg-white/5 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden hover:border-slate-600/50 transition-colors"
            >
              <div className={`bg-gradient-to-r ${agente.color} p-4`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-2xl">
                      {agente.icono}
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-lg">
                        {agente.id} - {agente.nombre}
                      </h3>
                      <p className="text-white/80 text-sm">{agente.descripcion}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">
                      {agente.completitud}%
                    </div>
                    <div className="text-xs text-white/70">
                      {agente.disponibles}/{agente.total_requeridos} docs
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4">
                <div className="w-full bg-slate-700 rounded-full h-2 mb-4">
                  <div
                    className={`h-2 rounded-full bg-gradient-to-r ${agente.color} transition-all`}
                    style={{ width: `${agente.completitud}%` }}
                  />
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Documentos Requeridos
                  </h4>
                  <div className="grid grid-cols-1 gap-1.5">
                    {agente.documentos.map((doc, idx) => (
                      <div
                        key={idx}
                        className={`flex items-center justify-between p-2 rounded-lg text-sm ${
                          doc.disponible
                            ? 'bg-green-900/20 border border-green-700/30'
                            : 'bg-red-900/20 border border-red-700/30'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-base">
                            {doc.disponible ? '✅' : '❌'}
                          </span>
                          <span className={doc.disponible ? 'text-green-300' : 'text-red-300'}>
                            {doc.nombre}
                          </span>
                        </div>
                        <span className="text-xs text-slate-500">
                          {doc.categoria.replace('_', ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {!agente.listo && (
                  <button
                    onClick={handleGoToBiblioteca}
                    className="mt-4 w-full py-2.5 bg-slate-700/50 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg transition-colors flex items-center justify-center gap-2 text-sm font-medium border border-slate-600/50"
                  >
                    <span>📥</span>
                    Cargar Documentos Faltantes
                  </button>
                )}
                
                {agente.listo && (
                  <div className="mt-4 py-2.5 bg-green-900/20 text-green-400 rounded-lg flex items-center justify-center gap-2 text-sm font-medium border border-green-700/30">
                    <span>✨</span>
                    Agente Listo
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {filteredAgentes.length === 0 && (
          <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-12 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h3 className="text-xl font-bold text-white mb-2">
              ¡Todos los agentes están listos!
            </h3>
            <p className="text-slate-400">
              Todos los agentes tienen sus documentos requeridos disponibles en el acervo.
            </p>
          </div>
        )}

        <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-4">
          <div className="flex items-center justify-between text-sm text-slate-400">
            <span>
              Mostrando {filteredAgentes.length} de {data?.agentes?.length || 0} agentes
            </span>
            <button
              onClick={loadAgentRequirements}
              className="flex items-center gap-2 text-purple-400 hover:text-purple-300 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Actualizar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentChecklist;
