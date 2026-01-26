import React, { useState, useEffect } from 'react';
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api`
    : '/api',
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('es-MX', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export default function EditarUsuario({ usuarioId, onClose, onSave }) {
  const [tab, setTab] = useState('perfil');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [usuario, setUsuario] = useState(null);
  const [empresa, setEmpresa] = useState(null);
  const [documentos, setDocumentos] = useState([]);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchUsuario();
  }, [usuarioId]);

  const fetchUsuario = async () => {
    try {
      setLoading(true);
      setError('');
      
      const resUsuario = await api.get(`/admin/usuarios/${usuarioId}`);
      const userData = resUsuario.data.usuario;
      setUsuario(userData);
      
      if (userData?.empresa_id) {
        try {
          const resEmpresa = await api.get(`/admin/empresas/${userData.empresa_id}`);
          setEmpresa(resEmpresa.data.empresa);
          
          const resDocs = await api.get(`/admin/empresas/${userData.empresa_id}/documentos`);
          setDocumentos(resDocs.data.documentos || []);
        } catch (empError) {
          console.log('No empresa data found');
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error cargando usuario');
    } finally {
      setLoading(false);
    }
  };

  const handleGuardarUsuario = async () => {
    if (!usuario) return;
    setSaving(true);
    setError('');
    
    try {
      await api.put(`/admin/usuarios/${usuarioId}`, {
        nombre: usuario.full_name,
        email: usuario.email,
        rol: usuario.role,
        estado: usuario.approval_status === 'approved' ? 'aprobado' : 
                usuario.approval_status === 'rejected' ? 'rechazado' : 'pendiente'
      });
      
      onSave();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error guardando usuario');
    } finally {
      setSaving(false);
    }
  };

  const handleGuardarEmpresa = async () => {
    if (!empresa) return;
    setSaving(true);
    setError('');
    
    try {
      await api.put(`/admin/empresas/${empresa.id}`, {
        nombre_comercial: empresa.nombre,
        razon_social: empresa.razon_social,
        rfc: empresa.rfc
      });
      
      onSave();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error guardando empresa');
    } finally {
      setSaving(false);
    }
  };

  const handleSubirDocumento = async (e) => {
    const files = e.target.files;
    const cliente_id = usuario?.cliente_id || usuario?.empresa_id;
    if (!files || !cliente_id) return;

    setUploading(true);
    setError('');
    
    try {
      // Upload each file separately to the cliente documentos endpoint
      for (let file of Array.from(files)) {
        const formData = new FormData();
        formData.append('file', file);
        // Optional: add document type, category, subcategory if needed
        // formData.append('tipo_documento', 'documento');

        await api.post(`/admin/clientes/${cliente_id}/documentos`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }
      
      // Refresh documents from cliente endpoint
      const resCliente = await api.get(`/admin/clientes/${cliente_id}`);
      setDocumentos(resCliente.data.documentos || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error subiendo documentos');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleEliminarDocumento = async (docId) => {
    if (!window.confirm('¿Eliminar este documento del Knowledge Base?')) return;
    
    try {
      await api.delete(`/admin/knowledge-base/${docId}`);
      setDocumentos(prev => prev.filter(d => d.id !== docId));
    } catch (err) {
      setError(err.response?.data?.detail || 'Error eliminando documento');
    }
  };

  const handleReindexar = async () => {
    if (!empresa) return;
    
    try {
      const res = await api.post(`/admin/knowledge-base/reindex/${empresa.id}`);
      alert(`Reindexacion iniciada: ${res.data.documentos_procesados} documento(s)`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error reindexando');
    }
  };

  const handleEliminarUsuario = async () => {
    if (!window.confirm('¿ELIMINAR este usuario? Esta accion no se puede deshacer.')) return;
    if (!window.confirm('¿Estas SEGURO? Se eliminaran todos sus datos.')) return;
    
    try {
      await api.delete(`/admin/usuarios/${usuarioId}`);
      onClose();
      onSave();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error eliminando usuario');
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8">
          <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-gray-500 mt-2">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-xl">
        
        <div className="bg-gradient-to-r from-emerald-600 to-teal-600 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{usuario?.full_name || 'Usuario'}</h2>
                <p className="text-emerald-100">{usuario?.email}</p>
              </div>
            </div>
            <button onClick={onClose} className="text-white/80 hover:text-white transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div className="flex gap-2 mt-4">
            {['perfil', 'empresa', 'documentos'].map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 ${
                  tab === t 
                    ? 'bg-white text-emerald-600' 
                    : 'bg-white/20 text-white hover:bg-white/30'
                }`}
              >
                {t === 'perfil' && (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                )}
                {t === 'empresa' && (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                )}
                {t === 'documentos' && (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                )}
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mx-6 mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-6">
          
          {tab === 'perfil' && usuario && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo</label>
                  <input
                    type="text"
                    value={usuario.full_name || ''}
                    onChange={(e) => setUsuario({ ...usuario, full_name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={usuario.email || ''}
                    onChange={(e) => setUsuario({ ...usuario, email: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Empresa (texto)</label>
                  <input
                    type="text"
                    value={usuario.company || ''}
                    onChange={(e) => setUsuario({ ...usuario, company: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
                  <select
                    value={usuario.role || 'user'}
                    onChange={(e) => setUsuario({ ...usuario, role: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  >
                    <option value="user">Usuario</option>
                    <option value="admin">Administrador</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                  <select
                    value={usuario.approval_status || 'pending'}
                    onChange={(e) => setUsuario({ ...usuario, approval_status: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  >
                    <option value="pending">Pendiente</option>
                    <option value="approved">Aprobado</option>
                    <option value="rejected">Rechazado</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Registrado</label>
                  <p className="px-4 py-2 bg-gray-50 rounded-lg text-gray-600">
                    {formatDate(usuario.created_at)}
                  </p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Empresas permitidas
                </label>
                <p className="text-sm text-gray-500 mb-2">
                  {usuario.allowed_companies?.length || 0} empresa(s) asignada(s)
                </p>
                {usuario.allowed_companies?.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {usuario.allowed_companies.map((comp, idx) => (
                      <span key={idx} className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm">
                        {comp}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex gap-3 pt-4 border-t">
                <button
                  onClick={handleGuardarUsuario}
                  disabled={saving}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                >
                  {saving ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  Guardar Cambios
                </button>
                <button
                  onClick={handleEliminarUsuario}
                  className="px-6 py-3 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 flex items-center gap-2 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Eliminar
                </button>
              </div>
            </div>
          )}

          {tab === 'empresa' && (
            <div className="space-y-6">
              {empresa ? (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Nombre comercial</label>
                      <input
                        type="text"
                        value={empresa.nombre || ''}
                        onChange={(e) => setEmpresa({ ...empresa, nombre: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">RFC</label>
                      <input
                        type="text"
                        value={empresa.rfc || ''}
                        onChange={(e) => setEmpresa({ ...empresa, rfc: e.target.value.toUpperCase() })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent uppercase"
                        maxLength={13}
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Razon social</label>
                      <input
                        type="text"
                        value={empresa.razon_social || ''}
                        onChange={(e) => setEmpresa({ ...empresa, razon_social: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Industria</label>
                      <p className="px-4 py-2 bg-gray-50 rounded-lg text-gray-600 capitalize">
                        {empresa.industria?.replace(/_/g, ' ') || '-'}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                      <p className={`px-4 py-2 rounded-lg ${empresa.activa ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-600'}`}>
                        {empresa.activa ? 'Activa' : 'Inactiva'}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3 pt-4 border-t">
                    <button
                      onClick={handleGuardarEmpresa}
                      disabled={saving}
                      className="flex-1 flex items-center justify-center gap-2 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                    >
                      {saving ? (
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                      Guardar Empresa
                    </button>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  <p className="text-gray-500 mb-4">Este usuario no tiene empresa asociada</p>
                  <p className="text-sm text-gray-400">La empresa se asocia cuando el usuario ingresa su empresa durante el registro</p>
                </div>
              )}
            </div>
          )}

          {tab === 'documentos' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-800">Knowledge Base</h3>
                  <p className="text-sm text-gray-500">
                    Documentos para el sistema RAG de esta empresa
                  </p>
                </div>
                {empresa && (
                  <div className="flex gap-2">
                    <button
                      onClick={handleReindexar}
                      className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Reindexar
                    </button>
                    <label className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 cursor-pointer transition-colors">
                      {uploading ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      )}
                      Subir Documentos
                      <input
                        type="file"
                        multiple
                        accept=".pdf,.doc,.docx,.txt,.xlsx,.csv"
                        onChange={handleSubirDocumento}
                        className="hidden"
                        disabled={uploading}
                      />
                    </label>
                  </div>
                )}
              </div>

              {empresa ? (
                <>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-emerald-50 rounded-xl p-4 text-center">
                      <p className="text-2xl font-bold text-emerald-600">{documentos.length}</p>
                      <p className="text-sm text-gray-600">Documentos</p>
                    </div>
                    <div className="bg-blue-50 rounded-xl p-4 text-center">
                      <p className="text-2xl font-bold text-blue-600">
                        {documentos.reduce((acc, d) => acc + (d.chunks || 0), 0)}
                      </p>
                      <p className="text-sm text-gray-600">Chunks RAG</p>
                    </div>
                    <div className="bg-purple-50 rounded-xl p-4 text-center">
                      <p className="text-2xl font-bold text-purple-600">
                        {formatBytes(documentos.reduce((acc, d) => acc + (d.tamaño || 0), 0))}
                      </p>
                      <p className="text-sm text-gray-600">Tamaño Total</p>
                    </div>
                  </div>

                  {documentos.length > 0 ? (
                    <div className="border rounded-lg divide-y">
                      {documentos.map((doc) => (
                        <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                              <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                            <div>
                              <p className="font-medium text-gray-800">{doc.nombre}</p>
                              <p className="text-sm text-gray-500">
                                {formatBytes(doc.tamaño)} | {doc.tipo?.toUpperCase()} | {formatDate(doc.fecha_subida)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              doc.estado === 'procesado' ? 'bg-green-100 text-green-700' :
                              doc.estado === 'error' ? 'bg-red-100 text-red-700' :
                              'bg-yellow-100 text-yellow-700'
                            }`}>
                              {doc.estado}
                            </span>
                            <button
                              onClick={() => handleEliminarDocumento(doc.id)}
                              className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                              title="Eliminar documento"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
                      <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-gray-500">No hay documentos en el Knowledge Base</p>
                      <p className="text-sm text-gray-400 mt-1">Sube documentos para alimentar el sistema RAG</p>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
                  <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  <p className="text-gray-500 mb-2">No hay empresa asociada</p>
                  <p className="text-sm text-gray-400">El Knowledge Base esta vinculado a empresas</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
