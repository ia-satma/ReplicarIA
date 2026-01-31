import React from 'react';

/**
 * PilaresFiscalesCard - Visualización de los 4 pilares fiscales del SAT
 * Muestra el estado de cumplimiento de cada pilar para un proyecto
 */

const pilaresConfig = [
  {
    id: 'razon_negocios',
    nombre: 'Razón de Negocios',
    articulo: 'Art. 5-A CFF',
    descripcion: 'El beneficio económico debe ser mayor al beneficio fiscal',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    color: 'blue',
    bgGradient: 'from-blue-50 to-blue-100',
    borderColor: 'border-blue-300',
    iconBg: 'bg-blue-500'
  },
  {
    id: 'beneficio_economico',
    nombre: 'Beneficio Económico',
    articulo: 'Art. 5-A CFF',
    descripcion: 'BEE cuantificable y documentado con KPIs medibles',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'indigo',
    bgGradient: 'from-indigo-50 to-indigo-100',
    borderColor: 'border-indigo-300',
    iconBg: 'bg-indigo-500'
  },
  {
    id: 'materialidad',
    nombre: 'Materialidad',
    articulo: 'Art. 69-B CFF',
    descripcion: 'Servicio efectivamente prestado con evidencia comprobable',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    color: 'purple',
    bgGradient: 'from-purple-50 to-purple-100',
    borderColor: 'border-purple-300',
    iconBg: 'bg-purple-500'
  },
  {
    id: 'trazabilidad',
    nombre: 'Trazabilidad',
    articulo: 'NOM-151',
    descripcion: 'Documentos con fecha cierta y cadena de custodia',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
    color: 'amber',
    bgGradient: 'from-amber-50 to-amber-100',
    borderColor: 'border-amber-300',
    iconBg: 'bg-amber-500'
  }
];

const getEstadoStyles = (estado) => {
  switch (estado) {
    case 'conforme':
      return {
        badge: 'bg-green-100 text-green-800',
        icon: (
          <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ),
        label: 'Conforme'
      };
    case 'condicionado':
      return {
        badge: 'bg-yellow-100 text-yellow-800',
        icon: (
          <svg className="w-5 h-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        ),
        label: 'Condicionado'
      };
    case 'no_conforme':
      return {
        badge: 'bg-red-100 text-red-800',
        icon: (
          <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ),
        label: 'No Conforme'
      };
    case 'pendiente':
    default:
      return {
        badge: 'bg-gray-100 text-gray-600',
        icon: (
          <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
        label: 'Pendiente'
      };
  }
};

const PilarCard = ({ pilar, estado = 'pendiente', puntos = null, detalles = null, onClick }) => {
  const estadoStyles = getEstadoStyles(estado);

  return (
    <div
      className={`relative bg-gradient-to-br ${pilar.bgGradient} border-2 ${pilar.borderColor} rounded-xl p-4 transition-all duration-200 hover:shadow-lg cursor-pointer`}
      onClick={onClick}
    >
      {/* Status badge */}
      <div className="absolute -top-2 -right-2">
        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${estadoStyles.badge}`}>
          {estadoStyles.icon}
          {estadoStyles.label}
        </span>
      </div>

      {/* Content */}
      <div className="flex items-start gap-3">
        <div className={`${pilar.iconBg} p-2 rounded-lg text-white`}>
          {pilar.icon}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-800">{pilar.nombre}</h3>
          <p className="text-xs text-gray-500 mt-1">{pilar.articulo}</p>
          <p className="text-sm text-gray-600 mt-2">{pilar.descripcion}</p>

          {/* Puntos de riesgo */}
          {puntos !== null && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Puntos de riesgo</span>
                <span className={`font-bold ${puntos <= 10 ? 'text-green-600' : puntos <= 18 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {puntos}/25
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div
                  className={`h-2 rounded-full ${puntos <= 10 ? 'bg-green-500' : puntos <= 18 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${(puntos / 25) * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Detalles adicionales */}
          {detalles && (
            <div className="mt-3">
              <ul className="text-xs text-gray-600 space-y-1">
                {detalles.map((d, i) => (
                  <li key={i} className="flex items-start gap-1">
                    <span className="text-gray-400">•</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const PilaresFiscalesCard = ({
  pilares = {}, // { razon_negocios: { estado, puntos, detalles }, ... }
  modo = 'grid', // 'grid' | 'horizontal' | 'vertical'
  onPilarClick
}) => {
  const renderPilares = () => {
    return pilaresConfig.map(pilar => {
      const datos = pilares[pilar.id] || {};
      return (
        <PilarCard
          key={pilar.id}
          pilar={pilar}
          estado={datos.estado || 'pendiente'}
          puntos={datos.puntos}
          detalles={datos.detalles}
          onClick={() => onPilarClick && onPilarClick(pilar)}
        />
      );
    });
  };

  const containerClass = {
    grid: 'grid grid-cols-1 md:grid-cols-2 gap-4',
    horizontal: 'flex flex-wrap gap-4',
    vertical: 'flex flex-col gap-4'
  };

  return (
    <div className={containerClass[modo] || containerClass.grid}>
      {renderPilares()}
    </div>
  );
};

/**
 * PilaresResumen - Resumen compacto de los 4 pilares
 */
export const PilaresResumen = ({ pilares = {} }) => {
  const getCount = (estado) => {
    return Object.values(pilares).filter(p => p?.estado === estado).length;
  };

  return (
    <div className="flex items-center gap-4 text-sm">
      <div className="flex items-center gap-1">
        <div className="w-3 h-3 rounded-full bg-green-500" />
        <span>{getCount('conforme')} conformes</span>
      </div>
      <div className="flex items-center gap-1">
        <div className="w-3 h-3 rounded-full bg-yellow-500" />
        <span>{getCount('condicionado')} condicionados</span>
      </div>
      <div className="flex items-center gap-1">
        <div className="w-3 h-3 rounded-full bg-red-500" />
        <span>{getCount('no_conforme')} no conformes</span>
      </div>
      <div className="flex items-center gap-1">
        <div className="w-3 h-3 rounded-full bg-gray-300" />
        <span>{getCount('pendiente')} pendientes</span>
      </div>
    </div>
  );
};

/**
 * PilarBadge - Badge individual de pilar
 */
export const PilarBadge = ({ pilarId, estado }) => {
  const pilar = pilaresConfig.find(p => p.id === pilarId);
  if (!pilar) return null;

  const estadoStyles = getEstadoStyles(estado);

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium bg-${pilar.color}-50 text-${pilar.color}-700 border border-${pilar.color}-200`}>
      <span className={`w-2 h-2 rounded-full ${estadoStyles.badge.split(' ')[0]}`} />
      {pilar.nombre}
    </span>
  );
};

// Exportar configuración
export const PILARES_CONFIG = pilaresConfig;

export default PilaresFiscalesCard;
