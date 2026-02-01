import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Componente principal del Chatbot de Onboarding
const ChatbotArchivo = () => {
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const { user, empresaId, isSuperAdmin, token } = useAuth();

  // Estado del chat
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Estado del onboarding
  const [step, setStep] = useState('select_type'); // select_type, upload_docs, enter_data, confirm, complete
  const [entityType, setEntityType] = useState(null); // 'cliente' o 'proveedor'
  const [extractedData, setExtractedData] = useState({});
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [emailContacto, setEmailContacto] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [error, setError] = useState(null);

  // Scroll automático al final de los mensajes
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Agregar mensaje al chat
  const addMessage = useCallback((text, sender = 'bot', options = {}) => {
    setMessages(prev => [...prev, {
      id: Date.now(),
      text,
      sender,
      timestamp: new Date(),
      ...options
    }]);
  }, []);

  // Mensaje inicial
  useEffect(() => {
    const timer = setTimeout(() => {
      addMessage(`Hola! Soy el Asistente de Archivo de REVISAR.IA.

Puedo ayudarte a dar de alta nuevos **clientes** o **proveedores** de forma inteligente.

**Como funciona?**
1. Sube los documentos que tengas (contratos, facturas, CSF, etc.)
2. Dame un email de contacto
3. Analizare los documentos y extraere los datos automaticamente
4. Confirmas y creamos el registro

**Que quieres dar de alta hoy?**`, 'bot', {
        suggestions: [
          { text: 'Registrar cliente', value: 'cliente' },
          { text: 'Registrar proveedor', value: 'proveedor' },
        ]
      });
    }, 500);
    return () => clearTimeout(timer);
  }, [addMessage]);

  // Seleccionar tipo de entidad
  const handleSelectEntityType = useCallback((tipo) => {
    setEntityType(tipo);
    addMessage(`Quiero dar de alta un ${tipo}`, 'user');

    setTimeout(() => {
      if (tipo === 'cliente') {
        addMessage(`Perfecto, vamos a dar de alta un nuevo **cliente**.

Para clientes los requisitos son minimos:
- Nombre de la empresa
- Email de contacto
- RFC (opcional)

Puedes subir documentos para extraer datos automaticamente, o ingresar los datos manualmente.

**Que prefieres hacer?**`, 'bot', {
          suggestions: [
            { text: 'Subir documentos', value: 'upload' },
            { text: 'Ingresar datos manualmente', value: 'manual' },
          ]
        });
      } else {
        addMessage(`Perfecto, vamos a dar de alta un nuevo **proveedor**.

Para proveedores se requiere validacion fiscal:
- RFC obligatorio
- Constancia de Situacion Fiscal
- Verificacion en Lista 69-B del SAT

Sube los documentos del proveedor para analizarlos.`, 'bot', {
          suggestions: [
            { text: 'Subir documentos', value: 'upload' },
          ]
        });
      }
      setStep('upload_docs');
    }, 300);
  }, [addMessage]);

  // Manejar archivo seleccionado
  const handleFileChange = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setIsLoading(true);
    addMessage(`Subiendo ${files.length} archivo(s): ${files.map(f => f.name).join(', ')}`, 'user');
    addMessage('Analizando documentos con IA...', 'bot');

    const newFiles = [];
    const allExtracted = {};

    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/chat/archivo/analyze-document', {
          method: 'POST',
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          body: formData
        });

        const result = await response.json();

        if (response.ok && result.success !== false) {
          newFiles.push({
            id: Date.now() + Math.random(),
            name: file.name,
            status: 'analyzed',
            result
          });

          // Extraer datos del resultado
          if (result.extracted_data) {
            Object.assign(allExtracted, result.extracted_data);
          }
          if (result.rfc) allExtracted.rfc = result.rfc;
          if (result.razon_social) allExtracted.razon_social = result.razon_social;
          if (result.nombre) allExtracted.nombre = result.nombre;
          if (result.direccion) allExtracted.direccion = result.direccion;
          if (result.regimen_fiscal) allExtracted.regimen_fiscal = result.regimen_fiscal;
        } else {
          newFiles.push({
            id: Date.now() + Math.random(),
            name: file.name,
            status: 'error',
            error: result.detail || 'Error al analizar'
          });
        }
      } catch (err) {
        newFiles.push({
          id: Date.now() + Math.random(),
          name: file.name,
          status: 'error',
          error: err.message
        });
      }
    }

    setUploadedFiles(prev => [...prev, ...newFiles]);

    if (Object.keys(allExtracted).length > 0) {
      setExtractedData(prev => ({ ...prev, ...allExtracted }));

      const datosMsg = Object.entries(allExtracted)
        .filter(([k, v]) => v)
        .map(([k, v]) => `- **${k}:** ${v}`)
        .join('\n');

      addMessage(`Datos extraidos automaticamente:\n\n${datosMsg}\n\nPor favor proporciona un email de contacto para continuar.`, 'bot');
      setStep('enter_data');
    } else {
      addMessage('No se pudieron extraer datos automaticamente. Por favor ingresa los datos manualmente.\n\nEscribe el nombre de la empresa:', 'bot');
      setStep('enter_data');
    }

    setIsLoading(false);
    event.target.value = '';
  };

  // Manejar envío de mensaje
  const handleSendMessage = useCallback(() => {
    if (!inputValue.trim() || isLoading) return;

    const message = inputValue.trim();
    setInputValue('');
    addMessage(message, 'user');

    // Procesar según el paso actual
    if (step === 'enter_data') {
      // Detectar email
      const emailMatch = message.match(/[^\s@]+@[^\s@]+\.[^\s@]+/);
      if (emailMatch) {
        setEmailContacto(emailMatch[0]);
        addMessage(`Email registrado: ${emailMatch[0]}`, 'bot');
        setShowConfirmModal(true);
        setStep('confirm');
        return;
      }

      // Detectar RFC
      const rfcMatch = message.match(/[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}/i);
      if (rfcMatch) {
        setExtractedData(prev => ({ ...prev, rfc: rfcMatch[0].toUpperCase() }));
        addMessage(`RFC registrado: ${rfcMatch[0].toUpperCase()}`, 'bot');
      }

      // Si no hay nombre, usar el mensaje como nombre
      if (!extractedData.nombre && !extractedData.razon_social && !emailMatch && !rfcMatch) {
        setExtractedData(prev => ({
          ...prev,
          nombre: message,
          razon_social: message
        }));
        addMessage(`Nombre registrado: ${message}\n\nAhora proporciona el email de contacto:`, 'bot');
      }
    }
  }, [inputValue, isLoading, step, addMessage, extractedData]);

  // Manejar sugerencias
  const handleSuggestionClick = useCallback((suggestion) => {
    const value = suggestion.value || suggestion.text;

    if (value === 'cliente' || value === 'proveedor') {
      handleSelectEntityType(value);
    } else if (value === 'upload') {
      fileInputRef.current?.click();
    } else if (value === 'manual') {
      addMessage('Ingresar datos manualmente', 'user');
      addMessage('Escribe el nombre o razon social de la empresa:', 'bot');
      setStep('enter_data');
    } else if (value === 'dashboard') {
      navigate('/dashboard');
    } else if (value === 'nuevo') {
      // Reiniciar
      setMessages([]);
      setStep('select_type');
      setEntityType(null);
      setExtractedData({});
      setUploadedFiles([]);
      setEmailContacto('');
      setShowConfirmModal(false);
    }
  }, [handleSelectEntityType, addMessage, navigate]);

  // Confirmar y crear entidad
  const handleConfirm = async () => {
    setIsLoading(true);
    setError(null);
    addMessage(`Creando ${entityType}...`, 'bot');

    try {
      const currentEmpresaId = empresaId || localStorage.getItem('selected_empresa_id');

      const response = await fetch('/api/archivo/crear-entidad', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          tipo: entityType || 'cliente',
          datos: extractedData,
          email_contacto: emailContacto || extractedData.email || '',
          archivos_ids: [],
          empresa_id: currentEmpresaId
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Error del servidor (${response.status})`);
      }

      setShowConfirmModal(false);
      setStep('complete');

      const displayName = extractedData.razon_social || extractedData.nombre || 'Entidad';

      addMessage(`**${entityType === 'proveedor' ? 'Proveedor' : 'Cliente'} creado exitosamente!**

**${displayName}**
RFC: ${extractedData.rfc || 'N/A'}

- Registro creado en el sistema
- Documentos guardados
${emailContacto ? `- Se enviara email de bienvenida a ${emailContacto}` : ''}

Que deseas hacer ahora?`, 'bot', {
        suggestions: [
          { text: 'Dar de alta otro', value: 'nuevo' },
          { text: 'Ir al Dashboard', value: 'dashboard' },
        ]
      });

    } catch (err) {
      setError(err.message);
      addMessage(`Error creando ${entityType}: ${err.message}`, 'bot');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Sidebar */}
      <aside className="hidden lg:block w-80 bg-black/30 backdrop-blur-sm border-r border-white/10 overflow-y-auto">
        <div className="p-4">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-xl">
              📁
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-100">ARCHIVO</h2>
              <p className="text-xs text-gray-400">Asistente de Onboarding</p>
            </div>
          </div>

          {entityType && (
            <div className="mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
              <p className="text-sm text-gray-300">
                Registrando: <span className="font-semibold text-indigo-400">
                  {entityType === 'cliente' ? 'Cliente' : 'Proveedor'}
                </span>
              </p>
            </div>
          )}

          {/* Archivos subidos */}
          {uploadedFiles.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Archivos</h3>
              <div className="space-y-2">
                {uploadedFiles.map(file => (
                  <div key={file.id} className="p-2 bg-white/5 rounded text-xs">
                    <span className={file.status === 'error' ? 'text-red-400' : 'text-green-400'}>
                      {file.status === 'error' ? '✗' : '✓'}
                    </span>
                    <span className="ml-2 text-gray-300">{file.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Datos extraídos */}
          {Object.keys(extractedData).length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Datos</h3>
              <div className="space-y-1 text-xs text-gray-400">
                {Object.entries(extractedData).filter(([k,v]) => v).map(([key, val]) => (
                  <div key={key}>
                    <span className="text-gray-500">{key}:</span> {val}
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={() => handleSuggestionClick({ value: 'nuevo' })}
            className="w-full mt-4 px-4 py-2 text-sm text-gray-400 hover:text-gray-200 hover:bg-white/10 rounded-lg transition-colors"
          >
            🔄 Empezar de nuevo
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Header móvil */}
        <header className="lg:hidden bg-black/30 backdrop-blur-sm border-b border-white/10 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">📁</span>
            <h1 className="font-semibold text-gray-100">ARCHIVO</h1>
          </div>
          {entityType && (
            <span className="text-sm text-indigo-400">
              {entityType === 'cliente' ? 'Cliente' : 'Proveedor'}
            </span>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white/10 text-gray-100'
              }`}>
                <div className="whitespace-pre-wrap text-sm">
                  {msg.text.split('**').map((part, i) =>
                    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
                  )}
                </div>

                {/* Sugerencias */}
                {msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {msg.suggestions.map((sug, i) => (
                      <button
                        key={i}
                        onClick={() => handleSuggestionClick(sug)}
                        className="px-3 py-1.5 text-xs bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                      >
                        {sug.text}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white/10 rounded-2xl px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Error */}
        {error && (
          <div className="px-4 py-2 bg-red-900/50 border-t border-red-500/50">
            <p className="text-sm text-red-300">{error}</p>
            <button onClick={() => setError(null)} className="text-xs text-red-400 hover:text-red-200">
              Cerrar
            </button>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-white/10 bg-black/20">
          <div className="flex gap-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              multiple
              accept=".pdf,.docx,.xlsx,.txt,.xml,.png,.jpg,.jpeg"
            />

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-gray-300 transition-colors disabled:opacity-50"
              title="Subir archivos"
            >
              📎
            </button>

            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder={step === 'enter_data' ? 'Escribe aqui...' : 'Selecciona una opcion arriba'}
              disabled={isLoading || step === 'select_type'}
              className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            />

            <button
              onClick={handleSendMessage}
              disabled={isLoading || !inputValue.trim()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white transition-colors disabled:opacity-50"
            >
              Enviar
            </button>
          </div>
        </div>
      </main>

      {/* Modal de Confirmación */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl max-w-lg w-full p-6 border border-white/10">
            <h2 className="text-xl font-bold text-gray-100 mb-4">
              Confirmar {entityType === 'proveedor' ? 'Proveedor' : 'Cliente'}
            </h2>

            <div className="space-y-3 mb-6">
              {extractedData.razon_social && (
                <div>
                  <span className="text-gray-400 text-sm">Razon Social:</span>
                  <p className="text-gray-100">{extractedData.razon_social}</p>
                </div>
              )}
              {extractedData.nombre && extractedData.nombre !== extractedData.razon_social && (
                <div>
                  <span className="text-gray-400 text-sm">Nombre:</span>
                  <p className="text-gray-100">{extractedData.nombre}</p>
                </div>
              )}
              {extractedData.rfc && (
                <div>
                  <span className="text-gray-400 text-sm">RFC:</span>
                  <p className="text-gray-100">{extractedData.rfc}</p>
                </div>
              )}
              {extractedData.direccion && (
                <div>
                  <span className="text-gray-400 text-sm">Direccion:</span>
                  <p className="text-gray-100">{extractedData.direccion}</p>
                </div>
              )}
              {emailContacto && (
                <div>
                  <span className="text-gray-400 text-sm">Email:</span>
                  <p className="text-gray-100">{emailContacto}</p>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirmModal(false)}
                disabled={isLoading}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-200 transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirm}
                disabled={isLoading}
                className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Creando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatbotArchivo;
