import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const BibliotecaChat = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [documentos, setDocumentos] = useState([]);
  const [documentosTotal, setDocumentosTotal] = useState(0);
  const [documentosPendientes, setDocumentosPendientes] = useState(0);
  const [categoriaFiltro, setCategoriaFiltro] = useState('');
  const [loadingDocumentos, setLoadingDocumentos] = useState(false);
  const [reingestando, setReingestando] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadGreeting();
    loadStats();
    loadDocumentos();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadGreeting = async () => {
    try {
      const response = await api.get('/api/kb/chat/greeting');
      setMessages([{
        id: '1',
        role: 'assistant',
        content: response.data.greeting,
        timestamp: new Date()
      }]);
    } catch (error) {
      setMessages([{
        id: '1',
        role: 'assistant',
        content: `¡Hola! Soy Bibliotecar.IA 📚 Tu aliada para mantener actualizado el conocimiento de Revisar.IA.

Puedo ayudarte a:
• 📊 Ver el estado del acervo
• 📥 Cargar nuevos documentos
• 🔍 Buscar información específica
• 🔔 Ver solicitudes pendientes`,
        timestamp: new Date()
      }]);
    }
  };

  const loadStats = async () => {
    try {
      const response = await api.get('/api/kb/dashboard');
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const loadDocumentos = async (categoria = '') => {
    setLoadingDocumentos(true);
    try {
      const params = categoria ? `?categoria=${categoria}&limit=20` : '?limit=20';
      const response = await api.get(`/kb/documentos-lista${params}`);
      setDocumentos(response.data.documentos || []);
      setDocumentosTotal(response.data.total || 0);
      setDocumentosPendientes(response.data.pendientes || 0);
    } catch (error) {
      console.error('Error loading documentos:', error);
      setDocumentos([]);
    } finally {
      setLoadingDocumentos(false);
    }
  };

  const handleCategoriaFiltro = (categoria) => {
    setCategoriaFiltro(categoria);
    loadDocumentos(categoria);
  };

  const handleReingest = async (documentoId) => {
    if (reingestando) return;
    setReingestando(documentoId);
    try {
      const response = await api.post(`/kb/reingest/${documentoId}`);
      if (response.data.success) {
        const assistantMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `🔄 Documento reingestado exitosamente.\n${response.data.message}`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
        loadDocumentos(categoriaFiltro);
        loadStats();
      }
    } catch (error) {
      console.error('Error reingesting:', error);
      const errorMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ Error al reingestar documento: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setReingestando(null);
    }
  };

  const getDocTypeIcon = (tipo) => {
    const tipoLower = (tipo || '').toLowerCase();
    if (tipoLower.includes('pdf')) return '📄';
    if (tipoLower.includes('doc')) return '📑';
    if (tipoLower.includes('xls') || tipoLower.includes('xlsx')) return '📊';
    if (tipoLower.includes('json')) return '📋';
    if (tipoLower.includes('csv')) return '📈';
    if (tipoLower.includes('txt') || tipoLower.includes('md')) return '📝';
    return '📄';
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await api.post('/api/kb/chat', {
        message: inputValue,
        session_id: sessionId
      });

      const data = response?.data || {};

      if (data.session_id) {
        setSessionId(data.session_id);
      }

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || data.message || 'Sin respuesta del servidor',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      loadStats();
    } catch (error) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Hubo un error al procesar tu mensaje. Por favor intenta de nuevo.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;
    
    setIsLoading(true);
    const file = files[0];
    
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: `📄 Analizando archivo: ${file.name}`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadResponse = await api.post('/api/kb/upload-file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (uploadResponse.data.success) {
        const { extracted_text, analysis_success, filename, rag_processed, chunks_created, documento_id, pcloud_uploaded, pcloud_link } = uploadResponse.data;
        
        let responseContent = '';
        if (rag_processed && chunks_created > 0) {
          const textPreview = extracted_text.length > 500 
            ? extracted_text.substring(0, 500) + '...' 
            : extracted_text;
          
          let storageInfo = `- Chunks RAG generados: **${chunks_created}**`;
          if (pcloud_uploaded) {
            storageInfo += `\n- Respaldado en pCloud`;
            if (pcloud_link) {
              storageInfo += ` ([ver enlace](${pcloud_link}))`;
            }
          }
          
          responseContent = `✅ **Documento "${filename}" procesado y guardado exitosamente**\n\n` +
            `📊 **Resumen del procesamiento:**\n` +
            `- ID del documento: \`${documento_id}\`\n` +
            `${storageInfo}\n` +
            `- Caracteres extraídos: ${extracted_text.length}\n\n` +
            `📄 **Vista previa del contenido:**\n\n` +
            `\`\`\`\n${textPreview}\n\`\`\`\n\n` +
            `El documento ya está disponible para consultas RAG.`;
        } else if (analysis_success && extracted_text) {
          const textPreview = extracted_text.length > 500 
            ? extracted_text.substring(0, 500) + '...' 
            : extracted_text;
          
          responseContent = `⚠️ **Documento "${filename}" analizado pero no indexado**\n\n` +
            `El texto se extrajo correctamente (${extracted_text.length} caracteres), pero hubo un problema al guardarlo en el RAG.\n\n` +
            `📄 **Vista previa:**\n\`\`\`\n${textPreview}\n\`\`\`\n\n` +
            `Por favor intenta nuevamente o contacta soporte.`;
        } else {
          responseContent = `⚠️ El archivo "${filename}" se subió correctamente, pero no se pudo extraer texto del documento.\n\n` +
            `Esto puede ocurrir con PDFs escaneados o archivos protegidos. ¿Deseas intentar con otro archivo?`;
        }
        
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: responseContent,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
        loadStats();
        loadDocumentos(categoriaFiltro);
      }
    } catch (error) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Error al procesar el archivo: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const categoriasDisponibles = [
    { value: '', label: 'Todas' },
    { value: 'marco_legal', label: 'Marco Legal' },
    { value: 'jurisprudencias', label: 'Jurisprudencias' },
    { value: 'criterios_sat', label: 'Criterios SAT' },
    { value: 'catalogos_sat', label: 'Catálogos SAT' },
    { value: 'casos_referencia', label: 'Casos Ref.' },
    { value: 'glosarios', label: 'Glosarios' },
    { value: 'plantillas', label: 'Plantillas' }
  ];

  const quickActions = [
    { label: '📊 Estado del acervo', query: 'estado' },
    { label: '🔔 Ver alertas', query: 'alertas' },
    { label: '📜 Versiones de leyes', query: 'versiones' },
    { label: '📥 Cargar documento', action: () => fileInputRef.current?.click() }
  ];

  const getStateIcon = (estado) => {
    switch (estado) {
      case 'completo': return '🟢';
      case 'actualizable': return '🟡';
      case 'incompleto': return '🟠';
      case 'critico': return '🔴';
      default: return '⚪';
    }
  };

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Sidebar */}
      <div className="w-80 bg-slate-800 border-r border-slate-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-slate-700 bg-gradient-to-r from-purple-600/20 to-indigo-600/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
              <span className="text-xl">📚</span>
            </div>
            <div>
              <h1 className="font-bold text-lg text-white">Bibliotecar.IA</h1>
              <p className="text-purple-300 text-sm">Dra. Elena Vázquez</p>
            </div>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="p-4 space-y-4 overflow-y-auto flex-1">
            <h2 className="font-semibold text-slate-300 flex items-center gap-2 text-sm">
              <span>🧠</span> Estado del Conocimiento
            </h2>

            {/* Completeness */}
            <div className="bg-slate-700/50 rounded-lg p-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-400">Completitud</span>
                <span className="font-semibold text-white">{Math.round(stats.completitud_general * 100)}%</span>
              </div>
              <div className="w-full bg-slate-600 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-indigo-500 h-2 rounded-full transition-all"
                  style={{ width: `${stats.completitud_general * 100}%` }}
                />
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-blue-900/30 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-blue-400">{stats.total_documentos}</div>
                <div className="text-xs text-blue-300">Documentos</div>
              </div>
              <div className="bg-green-900/30 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-green-400">{stats.total_chunks}</div>
                <div className="text-xs text-green-300">Chunks RAG</div>
              </div>
            </div>

            {/* Categories */}
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-400 uppercase">Categorías</h3>
              {stats.categorias?.map((cat, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className="text-slate-300">
                    {getStateIcon(cat.estado)} {cat.icono} {cat.nombre}
                  </span>
                  <span className="text-slate-500">{Math.round(cat.completitud * 100)}%</span>
                </div>
              ))}
            </div>

            {/* Documentos del Acervo */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-slate-400 uppercase flex items-center gap-1">
                  📚 Documentos del Acervo
                  {documentosPendientes > 0 && (
                    <span className="bg-amber-500 text-slate-900 text-xs px-1.5 py-0.5 rounded-full font-bold animate-pulse">
                      {documentosPendientes}
                    </span>
                  )}
                </h3>
                <span className="text-xs text-slate-500">{documentosTotal} total</span>
              </div>
              
              {/* Filtro por categoría */}
              <select
                value={categoriaFiltro}
                onChange={(e) => handleCategoriaFiltro(e.target.value)}
                className="w-full px-2 py-1.5 bg-slate-700 border border-slate-600 rounded text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-purple-500"
              >
                {categoriasDisponibles.map((cat) => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
              
              {/* Lista de documentos */}
              <div className="max-h-48 overflow-y-auto space-y-1 pr-1 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800">
                {loadingDocumentos ? (
                  <div className="text-center py-3 text-slate-500 text-xs">
                    <div className="animate-spin inline-block w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full"></div>
                  </div>
                ) : documentos.length === 0 ? (
                  <div className="text-center py-3 text-slate-500 text-xs">
                    No hay documentos
                  </div>
                ) : (
                  documentos.map((doc) => (
                    <div 
                      key={doc.id} 
                      className="bg-slate-700/50 rounded p-2 hover:bg-slate-700 transition-colors group"
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-base flex-shrink-0">{getDocTypeIcon(doc.tipo_archivo)}</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs text-slate-200 truncate font-medium" title={doc.nombre}>
                            {doc.nombre}
                          </div>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={`text-xs ${doc.estado === 'procesado' ? 'text-green-400' : 'text-amber-400'}`}>
                              {doc.estado === 'procesado' ? '✅' : '⏳'} {doc.estado}
                            </span>
                            <span className="text-xs text-slate-500">
                              {doc.chunks} chunks
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleReingest(doc.id)}
                          disabled={reingestando === doc.id}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded bg-slate-600 hover:bg-purple-600 text-slate-300 hover:text-white transition-all disabled:opacity-50"
                          title="Reingestar documento"
                        >
                          {reingestando === doc.id ? (
                            <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>
                          ) : (
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                          )}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
              
              {documentosTotal > 20 && (
                <div className="text-center text-xs text-slate-500">
                  Mostrando 20 de {documentosTotal}
                </div>
              )}
            </div>

            {/* Alerts */}
            {stats.alertas?.length > 0 && (
              <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-3">
                <div className="flex items-center gap-2 text-amber-400 mb-2">
                  <span>⚠️</span>
                  <span className="text-sm font-medium">{stats.alertas.length} alertas</span>
                </div>
                {stats.alertas.slice(0, 2).map((alert, idx) => (
                  <p key={idx} className="text-xs text-amber-300/80 mb-1">{alert.mensaje}</p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Quick Actions */}
        <div className="p-4 border-t border-slate-700 space-y-2">
          {quickActions.map((action, idx) => (
            <button 
              key={idx}
              onClick={() => action.action ? action.action() : setInputValue(action.query)}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-700 text-sm text-slate-300 transition-colors"
            >
              {action.label}
            </button>
          ))}
        </div>

        {/* Back Button */}
        <div className="p-4 border-t border-slate-700">
          <button 
            onClick={() => navigate('/')}
            className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors"
          >
            ← Volver al Dashboard
          </button>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-slate-900">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center mr-3 flex-shrink-0">
                  <span>📚</span>
                </div>
              )}
              <div className={`max-w-2xl rounded-2xl px-4 py-3 ${
                message.role === 'user' 
                  ? 'bg-purple-600 text-white rounded-br-md' 
                  : 'bg-slate-800 text-slate-200 rounded-bl-md'
              }`}>
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-3 text-slate-400">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
                <span>📚</span>
              </div>
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-700 bg-slate-800 p-4">
          <div className="flex items-center gap-3 max-w-4xl mx-auto">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 rounded-lg hover:bg-slate-700 text-slate-400 transition-colors"
              title="Subir documento"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            </button>
            
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Pregunta sobre el conocimiento o sube un documento..."
              className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              className="p-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.xlsx,.json,.csv,.txt,.md"
            onChange={(e) => handleFileUpload(e.target.files)}
            className="hidden"
          />
        </div>
      </div>
    </div>
  );
};

export default BibliotecaChat;
