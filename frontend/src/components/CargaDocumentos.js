import React, { useState, useCallback } from 'react';
import api from '../services/api';

const TIPOS_DOCUMENTO = [
  { value: 'SIB_BEE', label: 'SIB / BEE (Solicitud Interna / Beneficio Económico Esperado)', fases: ['F0'] },
  { value: 'SOW', label: 'SOW / Orden de Trabajo', fases: ['F1'] },
  { value: 'CONTRATO', label: 'Contrato', fases: ['F1', 'F2'] },
  { value: 'ANEXO_TECNICO', label: 'Anexo Técnico', fases: ['F1', 'F2'] },
  { value: 'CRONOGRAMA', label: 'Cronograma de Hitos', fases: ['F1', 'F2'] },
  { value: 'MINUTA_KICKOFF', label: 'Minuta Kick-off', fases: ['F3'] },
  { value: 'ENTREGABLE_V1', label: 'Entregable Versión 1', fases: ['F3'] },
  { value: 'ENTREGABLE_ITERATIVO', label: 'Entregable Iterativo', fases: ['F4'] },
  { value: 'MINUTA_REVISION', label: 'Minuta de Revisión', fases: ['F4'] },
  { value: 'ENTREGABLE_FINAL', label: 'Entregable Final', fases: ['F5'] },
  { value: 'ACTA_ACEPTACION', label: 'Acta de Aceptación Técnica', fases: ['F5', 'F6'] },
  { value: 'ESTUDIO_TP', label: 'Estudio de Precios de Transferencia', fases: ['F6'] },
  { value: 'CFDI', label: 'CFDI / Factura', fases: ['F8'] },
  { value: 'COMPROBANTE_PAGO', label: 'Comprobante de Pago', fases: ['F8'] },
  { value: 'EVIDENCIA_EJECUCION', label: 'Evidencia de Ejecución', fases: ['F3', 'F4', 'F5'] },
  { value: 'CORRESPONDENCIA', label: 'Correspondencia / Emails', fases: ['F0', 'F1', 'F2', 'F3', 'F4', 'F5'] },
  { value: 'OTRO', label: 'Otro', fases: ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9'] }
];

function CargaDocumentos({ proyectoId, faseActual, onDocumentoCargado, onClose }) {
  const [archivo, setArchivo] = useState(null);
  const [tipo, setTipo] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const tiposDisponibles = TIPOS_DOCUMENTO.filter(t => 
    t.fases.includes(faseActual) || t.value === 'OTRO'
  );

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setArchivo(e.dataTransfer.files[0]);
      setError(null);
    }
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      if (file.size > 50 * 1024 * 1024) {
        setError('El archivo excede el límite de 50MB');
        return;
      }
      
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'image/png',
        'image/jpeg',
        'application/xml',
        'text/xml'
      ];
      
      if (!allowedTypes.includes(file.type) && !file.name.endsWith('.xml')) {
        setError('Tipo de archivo no permitido. Use PDF, Word, Excel, PowerPoint, imágenes o XML.');
        return;
      }
      
      setArchivo(file);
      setError(null);
    }
  };

  async function handleUpload(e) {
    e.preventDefault();
    
    if (!archivo) {
      setError('Selecciona un archivo');
      return;
    }
    
    if (!tipo) {
      setError('Selecciona el tipo de documento');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('archivo', archivo);
      formData.append('tipo', tipo);
      formData.append('descripcion', descripcion || archivo.name);
      formData.append('fase_asociada', faseActual);

      // Usar api.js para que incluya el token de autenticación
      const data = await api.post(`/api/proyectos/${proyectoId}/documentos`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      // api.js ya extrae response.data
      if (data?.id || data?.success) {
        setArchivo(null);
        setTipo('');
        setDescripcion('');

        if (onDocumentoCargado) {
          onDocumentoCargado(data);
        }
      } else {
        setError(data?.error || data?.detail || 'Error al cargar el documento');
      }
    } catch (err) {
      setError(err?.message || err?.detail || 'Error de conexión');
    }

    setUploading(false);
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 max-w-lg w-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-gray-800 dark:text-white">
          Cargar Documento - Fase {faseActual}
        </h3>
        {onClose && (
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ✕
          </button>
        )}
      </div>

      <form onSubmit={handleUpload} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Tipo de documento *
          </label>
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            required
          >
            <option value="">Seleccionar tipo...</option>
            {tiposDisponibles.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Descripción
          </label>
          <input
            type="text"
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            placeholder="Ej: Informe Final V2.0 - Estudio de Mercado NL"
          />
        </div>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
            transition-colors duration-200
            ${dragActive 
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
            }
            ${archivo ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-600' : ''}
          `}
        >
          <input
            type="file"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.png,.jpg,.jpeg,.xml"
          />
          
          {archivo ? (
            <div className="space-y-2">
              <div className="text-green-600 text-4xl">✓</div>
              <div className="font-medium text-gray-800 dark:text-white">{archivo.name}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">{formatFileSize(archivo.size)}</div>
              <button
                type="button"
                onClick={() => setArchivo(null)}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Cambiar archivo
              </button>
            </div>
          ) : (
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="text-gray-400 text-4xl mb-2">📄</div>
              <div className="text-gray-600 dark:text-gray-300">
                Arrastra un archivo aquí o <span className="text-blue-600">selecciónalo</span>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                PDF, Word, Excel, PowerPoint, imágenes o XML (máx. 50MB)
              </div>
            </label>
          )}
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancelar
            </button>
          )}
          <button
            type="submit"
            disabled={uploading || !archivo || !tipo}
            className={`
              flex-1 px-4 py-2 rounded-md text-white font-medium
              ${uploading || !archivo || !tipo
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
              }
            `}
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Cargando...
              </span>
            ) : (
              'Cargar Documento'
            )}
          </button>
        </div>
      </form>

      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-md text-xs text-gray-600 dark:text-gray-300">
        <strong>Documentos sugeridos para {faseActual}:</strong>
        <ul className="mt-1 list-disc list-inside">
          {tiposDisponibles.slice(0, 4).map(t => (
            <li key={t.value}>{t.label}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default CargaDocumentos;
