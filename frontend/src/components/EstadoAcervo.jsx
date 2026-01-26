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

const getCriticidadColor = (criticidad) => {
  switch (criticidad) {
    case 'critico':
      return 'text-red-400 bg-red-500/20 border-red-500/30';
    case 'importante':
      return 'text-amber-400 bg-amber-500/20 border-amber-500/30';
    case 'recomendado':
      return 'text-blue-400 bg-blue-500/20 border-blue-500/30';
    default:
      return 'text-slate-400 bg-slate-500/20 border-slate-500/30';
  }
};

const getCriticidadLabel = (criticidad) => {
  switch (criticidad) {
    case 'critico':
      return 'Crítico';
    case 'importante':
      return 'Importante';
    case 'recomendado':
      return 'Recomendado';
    default:
      return criticidad;
  }
};

const formatFechaEspanol = (fecha) => {
  if (!fecha) return null;
  try {
    const date = new Date(fecha);
    return date.toLocaleDateString('es-MX', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  } catch {
    return fecha;
  }
};

const StatsModal = ({ statsDoc, onClose }) => {
  if (!statsDoc) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800/95 backdrop-blur-xl rounded-2xl border border-slate-700/50 max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span>📊</span> Estadísticas del Documento
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-slate-400 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-700/50 rounded-xl p-4 border border-slate-600/30">
                <div className="text-2xl font-bold text-purple-400">{statsDoc.total_chunks || 0}</div>
                <div className="text-xs text-slate-400 mt-1">Total Chunks</div>
              </div>
              <div className="bg-slate-700/50 rounded-xl p-4 border border-slate-600/30">
                <div className="text-2xl font-bold text-blue-400">{statsDoc.total_articulos || 0}</div>
                <div className="text-xs text-slate-400 mt-1">Total Artículos</div>
              </div>
              <div className="bg-slate-700/50 rounded-xl p-4 border border-slate-600/30">
                <div className="text-2xl font-bold text-green-400">{statsDoc.veces_recuperado || 0}</div>
                <div className="text-xs text-slate-400 mt-1">Veces Recuperado</div>
              </div>
              <div className="bg-slate-700/50 rounded-xl p-4 border border-slate-600/30">
                <div className="text-2xl font-bold text-amber-400">{(statsDoc.caracteres || 0).toLocaleString()}</div>
                <div className="text-xs text-slate-400 mt-1">Caracteres</div>
              </div>
            </div>

            {statsDoc.agentes_asignados && statsDoc.agentes_asignados.length > 0 && (
              <div className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/30">
                <h3 className="text-sm font-semibold text-slate-300 mb-3">🤖 Agentes Asignados</h3>
                <div className="flex flex-wrap gap-2">
                  {statsDoc.agentes_asignados.map((agente, idx) => (
                    <span key={idx} className="text-xs px-3 py-1.5 bg-purple-500/20 text-purple-300 rounded-full border border-purple-500/30">
                      {agente}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {statsDoc.tipos_contenido && statsDoc.tipos_contenido.length > 0 && (
              <div className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/30">
                <h3 className="text-sm font-semibold text-slate-300 mb-3">📑 Tipos de Contenido</h3>
                <div className="flex flex-wrap gap-2">
                  {statsDoc.tipos_contenido.map((tipo, idx) => (
                    <span key={idx} className="text-xs px-3 py-1.5 bg-blue-500/20 text-blue-300 rounded-full border border-blue-500/30">
                      {tipo}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-medium transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const AgentCard = ({ agente, onUpload, onReingestar, onVerStats, reingestando, expandedAgent, setExpandedAgent }) => {
  const isExpanded = expandedAgent === agente.id;
  
  return (
    <div className="bg-slate-800/50 backdrop-blur-lg rounded-xl border border-slate-700/50 overflow-hidden transition-all duration-300 hover:border-slate-600/50">
      <button
        onClick={() => setExpandedAgent(isExpanded ? null : agente.id)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-700/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{agente.icono}</span>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500">{agente.id}</span>
              <h3 className="font-semibold text-white">{agente.nombre}</h3>
            </div>
            <p className="text-sm text-slate-400">
              {agente.docs_cargados}/{agente.docs_totales} documentos
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="w-32">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Progreso</span>
              <span className={`font-bold ${agente.progreso >= 80 ? 'text-green-400' : agente.progreso >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                {agente.progreso}%
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all ${
                  agente.progreso >= 80 ? 'bg-green-500' : 
                  agente.progreso >= 50 ? 'bg-amber-500' : 
                  'bg-red-500'
                }`}
                style={{ width: `${agente.progreso}%` }}
              />
            </div>
          </div>
          <svg 
            className={`w-5 h-5 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>
      
      {isExpanded && (
        <div className="border-t border-slate-700/50 p-4 space-y-2 bg-slate-900/30">
          {agente.documentos.map((doc) => (
            <div 
              key={doc.id}
              className={`flex items-center justify-between p-3 rounded-lg border ${
                doc.cargado 
                  ? doc.pendiente_procesar 
                    ? 'bg-amber-500/10 border-amber-500/30'
                    : 'bg-green-500/10 border-green-500/30' 
                  : 'bg-slate-800/50 border-slate-600/30'
              }`}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <span className="text-lg">
                  {doc.cargado ? (doc.pendiente_procesar ? '⏳' : '✅') : '⬚'}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`${doc.cargado ? 'font-bold text-white' : 'text-slate-300'} truncate`}>
                      {doc.nombre}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${getCriticidadColor(doc.criticidad)}`}>
                      {getCriticidadLabel(doc.criticidad)}
                    </span>
                    {doc.cargado && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-600/50 text-slate-300 border border-slate-500/30">
                        v{doc.version || '1.0'}
                      </span>
                    )}
                    {doc.pendiente_procesar && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">
                        ⚠️ PENDIENTE PROCESAR
                      </span>
                    )}
                  </div>
                  {doc.cargado && (
                    <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                      {doc.fecha_carga && (
                        <span>📅 {formatFechaEspanol(doc.fecha_carga)}</span>
                      )}
                      {doc.ultima_reforma && (
                        <span className="text-amber-400">⚡ Reforma: {doc.ultima_reforma}</span>
                      )}
                    </div>
                  )}
                  {doc.descripcion && !doc.cargado && (
                    <p className="text-xs text-slate-500 truncate mt-0.5">{doc.descripcion}</p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-2 ml-2">
                {doc.cargado ? (
                  <>
                    <span className="text-xs text-green-400 bg-green-500/20 px-2 py-1 rounded-md">
                      {doc.chunks_count} chunks
                    </span>
                    <button 
                      className="p-1.5 hover:bg-slate-700 rounded-md transition-colors"
                      title="Ver documento"
                    >
                      <span className="text-lg">👁️</span>
                    </button>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        onVerStats(doc.documento_id || doc.id);
                      }}
                      className="p-1.5 hover:bg-slate-700 rounded-md transition-colors"
                      title="Ver estadísticas"
                    >
                      <span className="text-lg">📊</span>
                    </button>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        onReingestar(doc.documento_id || doc.id);
                      }}
                      disabled={reingestando === (doc.documento_id || doc.id)}
                      className={`p-1.5 hover:bg-slate-700 rounded-md transition-colors ${
                        reingestando === (doc.documento_id || doc.id) ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                      title={doc.pendiente_procesar ? "Procesar documento" : "Reingestar documento"}
                    >
                      <span className={`text-lg ${reingestando === (doc.documento_id || doc.id) ? 'animate-spin inline-block' : ''}`}>
                        ⟳
                      </span>
                    </button>
                  </>
                ) : (
                  <>
                    <span className="text-xs text-slate-500 bg-slate-700/50 px-2 py-1 rounded-md">
                      falta
                    </span>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        onUpload(doc);
                      }}
                      className="p-1.5 hover:bg-slate-700 rounded-md transition-colors"
                      title="Subir documento"
                    >
                      <span className="text-lg">📤</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const EstadoAcervo = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [expandedAgent, setExpandedAgent] = useState(null);
  const [reingestando, setReingestando] = useState(null);
  const [statsDoc, setStatsDoc] = useState(null);
  const [documentosPendientes, setDocumentosPendientes] = useState(0);

  useEffect(() => {
    loadEstadoAcervo();
  }, []);

  useEffect(() => {
    if (data?.documentos_pendientes !== undefined) {
      setDocumentosPendientes(data.documentos_pendientes);
    } else if (data?.agentes) {
      const pendientes = data.agentes.reduce((acc, agente) => {
        return acc + (agente.documentos?.filter(d => d.pendiente_procesar)?.length || 0);
      }, 0);
      setDocumentosPendientes(pendientes);
    }
  }, [data]);

  const loadEstadoAcervo = async () => {
    try {
      setLoading(true);
      const response = await api.get('/biblioteca/estado-acervo');
      setData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error loading estado acervo:', err);
      setError('No se pudo cargar el estado del acervo');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = (doc) => {
    navigate('/biblioteca', { state: { uploadDoc: doc } });
  };

  const handleReingestar = async (docId) => {
    if (!docId || reingestando) return;
    
    try {
      setReingestando(docId);
      const response = await api.post(`/biblioteca/documento/${docId}/reingestar`);
      
      if (response.data?.success) {
        alert(`✅ Documento reingestado exitosamente.\n${response.data.message || ''}`);
      } else {
        alert(`⚠️ ${response.data?.message || 'Documento procesado'}`);
      }
      
      await loadEstadoAcervo();
    } catch (err) {
      console.error('Error reingestando documento:', err);
      alert(`❌ Error al reingestar: ${err.response?.data?.detail || err.message}`);
    } finally {
      setReingestando(null);
    }
  };

  const handleReingestarTodos = async () => {
    if (reingestando) return;
    
    const confirmar = window.confirm(`¿Desea procesar ${documentosPendientes} documento(s) pendiente(s)?`);
    if (!confirmar) return;
    
    try {
      setReingestando('todos');
      const response = await api.post('/biblioteca/reingestar-todos');
      
      if (response.data?.success) {
        alert(`✅ ${response.data.procesados || documentosPendientes} documentos procesados exitosamente.`);
      } else {
        alert(`⚠️ ${response.data?.message || 'Proceso completado'}`);
      }
      
      await loadEstadoAcervo();
    } catch (err) {
      console.error('Error reingestando todos:', err);
      alert(`❌ Error al procesar: ${err.response?.data?.detail || err.message}`);
    } finally {
      setReingestando(null);
    }
  };

  const handleVerStats = async (docId) => {
    if (!docId) return;
    
    try {
      const response = await api.get(`/biblioteca/documento/${docId}/stats`);
      setStatsDoc(response.data);
    } catch (err) {
      console.error('Error obteniendo stats:', err);
      alert(`❌ Error al obtener estadísticas: ${err.response?.data?.detail || err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-200 rounded-full animate-spin border-t-purple-600 mx-auto" />
          <p className="mt-6 text-slate-400">Cargando estado del acervo...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <p className="text-red-400">{error}</p>
          <button 
            onClick={loadEstadoAcervo}
            className="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const completitudColor = data?.completitud_global >= 80 ? 'text-green-400' : 
                           data?.completitud_global >= 50 ? 'text-amber-400' : 
                           'text-red-400';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg">
                <span className="text-3xl">📚</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Estado del Acervo</h1>
                <p className="text-slate-400">Documentos requeridos por agente para Bibliotecar.IA</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={loadEstadoAcervo}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium transition-all shadow-lg hover:shadow-purple-500/25 disabled:opacity-50"
              >
                <svg className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Actualizar
              </button>
              
              {documentosPendientes > 0 && (
                <button
                  onClick={handleReingestarTodos}
                  disabled={reingestando === 'todos'}
                  className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white rounded-xl font-medium transition-all shadow-lg hover:shadow-amber-500/25 disabled:opacity-50"
                >
                  {reingestando === 'todos' ? (
                    <span className="animate-spin">⟳</span>
                  ) : (
                    <span>⚡</span>
                  )}
                  Procesar {documentosPendientes} pendiente{documentosPendientes !== 1 ? 's' : ''}
                </button>
              )}
            </div>
          </div>
          
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/30">
              <div className={`text-3xl font-bold ${completitudColor}`}>
                {data?.completitud_global || 0}%
              </div>
              <p className="text-xs text-slate-500 mt-1">Completitud Global</p>
            </div>
            <div className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/30">
              <div className="text-3xl font-bold text-white">
                {data?.documentos_cargados || 0}/{data?.total_documentos || 0}
              </div>
              <p className="text-xs text-slate-500 mt-1">Documentos</p>
            </div>
            <div className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/30">
              <div className="text-3xl font-bold text-green-400">
                {data?.documentos_cargados || 0}
              </div>
              <p className="text-xs text-slate-500 mt-1">Cargados</p>
            </div>
            <div className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/30">
              <div className={`text-3xl font-bold ${documentosPendientes > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
                {documentosPendientes}
              </div>
              <p className="text-xs text-slate-500 mt-1">Pendientes</p>
            </div>
          </div>
          
          <div className="mt-6">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-400">Progreso General</span>
              <span className={`font-semibold ${completitudColor}`}>
                {data?.completitud_global || 0}%
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-3">
              <div 
                className={`h-3 rounded-full transition-all ${
                  data?.completitud_global >= 80 ? 'bg-gradient-to-r from-green-500 to-emerald-400' : 
                  data?.completitud_global >= 50 ? 'bg-gradient-to-r from-amber-500 to-yellow-400' : 
                  'bg-gradient-to-r from-red-500 to-rose-400'
                }`}
                style={{ width: `${data?.completitud_global || 0}%` }}
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <span>🤖</span> Agentes
          </h2>
        </div>
        
        <div className="space-y-3">
          {data?.agentes?.map((agente) => (
            <AgentCard 
              key={agente.id} 
              agente={agente}
              onUpload={handleUpload}
              onReingestar={handleReingestar}
              onVerStats={handleVerStats}
              reingestando={reingestando}
              expandedAgent={expandedAgent}
              setExpandedAgent={setExpandedAgent}
            />
          ))}
        </div>

        <div className="mt-6 bg-slate-800/30 backdrop-blur rounded-xl border border-slate-700/50 p-4">
          <h3 className="text-sm font-semibold text-slate-400 mb-3">Leyenda de Criticidad</h3>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-1 rounded-full border ${getCriticidadColor('critico')}`}>
                Crítico
              </span>
              <span className="text-xs text-slate-500">Indispensable para el agente</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-1 rounded-full border ${getCriticidadColor('importante')}`}>
                Importante
              </span>
              <span className="text-xs text-slate-500">Mejora significativamente la calidad</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-1 rounded-full border ${getCriticidadColor('recomendado')}`}>
                Recomendado
              </span>
              <span className="text-xs text-slate-500">Complementa el conocimiento</span>
            </div>
          </div>
        </div>

        <div className="mt-4 text-center">
          <button
            onClick={() => navigate('/biblioteca')}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium transition-all shadow-lg hover:shadow-purple-500/25"
          >
            <span>📚</span>
            Ir a Bibliotecar.IA
          </button>
        </div>
      </div>

      <StatsModal statsDoc={statsDoc} onClose={() => setStatsDoc(null)} />
    </div>
  );
};

export default EstadoAcervo;
