import React from 'react';

function RiskScoreMiniChart({ 
  razonNegocios = 0, 
  beneficioEconomico = 0, 
  materialidad = 0, 
  trazabilidad = 0 
}) {
  const pilares = [
    { key: 'rn', valor: razonNegocios, color: 'bg-blue-500', label: 'RN' },
    { key: 'be', valor: beneficioEconomico, color: 'bg-green-500', label: 'BE' },
    { key: 'ma', valor: materialidad, color: 'bg-purple-500', label: 'MA' },
    { key: 'tr', valor: trazabilidad, color: 'bg-orange-500', label: 'TR' }
  ];
  
  return (
    <div 
      className="flex items-center gap-1" 
      title="RN: Razón Negocios | BE: Beneficio Económico | MA: Materialidad | TR: Trazabilidad"
    >
      {pilares.map(pilar => (
        <div key={pilar.key} className="flex flex-col items-center">
          <div className="w-6 h-12 bg-gray-200 rounded-sm overflow-hidden flex flex-col-reverse">
            <div 
              className={`${pilar.color} transition-all duration-300`}
              style={{ height: `${(pilar.valor / 25) * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-gray-500 mt-0.5">{pilar.label}</span>
        </div>
      ))}
    </div>
  );
}

export default RiskScoreMiniChart;
