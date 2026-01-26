import React, { useState, useCallback } from 'react';

const DocumentUploadOCR = ({
  tipoDocumento,
  titulo,
  descripcion,
  obligatorio = false,
  onOCRComplete,
  onFileUploaded,
  empresaId,
  authToken
}) => {
  const [archivo, setArchivo] = useState(null);
  const [estado, setEstado] = useState('idle');
  const [datosExtraidos, setDatosExtraidos] = useState(null);
  const [nivelConfianza, setNivelConfianza] = useState(null);
  const [errores, setErrores] = useState([]);
  const [mostrarDatos, setMostrarDatos] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isServiceUnavailable, setIsServiceUnavailable] = useState(false);

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result;
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
    });
  };

  const procesarConOCR = async (file) => {
    setEstado('processing');
    setIsServiceUnavailable(false);
    
    try {
      const base64 = await fileToBase64(file);
      const mediaType = file.type || 'application/pdf';

      const endpoints = {
        constancia_situacion_fiscal: '/api/proveedores/ocr/constancia-fiscal',
        acta_constitutiva: '/api/proveedores/ocr/acta-constitutiva',
        opinion_cumplimiento: '/api/proveedores/ocr/opinion-cumplimiento',
        repse: '/api/proveedores/ocr/repse'
      };

      const endpoint = endpoints[tipoDocumento] || '/api/proveedores/ocr/clasificar';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
          'X-Empresa-ID': empresaId
        },
        body: JSON.stringify({ archivo_base64: base64, media_type: mediaType })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || 'Error en OCR';
        
        if (response.status === 503 || 
            errorMessage.toLowerCase().includes('no disponible') ||
            errorMessage.toLowerCase().includes('temporalmente')) {
          setIsServiceUnavailable(true);
          setErrores(['El servicio de análisis de documentos no está disponible temporalmente. Por favor intente más tarde.']);
          setEstado('error');
          return;
        }
        
        throw new Error(errorMessage);
      }

      const resultado = await response.json();

      if (resultado.exito) {
        setDatosExtraidos(resultado.datos_extraidos);
        setNivelConfianza(resultado.nivel_confianza);
        setEstado('success');
        if (onOCRComplete) {
          onOCRComplete(resultado.datos_extraidos);
        }
        if (onFileUploaded) {
          onFileUploaded(file, URL.createObjectURL(file));
        }
      } else {
        const errorMsg = resultado.error || 'Error procesando documento';
        if (errorMsg.toLowerCase().includes('no disponible')) {
          setIsServiceUnavailable(true);
          setErrores(['El servicio de análisis de documentos no está disponible temporalmente. Por favor intente más tarde.']);
        } else {
          setErrores(resultado.errores || [errorMsg]);
        }
        setEstado('error');
      }
    } catch (error) {
      console.error('Error procesando documento:', error);
      const errorMsg = error.message || 'Error procesando el documento';
      
      if (errorMsg.toLowerCase().includes('no disponible') || 
          errorMsg.toLowerCase().includes('temporalmente') ||
          errorMsg.toLowerCase().includes('503')) {
        setIsServiceUnavailable(true);
        setErrores(['El servicio de análisis de documentos no está disponible temporalmente. Por favor intente más tarde.']);
      } else {
        setErrores([errorMsg || 'Error procesando el documento. Por favor intente de nuevo.']);
      }
      setEstado('error');
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragActive(false);
    
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.size > 10 * 1024 * 1024) {
        setErrores(['El archivo excede el límite de 10MB']);
        setEstado('error');
        return;
      }
      setArchivo(file);
      setEstado('uploading');
      setTimeout(() => {
        procesarConOCR(file);
      }, 500);
    }
  }, [tipoDocumento]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setErrores(['El archivo excede el límite de 10MB']);
        setEstado('error');
        return;
      }
      setArchivo(file);
      setEstado('uploading');
      setTimeout(() => {
        procesarConOCR(file);
      }, 500);
    }
  };

  const resetUpload = () => {
    setArchivo(null);
    setEstado('idle');
    setDatosExtraidos(null);
    setNivelConfianza(null);
    setErrores([]);
    setMostrarDatos(false);
    setIsServiceUnavailable(false);
  };

  const getConfianzaColor = (nivel) => {
    switch (nivel) {
      case 'alto': return 'bg-green-100 text-green-800';
      case 'medio': return 'bg-yellow-100 text-yellow-800';
      case 'bajo': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          {titulo}
          {obligatorio && <span className="text-red-500 ml-1">*</span>}
        </label>
        {nivelConfianza && (
          <span className={`px-2 py-1 text-xs rounded-full ${getConfianzaColor(nivelConfianza)}`}>
            Confianza: {nivelConfianza}
          </span>
        )}
      </div>
      
      <p className="text-xs text-gray-500">{descripcion}</p>

      {(estado === 'idle' || estado === 'error') && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`
            border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
            transition-colors duration-200
            ${isDragActive 
              ? 'border-blue-500 bg-blue-50' 
              : estado === 'error'
                ? isServiceUnavailable
                  ? 'border-orange-300 bg-orange-50'
                  : 'border-red-300 bg-red-50'
                : 'border-gray-300 hover:border-blue-500'
            }
          `}
        >
          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFileSelect}
            className="hidden"
            id={`file-upload-${tipoDocumento}`}
          />
          <label htmlFor={`file-upload-${tipoDocumento}`} className="cursor-pointer">
            {isServiceUnavailable ? (
              <svg className="mx-auto h-10 w-10 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            ) : (
              <svg className={`mx-auto h-10 w-10 ${estado === 'error' ? 'text-red-400' : 'text-gray-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
            <p className="mt-2 text-sm text-gray-600">
              {isDragActive 
                ? 'Suelta el archivo aquí...' 
                : 'Arrastra un archivo o haz clic para seleccionar'
              }
            </p>
            <p className="mt-1 text-xs text-gray-500">
              PDF, JPG o PNG (máx. 10MB)
            </p>
          </label>
          
          {errores.length > 0 && (
            <div className="mt-3 text-left">
              {isServiceUnavailable && (
                <div className="mb-2 p-2 bg-orange-100 rounded-md border border-orange-200">
                  <p className="text-sm text-orange-800 font-medium flex items-center gap-2">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Servicio temporalmente no disponible
                  </p>
                  <p className="text-xs text-orange-700 mt-1">
                    El servicio de análisis automático de documentos no está disponible en este momento. 
                    Por favor intente de nuevo más tarde o contacte al soporte técnico.
                  </p>
                </div>
              )}
              {errores.map((error, i) => (
                <p key={i} className={`text-xs flex items-center gap-1 ${isServiceUnavailable ? 'text-orange-600' : 'text-red-600'}`}>
                  <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {error}
                </p>
              ))}
              {estado === 'error' && (
                <button
                  type="button"
                  onClick={resetUpload}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  Intentar de nuevo
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {(estado === 'uploading' || estado === 'processing') && (
        <div className="border-2 border-dashed border-blue-500 rounded-lg p-6 text-center bg-blue-50">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="mt-2 text-sm text-blue-700 font-medium">
            {estado === 'uploading' ? 'Subiendo archivo...' : 'Analizando documento con IA...'}
          </p>
          {archivo && (
            <p className="mt-1 text-xs text-gray-500">{archivo.name}</p>
          )}
        </div>
      )}

      {estado === 'success' && (
        <div className="border-2 border-green-200 rounded-lg p-4 bg-green-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-green-800">
                  Documento procesado correctamente
                </p>
                <p className="text-xs text-green-600">{archivo?.name}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMostrarDatos(!mostrarDatos)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 flex items-center gap-1"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                {mostrarDatos ? 'Ocultar' : 'Ver datos'}
              </button>
              <button
                type="button"
                onClick={resetUpload}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              >
                Cambiar
              </button>
            </div>
          </div>

          {mostrarDatos && datosExtraidos && (
            <div className="mt-4 p-3 bg-white rounded border border-green-200">
              <p className="text-xs font-medium text-gray-700 mb-2">
                Datos extraídos automáticamente:
              </p>
              <pre className="text-xs text-gray-600 overflow-auto max-h-48 whitespace-pre-wrap">
                {JSON.stringify(datosExtraidos, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentUploadOCR;
