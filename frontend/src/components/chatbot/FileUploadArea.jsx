import { useState, useRef, useCallback } from 'react';
import { ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE, FILE_STATUS } from '../../constants/onboarding';

export function FileUploadArea({
  onFilesSelected,
  uploadedFiles = [],
  isProcessing = false,
  onRemoveFile,
  maxFiles = 10,
  className = '',
}) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        onFilesSelected(files);
      }
    },
    [onFilesSelected]
  );

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    (e) => {
      const files = Array.from(e.target.files || []);
      if (files.length > 0) {
        onFilesSelected(files);
      }
      e.target.value = '';
    },
    [onFilesSelected]
  );

  const getStatusIcon = (status) => {
    switch (status) {
      case FILE_STATUS.PENDING:
      case 'pending':
        return '⏳';
      case FILE_STATUS.ANALYZING:
      case 'analyzing':
        return '🔍';
      case FILE_STATUS.ANALYZED:
      case 'analyzed':
        return '✅';
      case FILE_STATUS.UPLOADING:
      case 'uploading':
        return '📤';
      case FILE_STATUS.UPLOADED:
      case 'uploaded':
        return '☁️';
      case FILE_STATUS.ERROR:
      case 'error':
        return '❌';
      default:
        return '📄';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case FILE_STATUS.PENDING:
      case 'pending':
        return 'Pendiente';
      case FILE_STATUS.ANALYZING:
      case 'analyzing':
        return 'Analizando con IA...';
      case FILE_STATUS.ANALYZED:
      case 'analyzed':
        return 'Analizado';
      case FILE_STATUS.UPLOADING:
      case 'uploading':
        return 'Subiendo...';
      case FILE_STATUS.UPLOADED:
      case 'uploaded':
        return 'Subido';
      case FILE_STATUS.ERROR:
      case 'error':
        return 'Error';
      default:
        return '';
    }
  };

  const canAddMore = uploadedFiles.length < maxFiles;

  return (
    <div className={className}>
      {canAddMore && (
        <div
          onClick={handleClick}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-blue-500 bg-blue-500/10'
              : 'border-white/30 hover:border-white/50 hover:bg-white/5'
          } ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept={ALLOWED_FILE_EXTENSIONS.join(',')}
            onChange={handleFileChange}
            className="hidden"
          />

          <div className="text-4xl mb-3">📁</div>
          <p className="text-gray-200 font-medium">
            {isDragging ? 'Suelta los archivos aquí' : 'Arrastra archivos o haz clic para seleccionar'}
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Formatos: {ALLOWED_FILE_EXTENSIONS.join(', ')}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Máximo {MAX_FILE_SIZE / 1024 / 1024}MB por archivo
          </p>
        </div>
      )}

      {uploadedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-sm font-medium text-gray-300">
            Archivos ({uploadedFiles.length}/{maxFiles})
          </p>

          {uploadedFiles.map((file) => (
            <div
              key={file.id}
              className={`flex items-center justify-between p-3 bg-white/5 rounded-lg border ${
                file.status === 'error' ? 'border-red-500/50 bg-red-500/10' : 'border-white/10'
              }`}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <span className="text-xl">{getStatusIcon(file.status)}</span>
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-200 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {(file.size / 1024).toFixed(1)} KB · {getStatusText(file.status)}
                  </p>
                  {file.error && (
                    <p className="text-xs text-red-400 mt-1">{file.error}</p>
                  )}
                </div>
              </div>

              {file.status !== 'uploading' && (
                <button
                  onClick={() => onRemoveFile?.(file.id)}
                  className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                  title="Eliminar archivo"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}

              {(file.status === 'analyzing' || file.status === 'uploading') && (
                <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              )}
            </div>
          ))}
        </div>
      )}

      {uploadedFiles.some((f) => f.analysis) && (
        <div className="mt-4 p-4 bg-green-500/10 rounded-lg border border-green-500/30">
          <p className="text-sm font-medium text-green-300 mb-2">
            ✨ Datos extraídos por IA
          </p>
          {uploadedFiles
            .filter((f) => f.analysis)
            .map((file) => (
              <div key={file.id} className="text-sm text-green-200">
                <p className="font-medium">{file.name}:</p>
                {file.analysis.categoria && (
                  <p className="ml-2">Categoría: {file.analysis.categoria}</p>
                )}
                {file.analysis.resumen && (
                  <p className="ml-2 text-xs text-green-300">{file.analysis.resumen}</p>
                )}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

export default FileUploadArea;
