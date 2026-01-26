import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Shield,
  Clock,
  Users,
  FileText,
  Scale,
  Calculator,
  Cloud,
  Download,
  Lock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Upload,
  RefreshCw,
  ChevronLeft,
  Hash,
  Calendar,
  Building
} from 'lucide-react';

const API_BASE = '/api/defense-files';

const TABS = [
  { id: 'timeline', label: 'Timeline', icon: Clock },
  { id: 'proveedores', label: 'Proveedores', icon: Users },
  { id: 'cfdis', label: 'CFDIs', icon: FileText },
  { id: 'fundamentos', label: 'Fundamentos', icon: Scale },
  { id: 'calculos', label: 'Cálculos', icon: Calculator }
];

const ESTADO_CONFIG = {
  abierto: { color: 'bg-green-500', text: 'Abierto', icon: CheckCircle },
  en_revision: { color: 'bg-yellow-500', text: 'En Revisión', icon: AlertTriangle },
  pendiente: { color: 'bg-orange-500', text: 'Pendiente', icon: Clock },
  cerrado: { color: 'bg-blue-500', text: 'Cerrado', icon: Lock },
  archivado: { color: 'bg-gray-500', text: 'Archivado', icon: FileText }
};

const AGENTE_COLORS = {
  A1: 'bg-purple-600', A2: 'bg-blue-600', A3: 'bg-green-600',
  A4: 'bg-orange-600', A5: 'bg-pink-600', A6: 'bg-cyan-600',
  A7: 'bg-red-600', SYS: 'bg-gray-600', USR: 'bg-indigo-600'
};

export default function DefenseFileViewer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('timeline');
  const [defenseFile, setDefenseFile] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [proveedores, setProveedores] = useState([]);
  const [cfdis, setCfdis] = useState([]);
  const [fundamentos, setFundamentos] = useState([]);
  const [calculos, setCalculos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [closing, setClosing] = useState(false);
  const [error, setError] = useState(null);

  const fetchDefenseFile = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/${id}`);
      const data = await response.json();
      if (data.success) {
        setDefenseFile(data.defense_file);
      } else {
        setError(data.error || 'Error cargando expediente');
      }
    } catch (err) {
      setError('Error de conexión');
    }
  }, [id]);

  const fetchTimeline = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/${id}/timeline`);
      const data = await response.json();
      if (data.success) {
        setTimeline(data.timeline || []);
      }
    } catch (err) {
      console.error('Error fetching timeline:', err);
    }
  }, [id]);

  const fetchProveedores = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/${id}/proveedores`);
      const data = await response.json();
      if (data.success) {
        setProveedores(data.proveedores || []);
      }
    } catch (err) {
      console.error('Error fetching proveedores:', err);
    }
  }, [id]);

  const fetchCfdis = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/${id}/cfdis`);
      const data = await response.json();
      if (data.success) {
        setCfdis(data.cfdis || []);
      }
    } catch (err) {
      console.error('Error fetching cfdis:', err);
    }
  }, [id]);

  const fetchFundamentos = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/${id}/fundamentos`);
      const data = await response.json();
      if (data.success) {
        setFundamentos(data.fundamentos || []);
      }
    } catch (err) {
      console.error('Error fetching fundamentos:', err);
    }
  }, [id]);

  const fetchCalculos = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/${id}/calculos`);
      const data = await response.json();
      if (data.success) {
        setCalculos(data.calculos || []);
      }
    } catch (err) {
      console.error('Error fetching calculos:', err);
    }
  }, [id]);

  useEffect(() => {
    const loadAll = async () => {
      setLoading(true);
      await Promise.all([
        fetchDefenseFile(),
        fetchTimeline(),
        fetchProveedores(),
        fetchCfdis(),
        fetchFundamentos(),
        fetchCalculos()
      ]);
      setLoading(false);
    };
    loadAll();
  }, [fetchDefenseFile, fetchTimeline, fetchProveedores, fetchCfdis, fetchFundamentos, fetchCalculos]);

  const handleSyncPCloud = async () => {
    setSyncing(true);
    try {
      const response = await fetch(`${API_BASE}/${id}/sincronizar-pcloud`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        alert(`Sincronizado correctamente. Carpetas creadas: ${data.carpetas_creadas || 0}`);
        fetchDefenseFile();
        fetchTimeline();
      } else {
        alert('Error: ' + (data.error || data.detail));
      }
    } catch (err) {
      alert('Error de conexión');
    } finally {
      setSyncing(false);
    }
  };

  const handleExportPDF = async () => {
    try {
      const response = await fetch(`${API_BASE}/${id}/exportar-pdf`);
      if (response.headers.get('content-type')?.includes('application/pdf')) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `expediente_${id}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const data = await response.json();
        alert('PDF generado (datos JSON): ' + JSON.stringify(data).slice(0, 200));
      }
    } catch (err) {
      alert('Error exportando PDF');
    }
  };

  const handleCloseExpediente = async () => {
    if (!window.confirm('¿Está seguro de cerrar el expediente? Esta acción generará el hash de integridad final.')) {
      return;
    }
    setClosing(true);
    try {
      const response = await fetch(`${API_BASE}/${id}/cerrar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await response.json();
      if (data.success) {
        alert(`Expediente cerrado. Hash: ${data.hash_contenido?.slice(0, 16)}...`);
        fetchDefenseFile();
        fetchTimeline();
      } else {
        alert('Error: ' + (data.error || data.detail));
      }
    } catch (err) {
      alert('Error cerrando expediente');
    } finally {
      setClosing(false);
    }
  };

  const groupEventsByDate = (events) => {
    const grouped = {};
    events.forEach(event => {
      const date = event.timestamp?.split('T')[0] || 'Sin fecha';
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(event);
    });
    return Object.entries(grouped).sort((a, b) => b[0].localeCompare(a[0]));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <p className="text-red-400">{error}</p>
          <button onClick={() => navigate('/defense-files')} className="mt-4 px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
            Volver
          </button>
        </div>
      </div>
    );
  }

  const estadoConfig = ESTADO_CONFIG[defenseFile?.estado] || ESTADO_CONFIG.abierto;
  const EstadoIcon = estadoConfig.icon;
  const stats = defenseFile?.estadisticas || {};

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <button onClick={() => navigate('/defense-files')} className="flex items-center text-gray-400 hover:text-white mb-6">
          <ChevronLeft className="w-5 h-5 mr-1" /> Volver a expedientes
        </button>

        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-4">
              <Shield className="w-12 h-12 text-blue-400" />
              <div>
                <h1 className="text-2xl font-bold">{defenseFile?.nombre}</h1>
                <p className="text-gray-400">ID: {id} | Año Fiscal: {defenseFile?.anio_fiscal}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 rounded-full text-sm flex items-center ${estadoConfig.color}`}>
                <EstadoIcon className="w-4 h-4 mr-1" />
                {estadoConfig.text}
              </span>
            </div>
          </div>

          {defenseFile?.hash_contenido && (
            <div className="mt-4 p-3 bg-gray-700 rounded flex items-center">
              <Hash className="w-5 h-5 text-green-400 mr-2" />
              <span className="text-sm font-mono text-green-400">
                Hash Integridad: {defenseFile.hash_contenido.slice(0, 32)}...
              </span>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mt-6">
            <div className="bg-gray-700 p-3 rounded text-center">
              <p className="text-2xl font-bold text-blue-400">{stats.total_eventos || 0}</p>
              <p className="text-xs text-gray-400">Eventos</p>
            </div>
            <div className="bg-gray-700 p-3 rounded text-center">
              <p className="text-2xl font-bold text-purple-400">{stats.total_proveedores || 0}</p>
              <p className="text-xs text-gray-400">Proveedores</p>
            </div>
            <div className="bg-gray-700 p-3 rounded text-center">
              <p className="text-2xl font-bold text-green-400">{stats.total_cfdis || 0}</p>
              <p className="text-xs text-gray-400">CFDIs</p>
            </div>
            <div className="bg-gray-700 p-3 rounded text-center">
              <p className="text-2xl font-bold text-orange-400">{stats.total_fundamentos || 0}</p>
              <p className="text-xs text-gray-400">Fundamentos</p>
            </div>
            <div className="bg-gray-700 p-3 rounded text-center">
              <p className="text-2xl font-bold text-pink-400">{stats.total_calculos || 0}</p>
              <p className="text-xs text-gray-400">Cálculos</p>
            </div>
            <div className="bg-gray-700 p-3 rounded text-center">
              <p className="text-lg font-bold text-yellow-400">${(stats.monto_total_cfdis || 0).toLocaleString()}</p>
              <p className="text-xs text-gray-400">Monto Total</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 mt-6">
            <button
              onClick={handleSyncPCloud}
              disabled={syncing}
              className="flex items-center px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              <Cloud className={`w-4 h-4 mr-2 ${syncing ? 'animate-pulse' : ''}`} />
              {syncing ? 'Sincronizando...' : 'Sincronizar pCloud'}
            </button>
            <button onClick={handleExportPDF} className="flex items-center px-4 py-2 bg-green-600 rounded hover:bg-green-700">
              <Download className="w-4 h-4 mr-2" /> Exportar PDF
            </button>
            {defenseFile?.estado !== 'cerrado' && (
              <button
                onClick={handleCloseExpediente}
                disabled={closing}
                className="flex items-center px-4 py-2 bg-red-600 rounded hover:bg-red-700 disabled:opacity-50"
              >
                <Lock className={`w-4 h-4 mr-2 ${closing ? 'animate-pulse' : ''}`} />
                {closing ? 'Cerrando...' : 'Cerrar Expediente'}
              </button>
            )}
          </div>
        </div>

        <div className="flex space-x-1 mb-4 bg-gray-800 p-1 rounded-lg overflow-x-auto">
          {TABS.map(tab => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-4 py-2 rounded transition-colors whitespace-nowrap ${
                  activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-700'
                }`}
              >
                <TabIcon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          {activeTab === 'timeline' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold flex items-center">
                <Clock className="w-5 h-5 mr-2 text-blue-400" /> Timeline de Eventos
              </h2>
              {groupEventsByDate(timeline).map(([date, events]) => (
                <div key={date} className="border-l-2 border-gray-600 pl-4">
                  <div className="flex items-center mb-3">
                    <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                    <span className="font-medium text-gray-300">{date}</span>
                    <span className="ml-2 text-xs text-gray-500">({events.length} eventos)</span>
                  </div>
                  <div className="space-y-3">
                    {events.map((event, idx) => (
                      <div key={idx} className="bg-gray-700 rounded p-3">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-0.5 rounded text-xs ${AGENTE_COLORS[event.agente] || 'bg-gray-600'}`}>
                              {event.agente}
                            </span>
                            <span className="font-medium">{event.titulo}</span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {event.timestamp?.split('T')[1]?.slice(0, 8)}
                          </span>
                        </div>
                        {event.descripcion && (
                          <p className="text-sm text-gray-400 mt-2">{event.descripcion}</p>
                        )}
                        <div className="flex items-center mt-2 space-x-2">
                          <span className="text-xs px-2 py-0.5 bg-gray-600 rounded">{event.tipo}</span>
                          {event.hash_evento && (
                            <span className="text-xs text-gray-500 font-mono">#{event.hash_evento?.slice(0, 8)}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {timeline.length === 0 && (
                <p className="text-gray-500 text-center py-8">No hay eventos registrados</p>
              )}
            </div>
          )}

          {activeTab === 'proveedores' && (
            <div>
              <h2 className="text-xl font-semibold flex items-center mb-4">
                <Users className="w-5 h-5 mr-2 text-purple-400" /> Proveedores ({proveedores.length})
              </h2>
              <div className="grid gap-4">
                {proveedores.map((prov, idx) => (
                  <div key={idx} className="bg-gray-700 rounded p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold">{prov.rfc}</p>
                        <p className="text-gray-400">{prov.razon_social || prov.nombre_comercial}</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${
                        prov.nivel_riesgo === 'alto' ? 'bg-red-600' :
                        prov.nivel_riesgo === 'medio' ? 'bg-yellow-600' : 'bg-green-600'
                      }`}>
                        Riesgo: {prov.nivel_riesgo || 'N/A'}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-3 text-sm">
                      <div>
                        <span className="text-gray-500">69B:</span>
                        <span className="ml-1">{prov.lista_69b_status || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">EFOS:</span>
                        <span className="ml-1">{prov.efos_status || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Opinión:</span>
                        <span className="ml-1">{prov.opinion_cumplimiento || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {proveedores.length === 0 && (
                  <p className="text-gray-500 text-center py-8">No hay proveedores registrados</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'cfdis' && (
            <div>
              <h2 className="text-xl font-semibold flex items-center mb-4">
                <FileText className="w-5 h-5 mr-2 text-green-400" /> CFDIs ({cfdis.length})
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="p-2 text-left">UUID</th>
                      <th className="p-2 text-left">Emisor</th>
                      <th className="p-2 text-right">Total</th>
                      <th className="p-2 text-center">Estado SAT</th>
                      <th className="p-2 text-center">Deducible</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cfdis.map((cfdi, idx) => (
                      <tr key={idx} className="border-b border-gray-700 hover:bg-gray-750">
                        <td className="p-2 font-mono text-xs">{cfdi.uuid?.slice(0, 12)}...</td>
                        <td className="p-2">{cfdi.emisor_rfc}</td>
                        <td className="p-2 text-right">${(cfdi.total || 0).toLocaleString()}</td>
                        <td className="p-2 text-center">
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            cfdi.status_sat === 'Vigente' ? 'bg-green-600' : 'bg-red-600'
                          }`}>
                            {cfdi.status_sat || 'N/A'}
                          </span>
                        </td>
                        <td className="p-2 text-center">
                          {cfdi.es_deducible ? (
                            <CheckCircle className="w-4 h-4 text-green-400 mx-auto" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-400 mx-auto" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {cfdis.length === 0 && (
                  <p className="text-gray-500 text-center py-8">No hay CFDIs registrados</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'fundamentos' && (
            <div>
              <h2 className="text-xl font-semibold flex items-center mb-4">
                <Scale className="w-5 h-5 mr-2 text-orange-400" /> Fundamentos Legales ({fundamentos.length})
              </h2>
              <div className="grid gap-4">
                {fundamentos.map((fund, idx) => (
                  <div key={idx} className="bg-gray-700 rounded p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold">{fund.documento} - Art. {fund.articulo}</p>
                        {fund.fraccion && <p className="text-sm text-gray-400">Fracción {fund.fraccion}</p>}
                      </div>
                      <span className="px-2 py-1 bg-orange-600 rounded text-xs">{fund.tipo}</span>
                    </div>
                    {fund.texto_relevante && (
                      <p className="text-sm text-gray-300 mt-2 italic">"{fund.texto_relevante}"</p>
                    )}
                    {fund.aplicacion && (
                      <p className="text-sm text-gray-400 mt-2">Aplicación: {fund.aplicacion}</p>
                    )}
                  </div>
                ))}
                {fundamentos.length === 0 && (
                  <p className="text-gray-500 text-center py-8">No hay fundamentos registrados</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'calculos' && (
            <div>
              <h2 className="text-xl font-semibold flex items-center mb-4">
                <Calculator className="w-5 h-5 mr-2 text-pink-400" /> Cálculos Fiscales ({calculos.length})
              </h2>
              <div className="grid gap-4">
                {calculos.map((calc, idx) => (
                  <div key={idx} className="bg-gray-700 rounded p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold">{calc.tipo} - {calc.periodo}</p>
                        {calc.concepto && <p className="text-sm text-gray-400">{calc.concepto}</p>}
                      </div>
                      <span className="text-xl font-bold text-pink-400">
                        ${(calc.impuesto_calculado || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-3 text-sm">
                      <div>
                        <span className="text-gray-500">Base:</span>
                        <span className="ml-1">${(calc.base_gravable || 0).toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Tasa:</span>
                        <span className="ml-1">{((calc.tasa || 0) * 100).toFixed(2)}%</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Por:</span>
                        <span className="ml-1">{calc.calculado_por || 'Sistema'}</span>
                      </div>
                    </div>
                    {calc.fundamento_legal && (
                      <p className="text-xs text-gray-500 mt-2">Fundamento: {calc.fundamento_legal}</p>
                    )}
                  </div>
                ))}
                {calculos.length === 0 && (
                  <p className="text-gray-500 text-center py-8">No hay cálculos registrados</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
