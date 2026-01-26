import React, { useState, useEffect, useCallback } from 'react';

function ListaDocumentos({ proyectoId, faseActual, refreshTrigger }) {
  const [documentos, setDocumentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtroFase, setFiltroFase] = useState('TODAS');

  const cargarDocumentos = useCallback(async () => {
    if (!proyectoId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/proyectos/${proyectoId}/documentos`);
      const data = await response.json();
      setDocumentos(data.documentos || data || []);
    } catch (error) {
      console.error('Error cargando documentos:', error);
    }
    setLoading(false);
  }, [proyectoId]);

  useEffect(() => {
    cargarDocumentos();
  }, [cargarDocumentos, refreshTrigger]);

  const documentosFiltrados = filtroFase === 'TODAS' 
    ? documentos 
    : documentos.filter(d => d.fase_asociada === filtroFase);

  const getIconoTipo = (tipo) => {
    const iconos = {
      'SIB_BEE': '📋',
      'SOW': '📝',
      'CONTRATO': '📜',
      'CFDI': '🧾',
      'ENTREGABLE_FINAL': '📦',
      'ENTREGABLE_V1': '📦',
      'ENTREGABLE_ITERATIVO': '📦',
      'MINUTA_KICKOFF': '📑',
      'MINUTA_REVISION': '📑',
      'EVIDENCIA_EJECUCION': '📸',
      'ACTA_ACEPTACION': '✅',
      'ESTUDIO_TP': '📊',
      'COMPROBANTE_PAGO': '💳',
      'CORRESPONDENCIA': '📧',
      'ANEXO_TECNICO': '📎',
      'CRONOGRAMA': '📅',
      'default': '📄'
    };
    return iconos[tipo] || iconos.default;
  };

  const formatFecha = (fecha) => {
    if (!fecha) return '-';
    return new Date(fecha).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTipo = (tipo) => {
    if (!tipo) return '-';
    return tipo.replace(/_/g, ' ');
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-3"></div>
        <div className="text-gray-500 dark:text-gray-400">Cargando documentos...</div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="p-4 border-b dark:border-gray-700 flex justify-between items-center">
        <h3 className="font-bold text-gray-800 dark:text-white">
          Documentos del Proyecto ({documentos.length})
        </h3>
        <select
          value={filtroFase}
          onChange={(e) => setFiltroFase(e.target.value)}
          className="border dark:border-gray-600 rounded px-2 py-1 text-sm dark:bg-gray-700 dark:text-white"
        >
          <option value="TODAS">Todas las fases</option>
          {['F0','F1','F2','F3','F4','F5','F6','F7','F8','F9'].map(f => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
      </div>

      {documentosFiltrados.length === 0 ? (
        <div className="p-8 text-center text-gray-500 dark:text-gray-400">
          <div className="text-4xl mb-2">📂</div>
          <div>No hay documentos {filtroFase !== 'TODAS' ? `en fase ${filtroFase}` : ''}</div>
        </div>
      ) : (
        <ul className="divide-y dark:divide-gray-700">
          {documentosFiltrados.map(doc => (
            <li key={doc.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-4">
              <span className="text-2xl">{getIconoTipo(doc.tipo)}</span>
              
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-800 dark:text-white truncate">
                  {doc.descripcion || doc.nombre_archivo}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 flex flex-wrap gap-3">
                  <span className="bg-gray-100 dark:bg-gray-600 px-2 py-0.5 rounded">{doc.fase_asociada}</span>
                  <span>{formatTipo(doc.tipo)}</span>
                  <span>{formatFecha(doc.fecha_carga)}</span>
                </div>
              </div>

              <div className="flex gap-2">
                {doc.url_descarga && (
                  <a
                    href={doc.url_descarga}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800"
                  >
                    Ver
                  </a>
                )}
                {doc.pcloud_link && (
                  <a
                    href={doc.pcloud_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 text-sm bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded hover:bg-green-200 dark:hover:bg-green-800"
                  >
                    pCloud
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default ListaDocumentos;
