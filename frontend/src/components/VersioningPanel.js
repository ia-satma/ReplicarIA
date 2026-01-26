import React, { useState, useEffect } from 'react';
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api`
    : '/api'
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  const empresaId = localStorage.getItem('empresa_id') || 'demo-empresa-001';
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  config.headers['X-Empresa-ID'] = empresaId;
  return config;
});

const severidadColors = {
  critica: 'bg-red-100 text-red-800 border-red-300',
  alta: 'bg-orange-100 text-orange-800 border-orange-300',
  media: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  baja: 'bg-blue-100 text-blue-800 border-blue-300',
  info: 'bg-gray-100 text-gray-800 border-gray-300'
};

const tipoCambioIcons = {
  creacion: '🆕',
  documento_agregado: '📄',
  documento_eliminado: '🗑️',
  documento_actualizado: '📝',
  validacion_ocr: '🔍',
  simulacion_red_team: '🛡️',
  correccion_vulnerabilidad: '✅',
  cambio_datos_proyecto: '📊',
  comunicacion_proveedor: '📧',
  comunicacion_cliente: '💼',
  ajuste_monto: '💰',
  ajuste_fecha: '📅',
  regeneracion_expediente: '🔄',
  nota_interna: '📌',
  aprobacion: '✓',
  rechazo: '✗',
  otro: '📋'
};

export default function VersioningPanel({ proyectoId, onClose }) {
  const [proyecto, setProyecto] = useState(null);
  const [versiones, setVersiones] = useState([]);
  const [bitacora, setBitacora] = useState([]);
  const [activeTab, setActiveTab] = useState('resumen');
  const [loading, setLoading] = useState(true);
  const [showNuevaVersion, setShowNuevaVersion] = useState(false);
  const [showComunicacion, setShowComunicacion] = useState(false);
  const [motivo, setMotivo] = useState('');
  const [comunicacion, setComunicacion] = useState({
    contraparte: '',
    tipo_contraparte: 'proveedor',
    asunto: '',
    descripcion: ''
  });

  useEffect(() => {
    if (proyectoId) {
      cargarDatos();
    }
  }, [proyectoId]);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const [proyRes, verRes, bitRes] = await Promise.all([
        api.get(`/versioning/proyectos/${proyectoId}`),
        api.get(`/versioning/proyectos/${proyectoId}/versiones`),
        api.get(`/versioning/proyectos/${proyectoId}/bitacora`)
      ]);
      setProyecto(proyRes.data.proyecto);
      setVersiones(verRes.data.versiones || []);
      setBitacora(bitRes.data.bitacora || []);
    } catch (error) {
      console.error('Error cargando datos:', error);
    }
    setLoading(false);
  };

  const crearNuevaVersion = async () => {
    if (!motivo.trim()) return;
    try {
      await api.post(`/versioning/proyectos/${proyectoId}/versiones`, {
        datos_proyecto: proyecto?.ultima_version?.snapshot_proyecto || {},
        documentos: [],
        motivo: motivo,
        usuario: 'Usuario Dashboard',
        generar_expediente: true
      });
      setMotivo('');
      setShowNuevaVersion(false);
      cargarDatos();
    } catch (error) {
      console.error('Error creando versión:', error);
    }
  };

  const registrarComunicacion = async () => {
    if (!comunicacion.contraparte || !comunicacion.asunto) return;
    try {
      await api.post(`/versioning/proyectos/${proyectoId}/bitacora/comunicacion`, {
        usuario: 'Usuario Dashboard',
        ...comunicacion
      });
      setComunicacion({ contraparte: '', tipo_contraparte: 'proveedor', asunto: '', descripcion: '' });
      setShowComunicacion(false);
      cargarDatos();
    } catch (error) {
      console.error('Error registrando comunicación:', error);
    }
  };

  const exportarBitacora = async (formato) => {
    try {
      const res = await api.get(`/versioning/proyectos/${proyectoId}/bitacora/reporte?formato=${formato}`);
      if (formato === 'markdown') {
        const blob = new Blob([res.data.contenido], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bitacora_${proyectoId}.md`;
        a.click();
      } else {
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bitacora_${proyectoId}.json`;
        a.click();
      }
    } catch (error) {
      console.error('Error exportando:', error);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando historial de cambios...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-6">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold">Historial y Control de Cambios</h2>
              {proyecto && (
                <div className="mt-2 space-y-1">
                  <p className="text-blue-100">{proyecto.nombre}</p>
                  <p className="font-mono text-lg">{proyecto.folio_actual}</p>
                </div>
              )}
            </div>
            <button onClick={onClose} className="text-white/80 hover:text-white text-2xl">
              ✕
            </button>
          </div>
          
          <div className="flex gap-2 mt-4">
            {['resumen', 'versiones', 'bitacora'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === tab 
                    ? 'bg-white text-blue-700' 
                    : 'bg-blue-500/30 text-white hover:bg-blue-500/50'
                }`}
              >
                {tab === 'resumen' && '📊 Vista General'}
                {tab === 'versiones' && '📁 Historial'}
                {tab === 'bitacora' && '📋 Registro de Actividad'}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'resumen' && proyecto && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 rounded-xl p-4 text-center">
                  <div className="text-3xl font-bold text-blue-700">v{proyecto.version_actual}</div>
                  <div className="text-sm text-gray-600">Versión Actual</div>
                </div>
                <div className="bg-green-50 rounded-xl p-4 text-center">
                  <div className="text-3xl font-bold text-green-700">{proyecto.total_versiones}</div>
                  <div className="text-sm text-gray-600">Versiones Creadas</div>
                </div>
                <div className="bg-purple-50 rounded-xl p-4 text-center">
                  <div className="text-3xl font-bold text-purple-700">{proyecto.total_entradas_bitacora}</div>
                  <div className="text-sm text-gray-600">Actividades Registradas</div>
                </div>
                <div className="bg-orange-50 rounded-xl p-4 text-center">
                  <div className="text-3xl font-bold text-orange-700 capitalize">{proyecto.estado}</div>
                  <div className="text-sm text-gray-600">Estado</div>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowNuevaVersion(true)}
                  className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  🔄 Crear Nueva Versión
                </button>
                <button
                  onClick={() => setShowComunicacion(true)}
                  className="flex-1 bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 transition-colors"
                >
                  📧 Documentar Comunicación
                </button>
              </div>

              {proyecto.ultima_version && (
                <div className="bg-gray-50 rounded-xl p-4">
                  <h3 className="font-semibold text-gray-700 mb-3">Versión Más Reciente</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><span className="text-gray-500">Estado:</span> {proyecto.ultima_version.estado}</div>
                    <div><span className="text-gray-500">Documentos:</span> {proyecto.ultima_version.documentos}</div>
                    <div><span className="text-gray-500">Puntuación de Riesgo:</span> {proyecto.ultima_version.risk_score || 'N/A'}</div>
                    <div><span className="text-gray-500">PDF:</span> {proyecto.ultima_version.pdf_generado ? '✅' : '❌'}</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'versiones' && (
            <div className="space-y-4">
              {versiones.map((v, idx) => (
                <div key={idx} className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-mono text-lg font-semibold text-blue-700">{v.folio}</div>
                      <div className="text-sm text-gray-500 mt-1">
                        {new Date(v.fecha_creacion).toLocaleString('es-MX')} por {v.creado_por}
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      v.estado === 'aprobado' ? 'bg-green-100 text-green-800' :
                      v.estado === 'borrador' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {v.estado}
                    </span>
                  </div>
                  <p className="mt-2 text-gray-700">{v.motivo}</p>
                  <div className="mt-3 flex gap-4 text-sm text-gray-500">
                    <span>📄 {v.documentos} docs</span>
                    {v.risk_score && <span>⚠️ Riesgo: {v.risk_score}</span>}
                    {v.pdf_generado && <span>📕 PDF</span>}
                    {v.zip_generado && <span>📦 ZIP</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'bitacora' && (
            <div className="space-y-4">
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => exportarBitacora('markdown')}
                  className="px-4 py-2 bg-gray-100 rounded-lg text-sm hover:bg-gray-200"
                >
                  📥 Descargar Markdown
                </button>
                <button
                  onClick={() => exportarBitacora('json')}
                  className="px-4 py-2 bg-gray-100 rounded-lg text-sm hover:bg-gray-200"
                >
                  📥 Descargar Datos
                </button>
              </div>
              
              {bitacora.map((entrada, idx) => (
                <div key={idx} className={`rounded-xl p-4 border ${severidadColors[entrada.severidad] || severidadColors.info}`}>
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{tipoCambioIcons[entrada.tipo_cambio] || '📋'}</span>
                    <div className="flex-1">
                      <div className="flex justify-between items-start">
                        <h4 className="font-semibold">{entrada.titulo}</h4>
                        <span className="text-xs opacity-70">
                          {new Date(entrada.timestamp).toLocaleString('es-MX')}
                        </span>
                      </div>
                      <p className="text-sm mt-1 opacity-80">{entrada.descripcion}</p>
                      <div className="mt-2 text-xs opacity-60">
                        Por: {entrada.usuario}
                        {entrada.es_comunicacion_externa && ` → ${entrada.contraparte}`}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {showNuevaVersion && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-60">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <h3 className="text-xl font-bold mb-4">Crear Nueva Versión</h3>
              <textarea
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                placeholder="Describe brevemente los cambios realizados..."
                className="w-full border rounded-lg p-3 h-32 mb-4"
              />
              <div className="flex gap-3">
                <button onClick={() => setShowNuevaVersion(false)} className="flex-1 py-2 border rounded-lg">
                  Cancelar
                </button>
                <button onClick={crearNuevaVersion} className="flex-1 py-2 bg-blue-600 text-white rounded-lg">
                  Crear Versión
                </button>
              </div>
            </div>
          </div>
        )}

        {showComunicacion && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-60">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <h3 className="text-xl font-bold mb-4">Documentar Comunicación</h3>
              <div className="space-y-3">
                <input
                  value={comunicacion.contraparte}
                  onChange={(e) => setComunicacion({...comunicacion, contraparte: e.target.value})}
                  placeholder="Nombre de la persona o empresa..."
                  className="w-full border rounded-lg p-3"
                />
                <select
                  value={comunicacion.tipo_contraparte}
                  onChange={(e) => setComunicacion({...comunicacion, tipo_contraparte: e.target.value})}
                  className="w-full border rounded-lg p-3"
                >
                  <option value="proveedor">Proveedor</option>
                  <option value="cliente">Cliente</option>
                </select>
                <input
                  value={comunicacion.asunto}
                  onChange={(e) => setComunicacion({...comunicacion, asunto: e.target.value})}
                  placeholder="Asunto..."
                  className="w-full border rounded-lg p-3"
                />
                <textarea
                  value={comunicacion.descripcion}
                  onChange={(e) => setComunicacion({...comunicacion, descripcion: e.target.value})}
                  placeholder="Detalla la conversación o acuerdo..."
                  className="w-full border rounded-lg p-3 h-24"
                />
              </div>
              <div className="flex gap-3 mt-4">
                <button onClick={() => setShowComunicacion(false)} className="flex-1 py-2 border rounded-lg">
                  Cancelar
                </button>
                <button onClick={registrarComunicacion} className="flex-1 py-2 bg-green-600 text-white rounded-lg">
                  Registrar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
