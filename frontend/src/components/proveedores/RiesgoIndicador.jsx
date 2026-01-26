import React from 'react';

const RiesgoIndicador = ({ riesgo, mostrarDetalles = true }) => {
  if (!riesgo) {
    return (
      <div className="rounded-lg p-4 bg-gray-100">
        <p className="text-gray-500 text-sm">Sin evaluación de riesgo</p>
      </div>
    );
  }

  const getColorNivel = (nivel) => {
    switch (nivel) {
      case 'bajo': return { bg: 'bg-green-100', text: 'text-green-800', bar: 'bg-green-500' };
      case 'medio': return { bg: 'bg-yellow-100', text: 'text-yellow-800', bar: 'bg-yellow-500' };
      case 'alto': return { bg: 'bg-orange-100', text: 'text-orange-800', bar: 'bg-orange-500' };
      case 'critico': return { bg: 'bg-red-100', text: 'text-red-800', bar: 'bg-red-500' };
      default: return { bg: 'bg-gray-100', text: 'text-gray-800', bar: 'bg-gray-500' };
    }
  };

  const formatearFlag = (flag) => {
    const mapeo = {
      proveedor_reciente: 'Proveedor reciente (< 12 meses)',
      proveedor_muy_reciente: 'Proveedor muy reciente (< 6 meses)',
      capital_vs_montos_incongruente: 'Capital social incongruente con montos',
      sin_opinion_cumplimiento: 'Sin opinión de cumplimiento',
      opinion_negativa: 'Opinión de cumplimiento negativa',
      sin_repse_si_aplica: 'REPSE requerido pero no presentado',
      repse_vencido: 'REPSE vencido',
      domicilio_alto_riesgo: 'Domicilio de alto riesgo',
      rfc_en_lista_69b: 'RFC en lista 69-B del SAT',
      rfc_en_lista_efos: 'RFC en lista EFOS',
      objeto_social_incongruente: 'Objeto social no coincide con servicios',
      regimen_fiscal_incongruente: 'Régimen fiscal incongruente',
      sin_presencia_digital: 'Sin presencia digital verificable',
      email_no_coincide_con_dominio: 'Email no coincide con dominio web'
    };
    return mapeo[flag] || flag.replace(/_/g, ' ');
  };

  const config = getColorNivel(riesgo.nivel_riesgo);

  const flagsActivos = riesgo.flags 
    ? Object.entries(riesgo.flags)
        .filter(([key, value]) => value === true && !['revisado_manualmente', 'aprobado_con_excepcion'].includes(key))
        .map(([key]) => key)
    : [];

  const IconoNivel = () => {
    switch (riesgo.nivel_riesgo) {
      case 'bajo':
        return (
          <svg className={`h-8 w-8 ${config.text}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'medio':
        return (
          <svg className={`h-8 w-8 ${config.text}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'alto':
        return (
          <svg className={`h-8 w-8 ${config.text}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      case 'critico':
        return (
          <svg className={`h-8 w-8 ${config.text}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const ScoreBar = ({ label, score }) => {
    const getColor = (s) => {
      if (s >= 70) return 'bg-red-500';
      if (s >= 40) return 'bg-orange-500';
      if (s >= 20) return 'bg-yellow-500';
      return 'bg-green-500';
    };

    return (
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-600 w-16">{label}</span>
        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className={`h-full ${getColor(score)} transition-all duration-500`}
            style={{ width: `${score}%` }}
          />
        </div>
        <span className="text-xs font-medium text-gray-700 w-8 text-right">
          {Math.round(score)}
        </span>
      </div>
    );
  };

  return (
    <div className={`rounded-lg p-4 ${config.bg}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <IconoNivel />
          <div>
            <p className={`text-lg font-semibold ${config.text} capitalize`}>
              Riesgo {riesgo.nivel_riesgo}
            </p>
            <p className="text-sm text-gray-600">
              Score general: {Math.round(riesgo.score_general)}/100
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <p className="text-xs text-gray-500">Materialidad potencial</p>
          <p className={`text-lg font-bold ${
            riesgo.score_materialidad_potencial >= 70 ? 'text-green-600' :
            riesgo.score_materialidad_potencial >= 40 ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {Math.round(riesgo.score_materialidad_potencial)}%
          </p>
        </div>
      </div>

      {mostrarDetalles && (
        <>
          <div className="space-y-2 mb-4">
            <ScoreBar label="Fiscal" score={riesgo.score_fiscal || 0} />
            <ScoreBar label="Legal" score={riesgo.score_legal || 0} />
            <ScoreBar label="Operativo" score={riesgo.score_operativo || 0} />
          </div>

          {flagsActivos.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Alertas detectadas ({flagsActivos.length}):
              </p>
              <ul className="space-y-1">
                {flagsActivos.map((flag) => (
                  <li key={flag} className="text-xs text-gray-600 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                    {formatearFlag(flag)}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RiesgoIndicador;
