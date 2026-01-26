import React, { useState, useEffect } from 'react';

function ChecklistProveedor({ proyectoId, tipologia, faseActual }) {
  const [checklist, setChecklist] = useState([]);
  const [itemsCumplidos, setItemsCumplidos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [mensajeExito, setMensajeExito] = useState('');
  const [emailProveedor, setEmailProveedor] = useState('');
  const [mostrarEnvio, setMostrarEnvio] = useState(false);

  useEffect(() => {
    cargarChecklistProveedor();
  }, [proyectoId, tipologia, faseActual]);

  async function cargarChecklistProveedor() {
    setLoading(true);
    try {
      const res = await fetch(`/api/proyectos/${proyectoId}/checklist-proveedor`);
      const data = await res.json();
      if (data.success) {
        setChecklist(data.checklist || []);
        setItemsCumplidos(data.items_cumplidos || []);
      }
    } catch (error) {
      console.error('Error cargando checklist:', error);
      if (tipologia) {
        try {
          const res = await fetch(`/api/checklists/tipologia/${tipologia}/responsable/PROVEEDOR`);
          const data = await res.json();
          setChecklist(data.items || []);
        } catch (e) {
          console.error('Error cargando items de proveedor:', e);
        }
      }
    }
    setLoading(false);
  }

  async function enviarChecklistProveedor() {
    if (!emailProveedor) return;
    
    setEnviando(true);
    try {
      const res = await fetch(`/api/proyectos/${proyectoId}/enviar-checklist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_proveedor: emailProveedor,
          items_pendientes: checklist.filter(item => !itemsCumplidos.includes(item.id))
        })
      });
      const data = await res.json();
      if (data.success) {
        setMensajeExito('Checklist enviado exitosamente al proveedor');
        setMostrarEnvio(false);
        setEmailProveedor('');
        setTimeout(() => setMensajeExito(''), 5000);
      }
    } catch (error) {
      console.error('Error enviando checklist:', error);
    }
    setEnviando(false);
  }

  const toggleItemCumplido = (itemId) => {
    setItemsCumplidos(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const calcularProgreso = () => {
    if (checklist.length === 0) return 0;
    const obligatorios = checklist.filter(item => item.obligatorio);
    const cumplidos = obligatorios.filter(item => itemsCumplidos.includes(item.id));
    return Math.round((cumplidos.length / obligatorios.length) * 100) || 0;
  };

  const agruparPorFase = () => {
    const grupos = {};
    checklist.forEach(item => {
      const fase = item.fase || 'Sin fase';
      if (!grupos[fase]) {
        grupos[fase] = [];
      }
      grupos[fase].push(item);
    });
    return grupos;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const progreso = calcularProgreso();
  const fasesPendientes = agruparPorFase();
  const pendientes = checklist.filter(item => !itemsCumplidos.includes(item.id) && item.obligatorio);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">
            Checklist del Proveedor
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Documentos y entregables pendientes por parte del proveedor
          </p>
        </div>
        
        <div className="text-right">
          <div className="text-3xl font-bold text-blue-600">{progreso}%</div>
          <div className="text-sm text-gray-500">Completado</div>
        </div>
      </div>

      {mensajeExito && (
        <div className="mb-4 p-3 bg-green-100 text-green-800 rounded-lg flex items-center gap-2">
          <span>✓</span>
          {mensajeExito}
        </div>
      )}

      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-600">Progreso de cumplimiento</span>
          <span className="font-medium">{itemsCumplidos.length} de {checklist.filter(i => i.obligatorio).length} obligatorios</span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-500 ${
              progreso === 100 ? 'bg-green-500' :
              progreso >= 80 ? 'bg-blue-500' :
              progreso >= 50 ? 'bg-yellow-500' :
              'bg-red-500'
            }`}
            style={{ width: `${progreso}%` }}
          />
        </div>
      </div>

      {pendientes.length > 0 && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 className="font-semibold text-yellow-800 mb-2 flex items-center gap-2">
            <span>⚠️</span>
            {pendientes.length} elemento{pendientes.length > 1 ? 's' : ''} pendiente{pendientes.length > 1 ? 's' : ''}
          </h3>
          <ul className="text-sm text-yellow-700 space-y-1">
            {pendientes.slice(0, 5).map(item => (
              <li key={item.id} className="flex items-start gap-2">
                <span className="text-yellow-500">•</span>
                {item.descripcion}
              </li>
            ))}
            {pendientes.length > 5 && (
              <li className="text-yellow-600 font-medium">
                +{pendientes.length - 5} más...
              </li>
            )}
          </ul>
        </div>
      )}

      <div className="space-y-6">
        {Object.entries(fasesPendientes).map(([fase, items]) => (
          <div key={fase} className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b">
              <h3 className="font-semibold text-gray-700 flex items-center justify-between">
                <span>Fase {fase}</span>
                <span className="text-sm font-normal text-gray-500">
                  {items.filter(i => itemsCumplidos.includes(i.id)).length}/{items.length} completados
                </span>
              </h3>
            </div>
            
            <div className="divide-y">
              {items.map(item => {
                const cumplido = itemsCumplidos.includes(item.id);
                
                return (
                  <div 
                    key={item.id}
                    className={`p-4 flex items-start gap-3 cursor-pointer hover:bg-gray-50 transition-colors
                      ${cumplido ? 'bg-green-50' : ''}
                    `}
                    onClick={() => toggleItemCumplido(item.id)}
                  >
                    <div className={`
                      w-6 h-6 rounded-full border-2 flex-shrink-0 flex items-center justify-center
                      ${cumplido 
                        ? 'bg-green-500 border-green-500 text-white' 
                        : 'border-gray-300 hover:border-blue-400'
                      }
                    `}>
                      {cumplido && <span className="text-sm">✓</span>}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <span className={`font-medium ${cumplido ? 'text-green-700 line-through' : 'text-gray-800'}`}>
                            {item.descripcion}
                          </span>
                          <span className={`ml-2 text-xs px-2 py-0.5 rounded-full
                            ${item.obligatorio 
                              ? 'bg-red-100 text-red-700' 
                              : 'bg-gray-100 text-gray-600'
                            }
                          `}>
                            {item.obligatorio ? 'Obligatorio' : 'Opcional'}
                          </span>
                        </div>
                        <span className="text-xs text-gray-400 font-mono">{item.id}</span>
                      </div>
                      
                      {item.criterio_aceptacion && (
                        <div className="mt-2 text-sm text-gray-600">
                          <span className="font-medium">Criterio:</span> {item.criterio_aceptacion}
                        </div>
                      )}
                      
                      {item.ejemplo_bueno && (
                        <div className="mt-1 text-sm">
                          <span className="text-green-600">✓ Ejemplo válido:</span>{' '}
                          <span className="text-gray-600">{item.ejemplo_bueno}</span>
                        </div>
                      )}
                      
                      {item.ejemplo_malo && (
                        <div className="mt-1 text-sm">
                          <span className="text-red-600">✗ Evitar:</span>{' '}
                          <span className="text-gray-600">{item.ejemplo_malo}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 border-t pt-4">
        {!mostrarEnvio ? (
          <button
            onClick={() => setMostrarEnvio(true)}
            className="w-full py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
          >
            <span>📧</span>
            Enviar checklist al proveedor
          </button>
        ) : (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-3">Enviar checklist de requisitos pendientes</h4>
            <div className="flex gap-3">
              <input
                type="email"
                value={emailProveedor}
                onChange={(e) => setEmailProveedor(e.target.value)}
                placeholder="correo@proveedor.com"
                className="flex-1 border rounded-lg px-4 py-2"
              />
              <button
                onClick={enviarChecklistProveedor}
                disabled={!emailProveedor || enviando}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:bg-gray-300 transition-colors"
              >
                {enviando ? 'Enviando...' : 'Enviar'}
              </button>
              <button
                onClick={() => {
                  setMostrarEnvio(false);
                  setEmailProveedor('');
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancelar
              </button>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Se enviará un correo con el detalle de los {pendientes.length} elementos pendientes.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChecklistProveedor;
