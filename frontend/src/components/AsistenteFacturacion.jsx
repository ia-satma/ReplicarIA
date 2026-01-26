import React, { useState, useRef, useEffect } from 'react';

const AsistenteFacturacion = () => {
  const [mensajes, setMensajes] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [grabando, setGrabando] = useState(false);
  const [audioHabilitado, setAudioHabilitado] = useState(true);
  const [archivoSeleccionado, setArchivoSeleccionado] = useState(null);
  const [analizando, setAnalizando] = useState(false);
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  useEffect(() => {
    const bienvenida = {
      id: 'welcome',
      tipo: 'asistente',
      contenido: '¡Hola! Soy Facturar.IA, tu asistente de facturación SAT de REVISAR.IA.\n\nPuedo ayudarte a:\n• Encontrar la clave SAT correcta para tu factura\n• Analizar documentos y sugerir conceptos de facturación\n• Asegurar que tus gastos sean deducibles\n\n¿Qué servicio necesitas facturar? O puedes subir un documento para que lo analice.',
      timestamp: new Date()
    };
    setMensajes([bienvenida]);
  }, []);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setArchivoSeleccionado(file);
    }
  };

  const handleAnalizarDocumento = async () => {
    if (!archivoSeleccionado) return;

    setAnalizando(true);

    const msgUsuario = {
      id: Date.now().toString(),
      tipo: 'usuario',
      contenido: 'Analiza este documento para sugerirme cómo facturarlo',
      timestamp: new Date(),
      archivo: {
        nombre: archivoSeleccionado.name,
        tipo: archivoSeleccionado.type
      }
    };
    setMensajes(prev => [...prev, msgUsuario]);

    try {
      const formData = new FormData();
      formData.append('file', archivoSeleccionado);
      formData.append('accion', 'analizar_facturacion');

      const response = await fetch('/api/asistente-facturacion/analizar', {
        method: 'POST',
        body: formData
      });

      const responseText = await response.text();
      let data;
      try {
        data = JSON.parse(responseText);
      } catch {
        data = { analisis: responseText || 'Error al procesar respuesta' };
      }

      const msgAsistente = {
        id: (Date.now() + 1).toString(),
        tipo: 'asistente',
        contenido: data.analisis || 'He analizado tu documento.',
        timestamp: new Date(),
        sugerencias: data.sugerencias
      };
      setMensajes(prev => [...prev, msgAsistente]);

      setArchivoSeleccionado(null);
      if (fileInputRef.current) fileInputRef.current.value = '';

    } catch (error) {
      console.error('Error analizando documento:', error);
      const msgError = {
        id: (Date.now() + 1).toString(),
        tipo: 'sistema',
        contenido: 'Error al analizar el documento. Intenta de nuevo.',
        timestamp: new Date()
      };
      setMensajes(prev => [...prev, msgError]);
    } finally {
      setAnalizando(false);
    }
  };

  const handleEnviarMensaje = async () => {
    if (!input.trim() && !archivoSeleccionado) return;

    if (archivoSeleccionado) {
      await handleAnalizarDocumento();
      return;
    }

    setLoading(true);

    const msgUsuario = {
      id: Date.now().toString(),
      tipo: 'usuario',
      contenido: input.trim(),
      timestamp: new Date()
    };
    setMensajes(prev => [...prev, msgUsuario]);
    setInput('');

    try {
      const response = await fetch('/api/asistente-facturacion/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: msgUsuario.contenido })
      });

      const responseText = await response.text();
      let data;
      try {
        data = JSON.parse(responseText);
      } catch {
        data = { respuesta: responseText || 'Error al procesar respuesta' };
      }

      const msgAsistente = {
        id: (Date.now() + 1).toString(),
        tipo: 'asistente',
        contenido: data.respuesta,
        timestamp: new Date(),
        sugerencias: data.sugerencias
      };
      setMensajes(prev => [...prev, msgAsistente]);

    } catch (error) {
      console.error('Error:', error);
      const msgError = {
        id: (Date.now() + 1).toString(),
        tipo: 'sistema',
        contenido: 'Error al enviar mensaje. Intenta de nuevo.',
        timestamp: new Date()
      };
      setMensajes(prev => [...prev, msgError]);
    } finally {
      setLoading(false);
    }
  };

  const handleIniciarGrabacion = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const chunks = [];
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        await enviarAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setGrabando(true);
    } catch (error) {
      console.error('Error accediendo al micrófono:', error);
      alert('No se pudo acceder al micrófono');
    }
  };

  const handleDetenerGrabacion = () => {
    if (mediaRecorderRef.current && grabando) {
      mediaRecorderRef.current.stop();
      setGrabando(false);
    }
  };

  const enviarAudio = async (audioBlob) => {
    setLoading(true);

    const msgUsuario = {
      id: Date.now().toString(),
      tipo: 'usuario',
      contenido: '[Mensaje de voz]',
      timestamp: new Date()
    };
    setMensajes(prev => [...prev, msgUsuario]);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.webm');

      const response = await fetch('/api/asistente-facturacion/voz', {
        method: 'POST',
        body: formData
      });

      const responseText = await response.text();
      let data;
      try {
        data = JSON.parse(responseText);
      } catch {
        data = { respuesta: responseText || 'Error al procesar respuesta' };
      }

      setMensajes(prev => prev.map(m => 
        m.id === msgUsuario.id 
          ? { ...m, contenido: data.transcripcion || '[Mensaje de voz]' }
          : m
      ));

      const msgAsistente = {
        id: (Date.now() + 1).toString(),
        tipo: 'asistente',
        contenido: data.respuesta,
        timestamp: new Date(),
        sugerencias: data.sugerencias
      };
      setMensajes(prev => [...prev, msgAsistente]);

    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopiarSugerencia = (sugerencia) => {
    const texto = `Clave SAT: ${sugerencia.claveSAT}\nConcepto: ${sugerencia.conceptoSugerido}\nUnidad: ${sugerencia.unidadMedida}`;
    navigator.clipboard.writeText(texto);
    alert('Copiado al portapapeles');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleEnviarMensaje();
    }
  };

  return (
    <div className="bg-gray-900/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-emerald-500/30 overflow-hidden h-full flex flex-col">
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-white font-bold text-lg">Facturar.IA</h2>
              <p className="text-emerald-100 text-sm">Claves SAT y conceptos deducibles</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setAudioHabilitado(!audioHabilitado)}
              className={`p-2 rounded-lg transition ${
                audioHabilitado ? 'bg-white/20 text-white' : 'bg-white/10 text-white/50'
              }`}
              title={audioHabilitado ? 'Desactivar audio' : 'Activar audio'}
            >
              {audioHabilitado ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" clipRule="evenodd" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-800/50">
        {mensajes.map((msg) => (
          <div key={msg.id}>
            <div className={`flex gap-3 ${msg.tipo === 'usuario' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                msg.tipo === 'usuario' 
                  ? 'bg-blue-600' 
                  : msg.tipo === 'sistema'
                  ? 'bg-yellow-600'
                  : 'bg-gradient-to-br from-emerald-500 to-teal-500'
              }`}>
                {msg.tipo === 'usuario' ? (
                  <span className="text-white text-xs font-medium">Tú</span>
                ) : msg.tipo === 'sistema' ? (
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                  </svg>
                )}
              </div>

              <div className={`max-w-[80%] ${msg.tipo === 'usuario' ? 'text-right' : ''}`}>
                {msg.archivo && (
                  <div className="mb-2 inline-flex items-center gap-2 bg-blue-500/20 text-blue-300 px-3 py-2 rounded-lg text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {msg.archivo.nombre}
                  </div>
                )}
                
                <div className={`rounded-2xl px-4 py-3 ${
                  msg.tipo === 'usuario'
                    ? 'bg-blue-600 text-white rounded-tr-sm'
                    : msg.tipo === 'sistema'
                    ? 'bg-yellow-600/20 text-yellow-300 border border-yellow-500/30 rounded-tl-sm'
                    : 'bg-gray-700/80 text-gray-100 border border-gray-600/50 rounded-tl-sm'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{msg.contenido}</p>
                </div>

                {msg.sugerencias && msg.sugerencias.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <p className="text-xs text-gray-400 font-medium">Sugerencias de facturación:</p>
                    {msg.sugerencias.map((sug, idx) => (
                      <div 
                        key={idx}
                        className="bg-gradient-to-r from-emerald-900/50 to-teal-900/50 border border-emerald-500/30 rounded-xl p-3 hover:shadow-lg hover:border-emerald-400/50 transition cursor-pointer"
                        onClick={() => handleCopiarSugerencia(sug)}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="bg-emerald-600 text-white text-xs font-bold px-2 py-0.5 rounded">
                                {sug.claveSAT}
                              </span>
                              <span className="text-xs text-gray-400">
                                {Math.round((sug.confianza || 0) * 100)}% match
                              </span>
                            </div>
                            <p className="text-sm font-medium text-gray-200">{sug.descripcion}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              <strong className="text-emerald-400">Concepto:</strong> "{sug.conceptoSugerido}"
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              Unidad: {sug.unidadMedida}
                            </p>
                          </div>
                          <button className="text-emerald-400 hover:text-emerald-300">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                    <p className="text-xs text-gray-500 text-center">Haz clic en una sugerencia para copiarla</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {(loading || analizando) && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <div className="bg-gray-700/80 border border-gray-600/50 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {analizando ? 'Analizando documento...' : 'Pensando...'}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {archivoSeleccionado && (
        <div className="px-4 py-2 bg-blue-900/30 border-t border-blue-500/30 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-blue-300">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span className="font-medium">{archivoSeleccionado.name}</span>
            <span className="text-blue-400">({(archivoSeleccionado.size / 1024).toFixed(1)} KB)</span>
          </div>
          <button
            onClick={() => {
              setArchivoSeleccionado(null);
              if (fileInputRef.current) fileInputRef.current.value = '';
            }}
            className="text-blue-400 hover:text-blue-300"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="p-4 border-t border-gray-700 bg-gray-800/80">
        <div className="flex items-center gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={loading || analizando}
            className="p-3 rounded-xl bg-gray-700 text-gray-300 hover:bg-emerald-600/30 hover:text-emerald-400 transition disabled:opacity-50"
            title="Subir documento"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.txt,.xlsx,.xls"
            onChange={handleFileSelect}
            className="hidden"
          />

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={archivoSeleccionado ? "Agregar instrucciones (opcional)..." : "¿Qué servicio quieres facturar?"}
            disabled={loading || analizando}
            className="flex-1 px-4 py-3 bg-gray-700 text-white placeholder-gray-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
          />

          <button
            onClick={handleEnviarMensaje}
            disabled={loading || analizando || (!input.trim() && !archivoSeleccionado)}
            className="p-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading || analizando ? (
              <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>

        <p className="text-xs text-gray-500 mt-2 text-center">
          Sube contratos, cotizaciones o describe el servicio para obtener la clave SAT correcta
        </p>
      </div>
    </div>
  );
};

export default AsistenteFacturacion;
