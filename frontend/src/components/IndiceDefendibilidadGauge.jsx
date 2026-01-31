import React from 'react';

/**
 * IndiceDefendibilidadGauge - Visualización del índice de defendibilidad fiscal
 * Muestra un gauge semicircular con el puntaje de riesgo (0-100)
 * Donde 0 = máxima defendibilidad, 100 = máximo riesgo
 */

const IndiceDefendibilidadGauge = ({
  valor = 0,
  size = 'medium', // 'small' | 'medium' | 'large'
  showDetails = true,
  pilares = null // { razon_negocios: 0-25, bee: 0-25, materialidad: 0-25, trazabilidad: 0-25 }
}) => {
  // Clamp value between 0 and 100
  const valorClamped = Math.max(0, Math.min(100, valor));

  // Calculate color based on value (inverted - lower is better)
  const getColor = (val) => {
    if (val <= 20) return { color: '#22c55e', label: 'Excelente', bg: 'bg-green-50', text: 'text-green-700' };
    if (val <= 40) return { color: '#84cc16', label: 'Bueno', bg: 'bg-lime-50', text: 'text-lime-700' };
    if (val <= 60) return { color: '#eab308', label: 'Moderado', bg: 'bg-yellow-50', text: 'text-yellow-700' };
    if (val <= 80) return { color: '#f97316', label: 'Alto Riesgo', bg: 'bg-orange-50', text: 'text-orange-700' };
    return { color: '#ef4444', label: 'Crítico', bg: 'bg-red-50', text: 'text-red-700' };
  };

  const colorInfo = getColor(valorClamped);

  // SVG dimensions based on size
  const dimensions = {
    small: { width: 120, height: 80, strokeWidth: 8, fontSize: 20 },
    medium: { width: 180, height: 110, strokeWidth: 12, fontSize: 28 },
    large: { width: 240, height: 140, strokeWidth: 16, fontSize: 36 }
  };

  const dim = dimensions[size] || dimensions.medium;
  const radius = (dim.width - dim.strokeWidth) / 2;
  const circumference = Math.PI * radius;
  const progress = (valorClamped / 100) * circumference;

  // Pilar colors
  const pilarConfig = {
    razon_negocios: { label: 'Razón de Negocios', color: 'bg-blue-500' },
    bee: { label: 'Beneficio Económico', color: 'bg-indigo-500' },
    materialidad: { label: 'Materialidad', color: 'bg-purple-500' },
    trazabilidad: { label: 'Trazabilidad', color: 'bg-amber-500' }
  };

  return (
    <div className={`${colorInfo.bg} rounded-xl p-4 inline-block`}>
      {/* Gauge SVG */}
      <div className="flex flex-col items-center">
        <svg
          width={dim.width}
          height={dim.height}
          viewBox={`0 0 ${dim.width} ${dim.height}`}
        >
          {/* Background arc */}
          <path
            d={`M ${dim.strokeWidth / 2} ${dim.height - 10}
                A ${radius} ${radius} 0 0 1 ${dim.width - dim.strokeWidth / 2} ${dim.height - 10}`}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={dim.strokeWidth}
            strokeLinecap="round"
          />

          {/* Progress arc */}
          <path
            d={`M ${dim.strokeWidth / 2} ${dim.height - 10}
                A ${radius} ${radius} 0 0 1 ${dim.width - dim.strokeWidth / 2} ${dim.height - 10}`}
            fill="none"
            stroke={colorInfo.color}
            strokeWidth={dim.strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            style={{ transition: 'stroke-dashoffset 0.5s ease-in-out' }}
          />

          {/* Center text */}
          <text
            x={dim.width / 2}
            y={dim.height - 25}
            textAnchor="middle"
            fill={colorInfo.color}
            fontSize={dim.fontSize}
            fontWeight="bold"
          >
            {valorClamped}
          </text>
          <text
            x={dim.width / 2}
            y={dim.height - 5}
            textAnchor="middle"
            fill="#6b7280"
            fontSize={dim.fontSize * 0.4}
          >
            /100
          </text>
        </svg>

        {/* Label */}
        <div className={`mt-2 px-3 py-1 rounded-full ${colorInfo.text} ${colorInfo.bg} border border-current font-semibold text-sm`}>
          {colorInfo.label}
        </div>

        {/* Inversión explicativa */}
        <p className="text-xs text-gray-500 mt-2 text-center">
          {valorClamped <= 40 ? '✓ Alta defendibilidad' : '⚠ Requiere atención'}
        </p>
      </div>

      {/* Desglose por pilar */}
      {showDetails && pilares && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-xs font-semibold text-gray-500 mb-2 uppercase">Desglose por Pilar</h4>
          <div className="space-y-2">
            {Object.entries(pilares).map(([key, value]) => {
              const config = pilarConfig[key];
              if (!config) return null;

              const percentage = (value / 25) * 100;

              return (
                <div key={key} className="flex items-center gap-2">
                  <div className="flex-1">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600">{config.label}</span>
                      <span className="font-medium">{value}/25</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`${config.color} h-2 rounded-full transition-all duration-300`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * DefendibilidadCompact - Versión compacta del indicador
 */
export const DefendibilidadCompact = ({ valor = 0, className = '' }) => {
  const getColorClass = (val) => {
    if (val <= 20) return 'bg-green-500';
    if (val <= 40) return 'bg-lime-500';
    if (val <= 60) return 'bg-yellow-500';
    if (val <= 80) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getLabel = (val) => {
    if (val <= 20) return 'Excelente';
    if (val <= 40) return 'Bueno';
    if (val <= 60) return 'Moderado';
    if (val <= 80) return 'Alto';
    return 'Crítico';
  };

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <div className={`w-3 h-3 rounded-full ${getColorClass(valor)}`} />
      <span className="text-sm font-medium text-gray-700">{valor}/100</span>
      <span className="text-xs text-gray-500">({getLabel(valor)})</span>
    </div>
  );
};

/**
 * DefendibilidadBadge - Badge para mostrar en listas y tarjetas
 */
export const DefendibilidadBadge = ({ valor = 0, showLabel = true }) => {
  const getStyles = (val) => {
    if (val <= 20) return 'bg-green-100 text-green-800 border-green-300';
    if (val <= 40) return 'bg-lime-100 text-lime-800 border-lime-300';
    if (val <= 60) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    if (val <= 80) return 'bg-orange-100 text-orange-800 border-orange-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  const getLabel = (val) => {
    if (val <= 20) return 'Excelente';
    if (val <= 40) return 'Bueno';
    if (val <= 60) return 'Moderado';
    if (val <= 80) return 'Alto';
    return 'Crítico';
  };

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${getStyles(valor)}`}>
      <span className="font-bold">{valor}</span>
      {showLabel && <span className="text-xs opacity-75">• {getLabel(valor)}</span>}
    </span>
  );
};

/**
 * DefendibilidadTrend - Muestra la tendencia del índice
 */
export const DefendibilidadTrend = ({ valorActual, valorAnterior }) => {
  const diff = valorActual - valorAnterior;
  const isImproving = diff < 0; // Menor es mejor

  if (diff === 0) {
    return (
      <span className="inline-flex items-center text-gray-500 text-sm">
        <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
        </svg>
        Sin cambio
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center text-sm ${isImproving ? 'text-green-600' : 'text-red-600'}`}>
      {isImproving ? (
        <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      ) : (
        <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      )}
      {Math.abs(diff)} pts {isImproving ? 'mejor' : 'peor'}
    </span>
  );
};

export default IndiceDefendibilidadGauge;
