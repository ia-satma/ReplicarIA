import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const ChatbotArchivo = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [collectedData, setCollectedData] = useState({});
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [useRealAI, setUseRealAI] = useState(true);
  const [onboardingStatus, setOnboardingStatus] = useState('idle');
  const [createdCompany, setCreatedCompany] = useState(null);
  const [onboardingError, setOnboardingError] = useState(null);
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [fileAnalysisResults, setFileAnalysisResults] = useState([]);
  const [extractedDocumentContents, setExtractedDocumentContents] = useState([]);
  const [entityType, setEntityType] = useState(null);
  const [intelligentMode, setIntelligentMode] = useState(false);
  const [extractedData, setExtractedData] = useState({});
  const [isSearchingWeb, setIsSearchingWeb] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [emailContacto, setEmailContacto] = useState('');
  const [createdClienteId, setCreatedClienteId] = useState(null);
  const [showDocumentUpload, setShowDocumentUpload] = useState(false);
  const [additionalFiles, setAdditionalFiles] = useState([]);
  const [isUploadingDocuments, setIsUploadingDocuments] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const additionalFileInputRef = useRef(null);
  const abortControllerRef = useRef(null);

  const onboardingSteps = [
    {
      id: 'welcome',
      botMessage: '¡Hola! Soy ARCHIVO 📚, tu archivista digital. Te ayudaré a configurar tu empresa en Revisar.ia para que puedas auditar tus servicios intangibles antes de que lo haga el SAT. ¿Comenzamos?',
      expectsResponse: false,
      nextDelay: 2000
    },
    {
      id: 'company_name',
      botMessage: '¿Cuál es el nombre o razón social de tu empresa?',
      field: 'companyName',
      expectsResponse: true
    },
    {
      id: 'rfc',
      botMessage: 'Perfecto. Ahora necesito el RFC de la empresa.',
      field: 'rfc',
      expectsResponse: true,
      validate: (value) => /^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$/i.test(value.trim())
    },
    {
      id: 'industry',
      botMessage: '¿En qué industria opera tu empresa? (ej: Construcción, Tecnología, Servicios Financieros, etc.)',
      field: 'industry',
      expectsResponse: true
    },
    {
      id: 'annual_revenue',
      botMessage: '¿Cuál es la facturación anual aproximada de la empresa? (en millones MXN)',
      field: 'annualRevenue',
      expectsResponse: true
    },
    {
      id: 'main_services',
      botMessage: '¿Cuáles son los principales tipos de servicios intangibles que contratan? (ej: Consultoría, Software, Marketing, etc.)',
      field: 'mainServices',
      expectsResponse: true
    },
    {
      id: 'documents',
      botMessage: 'Excelente. Si tienes documentos de muestra como contratos, facturas o políticas internas, puedes subirlos ahora. Esto me ayudará a personalizar mejor el sistema. Puedes subir archivos o escribir "continuar" para omitir este paso.',
      field: 'documents',
      expectsResponse: true,
      allowFiles: true
    },
    {
      id: 'contact_email',
      botMessage: '¿Cuál es el correo electrónico del responsable fiscal o administrativo?',
      field: 'contactEmail',
      expectsResponse: true,
      validate: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())
    },
    {
      id: 'complete',
      botMessage: '¡Listo! He registrado toda la información de tu empresa. Tu cuenta está configurada y lista para comenzar a auditar servicios intangibles. ¿Te gustaría crear tu primer proyecto ahora?',
      expectsResponse: false,
      showActions: true
    }
  ];

  const totalSteps = onboardingSteps.filter(s => s.expectsResponse).length;
  const completedSteps = Object.keys(collectedData).length;
  const progressPercent = Math.round((completedSteps / totalSteps) * 100);

  const addBotMessage = useCallback((text, isStreamStart = false) => {
    if (isStreamStart) {
      setMessages(prev => [...prev, { type: 'bot', text: '', timestamp: new Date(), isStreaming: true }]);
    } else {
      setIsTyping(true);
      setTimeout(() => {
        setMessages(prev => [...prev, { type: 'bot', text, timestamp: new Date() }]);
        setIsTyping(false);
      }, 800 + Math.random() * 500);
    }
  }, []);

  const updateStreamingMessage = useCallback((chunk) => {
    setMessages(prev => {
      const updated = [...prev];
      const lastIndex = updated.length - 1;
      if (lastIndex >= 0 && updated[lastIndex].isStreaming) {
        updated[lastIndex] = {
          ...updated[lastIndex],
          text: updated[lastIndex].text + chunk
        };
      }
      return updated;
    });
  }, []);

  const finalizeStreamingMessage = useCallback(() => {
    setMessages(prev => {
      const updated = [...prev];
      const lastIndex = updated.length - 1;
      if (lastIndex >= 0 && updated[lastIndex].isStreaming) {
        updated[lastIndex] = {
          ...updated[lastIndex],
          isStreaming: false
        };
      }
      return updated;
    });
    setIsStreaming(false);
  }, []);

  useEffect(() => {
    if (messages.length === 0) {
      setTimeout(() => {
        addBotMessage(`¡Hola! 👋 Soy el Asistente de Archivo de REVISAR.IA.

Puedo ayudarte a dar de alta nuevos **clientes** o **proveedores** de forma inteligente.

**¿Cómo funciona?**
1. 📁 Sube los documentos que tengas (contratos, facturas, CSF, etc.)
2. 📧 Dame un email de contacto
3. 🔍 Analizaré los documentos y buscaré datos faltantes en internet
4. ✅ Confirmas y creamos el registro automáticamente

**¿Qué quieres dar de alta hoy?**`);
        setCurrentStep('select_type');
      }, 500);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendToClaudeAPI = async (userMessage) => {
    setIsStreaming(true);
    addBotMessage('', true);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/chat/archivo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          history: conversationHistory,
          company_id: collectedData.rfc || null,
          company_context: collectedData
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        fullResponse += chunk;
        updateStreamingMessage(chunk);
      }

      setConversationHistory(prev => [
        ...prev,
        { role: 'user', content: userMessage },
        { role: 'assistant', content: fullResponse }
      ]);

      finalizeStreamingMessage();

    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request aborted');
      } else {
        console.error('Chat error:', error);
        updateStreamingMessage('⚠️ Error de conexión. Usando respuesta local.');
        finalizeStreamingMessage();
        setUseRealAI(false);
      }
    }
  };

  const uploadFilesToCloud = async (files, mensaje = '') => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    if (mensaje) formData.append('mensaje', mensaje);
    if (collectedData.rfc) formData.append('empresaId', collectedData.rfc);

    try {
      const response = await fetch('/api/upload', {
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

      return responseData;
    } catch (error) {
      console.error('Upload error:', error);
      return { success: false, error: error.message };
    }
  };

  const analyzeDocument = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      setIsProcessingFile(true);
      const response = await fetch('/api/chat/archivo/analyze-document', {
        method: 'POST',
        body: formData
      });

      const responseText = await response.text();
      let result;
      try {
        result = responseText ? JSON.parse(responseText) : {};
      } catch {
        throw new Error('Invalid JSON response from server');
      }

      if (!response.ok) {
        throw new Error(result.detail || 'Error analyzing document');
      }

      setFileAnalysisResults(prev => [...prev, result]);
      return result;
    } catch (error) {
      console.error('Document analysis error:', error);
      return {
        success: false,
        classification: 'unknown',
        file_name: file.name,
        error: error.message
      };
    } finally {
      setIsProcessingFile(false);
    }
  };

  const addUserMessage = (text) => {
    setMessages(prev => [...prev, { type: 'user', text, timestamp: new Date() }]);
  };

  const handleSend = async () => {
    if (!inputValue.trim() && uploadedFiles.length === 0) return;

    const currentStepData = onboardingSteps[currentStep];
    const userInput = inputValue.trim();

    if (userInput) {
      addUserMessage(userInput);
    }

    if (intelligentMode && typeof currentStep === 'string') {
      setInputValue('');
      
      if (currentStep === 'request_email' && userInput) {
        const emailMatch = userInput.match(/[^\s@]+@[^\s@]+\.[^\s@]+/);
        if (emailMatch) {
          setEmailContacto(emailMatch[0]);
          addBotMessage(`✅ Email registrado: ${emailMatch[0]}`);
          showConfirmationUI();
        } else {
          addBotMessage('⚠️ No encontré un email válido. Por favor proporciona un email como ejemplo@empresa.com');
        }
        return;
      }
      
      if (currentStep === 'upload_docs' && userInput && uploadedFiles.length === 0) {
        if (entityType === 'cliente') {
          const nombreMatch = userInput.match(/(?:somos|soy|empresa|cliente|nombre)[:\s]+([^\n,]+)/i) || 
                             userInput.match(/^([A-Za-záéíóúñÁÉÍÓÚÑ\s\.]+)(?:,|\s+y\s+)/i);
          const emailMatch = userInput.match(/[^\s@]+@[^\s@]+\.[^\s@]+/);
          
          const nuevosDatos = { ...(extractedData || {}) };
          if (nombreMatch) nuevosDatos.nombre = nombreMatch[1].trim();
          if (emailMatch) {
            nuevosDatos.email = emailMatch[0];
            setEmailContacto(emailMatch[0]);
          }
          
          const rfcMatch = userInput.match(/[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}/i);
          if (rfcMatch) nuevosDatos.rfc = rfcMatch[0].toUpperCase();
          
          setExtractedData(nuevosDatos);
          
          if (nuevosDatos.nombre || nuevosDatos.razon_social) {
            if (!nuevosDatos.email && !emailContacto) {
              requestEmail();
            } else {
              showConfirmationUI();
            }
          } else {
            addBotMessage('Entendido. ¿Cuál es el nombre o razón social del cliente?');
            setCurrentStep('awaiting_data');
          }
        } else {
          addBotMessage('Para proveedores necesito que subas los documentos requeridos (Acta Constitutiva, CSF, Opinión de Cumplimiento). Por favor adjunta los archivos.');
        }
        return;
      }
      
      if (currentStep === 'awaiting_data' && userInput) {
        const nuevosDatos = { ...(extractedData || {}) };
        
        if (!nuevosDatos.nombre && !nuevosDatos.razon_social) {
          nuevosDatos.nombre = userInput;
          nuevosDatos.razon_social = userInput;
        }
        
        const rfcMatch = userInput.match(/[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}/i);
        if (rfcMatch) nuevosDatos.rfc = rfcMatch[0].toUpperCase();
        
        const emailMatch = userInput.match(/[^\s@]+@[^\s@]+\.[^\s@]+/);
        if (emailMatch) {
          nuevosDatos.email = emailMatch[0];
          setEmailContacto(emailMatch[0]);
        }
        
        setExtractedData(nuevosDatos);
        
        if (!nuevosDatos.email && !emailContacto) {
          requestEmail();
        } else {
          showConfirmationUI();
        }
        return;
      }
      
      if (uploadedFiles.length === 0) {
        return;
      }
    }

    if (uploadedFiles.length > 0) {
      const fileNames = uploadedFiles.map(f => f.name).join(', ');
      addUserMessage(`📎 Subiendo ${uploadedFiles.length} archivo(s): ${fileNames}`);
      
      addBotMessage('🔍 Analizando documentos...', false);
      
      const allExtractedTexts = [];
      const analysisResults = [];
      
      for (const file of uploadedFiles) {
        const analysis = await analyzeDocument(file);
        analysisResults.push(analysis);
        
        if (analysis.success && analysis.extracted_text) {
          allExtractedTexts.push({
            filename: file.name,
            text: analysis.extracted_text,
            classification: analysis.classification
          });
        }
      }
      
      setMessages(prev => prev.filter(m => m.text !== '🔍 Analizando documentos...'));
      
      if (allExtractedTexts.length > 0) {
        setExtractedDocumentContents(prev => [...prev, ...allExtractedTexts]);
        
        let documentSummary = `He recibido y analizado ${allExtractedTexts.length} documento(s):\n`;
        allExtractedTexts.forEach((doc, idx) => {
          documentSummary += `- ${doc.filename} (${doc.classification})\n`;
        });
        
        const fullDocumentContext = allExtractedTexts.map((doc, idx) => 
          `=== DOCUMENTO ${idx + 1}: ${doc.filename} (${doc.classification}) ===\n${doc.text.substring(0, 30000)}\n=== FIN DOCUMENTO ${idx + 1} ===`
        ).join('\n\n');
        
        const analysisPrompt = `El usuario acaba de subir ${allExtractedTexts.length} documento(s) para el onboarding de su empresa.

CONTENIDO DE LOS DOCUMENTOS:
${fullDocumentContext}

INSTRUCCIONES CRÍTICAS:
1. Analiza TODO el contenido de los documentos
2. Extrae TODA la información que puedas encontrar: nombre de empresa, RFC, industria/giro, facturación, tipos de servicios, emails, etc.
3. Resume TODA la información que encontraste en los documentos
4. Lista claramente qué datos YA tienes de los documentos vs qué datos FALTAN
5. Solo pregunta por información que NO está en ningún documento

Responde de forma estructurada mostrando primero qué información extraíste, y luego qué necesitas que el usuario confirme o complete.`;
        
        if (useRealAI) {
          await sendToClaudeAPI(analysisPrompt);
        } else {
          addBotMessage(documentSummary + '\nEstoy analizando el contenido para extraer la información de tu empresa...');
        }
        
        setInputValue('');
        setUploadedFiles([]);
        return;
      } else {
        addBotMessage('⚠️ No pude extraer texto de los archivos subidos. ¿Podrías subir documentos en formato PDF, DOCX o imágenes claras?');
        setInputValue('');
        setUploadedFiles([]);
        return;
      }
    }

    if (currentStepData.validate && userInput && !currentStepData.validate(userInput)) {
      if (useRealAI) {
        await sendToClaudeAPI(`El usuario proporcionó un ${currentStepData.field} inválido: "${userInput}". Por favor, indica amablemente que el formato no es correcto y solicita que lo verifique.`);
      } else {
        setTimeout(() => {
          if (currentStepData.field === 'rfc') {
            addBotMessage('El RFC no parece tener el formato correcto. Por favor, verifica e intenta de nuevo. (Ejemplo: ABC123456XY0)');
          } else if (currentStepData.field === 'contactEmail') {
            addBotMessage('El correo electrónico no parece válido. Por favor, verifica e intenta de nuevo.');
          }
        }, 500);
      }
      setInputValue('');
      return;
    }

    if (currentStepData.field) {
      if (currentStepData.allowFiles && uploadedFiles.length > 0) {
        setCollectedData(prev => ({ ...prev, [currentStepData.field]: uploadedFiles.map(f => f.name) }));
      } else if (userInput.toLowerCase() !== 'continuar') {
        setCollectedData(prev => ({ ...prev, [currentStepData.field]: userInput }));
      }
    }

    setInputValue('');
    setUploadedFiles([]);

    const nextStep = currentStep + 1;
    if (nextStep < onboardingSteps.length) {
      setCurrentStep(nextStep);

      if (onboardingSteps[nextStep].showActions) {
        setTimeout(async () => {
          addBotMessage('📋 Procesando tu información y registrando la empresa en el sistema...');
          await completeOnboarding();
        }, 500);
      } else if (useRealAI) {
        const extractedDocsContext = extractedDocumentContents.length > 0 
          ? `\n\nDOCUMENTOS YA ANALIZADOS (usa esta información para no preguntar lo que ya sabes):\n${extractedDocumentContents.map(d => `- ${d.filename}: ${d.text.substring(0, 5000)}...`).join('\n')}`
          : '';
        
        const contextMessage = `El usuario acaba de proporcionar su ${currentStepData.field || 'respuesta'}: "${userInput}".${extractedDocsContext}

Ahora necesitas preguntarle sobre: ${onboardingSteps[nextStep].id}. 
La pregunta sugerida es: "${onboardingSteps[nextStep].botMessage}"

IMPORTANTE: Si ya tienes esta información de los documentos analizados, confirma el dato y salta a la siguiente pregunta. NO pidas información que ya tienes.

Responde de manera natural y profesional, confirmando lo que recibiste y haciendo la siguiente pregunta solo si es necesaria.`;
        
        await sendToClaudeAPI(contextMessage);
      } else {
        setTimeout(() => {
          addBotMessage(onboardingSteps[nextStep].botMessage);
        }, 500);
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    setUploadedFiles(prev => [...prev, ...files]);
  };

  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSelectEntityType = (tipo) => {
    setEntityType(tipo);
    setIntelligentMode(true);
    addUserMessage(`Quiero dar de alta un ${tipo}`);
    setTimeout(() => {
      if (tipo === 'cliente') {
        addBotMessage(`Perfecto, vamos a dar de alta un nuevo **cliente**.

Para clientes los requisitos son mínimos. Puedes:

📝 **Opción 1: Datos básicos**
Simplemente dime el nombre de la empresa y un email de contacto.

📁 **Opción 2: Con documentos** (opcional)
Si tienes contratos u otros documentos, súbelos y extraeré los datos automáticamente.

*El RFC y CSF no son obligatorios para clientes.*

¿Cómo prefieres continuar?`);
      } else {
        addBotMessage(`Perfecto, vamos a dar de alta un nuevo **proveedor**.

⚠️ **Para proveedores se requiere validación fiscal completa:**

📋 **Documentos OBLIGATORIOS:**
1. **Acta Constitutiva** - Para verificar el objeto social vs lo que facturan
2. **Constancia de Situación Fiscal (CSF)** - Para validar régimen fiscal
3. **Opinión de Cumplimiento del SAT** - Para verificar que esté al corriente

📁 **Documentos opcionales:**
- Contratos de servicio
- Facturas de muestra
- Identificación del representante legal

Sube los documentos y analizaré que todo sea congruente.`);
      }
      setCurrentStep('upload_docs');
    }, 500);
  };

  const analyzeDocumentsIntelligent = async (files) => {
    setIsProcessingFile(true);
    addBotMessage('🔍 Analizando documentos con IA...');

    try {
      const formData = new FormData();
      files.forEach(f => formData.append('files', f));
      formData.append('tipo_entidad', entityType || 'cliente');
      formData.append('email_contacto', emailContacto);

      const token = localStorage.getItem('auth_token');
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch('/api/archivo/analizar', {
        method: 'POST',
        headers,
        body: formData
      });

      const responseText = await response.text();
      let data;
      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch {
        throw new Error('Respuesta inválida del servidor');
      }

      if (!response.ok) {
        throw new Error(data.detail || 'Error al analizar documentos');
      }

      setExtractedData(data.datos);
      
      const docContents = files.map(f => ({
        filename: f.name,
        classification: data.datos.clasificaciones_documentos?.[f.name] || f.name.toLowerCase()
      }));
      setExtractedDocumentContents(prev => [...prev, ...docContents]);
      
      setMessages(prev => prev.filter(m => !m.text.includes('Analizando documentos')));

      let resumen = '📊 **Análisis completado**\n\n**Datos extraídos de los documentos:**\n';
      if (data.datos.nombre) resumen += `✅ Nombre: ${data.datos.nombre}\n`;
      if (data.datos.rfc) resumen += `✅ RFC: ${data.datos.rfc}\n`;
      if (data.datos.razon_social) resumen += `✅ Razón Social: ${data.datos.razon_social}\n`;
      if (data.datos.direccion) resumen += `✅ Dirección: ${data.datos.direccion}\n`;
      if (data.datos.telefono) resumen += `✅ Teléfono: ${data.datos.telefono}\n`;
      if (data.datos.email) resumen += `✅ Email: ${data.datos.email}\n`;
      if (data.datos.giro) resumen += `✅ Giro: ${data.datos.giro}\n`;

      if (data.datos.datosFaltantes && data.datos.datosFaltantes.length > 0) {
        resumen += `\n⚠️ **Datos faltantes:** ${data.datos.datosFaltantes.join(', ')}`;
      }

      addBotMessage(resumen);

      if (data.datos.datosFaltantes && data.datos.datosFaltantes.length > 0) {
        await searchWebForMissingData(data.datos);
      } else {
        if (!data.datos.email) {
          requestEmail();
        } else {
          showConfirmationUI();
        }
      }

    } catch (error) {
      console.error('Error analyzing documents:', error);
      addBotMessage(`⚠️ Error analizando documentos: ${error.message}`);
    } finally {
      setIsProcessingFile(false);
    }
  };

  const searchWebForMissingData = async (datos) => {
    setIsSearchingWeb(true);
    addBotMessage(`🌐 **Buscando datos faltantes en internet...**

Faltan: ${datos.datosFaltantes?.join(', ') || 'algunos datos'}

Buscando en fuentes públicas...`);

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/archivo/buscar-web', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          datos_actuales: datos,
          campos_faltantes: datos.datosFaltantes || []
        })
      });

      const responseText = await response.text();
      let data;
      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch {
        throw new Error('Respuesta inválida del servidor');
      }
      
      const datosActualizados = { ...datos, ...data.datos_encontrados };
      datosActualizados.fuentes = [
        ...(datos.fuentes || []),
        ...(data.fuentes_nuevas || [])
      ];
      datosActualizados.datosFaltantes = data.aun_faltantes || [];
      
      setExtractedData(datosActualizados);

      let resumen = '🌐 **Resultados de búsqueda web:**\n\n';
      if (data.datos_encontrados && Object.keys(data.datos_encontrados).length > 0) {
        resumen += '**Datos encontrados:**\n';
        for (const [campo, valor] of Object.entries(data.datos_encontrados)) {
          resumen += `✅ ${campo}: ${valor}\n`;
        }
      }

      if (data.aun_faltantes?.length > 0) {
        resumen += `\n⚠️ No se encontraron: ${data.aun_faltantes.join(', ')}`;
      } else {
        resumen += '\n✅ ¡Todos los datos completados!';
      }

      setMessages(prev => prev.filter(m => !m.text.includes('Buscando datos faltantes')));
      addBotMessage(resumen);

      if (!datosActualizados.email && !emailContacto) {
        requestEmail();
      } else {
        showConfirmationUI();
      }

    } catch (error) {
      console.error('Error searching web:', error);
      if (!datos.email && !emailContacto) {
        requestEmail();
      } else {
        showConfirmationUI();
      }
    } finally {
      setIsSearchingWeb(false);
    }
  };

  const requestEmail = () => {
    setCurrentStep('request_email');
    addBotMessage(`📧 **¿Cuál es el email de contacto del ${entityType || 'cliente'}?**

Este email se usará para:
- Enviar notificaciones
- Comunicaciones del sistema
- Solicitar documentos adicionales`);
  };

  const showConfirmationUI = () => {
    if (entityType === 'proveedor') {
      const documentosInfo = extractedDocumentContents.map(d => {
        const texto = ((d.classification || '') + ' ' + (d.filename || '')).toLowerCase();
        return texto;
      });
      
      const tieneActa = documentosInfo.some(t => t.includes('acta') || t.includes('constitutiva'));
      const tieneCSF = documentosInfo.some(t => t.includes('csf') || t.includes('situación') || t.includes('situacion') || t.includes('fiscal'));
      const tieneOpinion = documentosInfo.some(t => t.includes('opinión') || t.includes('opinion') || t.includes('cumplimiento'));
      
      const documentosFaltantes = [];
      if (!tieneActa) documentosFaltantes.push('Acta Constitutiva');
      if (!tieneCSF) documentosFaltantes.push('Constancia de Situación Fiscal (CSF)');
      if (!tieneOpinion) documentosFaltantes.push('Opinión de Cumplimiento del SAT');
      
      if (documentosFaltantes.length > 0 && extractedDocumentContents.length > 0) {
        addBotMessage(`⚠️ **Documentos faltantes para proveedores:**\n\n${documentosFaltantes.map(d => `- ${d}`).join('\n')}\n\nPor favor sube los documentos faltantes para continuar con el alta del proveedor.`);
        return;
      }
      
      if (extractedDocumentContents.length === 0) {
        addBotMessage(`⚠️ **Para proveedores se requieren documentos obligatorios.**\n\nPor favor sube:\n- Acta Constitutiva\n- Constancia de Situación Fiscal (CSF)\n- Opinión de Cumplimiento del SAT`);
        return;
      }
    }
    
    setShowConfirmation(true);
    addBotMessage('✅ **¡Listo! He recopilado la siguiente información.** Revisa los datos y confirma para crear el registro.');
  };

  const handleEditExtractedField = (campo, valor) => {
    setExtractedData(prev => ({
      ...prev,
      [campo]: valor,
      fuentes: [
        ...(prev?.fuentes || []).filter(f => f.campo !== campo),
        { campo, fuente: 'usuario', confianza: 1 }
      ]
    }));
  };

  const handleConfirmCreation = async () => {
    setOnboardingStatus('loading');
    addBotMessage(`📋 Creando ${entityType || 'cliente'}...`);

    try {
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        throw new Error('No estás autenticado. Por favor, inicia sesión primero.');
      }

      const requestBody = JSON.stringify({
        tipo: entityType || 'cliente',
        datos: extractedData,
        email_contacto: emailContacto || extractedData?.email || '',
        archivos_ids: []
      });

      const response = await fetch('/api/archivo/crear-entidad', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: requestBody
      });

      let data;
      try {
        const clonedResponse = response.clone();
        data = await clonedResponse.json();
      } catch (jsonError) {
        try {
          const textResponse = await response.text();
          data = textResponse ? JSON.parse(textResponse) : {};
        } catch {
          throw new Error('El servidor no devolvió una respuesta válida');
        }
      }

      if (!response.ok) {
        const errorMsg = data?.detail || data?.error || data?.message || `Error del servidor (${response.status})`;
        throw new Error(errorMsg);
      }

      setCreatedCompany(data);
      setOnboardingStatus('success');
      setShowConfirmation(false);
      
      if (data.pg_cliente_id) {
        setCreatedClienteId(data.pg_cliente_id);
        setShowDocumentUpload(true);
      }

      addBotMessage(`🎉 **¡${entityType === 'proveedor' ? 'Proveedor' : 'Cliente'} creado exitosamente!**

**${extractedData?.nombre || extractedData?.razon_social}**
RFC: ${extractedData?.rfc || 'N/A'}

✅ Registro creado en el sistema
✅ Documentos guardados en su expediente
✅ Knowledge Base inicializado
${emailContacto ? `✅ Se enviará email de bienvenida a ${emailContacto}` : ''}

${data.pg_cliente_id ? '📎 Puedes subir documentos adicionales usando el botón de abajo.' : ''}

Puedes editar este ${entityType || 'cliente'} desde el **Panel de Administración**.`);

      setUploadedFiles([]);
      setEmailContacto('');

    } catch (error) {
      console.error('Error creating entity:', error);
      setOnboardingStatus('error');
      addBotMessage(`⚠️ Error creando ${entityType || 'cliente'}: ${error.message}`);
    }
  };

  const handleStartNewOnboarding = () => {
    setEntityType(null);
    setIntelligentMode(false);
    setExtractedData({});
    setShowConfirmation(false);
    setOnboardingStatus('idle');
    setCurrentStep(0);
    setUploadedFiles([]);
    setEmailContacto('');
    setCreatedClienteId(null);
    setShowDocumentUpload(false);
    setAdditionalFiles([]);
    addBotMessage('¿Qué quieres dar de alta hoy? Selecciona **Cliente** o **Proveedor**.');
  };

  const handleAdditionalFileChange = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(file => {
      const maxSize = 10 * 1024 * 1024;
      if (file.size > maxSize) {
        addBotMessage(`⚠️ El archivo "${file.name}" excede el límite de 10MB`);
        return false;
      }
      return true;
    });
    setAdditionalFiles(prev => [...prev, ...validFiles]);
  };

  const removeAdditionalFile = (index) => {
    setAdditionalFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUploadAdditionalDocuments = async () => {
    if (!createdClienteId || additionalFiles.length === 0) return;
    
    setIsUploadingDocuments(true);
    addBotMessage(`📤 Subiendo ${additionalFiles.length} documento(s)...`);
    
    try {
      const token = localStorage.getItem('auth_token');
      const formData = new FormData();
      formData.append('cliente_id', createdClienteId);
      
      additionalFiles.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await fetch('/api/archivo/documentos', {
        method: 'POST',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: formData
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al subir documentos');
      }
      
      addBotMessage(`✅ **Documentos subidos exitosamente**
      
${data.documentos_subidos?.map(d => `📄 ${d.filename} - ${d.status}`).join('\n') || 'Documentos procesados'}

${data.errores?.length > 0 ? `\n⚠️ Errores: ${data.errores.map(e => e.filename).join(', ')}` : ''}

¿Quieres subir más documentos o dar de alta otro cliente/proveedor?`);
      
      setAdditionalFiles([]);
      
    } catch (error) {
      console.error('Error uploading documents:', error);
      addBotMessage(`⚠️ Error al subir documentos: ${error.message}`);
    } finally {
      setIsUploadingDocuments(false);
    }
  };

  const completeOnboarding = async () => {
    setOnboardingStatus('loading');
    setOnboardingError(null);
    
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setOnboardingError('No estás autenticado. Por favor, inicia sesión primero.');
      setOnboardingStatus('error');
      return;
    }

    try {
      const response = await fetch('/api/onboarding/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          companyName: collectedData.companyName || '',
          rfc: collectedData.rfc || '',
          industry: collectedData.industry || '',
          annualRevenue: collectedData.annualRevenue || '',
          mainServices: collectedData.mainServices || '',
          contactEmail: collectedData.contactEmail || '',
          documents: collectedData.documents || []
        })
      });

      const responseText = await response.text();
      let data;
      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch {
        throw new Error('Respuesta inválida del servidor');
      }

      if (!response.ok) {
        throw new Error(data.detail || 'Error al completar el onboarding');
      }

      setCreatedCompany(data);
      setOnboardingStatus('success');
      
      addBotMessage(`🎉 ¡Excelente! Tu empresa "${data.company_name}" ha sido registrada exitosamente en Revisar.IA. Ya puedes comenzar a crear proyectos y auditar tus servicios intangibles.`);
      
    } catch (error) {
      console.error('Onboarding error:', error);
      setOnboardingError(error.message);
      setOnboardingStatus('error');
      addBotMessage(`⚠️ Hubo un problema al registrar tu empresa: ${error.message}. Por favor, intenta de nuevo.`);
    }
  };

  const handleCreateProject = () => {
    if (createdCompany?.company_id) {
      localStorage.setItem('activeCompanyId', createdCompany.company_id);
    }
    navigate('/submit');
  };

  const handleGoToDashboard = () => {
    if (createdCompany?.company_id) {
      localStorage.setItem('activeCompanyId', createdCompany.company_id);
    }
    navigate('/');
  };
  
  const handleRetryOnboarding = () => {
    setOnboardingStatus('idle');
    setOnboardingError(null);
    completeOnboarding();
  };
  
  const handleEditData = () => {
    setOnboardingStatus('idle');
    setOnboardingError(null);
    setCurrentStep(1);
    setCollectedData({});
    addBotMessage('Entendido. Vamos a empezar de nuevo. ¿Cuál es el nombre o razón social de tu empresa?');
  };

  const currentStepData = onboardingSteps[currentStep];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      <div className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">ARCHIVO</h1>
                <p className="text-xs text-slate-400">Archivista Digital {useRealAI ? '(Claude AI)' : '(Modo Local)'}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-white">{progressPercent}% completado</p>
              <p className="text-xs text-slate-400">{completedSteps} de {totalSteps} pasos</p>
            </div>
          </div>
          
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-emerald-400 to-teal-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.type === 'bot' && (
                <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-lg flex items-center justify-center mr-2 flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                  </svg>
                </div>
              )}
              
              <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl ${
                  message.type === 'user'
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-br-md'
                    : 'bg-slate-700/80 text-slate-100 rounded-bl-md'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.text}
                  {message.isStreaming && (
                    <span className="inline-block w-2 h-4 bg-emerald-400 ml-1 animate-pulse"></span>
                  )}
                </p>
                {!message.isStreaming && (
                  <p className={`text-xs mt-1 ${message.type === 'user' ? 'text-blue-200' : 'text-slate-400'}`}>
                    {message.timestamp.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                )}
              </div>
              
              {message.type === 'user' && (
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center ml-2 flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              )}
            </div>
          ))}
          
          {isTyping && !isStreaming && (
            <div className="flex justify-start">
              <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-lg flex items-center justify-center mr-2">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
              </div>
              <div className="bg-slate-700/80 px-4 py-3 rounded-2xl rounded-bl-md">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}

          {currentStep === 'select_type' && !entityType && !isTyping && (
            <div className="flex justify-center gap-4 pt-4">
              <button
                onClick={() => handleSelectEntityType('cliente')}
                className="flex flex-col items-center gap-3 px-8 py-6 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-2xl hover:from-blue-600 hover:to-indigo-700 transition-all shadow-lg shadow-blue-500/25"
              >
                <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <span className="font-bold text-lg">Cliente</span>
                <span className="text-xs text-blue-200">Empresa que contrata servicios</span>
              </button>
              <button
                onClick={() => handleSelectEntityType('proveedor')}
                className="flex flex-col items-center gap-3 px-8 py-6 bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-2xl hover:from-emerald-600 hover:to-teal-700 transition-all shadow-lg shadow-emerald-500/25"
              >
                <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span className="font-bold text-lg">Proveedor</span>
                <span className="text-xs text-emerald-200">Empresa que proporciona servicios</span>
              </button>
            </div>
          )}

          {showConfirmation && extractedData && (
            <div className="bg-slate-700/60 rounded-2xl p-6 mt-4 border border-slate-600">
              <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Datos Recopilados - Confirma para crear
              </h3>
              <div className="grid grid-cols-2 gap-4 mb-6">
                {[
                  { key: 'nombre', label: 'Nombre' },
                  { key: 'rfc', label: 'RFC' },
                  { key: 'razon_social', label: 'Razón Social' },
                  { key: 'direccion', label: 'Dirección' },
                  { key: 'email', label: 'Email' },
                  { key: 'telefono', label: 'Teléfono' },
                  { key: 'giro', label: 'Giro' },
                  { key: 'sitio_web', label: 'Sitio Web' }
                ].map(({ key, label }) => (
                  <div key={key} className={key === 'razon_social' || key === 'direccion' ? 'col-span-2' : ''}>
                    <label className="text-xs text-slate-400 block mb-1">{label}</label>
                    <input
                      type="text"
                      value={extractedData[key] || ''}
                      onChange={(e) => handleEditExtractedField(key, e.target.value)}
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                      placeholder={`Ingresa ${label.toLowerCase()}`}
                    />
                  </div>
                ))}
              </div>
              {!extractedData.email && (
                <div className="mb-4">
                  <label className="text-xs text-slate-400 block mb-1">Email de Contacto (requerido)</label>
                  <input
                    type="email"
                    value={emailContacto}
                    onChange={(e) => setEmailContacto(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="email@empresa.com"
                  />
                </div>
              )}
              <div className="flex gap-3">
                <button
                  onClick={handleConfirmCreation}
                  disabled={onboardingStatus === 'loading'}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold rounded-xl hover:from-emerald-600 hover:to-teal-700 transition-all disabled:opacity-50"
                >
                  {onboardingStatus === 'loading' ? (
                    <>
                      <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Creando...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Confirmar y Crear {entityType === 'proveedor' ? 'Proveedor' : 'Cliente'}</span>
                    </>
                  )}
                </button>
                <button
                  onClick={handleStartNewOnboarding}
                  className="px-6 py-3 bg-slate-600 text-white font-medium rounded-xl hover:bg-slate-500 transition-all"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {onboardingStatus === 'success' && intelligentMode && (
            <div className="flex flex-col gap-4 pt-4">
              {showDocumentUpload && createdClienteId && (
                <div className="bg-slate-700/60 rounded-2xl p-4 border border-slate-600">
                  <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    Subir Documentos Adicionales
                  </h4>
                  
                  <input
                    type="file"
                    ref={additionalFileInputRef}
                    onChange={handleAdditionalFileChange}
                    multiple
                    className="hidden"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg,.xml,.json"
                  />
                  
                  {additionalFiles.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {additionalFiles.map((file, index) => (
                        <div key={index} className="flex items-center gap-2 bg-slate-600 px-3 py-2 rounded-lg border border-slate-500">
                          <span className="text-sm text-slate-200 truncate max-w-[150px]">{file.name}</span>
                          <button 
                            onClick={() => removeAdditionalFile(index)} 
                            className="text-slate-400 hover:text-red-400 transition-colors"
                            disabled={isUploadingDocuments}
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  <div className="flex gap-3">
                    <button
                      onClick={() => additionalFileInputRef.current?.click()}
                      disabled={isUploadingDocuments}
                      className="flex-1 flex items-center justify-center gap-2 py-2 bg-slate-600 text-white font-medium rounded-lg hover:bg-slate-500 transition-all disabled:opacity-50"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Seleccionar Archivos
                    </button>
                    {additionalFiles.length > 0 && (
                      <button
                        onClick={handleUploadAdditionalDocuments}
                        disabled={isUploadingDocuments}
                        className="flex-1 flex items-center justify-center gap-2 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold rounded-lg hover:from-emerald-600 hover:to-teal-700 transition-all disabled:opacity-50"
                      >
                        {isUploadingDocuments ? (
                          <>
                            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>Subiendo...</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                            <span>Subir {additionalFiles.length} archivo(s)</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">PDF, Word, Excel, imágenes, XML, JSON (máx. 10MB)</p>
                </div>
              )}
              
              <div className="flex justify-center gap-4">
                <button
                  onClick={handleStartNewOnboarding}
                  className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all"
                >
                  Dar de Alta Otro
                </button>
                <button
                  onClick={handleGoToDashboard}
                  className="px-6 py-3 bg-slate-700 text-white font-semibold rounded-xl hover:bg-slate-600 transition-all border border-slate-600"
                >
                  Ir al Dashboard
                </button>
              </div>
            </div>
          )}

          {currentStepData?.showActions && !isTyping && !isStreaming && messages.length > 0 && (
            <div className="flex flex-col items-center gap-4 pt-4">
              {onboardingStatus === 'loading' && (
                <div className="flex items-center gap-3 text-slate-300">
                  <svg className="w-6 h-6 animate-spin text-emerald-400" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Registrando empresa...</span>
                </div>
              )}
              
              {onboardingStatus === 'error' && (
                <div className="flex flex-col items-center gap-3">
                  <div className="flex items-center gap-2 text-red-400 bg-red-400/10 px-4 py-2 rounded-lg">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{onboardingError}</span>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleEditData}
                      className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all"
                    >
                      Corregir Datos
                    </button>
                    <button
                      onClick={handleRetryOnboarding}
                      className="px-6 py-3 bg-slate-700 text-white font-semibold rounded-xl hover:bg-slate-600 transition-all border border-slate-600"
                    >
                      Reintentar
                    </button>
                  </div>
                </div>
              )}
              
              {onboardingStatus === 'success' && (
                <div className="flex flex-col items-center gap-4">
                  <div className="flex items-center gap-2 text-emerald-400 bg-emerald-400/10 px-4 py-2 rounded-lg">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Empresa registrada exitosamente</span>
                  </div>
                  <div className="flex gap-4">
                    <button
                      onClick={handleCreateProject}
                      className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold rounded-xl hover:from-emerald-600 hover:to-teal-700 transition-all shadow-lg shadow-emerald-500/25"
                    >
                      Crear Primer Proyecto
                    </button>
                    <button
                      onClick={handleGoToDashboard}
                      className="px-6 py-3 bg-slate-700 text-white font-semibold rounded-xl hover:bg-slate-600 transition-all border border-slate-600"
                    >
                      Ir al Dashboard
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {((currentStepData?.expectsResponse && !currentStepData?.showActions) || 
        (intelligentMode && !showConfirmation && onboardingStatus !== 'success' && 
         ['upload_docs', 'request_email', 'awaiting_data'].includes(currentStep))) && (
        <div className="bg-slate-800/50 backdrop-blur-sm border-t border-slate-700 px-4 py-4">
          <div className="max-w-3xl mx-auto">
            {uploadedFiles.length > 0 && (
              <div className="bg-slate-700/60 rounded-xl p-3 mb-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400 font-medium">
                    {uploadedFiles.length} archivo{uploadedFiles.length > 1 ? 's' : ''} listo{uploadedFiles.length > 1 ? 's' : ''} para analizar
                  </span>
                  {isProcessingFile && (
                    <div className="flex items-center gap-2 text-emerald-400">
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span className="text-xs">Analizando con IA...</span>
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  {uploadedFiles.map((file, index) => {
                    const getFileIcon = () => {
                      const type = file.type.toLowerCase();
                      const name = file.name.toLowerCase();
                      if (type.includes('pdf')) return { icon: '📕', color: 'text-red-400' };
                      if (type.includes('word') || name.endsWith('.doc') || name.endsWith('.docx')) return { icon: '📘', color: 'text-blue-400' };
                      if (type.includes('excel') || type.includes('spreadsheet') || name.endsWith('.xls') || name.endsWith('.xlsx') || name.endsWith('.csv')) return { icon: '📗', color: 'text-green-400' };
                      if (type.includes('image') || name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg')) return { icon: '🖼️', color: 'text-purple-400' };
                      if (name.endsWith('.xml')) return { icon: '📄', color: 'text-orange-400' };
                      if (name.endsWith('.json')) return { icon: '📋', color: 'text-yellow-400' };
                      if (name.endsWith('.txt')) return { icon: '📝', color: 'text-slate-300' };
                      return { icon: '📎', color: 'text-slate-400' };
                    };
                    const fileInfo = getFileIcon();
                    const formatSize = (bytes) => {
                      if (bytes < 1024) return bytes + ' B';
                      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
                      return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
                    };
                    return (
                      <div key={index} className="flex items-center gap-2 bg-slate-600 px-3 py-2 rounded-lg border border-slate-500">
                        <span className="text-lg">{fileInfo.icon}</span>
                        <div className="flex flex-col">
                          <span className="text-sm text-slate-200 truncate max-w-[180px]">{file.name}</span>
                          <span className="text-xs text-slate-400">{formatSize(file.size)}</span>
                        </div>
                        <button 
                          onClick={() => removeFile(index)} 
                          className="ml-2 text-slate-400 hover:text-red-400 transition-colors p-1 rounded hover:bg-slate-500/50"
                          disabled={isProcessingFile}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    );
                  })}
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Formatos: PDF, Word, Excel, imágenes, XML, JSON (máx. 10MB)
                </p>
              </div>
            )}
            
            <div className="flex items-center gap-3">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                multiple
                className="hidden"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg,.xml,.json"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-3 rounded-xl hover:bg-slate-700 text-slate-400 hover:text-emerald-400 transition-all border border-transparent hover:border-slate-600"
                title="Adjuntar archivo (PDF, Word, Excel, imágenes - máx 10MB)"
                disabled={isStreaming || isProcessingFile}
              >
                {isProcessingFile ? (
                  <svg className="w-5 h-5 text-emerald-400 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                )}
              </button>
              
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isStreaming ? "ARCHIVO está respondiendo..." : "Escribe tu respuesta..."}
                disabled={isStreaming}
                className="flex-1 bg-slate-700/80 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
              />
              
              <button
                onClick={() => {
                  if (intelligentMode && uploadedFiles.length > 0) {
                    addUserMessage(`Subiendo ${uploadedFiles.length} documento(s) para análisis`);
                    analyzeDocumentsIntelligent(uploadedFiles);
                    setUploadedFiles([]);
                  } else {
                    handleSend();
                  }
                }}
                disabled={(!inputValue.trim() && uploadedFiles.length === 0) || isStreaming || isProcessingFile}
                className="p-3 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 disabled:from-slate-600 disabled:to-slate-600 rounded-xl transition-all"
              >
                {intelligentMode && uploadedFiles.length > 0 ? (
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatbotArchivo;
