import React from 'react';

const ProveedorCard = ({ proveedor, onEdit, onView, onDelete }) => {
  const getEstatusConfig = (estatus) => {
    switch (estatus) {
      case 'activo': return { bg: 'bg-green-100', text: 'text-green-800', label: 'Activo' };
      case 'inactivo': return { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Inactivo' };
      case 'bloqueado': return { bg: 'bg-red-100', text: 'text-red-800', label: 'Bloqueado' };
      case 'pendiente_revision': return { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pendiente' };
      default: return { bg: 'bg-gray-100', text: 'text-gray-800', label: estatus };
    }
  };

  const getRiesgoConfig = (nivel) => {
    switch (nivel) {
      case 'bajo': return { bg: 'bg-green-500', label: 'Bajo' };
      case 'medio': return { bg: 'bg-yellow-500', label: 'Medio' };
      case 'alto': return { bg: 'bg-orange-500', label: 'Alto' };
      case 'critico': return { bg: 'bg-red-500', label: 'Crítico' };
      default: return { bg: 'bg-gray-500', label: '-' };
    }
  };

  const getTipoProveedorLabel = (tipo) => {
    const labels = {
      'CONSULTORIA_MACRO': 'Consultoría Macro',
      'CONSULTORIA_ESTRATEGICA': 'Consultoría Estratégica',
      'SOFTWARE_SAAS': 'Software/SaaS',
      'MARKETING_BRANDING': 'Marketing/Branding',
      'INTRAGRUPO': 'Intragrupo',
      'SERVICIOS_ESPECIALIZADOS': 'Servicios Especializados',
      'OUTSOURCING_PERMITIDO': 'Outsourcing Permitido',
      'OTRO': 'Otro'
    };
    return labels[tipo] || tipo;
  };

  const estatusConfig = getEstatusConfig(proveedor.estatus);
  const riesgoConfig = getRiesgoConfig(proveedor.riesgo?.nivel_riesgo);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {proveedor.nombre_comercial || proveedor.razon_social}
            </h3>
            <p className="text-sm text-gray-500 truncate">
              {proveedor.razon_social}
            </p>
          </div>
          <div className="flex items-center gap-2 ml-2">
            <span className={`px-2 py-1 text-xs rounded-full ${estatusConfig.bg} ${estatusConfig.text}`}>
              {estatusConfig.label}
            </span>
          </div>
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">RFC:</span>
            <span className="font-mono text-gray-900">{proveedor.rfc}</span>
          </div>
          
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">Tipo:</span>
            <span className="text-gray-900">{getTipoProveedorLabel(proveedor.tipo_proveedor)}</span>
          </div>

          {proveedor.contacto_principal?.email && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">Contacto:</span>
              <span className="text-gray-900 truncate">{proveedor.contacto_principal.email}</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between mb-4 p-2 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${riesgoConfig.bg}`}></div>
            <span className="text-sm text-gray-700">
              Riesgo: <span className="font-medium">{riesgoConfig.label}</span>
            </span>
          </div>
          <div className="text-sm text-gray-600">
            Materialidad: <span className="font-medium">{Math.round(proveedor.riesgo?.score_materialidad_potencial || 0)}%</span>
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex gap-2">
            {proveedor.requiere_repse && (
              <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">REPSE</span>
            )}
            {proveedor.tipo_persona === 'fisica' && (
              <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">P. Física</span>
            )}
          </div>
          
          <div className="flex gap-1">
            <button
              onClick={() => onView && onView(proveedor)}
              className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="Ver detalles"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
            <button
              onClick={() => onEdit && onEdit(proveedor)}
              className="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
              title="Editar"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              onClick={() => onDelete && onDelete(proveedor)}
              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Eliminar"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProveedorCard;
