import { useState, useCallback } from 'react';

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.txt', '.xml', '.png', '.jpg', '.jpeg'];
const MAX_FILE_SIZE = 50 * 1024 * 1024;

export function useFileUpload(onAnalysisComplete) {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [additionalFiles, setAdditionalFiles] = useState([]);
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [isUploadingDocuments, setIsUploadingDocuments] = useState(false);
  const [fileAnalysisResults, setFileAnalysisResults] = useState([]);
  const [extractedDocumentContents, setExtractedDocumentContents] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});
  const [error, setError] = useState(null);

  const validateFile = useCallback((file) => {
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return {
        valid: false,
        error: `Tipo de archivo no permitido: ${extension}. Permitidos: ${ALLOWED_EXTENSIONS.join(', ')}`
      };
    }

    if (file.size > MAX_FILE_SIZE) {
      return {
        valid: false,
        error: `Archivo muy grande: ${(file.size / 1024 / 1024).toFixed(2)}MB. Máximo: 50MB`
      };
    }

    return { valid: true };
  }, []);

  const handleFileSelect = useCallback(async (files) => {
    setError(null);
    const validFiles = [];
    const errors = [];

    for (const file of files) {
      const validation = validateFile(file);
      if (validation.valid) {
        validFiles.push({
          id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'pending',
          progress: 0,
        });
      } else {
        errors.push({ file: file.name, error: validation.error });
      }
    }

    if (errors.length > 0) {
      setError(errors.map(e => `${e.file}: ${e.error}`).join('\n'));
    }

    if (validFiles.length > 0) {
      setUploadedFiles((prev) => [...prev, ...validFiles]);
    }

    return validFiles;
  }, [validateFile]);

  const analyzeDocument = useCallback(async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    try {
      setIsProcessingFile(true);
      console.log(`[useFileUpload] Analizando: ${file.name}`);

      // Use backend URL from env or fallback to relative path (for Vercel rewrites)
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const apiUrl = `${backendUrl}/api/chat/archivo/analyze-document`;
      console.log(`[useFileUpload] API URL: ${apiUrl}`);

      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      
      const responseText = await response.text();
      console.log(`[useFileUpload] Respuesta para ${file.name}:`, responseText.substring(0, 200));
      
      let result;
      try {
        result = responseText ? JSON.parse(responseText) : {};
      } catch (parseErr) {
        console.error(`[useFileUpload] JSON parse error para ${file.name}:`, parseErr);
        throw new Error('Respuesta inválida del servidor');
      }

      if (!response.ok) {
        console.error(`[useFileUpload] Error HTTP ${response.status} para ${file.name}:`, result);
        throw new Error(result.detail || `Error del servidor (${response.status})`);
      }

      setFileAnalysisResults(prev => [...prev, result]);
      
      if (result.extracted_text) {
        setExtractedDocumentContents(prev => [...prev, {
          filename: file.name,
          text: result.extracted_text,
          classification: result.classification
        }]);
      }

      console.log(`[useFileUpload] Análisis exitoso para ${file.name}:`, result.classification);
      return { ...result, success: true };
    } catch (error) {
      clearTimeout(timeoutId);
      
      let errorMessage = error.message;
      if (error.name === 'AbortError') {
        errorMessage = 'Tiempo de espera agotado (60s). El archivo puede ser muy grande.';
      }
      
      console.error(`[useFileUpload] Error analizando ${file.name}:`, errorMessage);
      return {
        success: false,
        classification: 'unknown',
        file_name: file.name,
        error: errorMessage
      };
    } finally {
      setIsProcessingFile(false);
    }
  }, []);

  const analyzeFiles = useCallback(async (files) => {
    setIsProcessingFile(true);
    const results = [];

    for (const fileObj of files) {
      try {
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === fileObj.id ? { ...f, status: 'analyzing' } : f
          )
        );

        const file = fileObj.file || fileObj;
        const result = await analyzeDocument(file);
        
        results.push({
          fileId: fileObj.id,
          fileName: fileObj.name || file.name,
          ...result
        });

        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === fileObj.id
              ? { ...f, status: 'analyzed', analysis: result }
              : f
          )
        );

      } catch (err) {
        console.error(`Error analizando ${fileObj.name}:`, err);
        
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === fileObj.id
              ? { ...f, status: 'error', error: err.message }
              : f
          )
        );
      }
    }

    setIsProcessingFile(false);

    if (onAnalysisComplete && results.length > 0) {
      onAnalysisComplete(results);
    }

    return results;
  }, [analyzeDocument, onAnalysisComplete]);

  const uploadFilesToCloud = useCallback(async (mensaje = '', empresaId = null) => {
    const formData = new FormData();
    uploadedFiles.forEach(f => formData.append('files', f.file));
    if (mensaje) formData.append('mensaje', mensaje);
    if (empresaId) formData.append('empresaId', empresaId);

    try {
      setIsUploadingDocuments(true);
      // Use backend URL from env or fallback to relative path (for Vercel rewrites)
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const apiUrl = `${backendUrl}/api/upload`;

      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData
      });

      const responseText = await response.text();
      let responseData;
      try {
        responseData = JSON.parse(responseText);
      } catch {
        responseData = { detail: responseText || 'Error de servidor' };
      }

      if (!response.ok) {
        throw new Error(responseData.detail || responseData.error || 'Error uploading files');
      }

      setUploadedFiles((prev) =>
        prev.map((f) => ({ ...f, status: 'uploaded' }))
      );

      return responseData;
    } catch (error) {
      console.error('Upload error:', error);
      setError(`Error subiendo archivos: ${error.message}`);
      return { success: false, error: error.message };
    } finally {
      setIsUploadingDocuments(false);
    }
  }, [uploadedFiles]);

  const removeFile = useCallback((fileId) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    setFileAnalysisResults((prev) => prev.filter((r) => r.fileId !== fileId));
    setExtractedDocumentContents((prev) => prev.filter((c) => c.fileId !== fileId));
  }, []);

  const clearAllFiles = useCallback(() => {
    setUploadedFiles([]);
    setAdditionalFiles([]);
    setFileAnalysisResults([]);
    setExtractedDocumentContents([]);
    setError(null);
  }, []);

  const getFileById = useCallback((fileId) => {
    return uploadedFiles.find((f) => f.id === fileId);
  }, [uploadedFiles]);

  const getAnalysisForFile = useCallback((fileId) => {
    return fileAnalysisResults.find((r) => r.fileId === fileId);
  }, [fileAnalysisResults]);

  return {
    uploadedFiles,
    additionalFiles,
    isProcessingFile,
    isUploadingDocuments,
    fileAnalysisResults,
    extractedDocumentContents,
    uploadProgress,
    error,

    handleFileSelect,
    analyzeDocument,
    analyzeFiles,
    uploadFilesToCloud,
    removeFile,
    clearAllFiles,
    getFileById,
    getAnalysisForFile,
    setUploadedFiles,
    setAdditionalFiles,
    setExtractedDocumentContents,
    clearError: () => setError(null),
  };
}

export default useFileUpload;
