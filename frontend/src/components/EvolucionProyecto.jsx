import React, { useState, useEffect } from 'react';

function EvolucionProyecto({ proyectoId }) {
  const [versiones, setVersiones] = useState([]);
  const [versionSeleccionada, setVersionSeleccionada] = useState(null);
  const [comparando, setComparando] = useState(false);
  const [versionA, setVersionA] = useState(null);
  const [versionB, setVersionB] = useState(null);
  const [diferencias, setDiferencias] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarVersiones();
  }, [proyectoId]);

  async function cargarVersiones() {
    setLoading(true);
    try {
      const res = await fetch(`/api/versioning/proyectos/${proyectoId}/versiones`);
      const data = await res.json();
      setVersiones(data.versiones || data || []);
      if (data.length > 0) {
        setVersionSeleccionada(data[data.length - 1]);
      }
    } catch (error) {
      console.error('Error cargando versiones:', error);
    }
    setLoading(false);
  }

  async function compararVersiones() {
    if (!versionA || !versionB) return;
    try {
      const res = await fetch(
        `/api/versioning/proyectos/${proyectoId}/versiones/${versionA}/comparar/${versionB}`
      );
      const data = await res.json();
      setDiferencias(data);
    } catch (error) {
      console.error('Error comparando:', error);
    }
  }

  const getEstadoColor = (estado) => {
    const colores = {
      'APROBADO': 'bg-green-100 text-green-800 border-green-300',
      'RECHAZADO': 'bg-red-100 text-red-800 border-red-300',
      'REQUIERE_AJUSTES': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'EN_REVISION': 'bg-blue-100 text-blue-800 border-blue-300',
      'PENDIENTE': 'bg-gray-100 text-gray-800 border-gray-300'
    };
    return colores[estado] || colores['PENDIENTE'];
  };

  const getRiskScoreColor = (score) => {
    if (score < 40) return 'text-green-600';
    if (score < 60) return 'text-yellow-600';
    if (score < 80) return 'text-orange-600';
    return 'text-red-600';
  };

  const calcularProgreso = (version) => {
    const checklist = version.checklist_cumplimiento || {};
    const total = Object.keys(checklist).length || 1;
    const cumplidos = Object.values(checklist).filter(v => v === true).length;
    return Math.round((cumplidos / total) * 100);
  };

  if (loading) {
    return <div className="p-6 text-center">Cargando evolución del proyecto...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        Evolución del Proyecto
        <span className="text-sm font-normal text-gray-500">
          ({versiones.length} versiones)
        </span>
      </h2>

      <div className="relative mb-8">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
        
        {versiones.map((version, index) => {
          const progreso = calcularProgreso(version);
          const esUltima = index === versiones.length - 1;
          
          return (
            <div 
              key={version.id || index}
              className={`relative pl-10 pb-6 cursor-pointer transition-all
                ${versionSeleccionada?.id === version.id ? 'bg-blue-50 -mx-4 px-14 py-4 rounded-lg' : ''}
              `}
              onClick={() => setVersionSeleccionada(version)}
            >
              <div className={`
                absolute left-2 w-5 h-5 rounded-full border-2 
                ${esUltima ? 'bg-blue-500 border-blue-500' : 'bg-white border-gray-300'}
              `}>
                {esUltima && <div className="absolute inset-1 bg-white rounded-full" />}
              </div>
              
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">
                      Versión {version.numero_version || index + 1}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-xs border ${getEstadoColor(version.estado)}`}>
                      {version.estado || 'PENDIENTE'}
                    </span>
                    {esUltima && (
                      <span className="px-2 py-0.5 bg-blue-500 text-white rounded-full text-xs">
                        Actual
                      </span>
                    )}
                  </div>
                  
                  <div className="text-sm text-gray-500 mt-1">
                    {new Date(version.fecha_creacion).toLocaleDateString('es-MX', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                  
                  {version.motivo_version && (
                    <div className="text-sm mt-1 text-gray-600">
                      {version.motivo_version}
                    </div>
                  )}
                </div>
                
                <div className="text-right">
                  <div className={`text-2xl font-bold ${getRiskScoreColor(version.risk_score || 0)}`}>
                    {version.risk_score || 0}
                    <span className="text-sm text-gray-400">/100</span>
                  </div>
                  
                  <div className="w-32 mt-2">
                    <div className="flex justify-between text-xs mb-1">
                      <span>Cumplimiento</span>
                      <span>{progreso}%</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all ${
                          progreso === 100 ? 'bg-green-500' :
                          progreso >= 80 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${progreso}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {version.cambios_vs_anterior && version.cambios_vs_anterior.length > 0 && (
                <div className="mt-3 pl-4 border-l-2 border-gray-200">
                  <div className="text-xs text-gray-500 mb-1">Cambios en esta versión:</div>
                  {version.cambios_vs_anterior.slice(0, 3).map((cambio, i) => (
                    <div key={i} className="text-sm flex items-center gap-1">
                      <span className={
                        cambio.tipo === 'AGREGADO' ? 'text-green-600' :
                        cambio.tipo === 'MODIFICADO' ? 'text-blue-600' :
                        'text-red-600'
                      }>
                        {cambio.tipo === 'AGREGADO' ? '+' : 
                         cambio.tipo === 'MODIFICADO' ? '*' : '-'}
                      </span>
                      {cambio.descripcion}
                    </div>
                  ))}
                  {version.cambios_vs_anterior.length > 3 && (
                    <div className="text-xs text-gray-400">
                      +{version.cambios_vs_anterior.length - 3} cambios más
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="border-t pt-4">
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={() => setComparando(!comparando)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${comparando 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            {comparando ? 'Cancelar comparación' : 'Comparar versiones'}
          </button>
        </div>

        {comparando && (
          <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium mb-2">Versión A</label>
              <select
                value={versionA || ''}
                onChange={(e) => setVersionA(e.target.value)}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="">Seleccionar...</option>
                {versiones.map((v, i) => (
                  <option key={v.id || i} value={v.numero_version || i + 1}>
                    Versión {v.numero_version || i + 1}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Versión B</label>
              <select
                value={versionB || ''}
                onChange={(e) => setVersionB(e.target.value)}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="">Seleccionar...</option>
                {versiones.map((v, i) => (
                  <option key={v.id || i} value={v.numero_version || i + 1}>
                    Versión {v.numero_version || i + 1}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-span-2">
              <button
                onClick={compararVersiones}
                disabled={!versionA || !versionB}
                className="w-full py-2 bg-blue-500 text-white rounded-lg disabled:bg-gray-300"
              >
                Comparar
              </button>
            </div>
            
            {diferencias && (
              <div className="col-span-2 mt-4 p-4 bg-white rounded-lg border">
                <h4 className="font-semibold mb-2">Diferencias encontradas:</h4>
                {diferencias.campos_modificados?.map((campo, i) => (
                  <div key={i} className="text-sm py-1 border-b last:border-0">
                    <span className="font-medium">{campo.campo}:</span>
                    <span className="text-red-500 line-through ml-2">{campo.valor_anterior}</span>
                    <span className="text-green-500 ml-2">→ {campo.valor_nuevo}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default EvolucionProyecto;
