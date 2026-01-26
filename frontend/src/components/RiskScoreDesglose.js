import React from 'react';

const PILARES = [
  {
    key: 'razon_negocios',
    nombre: 'Razón de Negocios',
    descripcion: 'Art. 5-A CFF - Vinculación con el giro y objetivo económico',
    color: 'blue',
    colorClass: 'bg-blue-500',
    bgLight: 'bg-blue-50',
    textColor: 'text-blue-700',
    icon: '🎯'
  },
  {
    key: 'beneficio_economico',
    nombre: 'Beneficio Económico',
    descripcion: 'ROI documentado y beneficios cuantificables',
    color: 'green',
    colorClass: 'bg-green-500',
    bgLight: 'bg-green-50',
    textColor: 'text-green-700',
    icon: '📈'
  },
  {
    key: 'materialidad',
    nombre: 'Materialidad',
    descripcion: 'Art. 69-B CFF - Evidencia de operaciones reales',
    color: 'purple',
    colorClass: 'bg-purple-500',
    bgLight: 'bg-purple-50',
    textColor: 'text-purple-700',
    icon: '📦'
  },
  {
    key: 'trazabilidad',
    nombre: 'Trazabilidad',
    descripcion: 'NOM-151 - Integridad documental y timeline',
    color: 'orange',
    colorClass: 'bg-orange-500',
    bgLight: 'bg-orange-50',
    textColor: 'text-orange-700',
    icon: '🔗'
  }
];

function RiskScoreDesglose({ 
  riskScoreTotal,
  riskScoreRazonNegocios,
  riskScoreBeneficioEconomico,
  riskScoreMaterialidad,
  riskScoreTrazabilidad,
  showDetails = true,
  compact = false
}) {
  
  const scores = {
    razon_negocios: riskScoreRazonNegocios || 0,
    beneficio_economico: riskScoreBeneficioEconomico || 0,
    materialidad: riskScoreMaterialidad || 0,
    trazabilidad: riskScoreTrazabilidad || 0
  };
  
  const total = riskScoreTotal || Object.values(scores).reduce((a, b) => a + b, 0);
  
  const getNivelRiesgo = (score) => {
    if (score < 40) return { nivel: 'BAJO', color: 'text-green-600', bg: 'bg-green-100' };
    if (score < 60) return { nivel: 'MEDIO', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    if (score < 80) return { nivel: 'ALTO', color: 'text-orange-600', bg: 'bg-orange-100' };
    return { nivel: 'CRÍTICO', color: 'text-red-600', bg: 'bg-red-100' };
  };
  
  const nivelTotal = getNivelRiesgo(total);
  
  const getNivelPilar = (score, max = 25) => {
    const porcentaje = (score / max) * 100;
    if (porcentaje < 40) return 'bajo';
    if (porcentaje < 60) return 'medio';
    if (porcentaje < 80) return 'alto';
    return 'critico';
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <span className={`text-2xl font-bold ${nivelTotal.color}`}>
          {total}
        </span>
        <span className="text-gray-400">/100</span>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${nivelTotal.bg} ${nivelTotal.color}`}>
          {nivelTotal.nivel}
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-800">Puntuación de Riesgo</h3>
          <p className="text-sm text-gray-500">Evaluación de riesgo fiscal</p>
        </div>
        <div className="text-right">
          <div className={`text-4xl font-bold ${nivelTotal.color}`}>
            {total}
          </div>
          <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${nivelTotal.bg} ${nivelTotal.color}`}>
            Riesgo {nivelTotal.nivel}
          </div>
        </div>
      </div>

      <div className="mb-6">
        <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-500 ${
              total < 40 ? 'bg-green-500' :
              total < 60 ? 'bg-yellow-500' :
              total < 80 ? 'bg-orange-500' : 'bg-red-500'
            }`}
            style={{ width: `${total}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>0 - Bajo riesgo</span>
          <span>100 - Alto riesgo</span>
        </div>
      </div>

      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
          Desglose por Pilar
        </h4>
        
        {PILARES.map(pilar => {
          const score = scores[pilar.key];
          const porcentaje = (score / 25) * 100;
          const nivel = getNivelPilar(score);
          
          return (
            <div key={pilar.key} className={`p-4 rounded-lg ${pilar.bgLight}`}>
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{pilar.icon}</span>
                  <div>
                    <span className={`font-medium ${pilar.textColor}`}>
                      {pilar.nombre}
                    </span>
                    {showDetails && (
                      <p className="text-xs text-gray-500">{pilar.descripcion}</p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-xl font-bold ${pilar.textColor}`}>
                    {score}
                  </span>
                  <span className="text-gray-400 text-sm">/25</span>
                </div>
              </div>
              
              <div className="h-2 bg-white bg-opacity-50 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${pilar.colorClass} transition-all duration-500`}
                  style={{ width: `${porcentaje}%` }}
                />
              </div>
              
              <div className="flex justify-end mt-1">
                <span className={`text-xs px-2 py-0.5 rounded ${
                  nivel === 'bajo' ? 'bg-green-200 text-green-700' :
                  nivel === 'medio' ? 'bg-yellow-200 text-yellow-700' :
                  nivel === 'alto' ? 'bg-orange-200 text-orange-700' :
                  'bg-red-200 text-red-700'
                }`}>
                  {nivel === 'bajo' ? 'Bajo' :
                   nivel === 'medio' ? 'Medio' :
                   nivel === 'alto' ? 'Alto' : 'Crítico'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {showDetails && (
        <div className="mt-6 pt-4 border-t">
          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            Interpretación
          </h4>
          <div className="grid grid-cols-4 gap-2 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span>0-39: Bajo</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-yellow-500"></div>
              <span>40-59: Medio</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-orange-500"></div>
              <span>60-79: Alto</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span>80-100: Crítico</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RiskScoreDesglose;
