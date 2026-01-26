import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

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

const getEstadoBadge = (estado) => {
  const badges = {
    pendiente: { bg: 'bg-yellow-500/20', text: 'text-yellow-300', label: 'Pendiente' },
    aprobado: { bg: 'bg-green-500/20', text: 'text-green-300', label: 'Aprobado' },
    rechazado: { bg: 'bg-red-500/20', text: 'text-red-300', label: 'Rechazado' },
    suspendido: { bg: 'bg-gray-500/20', text: 'text-gray-300', label: 'Suspendido' }
  };
  const badge = badges[estado] || badges.pendiente;
  return (
    <span className={`px-3 py-1 text-xs font-medium rounded-full ${badge.bg} ${badge.text}`}>
      {badge.label}
    </span>
  );
};

const AdminClientes = () => {
  const { user } = useAuth();
  const [clientes, setClientes] = useState([]);
  const [totales, setTotales] = useState({ pendiente: 0, aprobado: 0, rechazado: 0, suspendido: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('pendiente');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCliente, setSelectedCliente] = useState(null);
  const [clienteDetail, setClienteDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [rechazarModal, setRechazarModal] = useState(false);
  const [motivoRechazo, setMotivoRechazo] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [versionesModal, setVersionesModal] = useState(null);
  const [versiones, setVersiones] = useState([]);
  const [autofillLoading, setAutofillLoading] = useState(false);

  const tabs = [
    { id: 'pendiente', label: 'Pendientes', icon: '⏳' },
    { id: 'aprobado', label: 'Aprobados', icon: '✅' },
    { id: 'rechazado', label: 'Rechazados', icon: '❌' },
    { id: 'todos', label: 'Todos', icon: '📋' }
  ];

  const fetchClientes = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('auth_token');
      const params = new URLSearchParams();
      if (activeTab !== 'todos') {
        params.append('estado', activeTab);
      }
      if (searchQuery) {
        params.append('search', searchQuery);
      }
      
      const response = await fetch(`/api/admin/clientes?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al cargar clientes');
      }
      
      setClientes(data.clientes || []);
      setTotales(data.totales_por_estado || { pendiente: 0, aprobado: 0, rechazado: 0, suspendido: 0 });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [activeTab, searchQuery]);

  useEffect(() => {
    fetchClientes();
  }, [fetchClientes]);

  useEffect(() => {
    if (message.text) {
      const timer = setTimeout(() => setMessage({ type: '', text: '' }), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  const fetchClienteDetail = async (clienteId) => {
    try {
      setDetailLoading(true);
      const token = localStorage.getItem('auth_token');
      
      const response = await fetch(`/api/admin/clientes/${clienteId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al cargar detalle del cliente');
      }
      
      setClienteDetail(data);
      setEditForm(data.cliente || {});
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setDetailLoading(false);
    }
  };

  const handleClienteClick = (cliente) => {
    setSelectedCliente(cliente);
    fetchClienteDetail(cliente.id);
    setEditMode(false);
  };

  const handleAprobar = async () => {
    if (!selectedCliente) return;
    
    try {
      setActionLoading(true);
      const token = localStorage.getItem('auth_token');
      
      const response = await fetch(`/api/admin/clientes/${selectedCliente.id}/aprobar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ notas: '' })
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al aprobar cliente');
      }
      
      setMessage({ type: 'success', text: 'Cliente aprobado exitosamente' });
      setSelectedCliente(null);
      setClienteDetail(null);
      fetchClientes();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRechazar = async () => {
    if (!selectedCliente || !motivoRechazo.trim()) return;
    
    try {
      setActionLoading(true);
      const token = localStorage.getItem('auth_token');
      
      const response = await fetch(`/api/admin/clientes/${selectedCliente.id}/rechazar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ motivo: motivoRechazo })
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al rechazar cliente');
      }
      
      setMessage({ type: 'success', text: 'Cliente rechazado' });
      setRechazarModal(false);
      setMotivoRechazo('');
      setSelectedCliente(null);
      setClienteDetail(null);
      fetchClientes();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleGuardarCambios = async () => {
    if (!selectedCliente) return;
    
    try {
      setActionLoading(true);
      const token = localStorage.getItem('auth_token');
      
      const response = await fetch(`/api/admin/clientes/${selectedCliente.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editForm)
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al actualizar cliente');
      }
      
      setMessage({ type: 'success', text: 'Cliente actualizado correctamente' });
      setEditMode(false);
      fetchClienteDetail(selectedCliente.id);
      fetchClientes();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleUploadDocument = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedCliente) return;
    
    try {
      setUploadingDoc(true);
      const token = localStorage.getItem('auth_token');
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('tipo_documento', 'general');
      
      const response = await fetch(`/api/admin/clientes/${selectedCliente.id}/documentos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al subir documento');
      }
      
      setMessage({ type: 'success', text: 'Documento subido correctamente' });
      fetchClienteDetail(selectedCliente.id);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setUploadingDoc(false);
      e.target.value = '';
    }
  };

  const handleVerVersiones = async (docUuid) => {
    if (!selectedCliente) return;
    
    try {
      const token = localStorage.getItem('auth_token');
      
      const response = await fetch(`/api/admin/clientes/${selectedCliente.id}/documentos/${docUuid}/versiones`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al cargar versiones');
      }
      
      setVersiones(data.versiones || []);
      setVersionesModal(docUuid);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const handleBack = () => {
    setSelectedCliente(null);
    setClienteDetail(null);
    setEditMode(false);
    setEditForm({});
  };

  const handleAutofillIA = async () => {
    if (!selectedCliente) return;
    
    try {
      setAutofillLoading(true);
      const token = localStorage.getItem('auth_token');
      
      const response = await fetch(`/api/admin/clientes/${selectedCliente.id}/autofill-ia`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error en auto-completado');
      }
      
      if (data.success && data.campos_actualizados?.length > 0) {
        setMessage({ 
          type: 'success', 
          text: `IA completó ${data.campos_actualizados.length} campos: ${data.campos_actualizados.join(', ')}`
        });
        fetchClienteDetail(selectedCliente.id);
      } else {
        setMessage({ 
          type: 'error', 
          text: data.message || 'No se encontraron datos adicionales para auto-completar'
        });
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setAutofillLoading(false);
    }
  };

  if (selectedCliente && clienteDetail) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <button
            onClick={handleBack}
            className="mb-6 flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Volver a la lista
          </button>

          {message.text && (
            <div className={`mb-6 p-4 rounded-xl backdrop-blur-xl border ${
              message.type === 'success' 
                ? 'bg-green-500/10 border-green-500/30 text-green-300' 
                : 'bg-red-500/10 border-red-500/30 text-red-300'
            }`}>
              {message.text}
            </div>
          )}

          <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 mb-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-white">{clienteDetail.cliente?.nombre || clienteDetail.cliente?.razon_social || 'Cliente'}</h1>
                <p className="text-slate-400 mt-1">RFC: {clienteDetail.cliente?.rfc || '-'}</p>
              </div>
              <div className="flex items-center gap-3">
                {getEstadoBadge(clienteDetail.cliente?.estado)}
                {!editMode && (
                  <>
                    <button
                      onClick={handleAutofillIA}
                      disabled={autofillLoading}
                      className="px-4 py-2 bg-purple-600/20 text-purple-300 rounded-lg hover:bg-purple-600/30 transition-colors border border-purple-500/30 flex items-center gap-2 disabled:opacity-50"
                    >
                      {autofillLoading ? (
                        <>
                          <div className="w-4 h-4 border-2 border-purple-400 rounded-full animate-spin border-t-transparent"></div>
                          Investigando...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                          Auto-completar IA
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => setEditMode(true)}
                      className="px-4 py-2 bg-blue-600/20 text-blue-300 rounded-lg hover:bg-blue-600/30 transition-colors border border-blue-500/30"
                    >
                      Editar
                    </button>
                  </>
                )}
              </div>
            </div>

            {detailLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-8 h-8 border-2 border-teal-400 rounded-full animate-spin border-t-transparent"></div>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-white border-b border-white/10 pb-2">Datos del Cliente</h3>
                  {editMode ? (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm text-slate-400 mb-1">Nombre / Razón Social</label>
                        <input
                          type="text"
                          value={editForm.nombre || editForm.razon_social || ''}
                          onChange={(e) => setEditForm({ ...editForm, nombre: e.target.value, razon_social: e.target.value })}
                          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-slate-400 mb-1">RFC</label>
                        <input
                          type="text"
                          value={editForm.rfc || ''}
                          onChange={(e) => setEditForm({ ...editForm, rfc: e.target.value.toUpperCase() })}
                          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-slate-400 mb-1">Giro</label>
                        <input
                          type="text"
                          value={editForm.giro || ''}
                          onChange={(e) => setEditForm({ ...editForm, giro: e.target.value })}
                          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-slate-400 mb-1">Email</label>
                        <input
                          type="email"
                          value={editForm.email || ''}
                          onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-slate-400 mb-1">Teléfono</label>
                        <input
                          type="text"
                          value={editForm.telefono || ''}
                          onChange={(e) => setEditForm({ ...editForm, telefono: e.target.value })}
                          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Razón Social</span>
                        <span className="text-white">{clienteDetail.cliente?.razon_social || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">RFC</span>
                        <span className="text-white font-mono">{clienteDetail.cliente?.rfc || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Giro</span>
                        <span className="text-white">{clienteDetail.cliente?.giro || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Email</span>
                        <span className="text-white">{clienteDetail.cliente?.email || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Teléfono</span>
                        <span className="text-white">{clienteDetail.cliente?.telefono || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Registrado</span>
                        <span className="text-white">{formatDate(clienteDetail.cliente?.created_at)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Origen</span>
                        <span className="text-white">{clienteDetail.cliente?.origen || '-'}</span>
                      </div>
                    </div>
                  )}
                </div>

                {clienteDetail.contexto && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-white border-b border-white/10 pb-2">Contexto</h3>
                    <div className="space-y-4">
                      {clienteDetail.contexto.resumen_ejecutivo && (
                        <div>
                          <span className="text-sm text-slate-400">Resumen Ejecutivo</span>
                          <p className="text-white mt-1 text-sm bg-white/5 p-3 rounded-lg">{clienteDetail.contexto.resumen_ejecutivo}</p>
                        </div>
                      )}
                      {clienteDetail.contexto.perfil_fiscal && (
                        <div>
                          <span className="text-sm text-slate-400">Perfil Fiscal</span>
                          <p className="text-white mt-1 text-sm bg-white/5 p-3 rounded-lg">{clienteDetail.contexto.perfil_fiscal}</p>
                        </div>
                      )}
                      {clienteDetail.contexto.alertas && clienteDetail.contexto.alertas.length > 0 && (
                        <div>
                          <span className="text-sm text-slate-400">Alertas</span>
                          <div className="mt-1 space-y-2">
                            {clienteDetail.contexto.alertas.map((alerta, idx) => (
                              <div key={idx} className="text-yellow-300 text-sm bg-yellow-500/10 p-3 rounded-lg border border-yellow-500/30">
                                ⚠️ {alerta}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Documentos</h3>
                <label className="px-4 py-2 bg-teal-600/20 text-teal-300 rounded-lg hover:bg-teal-600/30 transition-colors border border-teal-500/30 cursor-pointer">
                  {uploadingDoc ? 'Subiendo...' : '+ Subir documento'}
                  <input type="file" className="hidden" onChange={handleUploadDocument} disabled={uploadingDoc} />
                </label>
              </div>
              
              {clienteDetail?.documentos?.length > 0 ? (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {clienteDetail.documentos.map((doc, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                      <div className="flex items-center gap-3">
                        <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <div>
                          <p className="text-white text-sm">{doc.nombre_archivo || doc.nombre || 'Documento'}</p>
                          <p className="text-slate-500 text-xs">{formatDate(doc.created_at)}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleVerVersiones(doc.uuid || doc.id)}
                        className="text-xs text-teal-400 hover:text-teal-300"
                      >
                        Ver versiones
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No hay documentos</p>
              )}
            </div>

            <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Historial de Cambios</h3>
              
              {clienteDetail?.historial?.length > 0 ? (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {clienteDetail.historial.map((item, idx) => (
                    <div key={idx} className="relative pl-6 pb-4 border-l border-white/10 last:pb-0">
                      <div className="absolute left-0 top-0 w-3 h-3 bg-teal-500 rounded-full -translate-x-1.5"></div>
                      <p className="text-white text-sm">{item.descripcion || item.tipo_cambio}</p>
                      <p className="text-slate-500 text-xs mt-1">{formatDate(item.created_at)}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">Sin historial</p>
              )}
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
            <div className="flex items-center justify-end gap-4">
              {editMode ? (
                <>
                  <button
                    onClick={() => {
                      setEditMode(false);
                      setEditForm(clienteDetail.cliente || {});
                    }}
                    className="px-6 py-2.5 text-slate-300 hover:text-white transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleGuardarCambios}
                    disabled={actionLoading}
                    className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {actionLoading ? 'Guardando...' : 'Guardar Cambios'}
                  </button>
                </>
              ) : (
                <>
                  {clienteDetail.cliente?.estado !== 'rechazado' && (
                    <button
                      onClick={() => setRechazarModal(true)}
                      disabled={actionLoading}
                      className="px-6 py-2.5 bg-red-600/20 text-red-300 rounded-lg hover:bg-red-600/30 disabled:opacity-50 transition-colors border border-red-500/30"
                    >
                      Rechazar
                    </button>
                  )}
                  {clienteDetail.cliente?.estado !== 'aprobado' && (
                    <button
                      onClick={handleAprobar}
                      disabled={actionLoading}
                      className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                    >
                      {actionLoading ? 'Procesando...' : 'Aprobar Cliente'}
                    </button>
                  )}
                </>
              )}
            </div>
          </div>

          {rechazarModal && (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
              <div className="bg-slate-800 rounded-2xl border border-white/10 p-6 max-w-md w-full">
                <h3 className="text-xl font-semibold text-white mb-4">Rechazar Cliente</h3>
                <p className="text-slate-400 mb-4">Por favor, indica el motivo del rechazo:</p>
                <textarea
                  value={motivoRechazo}
                  onChange={(e) => setMotivoRechazo(e.target.value)}
                  placeholder="Motivo del rechazo..."
                  rows={4}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:border-red-500 focus:ring-1 focus:ring-red-500 outline-none resize-none"
                />
                <div className="flex justify-end gap-3 mt-4">
                  <button
                    onClick={() => {
                      setRechazarModal(false);
                      setMotivoRechazo('');
                    }}
                    className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleRechazar}
                    disabled={actionLoading || motivoRechazo.trim().length < 5}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                  >
                    {actionLoading ? 'Procesando...' : 'Confirmar Rechazo'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {versionesModal && (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
              <div className="bg-slate-800 rounded-2xl border border-white/10 p-6 max-w-md w-full">
                <h3 className="text-xl font-semibold text-white mb-4">Versiones del Documento</h3>
                {versiones.length > 0 ? (
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {versiones.map((v, idx) => (
                      <div key={idx} className="p-3 bg-white/5 rounded-lg">
                        <p className="text-white text-sm">Versión {v.version || idx + 1}</p>
                        <p className="text-slate-500 text-xs">{formatDate(v.created_at)}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-center py-4">Sin versiones anteriores</p>
                )}
                <div className="flex justify-end mt-4">
                  <button
                    onClick={() => setVersionesModal(null)}
                    className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Gestión de Clientes</h1>
          <p className="text-slate-400 mt-2">Administra y aprueba solicitudes de clientes</p>
        </div>

        {message.text && (
          <div className={`mb-6 p-4 rounded-xl backdrop-blur-xl border ${
            message.type === 'success' 
              ? 'bg-green-500/10 border-green-500/30 text-green-300' 
              : 'bg-red-500/10 border-red-500/30 text-red-300'
          }`}>
            {message.text}
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/5 backdrop-blur-xl rounded-xl border border-white/10 p-4">
            <p className="text-sm text-slate-400">Total Clientes</p>
            <p className="text-2xl font-bold text-white">{totales.pendiente + totales.aprobado + totales.rechazado + totales.suspendido}</p>
          </div>
          <div className="bg-yellow-500/10 backdrop-blur-xl rounded-xl border border-yellow-500/30 p-4">
            <p className="text-sm text-yellow-300">Pendientes</p>
            <p className="text-2xl font-bold text-yellow-400">{totales.pendiente}</p>
          </div>
          <div className="bg-green-500/10 backdrop-blur-xl rounded-xl border border-green-500/30 p-4">
            <p className="text-sm text-green-300">Aprobados</p>
            <p className="text-2xl font-bold text-green-400">{totales.aprobado}</p>
          </div>
          <div className="bg-red-500/10 backdrop-blur-xl rounded-xl border border-red-500/30 p-4">
            <p className="text-sm text-red-300">Rechazados</p>
            <p className="text-2xl font-bold text-red-400">{totales.rechazado}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 mb-6 border-b border-white/10 pb-4">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg transition-all ${
                activeTab === tab.id
                  ? 'bg-teal-600 text-white'
                  : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
              {tab.id !== 'todos' && totales[tab.id] > 0 && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-white/20 rounded-full">
                  {totales[tab.id]}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="mb-6">
          <div className="relative">
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar por nombre, RFC o razón social..."
              className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-teal-400 rounded-full animate-spin border-t-transparent"></div>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
            <p className="text-red-300">{error}</p>
            <button
              onClick={fetchClientes}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Reintentar
            </button>
          </div>
        ) : clientes.length === 0 ? (
          <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-12 text-center">
            <svg className="mx-auto h-16 w-16 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 className="mt-4 text-xl font-medium text-white">No hay clientes</h3>
            <p className="mt-2 text-slate-400">
              {activeTab === 'todos' ? 'No hay clientes registrados en el sistema.' : `No hay clientes con estado "${activeTab}".`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {clientes.map((cliente) => (
              <div
                key={cliente.id}
                onClick={() => handleClienteClick(cliente)}
                className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:bg-white/10 hover:border-teal-500/50 transition-all cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white group-hover:text-teal-300 transition-colors">
                      {cliente.nombre || cliente.razon_social || 'Sin nombre'}
                    </h3>
                    <p className="text-sm text-slate-400 font-mono mt-1">{cliente.rfc || '-'}</p>
                  </div>
                  {getEstadoBadge(cliente.estado)}
                </div>
                
                <div className="space-y-2 text-sm">
                  {cliente.razon_social && cliente.nombre !== cliente.razon_social && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Razón Social</span>
                      <span className="text-slate-300 truncate ml-2 max-w-[60%]">{cliente.razon_social}</span>
                    </div>
                  )}
                  {cliente.giro && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Giro</span>
                      <span className="text-slate-300 truncate ml-2 max-w-[60%]">{cliente.giro}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-slate-500">Registrado</span>
                    <span className="text-slate-300">{formatDate(cliente.created_at)}</span>
                  </div>
                  {cliente.total_documentos > 0 && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Documentos</span>
                      <span className="text-teal-400">{cliente.total_documentos}</span>
                    </div>
                  )}
                </div>
                
                <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
                  <span className="text-xs text-slate-500">Click para ver detalles</span>
                  <svg className="w-5 h-5 text-slate-500 group-hover:text-teal-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminClientes;
