import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import EditarUsuario from '../components/EditarUsuario';

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api`
    : '/api',
  headers: {
    'Content-Type': 'application/json',
  }
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const getApprovalStatusBadge = (status) => {
  switch (status) {
    case 'approved':
      return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">Aprobado</span>;
    case 'rejected':
      return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded-full">Rechazado</span>;
    case 'pending':
    default:
      return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-700 rounded-full">Pendiente</span>;
  }
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

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('usuarios');
  const [pendingUsers, setPendingUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [availableCompanies, setAvailableCompanies] = useState([]);
  const [empresas, setEmpresas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [editingUser, setEditingUser] = useState(null);
  const [selectedCompanies, setSelectedCompanies] = useState([]);
  const [editProfileUser, setEditProfileUser] = useState(null);
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    email: '',
    company: '',
    role: 'user'
  });
  const [fullEditUser, setFullEditUser] = useState(null);
  const [editingEmpresa, setEditingEmpresa] = useState(null);
  const [empresaForm, setEmpresaForm] = useState({
    nombre_comercial: '',
    razon_social: '',
    rfc: '',
    industria: '',
    vision: '',
    mision: '',
    plan: 'basico'
  });
  const [showNewEmpresaModal, setShowNewEmpresaModal] = useState(false);
  const [autofillLoading, setAutofillLoading] = useState(false);

  const autofillWithAI = async () => {
    if (!empresaForm.nombre_comercial) {
      setMessage({ type: 'error', text: 'Ingresa el nombre comercial primero' });
      return;
    }
    
    setAutofillLoading(true);
    try {
      const response = await api.post('/empresas/autofill-ia', {
        nombre_comercial: empresaForm.nombre_comercial,
        razon_social: empresaForm.razon_social,
        rfc: empresaForm.rfc,
        industria: empresaForm.industria
      });
      
      if (response.data.success) {
        const data = response.data.data;
        setEmpresaForm(prev => ({
          ...prev,
          vision: data.vision || prev.vision,
          mision: data.mision || prev.mision
        }));
        setMessage({ type: 'success', text: 'Perfil generado con IA exitosamente' });
      }
    } catch (error) {
      console.error('Error autofill:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Error al generar perfil con IA' });
    } finally {
      setAutofillLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin') {
      loadUsers();
      loadCompanies();
      loadEmpresas();
    }
  }, [user]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const [pendingRes, allRes] = await Promise.all([
        api.get('/auth/admin/pending-users'),
        api.get('/auth/admin/all-users')
      ]);
      setPendingUsers(pendingRes.data.users || []);
      setAllUsers(allRes.data.users || []);
    } catch (error) {
      console.error('Error loading users:', error);
      setMessage({ type: 'error', text: 'Error al cargar usuarios' });
    } finally {
      setLoading(false);
    }
  };

  const loadCompanies = async () => {
    try {
      const response = await api.get('/auth/admin/companies');
      setAvailableCompanies(response.data.companies || []);
    } catch (error) {
      console.error('Error loading companies:', error);
    }
  };

  const loadEmpresas = async () => {
    try {
      const response = await api.get('/empresas/');
      const data = response.data;
      const empresasArray = Array.isArray(data) ? data : (data?.empresas || data?.data || []);
      setEmpresas(empresasArray);
    } catch (error) {
      console.error('Error loading empresas:', error);
      setEmpresas([]);
    }
  };

  const openEmpresaEditor = (empresa) => {
    setEditingEmpresa(empresa);
    setEmpresaForm({
      nombre_comercial: empresa.nombre_comercial || '',
      razon_social: empresa.razon_social || '',
      rfc: empresa.rfc || '',
      industria: empresa.industria || '',
      vision: empresa.vision || '',
      mision: empresa.mision || '',
      plan: empresa.plan || 'basico'
    });
  };

  const closeEmpresaEditor = () => {
    setEditingEmpresa(null);
    setEmpresaForm({
      nombre_comercial: '',
      razon_social: '',
      rfc: '',
      industria: '',
      vision: '',
      mision: '',
      plan: 'basico'
    });
  };

  const saveEmpresa = async () => {
    if (!editingEmpresa) return;
    
    try {
      setActionLoading(editingEmpresa.id);
      const response = await api.patch(`/empresas/${editingEmpresa.id}`, empresaForm);
      if (response.data) {
        setMessage({ type: 'success', text: 'Empresa actualizada correctamente' });
        await loadEmpresas();
        await loadCompanies();
        closeEmpresaEditor();
      }
    } catch (error) {
      console.error('Error updating empresa:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Error al actualizar empresa' });
    } finally {
      setActionLoading(null);
    }
  };

  const createEmpresa = async () => {
    try {
      setActionLoading('new');
      const response = await api.post('/empresas/', empresaForm);
      if (response.data) {
        setMessage({ type: 'success', text: 'Empresa creada correctamente' });
        await loadEmpresas();
        await loadCompanies();
        setShowNewEmpresaModal(false);
        setEmpresaForm({
          nombre_comercial: '',
          razon_social: '',
          rfc: '',
          industria: '',
          vision: '',
          mision: '',
          plan: 'basico'
        });
      }
    } catch (error) {
      console.error('Error creating empresa:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Error al crear empresa' });
    } finally {
      setActionLoading(null);
    }
  };

  const deleteEmpresa = async (empresaId) => {
    if (!window.confirm('¿Desactivar esta empresa? Los datos se conservarán.')) return;
    
    try {
      setActionLoading(empresaId);
      await api.delete(`/empresas/${empresaId}`);
      setMessage({ type: 'success', text: 'Empresa desactivada correctamente' });
      await loadEmpresas();
      await loadCompanies();
    } catch (error) {
      console.error('Error deleting empresa:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Error al desactivar empresa' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleApprove = async (userId) => {
    try {
      setActionLoading(userId);
      const response = await api.post(`/auth/admin/approve-user/${userId}`);
      if (response.data.success) {
        setMessage({ type: 'success', text: response.data.message });
        await loadUsers();
      }
    } catch (error) {
      console.error('Error approving user:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Error al aprobar usuario' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (userId) => {
    try {
      setActionLoading(userId);
      const response = await api.post(`/auth/admin/reject-user/${userId}`);
      if (response.data.success) {
        setMessage({ type: 'success', text: response.data.message });
        await loadUsers();
      }
    } catch (error) {
      console.error('Error rejecting user:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Error al rechazar usuario' });
    } finally {
      setActionLoading(null);
    }
  };

  const openCompanyEditor = (userToEdit) => {
    setEditingUser(userToEdit);
    setSelectedCompanies(userToEdit.allowed_companies || []);
  };

  const closeCompanyEditor = () => {
    setEditingUser(null);
    setSelectedCompanies([]);
  };

  const toggleCompany = (company) => {
    setSelectedCompanies(prev => 
      prev.includes(company) 
        ? prev.filter(c => c !== company)
        : [...prev, company]
    );
  };

  const saveAllowedCompanies = async () => {
    if (!editingUser) return;
    
    try {
      setActionLoading(editingUser.user_id);
      const response = await api.post(`/auth/admin/user/${editingUser.user_id}/allowed-companies`, {
        allowed_companies: selectedCompanies
      });
      if (response.data.success) {
        setMessage({ type: 'success', text: response.data.message });
        await loadUsers();
        closeCompanyEditor();
      }
    } catch (error) {
      console.error('Error updating allowed companies:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Error al actualizar empresas' });
    } finally {
      setActionLoading(null);
    }
  };

  const openProfileEditor = (userToEdit) => {
    setEditProfileUser(userToEdit);
    setProfileForm({
      full_name: userToEdit.full_name || '',
      email: userToEdit.email || '',
      company: userToEdit.company || '',
      role: userToEdit.role || 'user'
    });
  };

  const closeProfileEditor = () => {
    setEditProfileUser(null);
    setProfileForm({ full_name: '', email: '', company: '', role: 'user' });
  };

  const saveUserProfile = async () => {
    if (!editProfileUser) return;
    
    try {
      setActionLoading(editProfileUser.user_id);
      const response = await api.put(`/auth/admin/user/${editProfileUser.user_id}`, profileForm);
      if (response.data.success) {
        setMessage({ type: 'success', text: response.data.message });
        await loadUsers();
        closeProfileEditor();
      }
    } catch (error) {
      console.error('Error updating user profile:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Error al actualizar usuario' });
    } finally {
      setActionLoading(null);
    }
  };

  useEffect(() => {
    if (message.text) {
      const timer = setTimeout(() => setMessage({ type: '', text: '' }), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">&#8987;</div>
          <p className="text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!user || user.role !== 'admin') {
    return <Navigate to="/" replace />;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">&#8987;</div>
          <p className="text-gray-600">Cargando panel de administracion...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Panel de Administracion</h1>
          <p className="text-sm text-gray-500 mt-1">Gestion de usuarios, empresas y permisos</p>
          
          <div className="mt-6 flex gap-2 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('usuarios')}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === 'usuarios'
                  ? 'bg-white text-indigo-600 border-t border-l border-r border-gray-200 -mb-px'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Usuarios
            </button>
            <button
              onClick={() => setActiveTab('empresas')}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === 'empresas'
                  ? 'bg-white text-indigo-600 border-t border-l border-r border-gray-200 -mb-px'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Empresas
            </button>
          </div>
        </div>

        {message.text && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-50 border border-green-200 text-green-700' 
              : 'bg-red-50 border border-red-200 text-red-700'
          }`}>
            <div className="flex items-center gap-2">
              {message.type === 'success' ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
              <span>{message.text}</span>
            </div>
          </div>
        )}

        {editingUser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Configurar Empresas Permitidas</h3>
                <p className="text-sm text-gray-500 mt-1">Usuario: {editingUser.email}</p>
              </div>
              <div className="p-6 overflow-y-auto max-h-[50vh]">
                <p className="text-sm text-gray-600 mb-4">
                  Selecciona las empresas que este usuario puede ver. Si no seleccionas ninguna, el usuario vera todas las empresas.
                </p>
                {availableCompanies.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No hay empresas disponibles</p>
                ) : (
                  <div className="space-y-2">
                    {availableCompanies.map((company) => (
                      <label key={company} className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedCompanies.includes(company)}
                          onChange={() => toggleCompany(company)}
                          className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                        />
                        <span className="text-gray-900">{company}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
                <button
                  onClick={closeCompanyEditor}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={saveAllowedCompanies}
                  disabled={actionLoading === editingUser.user_id}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {actionLoading === editingUser.user_id ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </div>
          </div>
        )}

        {editProfileUser && (
          <div className="fixed inset-0 bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl max-w-md w-full mx-4 border border-white/20 overflow-hidden">
              <div className="px-6 py-5 bg-gradient-to-r from-indigo-500 to-purple-600">
                <h3 className="text-lg font-semibold text-white">Editar Usuario</h3>
                <p className="text-sm text-indigo-100 mt-1">{editProfileUser.email}</p>
              </div>
              <div className="p-6 space-y-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Nombre completo</label>
                  <input
                    type="text"
                    value={profileForm.full_name}
                    onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none"
                    placeholder="Nombre completo"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                  <input
                    type="email"
                    value={profileForm.email}
                    onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none"
                    placeholder="correo@ejemplo.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Empresa</label>
                  <select
                    value={profileForm.company}
                    onChange={(e) => setProfileForm({ ...profileForm, company: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none bg-white"
                  >
                    <option value="">Seleccionar empresa...</option>
                    {availableCompanies.map((company) => (
                      <option key={company} value={company}>{company}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Rol</label>
                  <select
                    value={profileForm.role}
                    onChange={(e) => setProfileForm({ ...profileForm, role: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none bg-white"
                  >
                    <option value="user">Usuario</option>
                    <option value="admin">Administrador</option>
                  </select>
                </div>
              </div>
              <div className="px-6 py-4 bg-gray-50/80 border-t border-gray-100 flex justify-end gap-3">
                <button
                  onClick={closeProfileEditor}
                  className="px-5 py-2.5 text-gray-700 bg-white rounded-lg hover:bg-gray-100 border border-gray-200 transition-colors font-medium"
                >
                  Cancelar
                </button>
                <button
                  onClick={saveUserProfile}
                  disabled={actionLoading === editProfileUser.user_id}
                  className="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 transition-all font-medium shadow-lg shadow-indigo-500/25"
                >
                  {actionLoading === editProfileUser.user_id ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </div>
          </div>
        )}

        {fullEditUser && (
          <EditarUsuario
            usuarioId={fullEditUser.user_id}
            onClose={() => setFullEditUser(null)}
            onSave={() => {
              setFullEditUser(null);
              loadUsers();
              setMessage({ type: 'success', text: 'Usuario actualizado correctamente' });
            }}
          />
        )}

        {activeTab === 'usuarios' && (
          <>
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 mb-8 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Solicitudes Pendientes</h2>
              <p className="text-sm text-gray-500 mt-1">Usuarios que esperan aprobacion para acceder al sistema</p>
            </div>
            <span className="px-3 py-1 bg-yellow-100 text-yellow-700 text-sm font-medium rounded-full">
              {pendingUsers.length} pendiente{pendingUsers.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nombre Completo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Empresa
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha de Registro
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {pendingUsers.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                      <div className="text-4xl mb-2">&#10004;</div>
                      <p className="font-medium">No hay solicitudes pendientes</p>
                      <p className="text-sm mt-1">Todas las solicitudes han sido procesadas</p>
                    </td>
                  </tr>
                ) : (
                  pendingUsers.map((pendingUser) => (
                    <tr key={pendingUser.user_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <span className="text-gray-900">{pendingUser.email}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-gray-900">{pendingUser.full_name || '-'}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-gray-600">{pendingUser.company || '-'}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-gray-600 text-sm">{formatDate(pendingUser.created_at)}</span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleApprove(pendingUser.user_id)}
                            disabled={actionLoading === pendingUser.user_id}
                            className="px-3 py-1.5 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {actionLoading === pendingUser.user_id ? '...' : 'Aprobar'}
                          </button>
                          <button
                            onClick={() => handleReject(pendingUser.user_id)}
                            disabled={actionLoading === pendingUser.user_id}
                            className="px-3 py-1.5 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {actionLoading === pendingUser.user_id ? '...' : 'Rechazar'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Todos los Usuarios</h2>
              <p className="text-sm text-gray-500 mt-1">Lista completa de usuarios registrados - configura permisos por empresa</p>
            </div>
            <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full">
              {allUsers.length} usuario{allUsers.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nombre
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Empresas Permitidas
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {allUsers.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                      <p className="font-medium">No hay usuarios registrados</p>
                    </td>
                  </tr>
                ) : (
                  allUsers.map((listedUser) => (
                    <tr key={listedUser.user_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <span className="text-gray-900">{listedUser.email}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-gray-900">{listedUser.full_name || '-'}</span>
                      </td>
                      <td className="px-6 py-4">
                        {getApprovalStatusBadge(listedUser.approval_status)}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          listedUser.role === 'admin' 
                            ? 'bg-purple-100 text-purple-700' 
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {listedUser.role === 'admin' ? 'Admin' : 'Usuario'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {listedUser.allowed_companies && listedUser.allowed_companies.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {listedUser.allowed_companies.slice(0, 2).map((company, idx) => (
                              <span key={idx} className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded">
                                {company.length > 15 ? company.substring(0, 15) + '...' : company}
                              </span>
                            ))}
                            {listedUser.allowed_companies.length > 2 && (
                              <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                                +{listedUser.allowed_companies.length - 2} mas
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">Todas las empresas</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setFullEditUser(listedUser)}
                            className="px-3 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-medium rounded-lg hover:from-emerald-600 hover:to-teal-700 transition-all shadow-sm"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => openCompanyEditor(listedUser)}
                            className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors border border-gray-200"
                          >
                            Empresas
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
          </>
        )}

        {activeTab === 'empresas' && (
          <>
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Gestion de Empresas</h2>
                  <p className="text-sm text-gray-500 mt-1">Administra las empresas registradas en el sistema</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-700 text-sm font-medium rounded-full">
                    {empresas.length} empresa{empresas.length !== 1 ? 's' : ''}
                  </span>
                  <button
                    onClick={() => setShowNewEmpresaModal(true)}
                    className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-medium rounded-lg hover:from-indigo-600 hover:to-purple-700 transition-all shadow-sm"
                  >
                    + Nueva Empresa
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-100">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">RFC</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Industria</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plan</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {!Array.isArray(empresas) || empresas.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                          <div className="text-4xl mb-2">&#127970;</div>
                          <p className="font-medium">No hay empresas registradas</p>
                          <p className="text-sm mt-1">Crea una nueva empresa para comenzar</p>
                        </td>
                      </tr>
                    ) : (
                      empresas.map((empresa) => (
                        <tr key={empresa.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <div>
                              <span className="text-gray-900 font-medium">{empresa.nombre_comercial}</span>
                              {empresa.razon_social && (
                                <p className="text-xs text-gray-500 mt-0.5">{empresa.razon_social}</p>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-gray-600 font-mono text-sm">{empresa.rfc || '-'}</span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-gray-600 capitalize">{empresa.industria?.replace(/_/g, ' ') || '-'}</span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              empresa.plan === 'enterprise' ? 'bg-purple-100 text-purple-700' :
                              empresa.plan === 'profesional' ? 'bg-blue-100 text-blue-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {empresa.plan?.charAt(0).toUpperCase() + empresa.plan?.slice(1) || 'Basico'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              empresa.activa ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                            }`}>
                              {empresa.activa ? 'Activa' : 'Inactiva'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => openEmpresaEditor(empresa)}
                                className="px-3 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-medium rounded-lg hover:from-emerald-600 hover:to-teal-700 transition-all shadow-sm"
                              >
                                Editar
                              </button>
                              <button
                                onClick={() => deleteEmpresa(empresa.id)}
                                disabled={actionLoading === empresa.id}
                                className="px-3 py-1.5 bg-red-100 text-red-700 text-sm font-medium rounded-lg hover:bg-red-200 transition-colors"
                              >
                                {actionLoading === empresa.id ? '...' : 'Desactivar'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {(editingEmpresa || showNewEmpresaModal) && (
          <div className="fixed inset-0 bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl max-w-2xl w-full mx-4 border border-white/20 overflow-hidden max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-5 bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    {editingEmpresa ? 'Editar Empresa' : 'Nueva Empresa'}
                  </h3>
                  <p className="text-sm text-indigo-100 mt-1">
                    {editingEmpresa ? empresaForm.nombre_comercial : 'Registrar nueva empresa en el sistema'}
                  </p>
                </div>
                <button
                  onClick={autofillWithAI}
                  disabled={autofillLoading || !empresaForm.nombre_comercial}
                  className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white text-sm font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 backdrop-blur-sm border border-white/30"
                  title="Auto-rellenar Vision y Mision con IA"
                >
                  {autofillLoading ? (
                    <>
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Generando...</span>
                    </>
                  ) : (
                    <>
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span>Auto-rellenar con IA</span>
                    </>
                  )}
                </button>
              </div>
              <div className="p-6 space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Nombre Comercial *</label>
                    <input
                      type="text"
                      value={empresaForm.nombre_comercial}
                      onChange={(e) => setEmpresaForm({ ...empresaForm, nombre_comercial: e.target.value })}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none"
                      placeholder="Ej: Fortezza"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">RFC</label>
                    <input
                      type="text"
                      value={empresaForm.rfc}
                      onChange={(e) => setEmpresaForm({ ...empresaForm, rfc: e.target.value.toUpperCase() })}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none font-mono"
                      placeholder="XAXX010101000"
                      maxLength={13}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Razon Social</label>
                  <input
                    type="text"
                    value={empresaForm.razon_social}
                    onChange={(e) => setEmpresaForm({ ...empresaForm, razon_social: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none"
                    placeholder="Ej: Fortezza Consultores S.A. de C.V."
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Industria</label>
                    <select
                      value={empresaForm.industria}
                      onChange={(e) => setEmpresaForm({ ...empresaForm, industria: e.target.value })}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none bg-white"
                    >
                      <option value="">Seleccionar...</option>
                      <option value="tecnologia">Tecnologia</option>
                      <option value="servicios_profesionales">Servicios Profesionales</option>
                      <option value="manufactura">Manufactura</option>
                      <option value="comercio">Comercio</option>
                      <option value="construccion">Construccion</option>
                      <option value="salud">Salud</option>
                      <option value="educacion">Educacion</option>
                      <option value="finanzas">Finanzas</option>
                      <option value="inmobiliario">Inmobiliario</option>
                      <option value="otro">Otro</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Plan</label>
                    <select
                      value={empresaForm.plan}
                      onChange={(e) => setEmpresaForm({ ...empresaForm, plan: e.target.value })}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none bg-white"
                    >
                      <option value="basico">Basico</option>
                      <option value="profesional">Profesional</option>
                      <option value="enterprise">Enterprise</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Vision</label>
                  <textarea
                    value={empresaForm.vision}
                    onChange={(e) => setEmpresaForm({ ...empresaForm, vision: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none resize-none"
                    rows={2}
                    placeholder="Vision de la empresa..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Mision</label>
                  <textarea
                    value={empresaForm.mision}
                    onChange={(e) => setEmpresaForm({ ...empresaForm, mision: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none resize-none"
                    rows={2}
                    placeholder="Mision de la empresa..."
                  />
                </div>
              </div>
              <div className="px-6 py-4 bg-gray-50/80 border-t border-gray-100 flex justify-end gap-3">
                <button
                  onClick={() => {
                    closeEmpresaEditor();
                    setShowNewEmpresaModal(false);
                  }}
                  className="px-5 py-2.5 text-gray-700 bg-white rounded-lg hover:bg-gray-100 border border-gray-200 transition-colors font-medium"
                >
                  Cancelar
                </button>
                <button
                  onClick={editingEmpresa ? saveEmpresa : createEmpresa}
                  disabled={actionLoading === (editingEmpresa?.id || 'new') || !empresaForm.nombre_comercial}
                  className="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 transition-all font-medium shadow-lg shadow-indigo-500/25"
                >
                  {actionLoading === (editingEmpresa?.id || 'new') ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
