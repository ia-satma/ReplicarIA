import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import EditarUsuario from '../components/EditarUsuario';

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
    sitio_web: '',
    vision: '',
    mision: ''
  });
  const [showNewEmpresaModal, setShowNewEmpresaModal] = useState(false);
  const [autofillLoading, setAutofillLoading] = useState(false);

  // Abogado del Diablo state (solo super_admin)
  const [abogadoData, setAbogadoData] = useState({
    bloques: [],
    preguntas: [],
    estadisticas: null,
    loading: false,
    error: null
  });
  const [selectedBloque, setSelectedBloque] = useState(null);
  const [evaluacionProyecto, setEvaluacionProyecto] = useState({
    proyecto_id: '',
    respuestas: {},
    resultado: null
  });

  // Oráculo Estratégico state (solo super_admin)
  const [oraculoData, setOraculoData] = useState({
    loading: false,
    error: null,
    resultado: null,
    historial: []
  });
  const [oraculoForm, setOraculoForm] = useState({
    empresa: '',
    rfc: '',
    sitio_web: '',
    sector: '',
    tipo_investigacion: 'completa',
    nivel_profundidad: 'profundo',
    servicio_contratado: '',
    monto: ''
  });

  const autofillWithAI = async () => {
    if (!empresaForm.nombre_comercial) {
      setMessage({ type: 'error', text: 'Ingresa el nombre comercial primero' });
      return;
    }

    setAutofillLoading(true);
    try {
      const response = await api.post('/api/empresas/autofill-ia', {
        nombre_comercial: empresaForm.nombre_comercial,
        razon_social: empresaForm.razon_social,
        rfc: empresaForm.rfc,
        industria: empresaForm.industria,
        sitio_web: empresaForm.sitio_web
      });

      if (response.success) {
        const data = response.data;
        setEmpresaForm(prev => ({
          ...prev,
          vision: data.vision || prev.vision,
          mision: data.mision || prev.mision,
          razon_social: data.razon_social || prev.razon_social,
          rfc: data.rfc || prev.rfc,
          sitio_web: data.sitio_web || prev.sitio_web
        }));
        const source = response.source === 'deep_research' ? 'Deep Research + IA' :
                       response.source === 'ai' ? 'IA' : 'plantilla';
        setMessage({ type: 'success', text: `Perfil generado con ${source} exitosamente` });
      }
    } catch (error) {
      console.error('Error autofill:', error);
      const errorDetail = error.response?.data?.detail || error.message || 'Error al generar perfil con IA';
      if (errorDetail.includes('503') || errorDetail.includes('IA no disponible') || errorDetail.includes('OPENAI')) {
        setMessage({ type: 'error', text: 'Servicio de IA no disponible. Configure OPENAI_API_KEY en el servidor.' });
      } else {
        setMessage({ type: 'error', text: errorDetail });
      }
    } finally {
      setAutofillLoading(false);
    }
  };

  const isSuperAdmin = user?.role === 'super_admin' || user?.is_superadmin;

  const loadAbogadoDiablo = async () => {
    if (!isSuperAdmin) return;

    setAbogadoData(prev => ({ ...prev, loading: true, error: null }));
    try {
      const token = localStorage.getItem('auth_token');
      const headers = { 'X-Admin-Token': token };

      const [bloquesRes, preguntasRes, estadisticasRes] = await Promise.all([
        api.get('/api/admin/abogado-diablo/preguntas-estructuradas/bloques', { headers }),
        api.get('/api/admin/abogado-diablo/preguntas-estructuradas', { headers }),
        api.get('/api/admin/abogado-diablo/estadisticas', { headers })
      ]);

      setAbogadoData({
        bloques: bloquesRes || [],
        preguntas: preguntasRes?.preguntas || [],
        estadisticas: estadisticasRes,
        loading: false,
        error: null
      });
    } catch (error) {
      console.error('Error loading Abogado del Diablo:', error);
      setAbogadoData(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Error al cargar datos del Abogado del Diablo'
      }));
    }
  };

  const evaluarProyecto = async () => {
    if (!evaluacionProyecto.proyecto_id) {
      setMessage({ type: 'error', text: 'Ingresa un ID de proyecto' });
      return;
    }

    try {
      setAbogadoData(prev => ({ ...prev, loading: true }));
      const token = localStorage.getItem('auth_token');

      const response = await api.post('/api/admin/abogado-diablo/preguntas-estructuradas/evaluar-completo', {
        proyecto_id: evaluacionProyecto.proyecto_id,
        respuestas: evaluacionProyecto.respuestas
      }, {
        headers: { 'X-Admin-Token': token }
      });

      setEvaluacionProyecto(prev => ({ ...prev, resultado: response }));
      setMessage({ type: 'success', text: 'Evaluacion completada' });
    } catch (error) {
      console.error('Error evaluando proyecto:', error);
      setMessage({ type: 'error', text: error.message || 'Error al evaluar proyecto' });
    } finally {
      setAbogadoData(prev => ({ ...prev, loading: false }));
    }
  };

  const generarReporteAbogado = async () => {
    if (!evaluacionProyecto.proyecto_id) {
      setMessage({ type: 'error', text: 'Ingresa un ID de proyecto' });
      return;
    }

    try {
      setAbogadoData(prev => ({ ...prev, loading: true }));
      const token = localStorage.getItem('auth_token');

      const response = await api.post('/api/admin/abogado-diablo/reporte/trigger-f9', {
        proyecto_id: evaluacionProyecto.proyecto_id,
        fase_actual: 'F9',
        trigger: 'manual_admin'
      }, {
        headers: { 'X-Admin-Token': token }
      });

      if (response.success) {
        setMessage({ type: 'success', text: `Reporte generado. ${response.email_enviado ? 'Email enviado.' : ''}` });
        if (response.pcloud_link) {
          window.open(response.pcloud_link, '_blank');
        }
      }
    } catch (error) {
      console.error('Error generando reporte:', error);
      setMessage({ type: 'error', text: error.message || 'Error al generar reporte' });
    } finally {
      setAbogadoData(prev => ({ ...prev, loading: false }));
    }
  };

  // Funciones del Oráculo Estratégico
  const investigarEmpresa = async () => {
    if (!oraculoForm.empresa) {
      setMessage({ type: 'error', text: 'Ingresa el nombre de la empresa' });
      return;
    }

    setOraculoData(prev => ({ ...prev, loading: true, error: null }));
    try {
      const token = localStorage.getItem('auth_token');
      const response = await api.post('/api/admin/oraculo-estrategico/investigar', {
        empresa: oraculoForm.empresa,
        sitio_web: oraculoForm.sitio_web || null,
        sector: oraculoForm.sector || null,
        rfc: oraculoForm.rfc || null,
        tipo_investigacion: oraculoForm.tipo_investigacion,
        nivel_profundidad: oraculoForm.nivel_profundidad
      }, {
        headers: { 'X-Admin-Token': token }
      });

      setOraculoData(prev => ({
        ...prev,
        loading: false,
        resultado: response,
        historial: [response, ...prev.historial.slice(0, 9)]
      }));
      setMessage({ type: 'success', text: `Investigación de ${oraculoForm.empresa} completada` });
    } catch (error) {
      console.error('Error en investigación:', error);
      setOraculoData(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Error al investigar empresa'
      }));
      setMessage({ type: 'error', text: error.message || 'Error al investigar empresa' });
    }
  };

  const ejecutarDueDiligence = async () => {
    if (!oraculoForm.empresa || !oraculoForm.rfc) {
      setMessage({ type: 'error', text: 'Ingresa empresa y RFC para Due Diligence' });
      return;
    }

    setOraculoData(prev => ({ ...prev, loading: true, error: null }));
    try {
      const token = localStorage.getItem('auth_token');
      const response = await api.post('/api/admin/oraculo-estrategico/due-diligence', {
        empresa: oraculoForm.empresa,
        rfc: oraculoForm.rfc,
        sitio_web: oraculoForm.sitio_web || null,
        monto_operacion: oraculoForm.monto ? parseFloat(oraculoForm.monto) : null,
        tipo_servicio: oraculoForm.servicio_contratado || null
      }, {
        headers: { 'X-Admin-Token': token }
      });

      setOraculoData(prev => ({
        ...prev,
        loading: false,
        resultado: response
      }));
      setMessage({ type: 'success', text: `Due Diligence de ${oraculoForm.empresa} completado` });
    } catch (error) {
      console.error('Error en due diligence:', error);
      setOraculoData(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Error en due diligence'
      }));
    }
  };

  const documentarMaterialidad = async () => {
    if (!oraculoForm.empresa || !oraculoForm.rfc || !oraculoForm.servicio_contratado || !oraculoForm.monto) {
      setMessage({ type: 'error', text: 'Completa todos los campos para documentar materialidad' });
      return;
    }

    setOraculoData(prev => ({ ...prev, loading: true, error: null }));
    try {
      const token = localStorage.getItem('auth_token');
      const response = await api.post('/api/admin/oraculo-estrategico/materialidad', {
        empresa: oraculoForm.empresa,
        rfc: oraculoForm.rfc,
        servicio_contratado: oraculoForm.servicio_contratado,
        monto: parseFloat(oraculoForm.monto),
        sitio_web: oraculoForm.sitio_web || null
      }, {
        headers: { 'X-Admin-Token': token }
      });

      setOraculoData(prev => ({
        ...prev,
        loading: false,
        resultado: response
      }));
      setMessage({ type: 'success', text: `Documentación de materialidad para ${oraculoForm.empresa} generada` });
    } catch (error) {
      console.error('Error en materialidad:', error);
      setOraculoData(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Error al documentar materialidad'
      }));
    }
  };

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'super_admin' || user?.is_superadmin) {
      loadUsers();
      loadCompanies();
      loadEmpresas();
    }
    if (isSuperAdmin) {
      loadAbogadoDiablo();
    }
  }, [user]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const [pendingRes, allRes] = await Promise.all([
        api.get('/api/auth/admin/pending-users'),
        api.get('/api/auth/admin/all-users')
      ]);
      setPendingUsers(pendingRes.users || []);
      setAllUsers(allRes.users || []);
    } catch (error) {
      console.error('Error loading users:', error);
      setMessage({ type: 'error', text: 'Error al cargar usuarios' });
    } finally {
      setLoading(false);
    }
  };

  const loadCompanies = async () => {
    try {
      const response = await api.get('/api/auth/admin/companies');
      setAvailableCompanies(response.companies || []);
    } catch (error) {
      console.error('Error loading companies:', error);
    }
  };

  const loadEmpresas = async () => {
    try {
      const response = await api.get('/api/empresas/');
      const data = response;
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
      sitio_web: empresa.sitio_web || '',
      vision: empresa.vision || '',
      mision: empresa.mision || ''
    });
  };

  const closeEmpresaEditor = () => {
    setEditingEmpresa(null);
    setEmpresaForm({
      nombre_comercial: '',
      razon_social: '',
      rfc: '',
      industria: '',
      sitio_web: '',
      vision: '',
      mision: ''
    });
  };

  const saveEmpresa = async () => {
    if (!editingEmpresa) return;

    try {
      setActionLoading(editingEmpresa.id);
      const response = await api.patch(`/api/empresas/${editingEmpresa.id}`, empresaForm);
      if (response) {
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
      const response = await api.post('/api/empresas/', empresaForm);
      if (response) {
        setMessage({ type: 'success', text: 'Empresa creada correctamente' });
        await loadEmpresas();
        await loadCompanies();
        setShowNewEmpresaModal(false);
        setEmpresaForm({
          nombre_comercial: '',
          razon_social: '',
          rfc: '',
          industria: '',
          sitio_web: '',
          vision: '',
          mision: ''
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
      await api.delete(`/api/empresas/${empresaId}`);
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
      const response = await api.post(`/api/auth/admin/approve-user/${userId}`);
      if (response.success) {
        setMessage({ type: 'success', text: response.message });
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
      const response = await api.post(`/api/auth/admin/reject-user/${userId}`);
      if (response.success) {
        setMessage({ type: 'success', text: response.message });
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
      const response = await api.post(`/api/auth/admin/user/${editingUser.user_id}/allowed-companies`, {
        allowed_companies: selectedCompanies
      });
      if (response.success) {
        setMessage({ type: 'success', text: response.message });
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
      const response = await api.put(`/api/auth/admin/user/${editProfileUser.user_id}`, profileForm);
      if (response.success) {
        setMessage({ type: 'success', text: response.message });
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

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin' || user?.is_superadmin;
  if (!user || !isAdmin) {
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
            {isSuperAdmin && (
              <button
                onClick={() => setActiveTab('abogado-diablo')}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                  activeTab === 'abogado-diablo'
                    ? 'bg-white text-red-600 border-t border-l border-r border-gray-200 -mb-px'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Abogado del Diablo
              </button>
            )}
            {isSuperAdmin && (
              <button
                onClick={() => setActiveTab('oraculo-estrategico')}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-2 ${
                  activeTab === 'oraculo-estrategico'
                    ? 'bg-white text-[#34C759] border-t border-l border-r border-gray-200 -mb-px'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Oráculo Estratégico
              </button>
            )}
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
              <div className="px-6 py-5 bg-primary text-white">
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
                  className="px-5 py-2.5 bg-primary text-white text-white rounded-lg hover:opacity-90 disabled:opacity-50 transition-all font-medium shadow-lg shadow-primary/25"
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
                            className="px-3 py-1.5 text-white text-sm font-medium rounded-lg transition-all shadow-sm"
                            style={{ background: 'linear-gradient(180deg, #3CD366 0%, #34C759 100%)' }}
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

        {activeTab === 'abogado-diablo' && isSuperAdmin && (
          <div className="space-y-6">
            {/* Header del Abogado del Diablo */}
            <div className="bg-gradient-to-r from-red-600 to-red-800 rounded-lg shadow-lg p-6 text-white">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-lg">
                  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-bold">Abogado del Diablo</h2>
                  <p className="text-red-100 text-sm mt-1">
                    Modulo interno de control y aprendizaje organizacional - Solo Super Admin
                  </p>
                </div>
              </div>
              <div className="mt-4 p-3 bg-red-900/50 rounded-lg text-sm">
                <strong>ADVERTENCIA:</strong> Esta informacion es ALTAMENTE SENSIBLE.
                Herramienta interna de compliance. NO compartir con terceros.
              </div>
            </div>

            {/* Estadisticas Globales */}
            {abogadoData.estadisticas && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
                  <div className="text-3xl font-bold text-gray-900">
                    {abogadoData.estadisticas.total_proyectos || 0}
                  </div>
                  <div className="text-sm text-gray-500">Proyectos Analizados</div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
                  <div className="text-3xl font-bold text-green-600">
                    {abogadoData.estadisticas.aprobados || 0}
                  </div>
                  <div className="text-sm text-gray-500">Aprobados</div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
                  <div className="text-3xl font-bold text-red-600">
                    {abogadoData.estadisticas.rechazados || 0}
                  </div>
                  <div className="text-sm text-gray-500">Rechazados</div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
                  <div className="text-3xl font-bold text-yellow-600">
                    {abogadoData.estadisticas.banderas_rojas || 0}
                  </div>
                  <div className="text-sm text-gray-500">Banderas Rojas</div>
                </div>
              </div>
            )}

            {/* Evaluacion de Proyecto */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900">Evaluar Proyecto</h3>
                <p className="text-sm text-gray-500 mt-1">Genera un reporte de las 25 preguntas estructuradas</p>
              </div>
              <div className="p-6">
                <div className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-2">ID del Proyecto</label>
                    <input
                      type="text"
                      value={evaluacionProyecto.proyecto_id}
                      onChange={(e) => setEvaluacionProyecto(prev => ({ ...prev, proyecto_id: e.target.value }))}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-red-500 focus:ring-2 focus:ring-red-200 transition-all outline-none"
                      placeholder="Ej: PROJ-2024-001"
                    />
                  </div>
                  <button
                    onClick={evaluarProyecto}
                    disabled={abogadoData.loading || !evaluacionProyecto.proyecto_id}
                    className="px-6 py-2.5 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-medium rounded-lg hover:from-amber-600 hover:to-orange-700 disabled:opacity-50 transition-all shadow-sm"
                  >
                    {abogadoData.loading ? 'Evaluando...' : 'Evaluar'}
                  </button>
                  <button
                    onClick={generarReporteAbogado}
                    disabled={abogadoData.loading || !evaluacionProyecto.proyecto_id}
                    className="px-6 py-2.5 bg-gradient-to-r from-red-600 to-red-700 text-white font-medium rounded-lg hover:from-red-700 hover:to-red-800 disabled:opacity-50 transition-all shadow-sm"
                  >
                    {abogadoData.loading ? 'Generando...' : 'Generar Reporte PDF'}
                  </button>
                </div>

                {evaluacionProyecto.resultado && (
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <h4 className="font-semibold text-gray-900 mb-3">Resultado de Evaluacion</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center p-3 bg-white rounded-lg border">
                        <div className={`text-2xl font-bold ${
                          evaluacionProyecto.resultado.evaluacion?.semaforo === 'verde' ? 'text-green-600' :
                          evaluacionProyecto.resultado.evaluacion?.semaforo === 'amarillo' ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {evaluacionProyecto.resultado.evaluacion?.score_total?.toFixed(1) || 0}%
                        </div>
                        <div className="text-xs text-gray-500">Score Total</div>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg border">
                        <div className={`text-xl font-bold uppercase ${
                          evaluacionProyecto.resultado.evaluacion?.semaforo === 'verde' ? 'text-green-600' :
                          evaluacionProyecto.resultado.evaluacion?.semaforo === 'amarillo' ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {evaluacionProyecto.resultado.evaluacion?.semaforo || 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500">Semaforo</div>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg border">
                        <div className="text-2xl font-bold text-red-600">
                          {evaluacionProyecto.resultado.evaluacion?.banderas_rojas?.length || 0}
                        </div>
                        <div className="text-xs text-gray-500">Banderas Rojas</div>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg border">
                        <div className="text-2xl font-bold text-yellow-600">
                          {evaluacionProyecto.resultado.evaluacion?.alertas?.length || 0}
                        </div>
                        <div className="text-xs text-gray-500">Alertas</div>
                      </div>
                    </div>
                    {evaluacionProyecto.resultado.evaluacion?.recomendacion && (
                      <div className="p-3 bg-blue-50 rounded-lg text-blue-800 text-sm">
                        <strong>Recomendacion:</strong> {evaluacionProyecto.resultado.evaluacion.recomendacion}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* 25 Preguntas Estructuradas */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900">25 Preguntas Estructuradas</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Organizadas en 6 bloques con diferentes niveles de severidad
                </p>
              </div>

              {abogadoData.loading ? (
                <div className="p-12 text-center text-gray-500">
                  <div className="animate-spin text-4xl mb-4">&#8987;</div>
                  <p>Cargando preguntas...</p>
                </div>
              ) : abogadoData.error ? (
                <div className="p-6 text-center text-red-500">
                  <p>{abogadoData.error}</p>
                  <button
                    onClick={loadAbogadoDiablo}
                    className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                  >
                    Reintentar
                  </button>
                </div>
              ) : (
                <div className="p-6">
                  {/* Bloques */}
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
                    {abogadoData.bloques.map((bloque, idx) => (
                      <button
                        key={bloque.id || idx}
                        onClick={() => setSelectedBloque(selectedBloque === bloque.id ? null : bloque.id)}
                        className={`p-3 rounded-lg border text-left transition-all ${
                          selectedBloque === bloque.id
                            ? 'border-red-500 bg-red-50 shadow-sm'
                            : 'border-gray-200 hover:border-red-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="text-xs font-semibold text-gray-500">{bloque.id || `B${idx + 1}`}</div>
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {bloque.nombre || bloque.id?.replace(/_/g, ' ')}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {bloque.peso_porcentaje || 0}%
                        </div>
                      </button>
                    ))}
                  </div>

                  {/* Lista de Preguntas */}
                  <div className="space-y-3">
                    {(Array.isArray(abogadoData.preguntas) ? abogadoData.preguntas : [])
                      .filter(p => !selectedBloque || p.bloque === selectedBloque)
                      .map((pregunta, idx) => (
                        <div
                          key={pregunta.id || idx}
                          className={`p-4 rounded-lg border ${
                            pregunta.severidad === 'critico' ? 'border-red-200 bg-red-50' :
                            pregunta.severidad === 'importante' ? 'border-yellow-200 bg-yellow-50' :
                            'border-gray-200 bg-gray-50'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`px-2 py-1 text-xs font-bold rounded ${
                              pregunta.severidad === 'critico' ? 'bg-red-600 text-white' :
                              pregunta.severidad === 'importante' ? 'bg-yellow-500 text-white' :
                              'bg-gray-400 text-white'
                            }`}>
                              {pregunta.numero || `P${String(idx + 1).padStart(2, '0')}`}
                            </div>
                            <div className="flex-1">
                              <p className="text-gray-900 font-medium">{pregunta.pregunta}</p>
                              {pregunta.descripcion && (
                                <p className="text-sm text-gray-500 mt-1">{pregunta.descripcion}</p>
                              )}
                              <div className="flex items-center gap-2 mt-2">
                                <span className={`px-2 py-0.5 text-xs rounded-full ${
                                  pregunta.severidad === 'critico' ? 'bg-red-100 text-red-700' :
                                  pregunta.severidad === 'importante' ? 'bg-yellow-100 text-yellow-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {pregunta.severidad}
                                </span>
                                {pregunta.obligatoria && (
                                  <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full">
                                    Obligatoria
                                  </span>
                                )}
                                {pregunta.norma_relacionada && (
                                  <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                                    {pregunta.norma_relacionada}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>

                  {(!abogadoData.preguntas || abogadoData.preguntas.length === 0) && (
                    <div className="text-center py-8 text-gray-500">
                      <p>No se encontraron preguntas estructuradas</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'oraculo-estrategico' && isSuperAdmin && (
          <div className="space-y-6">
            {/* Header del Oráculo - Estilo ReplicarIA */}
            <div className="card-premium overflow-hidden">
              <div className="bg-gradient-to-r from-[#34C759] to-[#2CB24E] p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="icon-container-lg bg-white/20 text-white">
                      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-white">Oráculo Estratégico</h2>
                      <p className="text-white/80 text-sm mt-1">
                        Investigación profunda • Due Diligence • Materialidad SAT
                      </p>
                    </div>
                  </div>
                  <div className="hidden md:flex items-center gap-2">
                    <span className="px-3 py-1 bg-white/20 rounded-full text-white text-xs font-medium">
                      Art. 69-B CFF
                    </span>
                    <span className="px-3 py-1 bg-white/20 rounded-full text-white text-xs font-medium">
                      14 Fases
                    </span>
                  </div>
                </div>
              </div>
              <div className="px-6 py-3 bg-[#E8F9ED] border-t border-[#34C759]/20">
                <div className="flex items-center gap-6 text-sm text-[#249C43]">
                  <span className="flex items-center gap-1.5">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    PESTEL
                  </span>
                  <span className="flex items-center gap-1.5">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Porter
                  </span>
                  <span className="flex items-center gap-1.5">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    ESG
                  </span>
                  <span className="flex items-center gap-1.5">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Due Diligence
                  </span>
                </div>
              </div>
            </div>

            {/* Formulario de Investigación - Estilo ReplicarIA */}
            <div className="card-premium">
              <div className="px-6 py-4 border-b border-border flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-foreground">Investigar Empresa / Proveedor</h3>
                  <p className="text-sm text-muted-foreground mt-1">Ingresa los datos para iniciar la investigación</p>
                </div>
                <div className="icon-container">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="label-premium">Nombre de la Empresa *</label>
                    <input
                      type="text"
                      value={oraculoForm.empresa}
                      onChange={(e) => setOraculoForm({ ...oraculoForm, empresa: e.target.value })}
                      className="input-premium"
                      placeholder="Ej: Fortezza Consultores"
                    />
                  </div>
                  <div>
                    <label className="label-premium">RFC</label>
                    <input
                      type="text"
                      value={oraculoForm.rfc}
                      onChange={(e) => setOraculoForm({ ...oraculoForm, rfc: e.target.value.toUpperCase() })}
                      className="input-premium font-mono"
                      placeholder="XAXX010101000"
                      maxLength={13}
                    />
                  </div>
                  <div>
                    <label className="label-premium">Sitio Web</label>
                    <input
                      type="url"
                      value={oraculoForm.sitio_web}
                      onChange={(e) => setOraculoForm({ ...oraculoForm, sitio_web: e.target.value })}
                      className="input-premium"
                      placeholder="https://www.ejemplo.com"
                    />
                  </div>
                  <div>
                    <label className="label-premium">Sector / Industria</label>
                    <select
                      value={oraculoForm.sector}
                      onChange={(e) => setOraculoForm({ ...oraculoForm, sector: e.target.value })}
                      className="input-premium"
                    >
                      <option value="">Seleccionar...</option>
                      <option value="tecnologia">Tecnología</option>
                      <option value="servicios_profesionales">Servicios Profesionales</option>
                      <option value="manufactura">Manufactura</option>
                      <option value="comercio">Comercio</option>
                      <option value="construccion">Construcción</option>
                      <option value="salud">Salud</option>
                      <option value="finanzas">Finanzas</option>
                      <option value="inmobiliario">Inmobiliario</option>
                      <option value="otro">Otro</option>
                    </select>
                  </div>
                </div>

                {/* Campos para Materialidad */}
                <div className="divider-premium pt-4 mt-4">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="icon-container-sm">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-foreground">Para Documentación de Materialidad SAT:</p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="label-premium">Servicio Contratado</label>
                      <input
                        type="text"
                        value={oraculoForm.servicio_contratado}
                        onChange={(e) => setOraculoForm({ ...oraculoForm, servicio_contratado: e.target.value })}
                        className="input-premium"
                        placeholder="Ej: Consultoría fiscal especializada"
                      />
                    </div>
                    <div>
                      <label className="label-premium">Monto de Operación (MXN)</label>
                      <input
                        type="number"
                        value={oraculoForm.monto}
                        onChange={(e) => setOraculoForm({ ...oraculoForm, monto: e.target.value })}
                        className="input-premium"
                        placeholder="500000"
                      />
                    </div>
                  </div>
                </div>

                {/* Configuración */}
                <div className="divider-premium pt-4 mt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="label-premium">Tipo de Investigación</label>
                      <select
                        value={oraculoForm.tipo_investigacion}
                        onChange={(e) => setOraculoForm({ ...oraculoForm, tipo_investigacion: e.target.value })}
                        className="input-premium"
                      >
                        <option value="completa">Completa (14 fases)</option>
                        <option value="empresa">Solo Empresa</option>
                        <option value="industria">Análisis de Industria</option>
                        <option value="competidores">Competidores</option>
                      </select>
                    </div>
                    <div>
                      <label className="label-premium">Nivel de Profundidad</label>
                      <select
                        value={oraculoForm.nivel_profundidad}
                        onChange={(e) => setOraculoForm({ ...oraculoForm, nivel_profundidad: e.target.value })}
                        className="input-premium"
                      >
                        <option value="profundo">Profundo (~3-5 min)</option>
                        <option value="normal">Normal (~1-2 min)</option>
                        <option value="rapido">Rápido (~30 seg)</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Botones de Acción - Estilo ReplicarIA */}
                <div className="flex flex-wrap gap-3 pt-4 border-t border-border">
                  <button
                    onClick={investigarEmpresa}
                    disabled={oraculoData.loading || !oraculoForm.empresa}
                    className="btn-primary-premium flex items-center gap-2"
                  >
                    {oraculoData.loading ? (
                      <>
                        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Investigando...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <span>Investigar Empresa</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={ejecutarDueDiligence}
                    disabled={oraculoData.loading || !oraculoForm.empresa || !oraculoForm.rfc}
                    className="btn-secondary-premium flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span>Due Diligence</span>
                  </button>
                  <button
                    onClick={documentarMaterialidad}
                    disabled={oraculoData.loading || !oraculoForm.empresa || !oraculoForm.rfc || !oraculoForm.servicio_contratado || !oraculoForm.monto}
                    className="btn-secondary-premium flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span>Documentar Materialidad SAT</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Resultados - Estilo ReplicarIA */}
            {oraculoData.resultado && (
              <div className="card-premium overflow-hidden animate-fade-in">
                <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/30">
                  <div className="flex items-center gap-3">
                    <div className={`icon-container ${oraculoData.resultado.success ? 'bg-primary/10 text-primary' : 'bg-red-100 text-red-600'}`}>
                      {oraculoData.resultado.success ? (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-foreground">
                        {oraculoData.resultado.empresa}
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        {oraculoData.resultado.timestamp ? new Date(oraculoData.resultado.timestamp).toLocaleString('es-MX') : 'Resultado de investigación'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`badge-premium ${oraculoData.resultado.success ? 'badge-success' : 'badge-error'}`}>
                      {oraculoData.resultado.success ? 'Completado' : 'Error'}
                    </span>
                  </div>
                </div>

                {oraculoData.resultado.success ? (
                  <div className="p-6 space-y-6">
                    {/* Scores Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Score de Confianza */}
                      {oraculoData.resultado.score_confianza && (
                        <div className="card-premium-hover p-4 text-center">
                          <div className="text-3xl font-bold text-primary">
                            {oraculoData.resultado.score_confianza}%
                          </div>
                          <div className="text-sm font-medium text-foreground mt-1">Score de Confianza</div>
                          <div className="text-xs text-muted-foreground">
                            {oraculoData.resultado.fuentes_consultadas || 0} fuentes
                          </div>
                        </div>
                      )}

                      {/* Score de Materialidad */}
                      {oraculoData.resultado.score_materialidad !== undefined && (
                        <div className="card-premium-hover p-4 text-center">
                          <div className={`text-3xl font-bold ${
                            oraculoData.resultado.score_materialidad >= 70 ? 'text-primary' :
                            oraculoData.resultado.score_materialidad >= 50 ? 'text-amber-500' :
                            'text-red-500'
                          }`}>
                            {oraculoData.resultado.score_materialidad}%
                          </div>
                          <div className="text-sm font-medium text-foreground mt-1">Materialidad SAT</div>
                          <div className="text-xs text-muted-foreground">Art. 69-B CFF</div>
                        </div>
                      )}

                      {/* Evaluación Riesgo */}
                      {oraculoData.resultado.evaluacion_riesgo && (
                        <div className="card-premium-hover p-4 text-center">
                          <div className={`text-3xl font-bold ${
                            oraculoData.resultado.evaluacion_riesgo.nivel === 'bajo' ? 'text-primary' :
                            oraculoData.resultado.evaluacion_riesgo.nivel === 'medio' ? 'text-amber-500' :
                            'text-red-500'
                          }`}>
                            {oraculoData.resultado.evaluacion_riesgo.nivel?.toUpperCase() || 'N/A'}
                          </div>
                          <div className="text-sm font-medium text-foreground mt-1">Nivel de Riesgo</div>
                          <div className="text-xs text-muted-foreground">Evaluación general</div>
                        </div>
                      )}
                    </div>

                    {/* Resumen Ejecutivo */}
                    {oraculoData.resultado.resumen_ejecutivo && (
                      <div className="space-y-2">
                        <h4 className="font-semibold text-foreground flex items-center gap-2">
                          <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          Resumen Ejecutivo
                        </h4>
                        <div className="p-4 bg-muted/50 rounded-xl text-sm text-foreground whitespace-pre-wrap leading-relaxed">
                          {oraculoData.resultado.resumen_ejecutivo}
                        </div>
                      </div>
                    )}

                    {/* Banderas Rojas */}
                    {oraculoData.resultado.banderas_rojas && oraculoData.resultado.banderas_rojas.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-semibold text-red-600 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          Banderas Rojas ({oraculoData.resultado.banderas_rojas.length})
                        </h4>
                        <ul className="space-y-2">
                          {oraculoData.resultado.banderas_rojas.map((bandera, idx) => (
                            <li key={idx} className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-700 dark:text-red-400 flex items-start gap-2">
                              <span className="text-red-500 mt-0.5">•</span>
                              {bandera}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Recomendaciones */}
                    {oraculoData.resultado.recomendaciones && oraculoData.resultado.recomendaciones.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-semibold text-foreground flex items-center gap-2">
                          <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                          </svg>
                          Recomendaciones
                        </h4>
                        <ul className="space-y-2">
                          {oraculoData.resultado.recomendaciones.map((rec, idx) => (
                            <li key={idx} className="p-3 bg-primary/5 border border-primary/20 rounded-xl text-sm text-foreground flex items-start gap-2">
                              <span className="text-primary mt-0.5">✓</span>
                              {rec}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Conclusión */}
                    {oraculoData.resultado.conclusion && (
                      <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl">
                        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                          <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Conclusión
                        </h4>
                        <p className="text-sm text-foreground">{oraculoData.resultado.conclusion}</p>
                      </div>
                    )}

                    {/* Botones de Acción */}
                    <div className="flex flex-wrap gap-3 pt-4 border-t border-border">
                      <button
                        onClick={() => {
                          const dataStr = JSON.stringify(oraculoData.resultado, null, 2);
                          const dataBlob = new Blob([dataStr], { type: 'application/json' });
                          const url = URL.createObjectURL(dataBlob);
                          const link = document.createElement('a');
                          link.href = url;
                          link.download = `oraculo_${oraculoData.resultado.empresa?.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.json`;
                          link.click();
                        }}
                        className="btn-primary-premium flex items-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Descargar Reporte
                      </button>
                      <button
                        onClick={() => setOraculoData(prev => ({ ...prev, resultado: null }))}
                        className="btn-secondary-premium flex items-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Nueva Investigación
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="p-6">
                    <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-400">
                      <strong>Error:</strong> {oraculoData.resultado.error || 'Error desconocido'}
                    </div>
                    <button
                      onClick={() => setOraculoData(prev => ({ ...prev, resultado: null }))}
                      className="mt-4 btn-secondary-premium flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Reintentar
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Error General */}
            {oraculoData.error && !oraculoData.resultado && (
              <div className="card-premium p-4 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
                <div className="flex items-center gap-3 text-red-700 dark:text-red-400">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span><strong>Error:</strong> {oraculoData.error}</span>
                </div>
              </div>
            )}
          </div>
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
                  <span className="px-3 py-1 bg-primary/10 text-primary text-sm font-medium rounded-full">
                    {empresas.length} empresa{empresas.length !== 1 ? 's' : ''}
                  </span>
                  <button
                    onClick={() => setShowNewEmpresaModal(true)}
                    className="px-4 py-2 bg-primary text-white text-white text-sm font-medium rounded-lg hover:opacity-90 transition-all shadow-sm"
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
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {!Array.isArray(empresas) || empresas.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
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
                              empresa.activa ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                            }`}>
                              {empresa.activa ? 'Activa' : 'Inactiva'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => openEmpresaEditor(empresa)}
                                className="px-3 py-1.5 bg-primary text-white text-sm font-medium rounded-lg hover:opacity-90 transition-all shadow-sm"
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
              <div className="px-6 py-5 bg-primary text-white flex items-center justify-between">
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
                  <label className="block text-sm font-medium text-gray-700 mb-2">Sitio Web</label>
                  <input
                    type="url"
                    value={empresaForm.sitio_web}
                    onChange={(e) => setEmpresaForm({ ...empresaForm, sitio_web: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none"
                    placeholder="https://www.ejemplo.com"
                  />
                  <p className="mt-1 text-xs text-gray-500">Opcional - Para investigacion con Deep Research</p>
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
                  className="px-5 py-2.5 bg-primary text-white text-white rounded-lg hover:opacity-90 disabled:opacity-50 transition-all font-medium shadow-lg shadow-primary/25"
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
