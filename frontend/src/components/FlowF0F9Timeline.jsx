import React, { useState } from 'react';

/**
 * FlowF0F9Timeline - Componente visual del flujo de fases F0-F9 de Revisar-IA
 * Muestra el progreso de un proyecto a través de las 10 fases del sistema
 */

const fasesConfig = [
  {
    id: 'F0',
    nombre: 'Identificación de Necesidad',
    descripcion: 'Surge la necesidad de contratar un servicio',
    agentes: ['A1'],
    documentos: ['SIB (Service Initiation Brief)'],
    candado: false,
    pilar: 'razon_negocios',
    color: 'blue'
  },
  {
    id: 'F1',
    nombre: 'Registro Inicial',
    descripcion: 'Se registra el proyecto en el sistema con datos básicos',
    agentes: ['A2'],
    documentos: ['Datos del proyecto', 'Tipología asignada'],
    candado: false,
    pilar: 'trazabilidad',
    color: 'blue'
  },
  {
    id: 'F2',
    nombre: 'Evaluación Estratégica',
    descripcion: 'Análisis de razón de negocios y BEE',
    agentes: ['A1', 'A3'],
    documentos: ['Matriz BEE', 'Análisis razón de negocios'],
    candado: true,
    pilar: 'razon_negocios',
    color: 'indigo'
  },
  {
    id: 'F3',
    nombre: 'Due Diligence Proveedor',
    descripcion: 'Verificación del proveedor (RFC, 69-B, 32-D)',
    agentes: ['A6'],
    documentos: ['Score proveedor', 'Consulta 69-B', 'Opinión 32-D'],
    candado: false,
    pilar: 'materialidad',
    color: 'purple'
  },
  {
    id: 'F4',
    nombre: 'Elaboración de Contrato/SOW',
    descripcion: 'Redacción del alcance y términos contractuales',
    agentes: ['A4', 'A1'],
    documentos: ['SOW', 'Contrato firmado'],
    candado: false,
    pilar: 'trazabilidad',
    color: 'violet'
  },
  {
    id: 'F5',
    nombre: 'Validación Fiscal',
    descripcion: 'Verificación de cumplimiento de 4 pilares fiscales',
    agentes: ['A3', 'A5'],
    documentos: ['VBC Fiscal', 'Análisis deducibilidad'],
    candado: false,
    pilar: 'materialidad',
    color: 'pink'
  },
  {
    id: 'F6',
    nombre: 'Ejecución y Seguimiento',
    descripcion: 'Monitoreo de la prestación del servicio',
    agentes: ['A2', 'A6'],
    documentos: ['Minutas', 'Evidencia de ejecución'],
    candado: true,
    pilar: 'materialidad',
    color: 'rose'
  },
  {
    id: 'F7',
    nombre: 'Recepción de Entregables',
    descripcion: 'Validación técnica de lo recibido',
    agentes: ['A6', 'A2'],
    documentos: ['Acta de Aceptación Técnica', 'Entregables'],
    candado: false,
    pilar: 'materialidad',
    color: 'orange'
  },
  {
    id: 'F8',
    nombre: 'Three-Way Match',
    descripcion: 'Validación Contrato = CFDI = Pago',
    agentes: ['A5', 'A3'],
    documentos: ['Validación 3-Way', 'CFDI verificado'],
    candado: true,
    pilar: 'trazabilidad',
    color: 'amber'
  },
  {
    id: 'F9',
    nombre: 'Cierre y Defense File',
    descripcion: 'Integración del expediente de defensa fiscal',
    agentes: ['A7'],
    documentos: ['Defense File completo', 'Índice de defendibilidad'],
    candado: false,
    pilar: 'defensa',
    color: 'green'
  }
];

const pilarColors = {
  razon_negocios: 'bg-blue-100 text-blue-800 border-blue-300',
  materialidad: 'bg-purple-100 text-purple-800 border-purple-300',
  trazabilidad: 'bg-amber-100 text-amber-800 border-amber-300',
  defensa: 'bg-green-100 text-green-800 border-green-300'
};

const pilarLabels = {
  razon_negocios: 'Razón de Negocios',
  materialidad: 'Materialidad',
  trazabilidad: 'Trazabilidad',
  defensa: 'Defensa'
};

const FaseCard = ({ fase, estado, onClick, isExpanded }) => {
  const getEstadoStyles = () => {
    switch (estado) {
      case 'completado':
        return 'bg-green-50 border-green-500 ring-green-200';
      case 'actual':
        return 'bg-blue-50 border-blue-500 ring-blue-200 ring-2';
      case 'bloqueado':
        return 'bg-red-50 border-red-400 ring-red-200';
      case 'pendiente':
      default:
        return 'bg-gray-50 border-gray-300';
    }
  };

  const getEstadoIcon = () => {
    switch (estado) {
      case 'completado':
        return (
          <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'actual':
        return (
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center animate-pulse">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        );
      case 'bloqueado':
        return (
          <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
            <span className="text-gray-600 font-bold text-sm">{fase.id.replace('F', '')}</span>
          </div>
        );
    }
  };

  return (
    <div
      className={`relative border-2 rounded-xl p-4 cursor-pointer transition-all duration-200 hover:shadow-lg ${getEstadoStyles()}`}
      onClick={onClick}
    >
      {/* Candado indicator */}
      {fase.candado && (
        <div className="absolute -top-2 -right-2 bg-yellow-400 rounded-full p-1" title="Candado de Control">
          <svg className="w-4 h-4 text-yellow-800" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
      )}

      <div className="flex items-start gap-3">
        {getEstadoIcon()}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-gray-800">{fase.id}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${pilarColors[fase.pilar]}`}>
              {pilarLabels[fase.pilar]}
            </span>
          </div>
          <h3 className="font-semibold text-gray-900 text-sm">{fase.nombre}</h3>
          <p className="text-xs text-gray-600 mt-1">{fase.descripcion}</p>

          {isExpanded && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="mb-2">
                <span className="text-xs font-medium text-gray-500">Agentes involucrados:</span>
                <div className="flex gap-1 mt-1">
                  {fase.agentes.map(a => (
                    <span key={a} className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                      {a}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <span className="text-xs font-medium text-gray-500">Documentos:</span>
                <ul className="mt-1 space-y-1">
                  {fase.documentos.map((doc, i) => (
                    <li key={i} className="text-xs text-gray-600 flex items-center gap-1">
                      <svg className="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {doc}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const FlowF0F9Timeline = ({
  faseActual = 'F0',
  fasesCompletadas = [],
  fasesBloqueadas = [],
  onFaseClick,
  modo = 'horizontal', // 'horizontal' | 'vertical' | 'grid'
  showDetails = true
}) => {
  const [expandedFase, setExpandedFase] = useState(null);

  const getEstadoFase = (faseId) => {
    if (fasesBloqueadas.includes(faseId)) return 'bloqueado';
    if (fasesCompletadas.includes(faseId)) return 'completado';
    if (faseId === faseActual) return 'actual';
    return 'pendiente';
  };

  const handleFaseClick = (fase) => {
    setExpandedFase(expandedFase === fase.id ? null : fase.id);
    if (onFaseClick) onFaseClick(fase);
  };

  const renderConector = (index) => {
    if (modo === 'grid') return null;

    const isVertical = modo === 'vertical';
    const fase = fasesConfig[index];
    const nextFase = fasesConfig[index + 1];

    if (!nextFase) return null;

    const currentCompleted = fasesCompletadas.includes(fase.id) || fase.id === faseActual;

    return (
      <div className={`flex ${isVertical ? 'justify-center h-8' : 'items-center w-8'}`}>
        <div className={`
          ${isVertical ? 'h-full w-1' : 'w-full h-1'}
          ${currentCompleted ? 'bg-green-400' : 'bg-gray-300'}
          ${nextFase.candado ? 'border-dashed border-2 border-yellow-500 bg-transparent' : ''}
        `} />
      </div>
    );
  };

  // Render según modo
  if (modo === 'grid') {
    return (
      <div className="w-full">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {fasesConfig.map((fase, index) => (
            <FaseCard
              key={fase.id}
              fase={fase}
              estado={getEstadoFase(fase.id)}
              onClick={() => handleFaseClick(fase)}
              isExpanded={showDetails && expandedFase === fase.id}
            />
          ))}
        </div>

        {/* Leyenda */}
        <div className="mt-6 flex flex-wrap gap-4 justify-center text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500" />
            <span>Completado</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-500 animate-pulse" />
            <span>En proceso</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gray-300" />
            <span>Pendiente</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500" />
            <span>Bloqueado</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-yellow-400 flex items-center justify-center">
              <svg className="w-3 h-3 text-yellow-800" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <span>Candado de control</span>
          </div>
        </div>
      </div>
    );
  }

  if (modo === 'vertical') {
    return (
      <div className="w-full max-w-md mx-auto">
        {fasesConfig.map((fase, index) => (
          <React.Fragment key={fase.id}>
            <FaseCard
              fase={fase}
              estado={getEstadoFase(fase.id)}
              onClick={() => handleFaseClick(fase)}
              isExpanded={showDetails && expandedFase === fase.id}
            />
            {renderConector(index)}
          </React.Fragment>
        ))}
      </div>
    );
  }

  // Modo horizontal (default)
  return (
    <div className="w-full overflow-x-auto">
      <div className="flex items-start gap-2 min-w-max pb-4">
        {fasesConfig.map((fase, index) => (
          <React.Fragment key={fase.id}>
            <div className="w-48 flex-shrink-0">
              <FaseCard
                fase={fase}
                estado={getEstadoFase(fase.id)}
                onClick={() => handleFaseClick(fase)}
                isExpanded={showDetails && expandedFase === fase.id}
              />
            </div>
            {renderConector(index)}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

// Componente de resumen de progreso
export const FlowProgressSummary = ({ fasesCompletadas = [], faseActual, fasesBloqueadas = [] }) => {
  const totalFases = fasesConfig.length;
  const completadas = fasesCompletadas.length;
  const porcentaje = Math.round((completadas / totalFases) * 100);

  const candadosSuperados = fasesConfig
    .filter(f => f.candado && fasesCompletadas.includes(f.id))
    .length;
  const totalCandados = fasesConfig.filter(f => f.candado).length;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-800">Progreso del Flujo</h3>
        <span className="text-2xl font-bold text-blue-600">{porcentaje}%</span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
        <div
          className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500"
          style={{ width: `${porcentaje}%` }}
        />
      </div>

      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-green-600">{completadas}</div>
          <div className="text-xs text-gray-500">Fases completadas</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-blue-600">{faseActual || '-'}</div>
          <div className="text-xs text-gray-500">Fase actual</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-yellow-600">{candadosSuperados}/{totalCandados}</div>
          <div className="text-xs text-gray-500">Candados</div>
        </div>
      </div>
    </div>
  );
};

// Exportar configuración de fases para uso en otros componentes
export const FASES_CONFIG = fasesConfig;
export const PILAR_COLORS = pilarColors;
export const PILAR_LABELS = pilarLabels;

export default FlowF0F9Timeline;
