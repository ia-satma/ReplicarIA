import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

const API_BASE = process.env.REACT_APP_BACKEND_URL
  ? `${process.env.REACT_APP_BACKEND_URL}/api`
  : '/api';

const FileIcon = ({ mimeType, isFolder, size = "small" }) => {
  const sizeClass = size === "small" ? "w-6 h-6" : "w-10 h-10";

  if (isFolder) {
    return (
      <svg className={`${sizeClass} text-yellow-400`} fill="currentColor" viewBox="0 0 24 24">
        <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
      </svg>
    );
  }

  const type = mimeType || '';
  if (type.includes('pdf')) {
    return (
      <svg className={`${sizeClass} text-red-400`} fill="currentColor" viewBox="0 0 24 24">
        <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z" />
      </svg>
    );
  }
  if (type.includes('word') || type.includes('document')) {
    return (
      <svg className={`${sizeClass} text-blue-400`} fill="currentColor" viewBox="0 0 24 24">
        <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z" />
      </svg>
    );
  }
  if (type.includes('sheet') || type.includes('excel')) {
    return (
      <svg className={`${sizeClass} text-green-400`} fill="currentColor" viewBox="0 0 24 24">
        <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z" />
      </svg>
    );
  }
  if (type.includes('image')) {
    return (
      <svg className={`${sizeClass} text-purple-400`} fill="currentColor" viewBox="0 0 24 24">
        <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" />
      </svg>
    );
  }
  return (
    <svg className={`${sizeClass} text-gray-400`} fill="currentColor" viewBox="0 0 24 24">
      <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z" />
    </svg>
  );
};

const StatusBadge = ({ status }) => {
  const statusConfig = {
    uploaded: { label: 'Subido', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
    processing: { label: 'Procesando', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
    ready: { label: 'Listo', color: 'bg-green-500/20 text-green-400 border-green-500/30' },
    indexed: { label: 'Indexado', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
    error: { label: 'Error', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
    archived: { label: 'Archivado', color: 'bg-slate-500/20 text-slate-400 border-slate-500/30' }
  };

  const config = statusConfig[status] || statusConfig.uploaded;

  return (
    <span className={`px-2 py-0.5 text-xs rounded-full border ${config.color}`}>
      {config.label}
    </span>
  );
};

const formatFileSize = (bytes) => {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('es-MX', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export default function KnowledgeRepository() {
  const { user, empresaId, isSuperAdmin, selectEmpresa } = useAuth();
  const [currentPath, setCurrentPath] = useState('/');
  const [folders, setFolders] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('list');
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [showNewFolderModal, setShowNewFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [stats, setStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [initializing, setInitializing] = useState(false);
  const [semanticMode, setSemanticMode] = useState(false);
  const [semanticResults, setSemanticResults] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [empresas, setEmpresas] = useState([]);

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('auth_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }, []);

  // Cargar lista de empresas si es admin
  useEffect(() => {
    if (isSuperAdmin) {
      const fetchEmpresas = async () => {
        try {
          const token = localStorage.getItem('auth_token');
          const response = await fetch(`${API_BASE}/admin/clientes?limit=100`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const data = await response.json();
            setEmpresas(data.clientes || []);
          }
        } catch (err) {
          console.error("Error loading empresas:", err);
        }
      };
      fetchEmpresas();
    }
  }, [isSuperAdmin]);

  const getUrl = useCallback((endpoint) => {
    const baseUrl = `${API_BASE}/knowledge${endpoint}`;
    if (empresaId) {
      const separator = baseUrl.includes('?') ? '&' : '?';
      return `${baseUrl}${separator}empresa_id=${empresaId}`;
    }
    return baseUrl;
  }, [empresaId]);



  const fetchStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(getUrl('/stats'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const text = await response.text();
        try {
          const data = text ? JSON.parse(text) : {};
          setStats(data);
        } catch {
          console.error('Error parsing stats response');
        }
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, [getUrl]);

  const browse = useCallback(async (path = '/') => {
    setLoading(true);
    setError(null);
    setSearchResults(null);
    setSearchQuery('');
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Sesión no iniciada. Por favor inicia sesión.');
      }

      const url = getUrl(`/browse?path=${encodeURIComponent(path)}`);
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const text = await response.text();
      let data;
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        data = { detail: text || 'Error de servidor' };
      }

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Error al cargar contenido');
      }

      setFolders(data.folders || []);
      setDocuments(data.documents || []);
      setCurrentPath(path);
      setSelectedItems(new Set());
    } catch (err) {
      setError(err.message || 'Error desconocido');
      setFolders([]);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [getUrl]);

  useEffect(() => {
    browse('/');
    fetchStats();
  }, [browse, fetchStats]);

  // Función de sincronización/actualización
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        browse(currentPath),
        fetchStats()
      ]);
    } finally {
      setRefreshing(false);
    }
  }, [browse, fetchStats, currentPath]);

  const handleSearch = useCallback(async (query) => {
    if (!query || query.length < 2) {
      setSearchResults(null);
      setSemanticResults(null);
      return;
    }

    setSearching(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(getUrl(`/search?q=${encodeURIComponent(query)}`), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json().catch(() => ({}));
        setSearchResults(data.documents || []);
      }
    } catch (err) {
      console.error('Error searching:', err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, [getUrl]);

  const handleSemanticSearch = useCallback(async () => {
    if (!searchQuery || searchQuery.length < 3) return;

    setSearching(true);
    setSemanticResults(null);
    try {
      const token = localStorage.getItem('auth_token');
      // Hybrid search es POST, el query param empresa_id no se soporta en backend por defecto en POST body, 
      // pero podríamos agregarlo a la URL si el backend lo leyera. 
      // NOTA: El endpoint hybrid_search en backend aún no acepta query param empresa_id explícito,
      // pero usa get_user_empresa_id. Si falla el init, fallará esto.
      // Asumiremos que init/upload es lo crítico ahora.
      const response = await fetch(`${API_BASE}/knowledge/hybrid_search`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: searchQuery, limit: 20 })
      });

      if (response.ok) {
        const data = await response.json().catch(() => ({}));
        setSemanticResults(data.results || []);
        setSearchResults(null);
      }
    } catch (err) {
      console.error('Error en búsqueda semántica:', err);
      setSemanticResults([]);
    } finally {
      setSearching(false);
    }
  }, [searchQuery]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      handleSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery, handleSearch]);

  const handleInitializeStructure = async () => {
    if (!window.confirm('¿Inicializar la estructura de carpetas predeterminada? Esto creará las carpetas estándar del repositorio.')) return;

    if (!empresaId && user?.role === 'super_admin') {
      if (!window.confirm('No hay empresa seleccionada. ¿Estás seguro de continuar? Puede fallar si no tienes contexto.')) return;
    }

    setInitializing(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(getUrl('/init'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || 'Error al inicializar estructura');
      }

      alert(`Estructura inicializada: ${data.total_created || 0} carpetas creadas, ${data.total_skipped || 0} ya existían.`);
      browse('/');
      fetchStats();
    } catch (err) {
      alert(err.message || 'Error desconocido');
    } finally {
      setInitializing(false);
    }
  };

  const handleFolderClick = (folder) => {
    browse(folder.path);
  };

  const handleBreadcrumbClick = (path) => {
    browse(path);
  };

  const getBreadcrumbs = () => {
    const parts = currentPath.split('/').filter(Boolean);
    const crumbs = [{ name: 'Inicio', path: '/' }];
    let currentBreadcrumbPath = '';

    parts.forEach(part => {
      currentBreadcrumbPath += `/${part}`;
      crumbs.push({ name: part, path: currentBreadcrumbPath });
    });

    return crumbs;
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(getUrl('/folders'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          path: currentPath,
          name: newFolderName.trim()
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al crear carpeta');
      }

      setShowNewFolderModal(false);
      setNewFolderName('');
      browse(currentPath);
      fetchStats();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      const token = localStorage.getItem('auth_token');
      const totalFiles = files.length;
      let uploaded = 0;

      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('path', currentPath);

        const response = await fetch(getUrl('/upload'), {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Error al subir ${file.name}`);
        }

        uploaded++;
        setUploadProgress(Math.round((uploaded / totalFiles) * 100));
      }

      browse(currentPath);
      fetchStats();
    } catch (err) {
      alert(err.message);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    handleFileUpload(files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDownload = async (doc) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(getUrl(`/download/${doc.id}`), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Error al descargar');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDelete = async (doc) => {
    if (!window.confirm(`¿Eliminar "${doc.filename}"?`)) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(getUrl(`/documents/${doc.id}`), {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Error al eliminar');

      browse(currentPath);
      fetchStats();
    } catch (err) {
      alert(err.message);
    }
  };

  const toggleSelection = (id) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedItems(newSelected);
  };

  const displayDocuments = searchResults !== null ? searchResults : documents;
  const isSearchMode = searchResults !== null;
  const isSemanticMode = semanticResults !== null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl overflow-hidden">
          {stats && (
            <div className="px-6 py-3 bg-slate-900/50 border-b border-slate-700/30">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="text-slate-400">Documentos:</span>
                    <span className="text-white font-medium">{stats.total_documents || 0}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                    </svg>
                    <span className="text-slate-400">Tamaño Total:</span>
                    <span className="text-white font-medium">{formatFileSize(stats.total_size_bytes)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                    <span className="text-slate-400">Carpetas:</span>
                    <span className="text-white font-medium">{stats.total_folders || 0}</span>
                  </div>
                  {stats.last_upload && (
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-slate-400">Última carga:</span>
                      <span className="text-white font-medium">{formatDate(stats.last_upload)}</span>
                    </div>
                  )}
                </div>
                {stats.documents_by_status && Object.keys(stats.documents_by_status).length > 0 && (
                  <div className="flex items-center gap-2">
                    {Object.entries(stats.documents_by_status).map(([status, count]) => (
                      <div key={status} className="flex items-center gap-1">
                        <StatusBadge status={status} />
                        <span className="text-white text-xs font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="p-6 border-b border-slate-700/50">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white">Repositorio de Conocimiento</h1>
                  <p className="text-slate-400 text-sm">Gestión documental corporativa</p>
                </div>

                {isSuperAdmin && (
                  <div className="ml-6">
                    <select
                      value={empresaId || ''}
                      onChange={(e) => selectEmpresa(e.target.value)}
                      className="bg-slate-700/50 border border-slate-600 text-emerald-400 text-sm font-medium rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block w-64 p-2"
                    >
                      <option value="" className="text-slate-400">-- Seleccionar Empresa --</option>
                      {empresas.map((emp) => (
                        <option key={emp.id} value={emp.id} className="text-white">
                          {emp.nombre || emp.razon_social}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                <div className="relative flex items-center gap-2">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && semanticMode && handleSemanticSearch()}
                    placeholder={semanticMode ? "Buscar por significado..." : "Buscar documentos..."}
                    className="w-64 px-4 py-2 pl-10 rounded-lg bg-slate-700/50 border border-slate-600 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
                  />
                  <svg className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  {searching && (
                    <div className="absolute right-10 top-1/2 -translate-y-1/2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-500"></div>
                    </div>
                  )}
                  <button
                    onClick={() => setSemanticMode(!semanticMode)}
                    className={`p-2 rounded-lg transition-colors ${semanticMode
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/50'
                      }`}
                    title={semanticMode ? 'Modo semántico activo' : 'Activar búsqueda semántica'}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </button>
                  {semanticMode && (
                    <button
                      onClick={handleSemanticSearch}
                      disabled={searching || !searchQuery}
                      className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                    >
                      Buscar IA
                    </button>
                  )}
                </div>

                {/* Botón de Sincronización/Actualización */}
                <button
                  onClick={handleRefresh}
                  disabled={refreshing || loading}
                  className="p-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:from-cyan-500 hover:to-blue-500 transition-all disabled:opacity-50"
                  title="Sincronizar / Actualizar datos"
                >
                  {refreshing ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  )}
                </button>

                <button
                  onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                  className="p-2 rounded-lg bg-slate-700/50 text-slate-300 hover:bg-slate-600/50 transition-colors"
                  title={viewMode === 'grid' ? 'Vista lista' : 'Vista cuadrícula'}
                >
                  {viewMode === 'grid' ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                    </svg>
                  )}
                </button>

                <button
                  onClick={() => setShowNewFolderModal(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700/50 text-slate-300 hover:bg-slate-600/50 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                  </svg>
                  Nueva Carpeta
                </button>

                <button
                  onClick={handleInitializeStructure}
                  disabled={initializing}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700/50 text-slate-300 hover:bg-slate-600/50 transition-colors disabled:opacity-50"
                  title="Inicializar estructura de carpetas predeterminada"
                >
                  {initializing ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  )}
                  Inicializar Estructura
                </button>

                <label className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-500 hover:to-teal-500 transition-all cursor-pointer">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Subir Archivos
                  <input
                    type="file"
                    multiple
                    className="hidden"
                    onChange={(e) => handleFileUpload(Array.from(e.target.files))}
                  />
                </label>
              </div>
            </div>

            {!isSearchMode && (
              <nav className="flex items-center gap-2 text-sm">
                {getBreadcrumbs().map((crumb, index) => (
                  <React.Fragment key={crumb.path}>
                    {index > 0 && <span className="text-slate-500">/</span>}
                    <button
                      onClick={() => handleBreadcrumbClick(crumb.path)}
                      className={`px-2 py-1 rounded hover:bg-slate-700/50 transition-colors ${index === getBreadcrumbs().length - 1
                        ? 'text-emerald-400 font-medium'
                        : 'text-slate-400 hover:text-white'
                        }`}
                    >
                      {crumb.name}
                    </button>
                  </React.Fragment>
                ))}
              </nav>
            )}
            {isSearchMode && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-slate-400">Resultados de búsqueda para:</span>
                <span className="text-emerald-400 font-medium">"{searchQuery}"</span>
                <span className="text-slate-500">({searchResults.length} encontrados)</span>
                <button
                  onClick={() => { setSearchQuery(''); setSearchResults(null); }}
                  className="ml-2 text-slate-400 hover:text-white transition-colors"
                >
                  Limpiar
                </button>
              </div>
            )}
            {isSemanticMode && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-purple-400">Búsqueda semántica:</span>
                <span className="text-white font-medium">"{searchQuery}"</span>
                <span className="text-slate-500">({semanticResults.length} resultados)</span>
                <button
                  onClick={() => { setSearchQuery(''); setSemanticResults(null); }}
                  className="ml-2 text-slate-400 hover:text-white transition-colors"
                >
                  Limpiar
                </button>
              </div>
            )}
          </div>

          {isSemanticMode && semanticResults.length > 0 && (
            <div className="p-6 border-b border-slate-700/50 bg-purple-900/10">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Resultados de Búsqueda Semántica
              </h3>
              <div className="space-y-3">
                {semanticResults.map((result, idx) => (
                  <div key={idx} className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 hover:border-purple-500/50 transition-colors">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium truncate">{result.filename || result.title || 'Documento'}</p>
                        <p className="text-slate-400 text-sm mt-1 line-clamp-2">
                          {result.contenido?.substring(0, 250) || result.content?.substring(0, 250) || 'Sin contenido disponible'}...
                        </p>
                        {result.categoria && (
                          <span className="inline-block mt-2 px-2 py-1 bg-slate-700/50 text-slate-300 text-xs rounded">
                            {result.categoria}
                          </span>
                        )}
                      </div>
                      <div className="text-right flex-shrink-0">
                        <div className="text-purple-400 font-semibold">
                          {((result.similarity || result.score || 0) * 100).toFixed(1)}%
                        </div>
                        <p className="text-slate-500 text-xs">similitud</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div
            className={`p-6 min-h-[400px] ${dragOver ? 'bg-emerald-900/20 border-2 border-dashed border-emerald-500' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            {uploading && (
              <div className="mb-4 p-4 bg-slate-700/50 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white text-sm">Subiendo archivos...</span>
                  <span className="text-emerald-400 text-sm font-medium">{uploadProgress}%</span>
                </div>
                <div className="h-2 bg-slate-600 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
              </div>
            ) : error ? (
              <div className="text-center py-20">
                <p className="text-red-400 mb-4">{error}</p>
                <button
                  onClick={() => browse(currentPath)}
                  className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600"
                >
                  Reintentar
                </button>
              </div>
            ) : folders.length === 0 && displayDocuments.length === 0 ? (
              <div className="text-center py-20">
                <div className="w-20 h-20 mx-auto mb-4 text-slate-600">
                  <svg fill="currentColor" viewBox="0 0 24 24">
                    <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
                  </svg>
                </div>
                <p className="text-slate-400 text-lg mb-2">Carpeta vacía</p>
                <p className="text-slate-500 text-sm mb-4">Arrastra archivos aquí o usa el botón "Subir Archivos"</p>
                {currentPath === '/' && (
                  <button
                    onClick={handleInitializeStructure}
                    disabled={initializing}
                    className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg hover:from-emerald-500 hover:to-teal-500 transition-all disabled:opacity-50"
                  >
                    {initializing ? 'Inicializando...' : 'Inicializar Estructura de Carpetas'}
                  </button>
                )}
              </div>
            ) : viewMode === 'grid' ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {!isSearchMode && folders.map(folder => (
                  <div
                    key={folder.id}
                    onClick={() => handleFolderClick(folder)}
                    className="group p-4 rounded-xl bg-slate-700/30 hover:bg-slate-700/50 cursor-pointer transition-all border border-transparent hover:border-slate-600"
                  >
                    <div className="flex flex-col items-center text-center">
                      <FileIcon isFolder={true} size="large" />
                      <span className="mt-2 text-sm text-white truncate w-full">{folder.name}</span>
                      <span className="text-xs text-slate-500">{formatDate(folder.created_at)}</span>
                    </div>
                  </div>
                ))}

                {displayDocuments.map(doc => (
                  <div
                    key={doc.id}
                    className="group relative p-4 rounded-xl bg-slate-700/30 hover:bg-slate-700/50 transition-all border border-transparent hover:border-slate-600"
                  >
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                      <button
                        onClick={() => handleDownload(doc)}
                        className="p-1 bg-slate-600 rounded hover:bg-emerald-600 transition-colors"
                        title="Descargar"
                      >
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(doc)}
                        className="p-1 bg-slate-600 rounded hover:bg-red-600 transition-colors"
                        title="Eliminar"
                      >
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                    <div className="flex flex-col items-center text-center">
                      <FileIcon mimeType={doc.mime_type} size="large" />
                      <span className="mt-2 text-sm text-white truncate w-full" title={doc.filename}>{doc.filename}</span>
                      <span className="text-xs text-slate-500">{formatFileSize(doc.size_bytes)}</span>
                      <div className="mt-1">
                        <StatusBadge status={doc.status} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-slate-400 text-sm border-b border-slate-700">
                      <th className="pb-3 font-medium">Nombre</th>
                      <th className="pb-3 font-medium">Estado</th>
                      <th className="pb-3 font-medium">Tamaño</th>
                      <th className="pb-3 font-medium">Fecha</th>
                      {isSearchMode && <th className="pb-3 font-medium">Ubicación</th>}
                      <th className="pb-3 font-medium">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {!isSearchMode && folders.map(folder => (
                      <tr
                        key={folder.id}
                        onClick={() => handleFolderClick(folder)}
                        className="border-b border-slate-700/50 hover:bg-slate-700/30 cursor-pointer"
                      >
                        <td className="py-3">
                          <div className="flex items-center gap-3">
                            <FileIcon isFolder={true} size="small" />
                            <span className="text-white">{folder.name}</span>
                          </div>
                        </td>
                        <td className="py-3 text-slate-400">-</td>
                        <td className="py-3 text-slate-400">-</td>
                        <td className="py-3 text-slate-400">{formatDate(folder.created_at)}</td>
                        {isSearchMode && <td className="py-3 text-slate-400">-</td>}
                        <td className="py-3">-</td>
                      </tr>
                    ))}
                    {displayDocuments.map(doc => (
                      <tr key={doc.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="py-3">
                          <div className="flex items-center gap-3">
                            <FileIcon mimeType={doc.mime_type} size="small" />
                            <span className="text-white">{doc.filename}</span>
                          </div>
                        </td>
                        <td className="py-3">
                          <StatusBadge status={doc.status} />
                        </td>
                        <td className="py-3 text-slate-400">{formatFileSize(doc.size_bytes)}</td>
                        <td className="py-3 text-slate-400">{formatDate(doc.created_at)}</td>
                        {isSearchMode && <td className="py-3 text-slate-400 text-sm">{doc.path}</td>}
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleDownload(doc)}
                              className="p-1 text-slate-400 hover:text-emerald-400 transition-colors"
                              title="Descargar"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                            </button>
                            <button
                              onClick={() => handleDelete(doc)}
                              className="p-1 text-slate-400 hover:text-red-400 transition-colors"
                              title="Eliminar"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {showNewFolderModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md border border-slate-700 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-4">Nueva Carpeta</h3>
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Nombre de la carpeta"
              className="w-full px-4 py-3 rounded-lg bg-slate-700/50 border border-slate-600 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 mb-4"
              onKeyPress={(e) => e.key === 'Enter' && handleCreateFolder()}
              autoFocus
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setShowNewFolderModal(false); setNewFolderName(''); }}
                className="px-4 py-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateFolder}
                disabled={!newFolderName.trim()}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-500 hover:to-teal-500 transition-all disabled:opacity-50"
              >
                Crear
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
