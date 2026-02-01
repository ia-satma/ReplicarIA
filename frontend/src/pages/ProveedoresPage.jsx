import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import ProveedorCard from '../components/proveedores/ProveedorCard';
import RiesgoIndicador from '../components/proveedores/RiesgoIndicador';
import DocumentUploadOCR from '../components/proveedores/DocumentUploadOCR';

const ProveedoresPage = () => {
  const { token, empresaId, isSuperAdmin, user, selectEmpresa } = useAuth();
  const [proveedores, setProveedores] = useState([]);
  const [empresas, setEmpresas] = useState([]);
  const [estadisticas, setEstadisticas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtros, setFiltros] = useState({
    estatus: '',
    tipo_proveedor: '',
    nivel_riesgo: '',
    busqueda: ''
  });
  const [showForm, setShowForm] = useState(false);
  const [proveedorSeleccionado, setProveedorSeleccionado] = useState(null);
  const [vistaDetalle, setVistaDetalle] = useState(false);

  const fetchProveedores = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filtros.estatus) params.append('estatus', filtros.estatus);
      if (filtros.tipo_proveedor) params.append('tipo_proveedor', filtros.tipo_proveedor);
      if (filtros.nivel_riesgo) params.append('nivel_riesgo', filtros.nivel_riesgo);
      if (filtros.busqueda) params.append('busqueda', filtros.busqueda);

      const response = await fetch(`/api/proveedores?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Empresa-ID': empresaId
        }
      });

      if (!response.ok) throw new Error('Error cargando proveedores');
      
      const data = await response.json();
      setProveedores(data.proveedores || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchEstadisticas = async () => {
    try {
      const response = await fetch('/api/proveedores/estadisticas', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Empresa-ID': empresaId
        }
      });

      if (response.ok) {
        const data = await response.json();
        setEstadisticas(data);
      }
    } catch (err) {
      console.error('Error cargando estadísticas:', err);
    }
  };

  const fetchEmpresas = async () => {
    try {
      const response = await fetch('/api/empresas', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setEmpresas(data || []);
        // Si solo hay una empresa, seleccionarla automáticamente
        if (data && data.length === 1 && !empresaId) {
          selectEmpresa(data[0].id);
        }
      }
    } catch (err) {
      console.error('Error cargando empresas:', err);
    }
  };

  useEffect(() => {
    // Si es superadmin, cargar lista de empresas para el selector
    if (token && isSuperAdmin) {
      fetchEmpresas();
    }
  }, [token, isSuperAdmin]);

  useEffect(() => {
    if (token && empresaId) {
      fetchProveedores();
      fetchEstadisticas();
    } else if (token && !empresaId) {
      // Usuario autenticado pero sin empresa seleccionada
      setLoading(false);
    } else {
      // Sin autenticación
      setLoading(false);
      if (!token) {
        setError('Debes iniciar sesión para ver los proveedores');
      }
    }
  }, [token, empresaId, filtros]);

  const handleDelete = async (proveedor) => {
    if (!window.confirm(`¿Estás seguro de eliminar a ${proveedor.razon_social}?`)) return;

    try {
      const response = await fetch(`/api/proveedores/${proveedor.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Empresa-ID': empresaId
        }
      });

      if (!response.ok) throw new Error('Error eliminando proveedor');
      
      fetchProveedores();
      fetchEstadisticas();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleView = (proveedor) => {
    setProveedorSeleccionado(proveedor);
    setVistaDetalle(true);
  };

  const handleEdit = (proveedor) => {
    setProveedorSeleccionado(proveedor);
    setShowForm(true);
  };

  const tiposProveedor = [
    { value: '', label: 'Todos los tipos' },
    { value: 'CONSULTORIA_MACRO', label: 'Consultoría Macro' },
    { value: 'CONSULTORIA_ESTRATEGICA', label: 'Consultoría Estratégica' },
    { value: 'SOFTWARE_SAAS', label: 'Software/SaaS' },
    { value: 'MARKETING_BRANDING', label: 'Marketing/Branding' },
    { value: 'INTRAGRUPO', label: 'Intragrupo' },
    { value: 'SERVICIOS_ESPECIALIZADOS', label: 'Servicios Especializados' },
    { value: 'OUTSOURCING_PERMITIDO', label: 'Outsourcing Permitido' },
    { value: 'OTRO', label: 'Otro' }
  ];

  if (vistaDetalle && proveedorSeleccionado) {
    return (
      <DetalleProveedor 
        proveedor={proveedorSeleccionado} 
        onBack={() => { setVistaDetalle(false); setProveedorSeleccionado(null); }}
        token={token}
        empresaId={empresaId}
        onUpdate={fetchProveedores}
      />
    );
  }

  if (showForm) {
    return (
      <FormularioProveedor 
        proveedor={proveedorSeleccionado}
        onClose={() => { setShowForm(false); setProveedorSeleccionado(null); }}
        onSuccess={() => { setShowForm(false); setProveedorSeleccionado(null); fetchProveedores(); fetchEstadisticas(); }}
        token={token}
        empresaId={empresaId}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Proveedores</h1>
            <p className="text-gray-600 mt-1">Gestiona y evalúa el riesgo de tus proveedores de servicios</p>
            {isSuperAdmin && empresaId && empresas.length > 0 && (
              <div className="mt-2 flex items-center gap-2">
                <span className="text-sm text-gray-500">Empresa:</span>
                <select
                  value={empresaId}
                  onChange={(e) => selectEmpresa(e.target.value)}
                  className="text-sm px-2 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  {empresas.map(empresa => (
                    <option key={empresa.id} value={empresa.id}>
                      {empresa.nombre_comercial || empresa.razon_social}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            disabled={!empresaId}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Nuevo Proveedor
          </button>
        </div>

        {estadisticas && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <p className="text-sm text-gray-500">Total Proveedores</p>
              <p className="text-2xl font-bold text-gray-900">{estadisticas.total}</p>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <p className="text-sm text-gray-500">Activos</p>
              <p className="text-2xl font-bold text-green-600">{estadisticas.por_estatus?.activos || 0}</p>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <p className="text-sm text-gray-500">Pendientes Revisión</p>
              <p className="text-2xl font-bold text-yellow-600">{estadisticas.por_estatus?.pendientes || 0}</p>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <p className="text-sm text-gray-500">Riesgo Alto/Crítico</p>
              <p className="text-2xl font-bold text-red-600">
                {(estadisticas.por_riesgo?.alto || 0) + (estadisticas.por_riesgo?.critico || 0)}
              </p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Buscar</label>
              <input
                type="text"
                value={filtros.busqueda}
                onChange={(e) => setFiltros({ ...filtros, busqueda: e.target.value })}
                placeholder="RFC, razón social..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estatus</label>
              <select
                value={filtros.estatus}
                onChange={(e) => setFiltros({ ...filtros, estatus: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos</option>
                <option value="activo">Activo</option>
                <option value="inactivo">Inactivo</option>
                <option value="pendiente_revision">Pendiente Revisión</option>
                <option value="bloqueado">Bloqueado</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
              <select
                value={filtros.tipo_proveedor}
                onChange={(e) => setFiltros({ ...filtros, tipo_proveedor: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {tiposProveedor.map(tipo => (
                  <option key={tipo.value} value={tipo.value}>{tipo.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nivel de Riesgo</label>
              <select
                value={filtros.nivel_riesgo}
                onChange={(e) => setFiltros({ ...filtros, nivel_riesgo: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos</option>
                <option value="bajo">Bajo</option>
                <option value="medio">Medio</option>
                <option value="alto">Alto</option>
                <option value="critico">Crítico</option>
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-12 h-12 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600"></div>
          </div>
        ) : !empresaId && isSuperAdmin ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            <div className="text-center mb-6">
              <svg className="mx-auto h-12 w-12 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900">Selecciona una Empresa</h3>
              <p className="mt-2 text-gray-500">Como superadmin, debes seleccionar una empresa para gestionar sus proveedores.</p>
            </div>
            {empresas.length > 0 ? (
              <div className="max-w-md mx-auto">
                <select
                  onChange={(e) => selectEmpresa(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                  defaultValue=""
                >
                  <option value="" disabled>Selecciona una empresa...</option>
                  {empresas.map(empresa => (
                    <option key={empresa.id} value={empresa.id}>
                      {empresa.nombre_comercial || empresa.razon_social}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-gray-500">No hay empresas registradas.</p>
                <a href="/admin" className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Ir a Panel Admin para crear empresa
                </a>
              </div>
            )}
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        ) : proveedores.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No hay proveedores</h3>
            <p className="mt-2 text-gray-500">Comienza agregando tu primer proveedor de servicios.</p>
            <button
              onClick={() => setShowForm(true)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Agregar Proveedor
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {proveedores.map(proveedor => (
              <ProveedorCard
                key={proveedor.id}
                proveedor={proveedor}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const FormularioProveedor = ({ proveedor, onClose, onSuccess, token, empresaId }) => {
  const [formData, setFormData] = useState({
    razon_social: proveedor?.razon_social || '',
    nombre_comercial: proveedor?.nombre_comercial || '',
    rfc: proveedor?.rfc || '',
    regimen_fiscal: proveedor?.regimen_fiscal || '',
    tipo_persona: proveedor?.tipo_persona || 'moral',
    tipo_proveedor: proveedor?.tipo_proveedor || 'OTRO',
    fecha_constitucion: proveedor?.fecha_constitucion || '',
    sitio_web: proveedor?.sitio_web || '',
    requiere_repse: proveedor?.requiere_repse || false,
    tiene_personal_en_sitio: proveedor?.tiene_personal_en_sitio || false,
    descripcion_servicios_ofrecidos: proveedor?.descripcion_servicios_ofrecidos || '',
    contacto_nombre: proveedor?.contacto_principal?.nombre_completo || '',
    contacto_email: proveedor?.contacto_principal?.email || '',
    contacto_telefono: proveedor?.contacto_principal?.telefono || '',
    contacto_puesto: proveedor?.contacto_principal?.puesto || '',
    calle: proveedor?.domicilio_fiscal?.calle || '',
    colonia: proveedor?.domicilio_fiscal?.colonia || '',
    municipio: proveedor?.domicilio_fiscal?.municipio || '',
    estado: proveedor?.domicilio_fiscal?.estado || '',
    codigo_postal: proveedor?.domicilio_fiscal?.codigo_postal || ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [paso, setPaso] = useState(1);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        razon_social: formData.razon_social,
        nombre_comercial: formData.nombre_comercial || null,
        rfc: formData.rfc.toUpperCase(),
        regimen_fiscal: formData.regimen_fiscal,
        tipo_persona: formData.tipo_persona,
        tipo_proveedor: formData.tipo_proveedor,
        fecha_constitucion: formData.fecha_constitucion || null,
        sitio_web: formData.sitio_web || null,
        requiere_repse: formData.requiere_repse,
        tiene_personal_en_sitio: formData.tiene_personal_en_sitio,
        descripcion_servicios_ofrecidos: formData.descripcion_servicios_ofrecidos || null,
        contacto_principal: formData.contacto_nombre ? {
          nombre_completo: formData.contacto_nombre,
          email: formData.contacto_email,
          telefono: formData.contacto_telefono,
          puesto: formData.contacto_puesto || null
        } : null,
        domicilio_fiscal: formData.calle ? {
          calle: formData.calle,
          colonia: formData.colonia,
          municipio: formData.municipio,
          estado: formData.estado,
          codigo_postal: formData.codigo_postal
        } : null
      };

      const url = proveedor ? `/api/proveedores/${proveedor.id}` : '/api/proveedores';
      const method = proveedor ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'X-Empresa-ID': empresaId
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error guardando proveedor');
      }

      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const tiposProveedor = [
    { value: 'CONSULTORIA_MACRO', label: 'Consultoría Macro (proyectos >$5M)' },
    { value: 'CONSULTORIA_ESTRATEGICA', label: 'Consultoría Estratégica' },
    { value: 'SOFTWARE_SAAS', label: 'Software / SaaS' },
    { value: 'MARKETING_BRANDING', label: 'Marketing / Branding' },
    { value: 'INTRAGRUPO', label: 'Servicios Intragrupo' },
    { value: 'SERVICIOS_ESPECIALIZADOS', label: 'Servicios Especializados' },
    { value: 'OUTSOURCING_PERMITIDO', label: 'Outsourcing Permitido' },
    { value: 'OTRO', label: 'Otro' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-3xl">
        <div className="bg-white rounded-lg shadow-lg">
          <div className="border-b border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">
                {proveedor ? 'Editar Proveedor' : 'Nuevo Proveedor'}
              </h2>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex items-center gap-4 mt-4">
              {[1, 2, 3].map((num) => (
                <div key={num} className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    paso >= num ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {num}
                  </div>
                  <span className={`ml-2 text-sm ${paso >= num ? 'text-gray-900' : 'text-gray-500'}`}>
                    {num === 1 ? 'Datos Generales' : num === 2 ? 'Contacto' : 'Domicilio'}
                  </span>
                  {num < 3 && <div className={`w-8 h-0.5 mx-2 ${paso > num ? 'bg-blue-600' : 'bg-gray-200'}`} />}
                </div>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="p-6 space-y-6">
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                  {error}
                </div>
              )}

              {paso === 1 && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Razón Social <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={formData.razon_social}
                        onChange={(e) => setFormData({ ...formData, razon_social: e.target.value })}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Comercial</label>
                      <input
                        type="text"
                        value={formData.nombre_comercial}
                        onChange={(e) => setFormData({ ...formData, nombre_comercial: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        RFC <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={formData.rfc}
                        onChange={(e) => setFormData({ ...formData, rfc: e.target.value.toUpperCase() })}
                        required
                        maxLength={13}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Régimen Fiscal <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={formData.regimen_fiscal}
                        onChange={(e) => setFormData({ ...formData, regimen_fiscal: e.target.value })}
                        required
                        placeholder="Ej: Régimen General de Ley Personas Morales"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Persona</label>
                      <select
                        value={formData.tipo_persona}
                        onChange={(e) => setFormData({ ...formData, tipo_persona: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="moral">Persona Moral</option>
                        <option value="fisica">Persona Física</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Proveedor</label>
                      <select
                        value={formData.tipo_proveedor}
                        onChange={(e) => setFormData({ ...formData, tipo_proveedor: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        {tiposProveedor.map(tipo => (
                          <option key={tipo.value} value={tipo.value}>{tipo.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Fecha de Constitución</label>
                      <input
                        type="date"
                        value={formData.fecha_constitucion}
                        onChange={(e) => setFormData({ ...formData, fecha_constitucion: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Sitio Web</label>
                      <input
                        type="url"
                        value={formData.sitio_web}
                        onChange={(e) => setFormData({ ...formData, sitio_web: e.target.value })}
                        placeholder="https://..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Descripción de Servicios</label>
                    <textarea
                      value={formData.descripcion_servicios_ofrecidos}
                      onChange={(e) => setFormData({ ...formData, descripcion_servicios_ofrecidos: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Describe brevemente los servicios que ofrece este proveedor..."
                    />
                  </div>

                  <div className="flex items-center gap-6">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.requiere_repse}
                        onChange={(e) => setFormData({ ...formData, requiere_repse: e.target.checked })}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">Requiere REPSE</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.tiene_personal_en_sitio}
                        onChange={(e) => setFormData({ ...formData, tiene_personal_en_sitio: e.target.checked })}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">Personal en sitio</span>
                    </label>
                  </div>
                </>
              )}

              {paso === 2 && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Nombre del Contacto</label>
                      <input
                        type="text"
                        value={formData.contacto_nombre}
                        onChange={(e) => setFormData({ ...formData, contacto_nombre: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Puesto</label>
                      <input
                        type="text"
                        value={formData.contacto_puesto}
                        onChange={(e) => setFormData({ ...formData, contacto_puesto: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <input
                        type="email"
                        value={formData.contacto_email}
                        onChange={(e) => setFormData({ ...formData, contacto_email: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
                      <input
                        type="tel"
                        value={formData.contacto_telefono}
                        onChange={(e) => setFormData({ ...formData, contacto_telefono: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </>
              )}

              {paso === 3 && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Calle y Número</label>
                    <input
                      type="text"
                      value={formData.calle}
                      onChange={(e) => setFormData({ ...formData, calle: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Colonia</label>
                      <input
                        type="text"
                        value={formData.colonia}
                        onChange={(e) => setFormData({ ...formData, colonia: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Código Postal</label>
                      <input
                        type="text"
                        value={formData.codigo_postal}
                        onChange={(e) => setFormData({ ...formData, codigo_postal: e.target.value })}
                        maxLength={5}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Municipio/Alcaldía</label>
                      <input
                        type="text"
                        value={formData.municipio}
                        onChange={(e) => setFormData({ ...formData, municipio: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                      <input
                        type="text"
                        value={formData.estado}
                        onChange={(e) => setFormData({ ...formData, estado: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="border-t border-gray-200 p-6 flex items-center justify-between">
              <div>
                {paso > 1 && (
                  <button
                    type="button"
                    onClick={() => setPaso(paso - 1)}
                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Anterior
                  </button>
                )}
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                {paso < 3 ? (
                  <button
                    type="button"
                    onClick={() => setPaso(paso + 1)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Siguiente
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    {loading && <div className="w-4 h-4 border-2 border-white/30 rounded-full animate-spin border-t-white"></div>}
                    {proveedor ? 'Actualizar' : 'Crear Proveedor'}
                  </button>
                )}
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

const DetalleProveedor = ({ proveedor, onBack, token, empresaId, onUpdate }) => {
  const [activeTab, setActiveTab] = useState('general');
  const [creandoCarpeta, setCreandoCarpeta] = useState(false);

  const crearCarpetaPCloud = async () => {
    setCreandoCarpeta(true);
    try {
      const response = await fetch(`/api/proveedores/${proveedor.id}/pcloud/crear-carpeta`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Empresa-ID': empresaId
        }
      });

      if (response.ok) {
        alert('Carpeta creada exitosamente en pCloud');
        onUpdate();
      } else {
        const error = await response.json();
        alert('Error: ' + error.detail);
      }
    } catch (err) {
      alert('Error creando carpeta: ' + err.message);
    } finally {
      setCreandoCarpeta(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Volver a Proveedores
        </button>

        <div className="bg-white rounded-lg shadow-lg">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {proveedor.nombre_comercial || proveedor.razon_social}
                </h1>
                <p className="text-gray-600">{proveedor.razon_social}</p>
                <p className="text-sm text-gray-500 font-mono mt-1">RFC: {proveedor.rfc}</p>
              </div>
              <div className="flex gap-2">
                {!proveedor.pcloud_folder_id && (
                  <button
                    onClick={crearCarpetaPCloud}
                    disabled={creandoCarpeta}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    {creandoCarpeta ? (
                      <div className="w-4 h-4 border-2 border-white/30 rounded-full animate-spin border-t-white"></div>
                    ) : (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    )}
                    Crear Carpeta pCloud
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {[
                { id: 'general', label: 'Información General' },
                { id: 'documentos', label: 'Documentos' },
                { id: 'riesgo', label: 'Evaluación de Riesgo' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-6 py-3 text-sm font-medium border-b-2 ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'general' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Datos Fiscales</h3>
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm text-gray-500">Régimen Fiscal</dt>
                      <dd className="text-gray-900">{proveedor.regimen_fiscal || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Tipo de Persona</dt>
                      <dd className="text-gray-900 capitalize">{proveedor.tipo_persona}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Fecha de Constitución</dt>
                      <dd className="text-gray-900">{proveedor.fecha_constitucion || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-gray-500">Tipo de Proveedor</dt>
                      <dd className="text-gray-900">{proveedor.tipo_proveedor}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Contacto</h3>
                  {proveedor.contacto_principal ? (
                    <dl className="space-y-3">
                      <div>
                        <dt className="text-sm text-gray-500">Nombre</dt>
                        <dd className="text-gray-900">{proveedor.contacto_principal.nombre_completo}</dd>
                      </div>
                      <div>
                        <dt className="text-sm text-gray-500">Email</dt>
                        <dd className="text-gray-900">{proveedor.contacto_principal.email}</dd>
                      </div>
                      <div>
                        <dt className="text-sm text-gray-500">Teléfono</dt>
                        <dd className="text-gray-900">{proveedor.contacto_principal.telefono}</dd>
                      </div>
                    </dl>
                  ) : (
                    <p className="text-gray-500">Sin información de contacto</p>
                  )}
                </div>

                {proveedor.domicilio_fiscal && (
                  <div className="md:col-span-2">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Domicilio Fiscal</h3>
                    <p className="text-gray-900">
                      {proveedor.domicilio_fiscal.calle}, {proveedor.domicilio_fiscal.colonia}, 
                      {proveedor.domicilio_fiscal.municipio}, {proveedor.domicilio_fiscal.estado} 
                      CP {proveedor.domicilio_fiscal.codigo_postal}
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'documentos' && (
              <div className="space-y-6">
                {proveedor.pcloud_folder_id ? (
                  <>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                      <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <p className="font-medium text-green-800">Carpeta pCloud configurada</p>
                        <p className="text-sm text-green-600">{proveedor.pcloud_folder_path}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <DocumentUploadOCR
                        tipoDocumento="constancia_situacion_fiscal"
                        titulo="Constancia de Situación Fiscal"
                        descripcion="Documento emitido por el SAT con datos fiscales actualizados"
                        obligatorio={true}
                        empresaId={empresaId}
                        authToken={token}
                        onOCRComplete={() => {}}
                        onFileUploaded={() => {}}
                      />

                      <DocumentUploadOCR
                        tipoDocumento="opinion_cumplimiento"
                        titulo="Opinión de Cumplimiento (32-D)"
                        descripcion="Opinión positiva de obligaciones fiscales"
                        obligatorio={true}
                        empresaId={empresaId}
                        authToken={token}
                        onOCRComplete={() => {}}
                        onFileUploaded={() => {}}
                      />

                      <DocumentUploadOCR
                        tipoDocumento="acta_constitutiva"
                        titulo="Acta Constitutiva"
                        descripcion="Documento notarial de constitución de la empresa"
                        empresaId={empresaId}
                        authToken={token}
                        onOCRComplete={() => {}}
                        onFileUploaded={() => {}}
                      />

                      {proveedor.requiere_repse && (
                        <DocumentUploadOCR
                          tipoDocumento="repse"
                          titulo="REPSE"
                          descripcion="Registro de Prestadoras de Servicios Especializados"
                          obligatorio={true}
                          empresaId={empresaId}
                          authToken={token}
                          onOCRComplete={() => {}}
                          onFileUploaded={() => {}}
                        />
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-center py-12">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <h3 className="mt-4 text-lg font-medium text-gray-900">Configura el almacenamiento</h3>
                    <p className="mt-2 text-gray-500">Primero debes crear la carpeta en pCloud para subir documentos.</p>
                    <button
                      onClick={crearCarpetaPCloud}
                      disabled={creandoCarpeta}
                      className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                    >
                      Crear Carpeta pCloud
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'riesgo' && (
              <div>
                <RiesgoIndicador riesgo={proveedor.riesgo} mostrarDetalles={true} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProveedoresPage;
