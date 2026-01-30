import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

import { useChatMessages, useFileUpload, useOnboardingSteps, useChatAPI } from '../hooks';
import { MessageList, ChatInput, FileUploadArea, ProgressIndicator, ConfirmationCard } from './chatbot';
import { Modal, ErrorMessage } from './shared';
import { SYSTEM_MESSAGES, AGENTS, ONBOARDING_STEPS } from '../constants/onboarding';

const ChatbotArchivo = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  
  const chat = useChatMessages();
  const files = useFileUpload(handleFileAnalysisComplete);
  const steps = useOnboardingSteps();
  const api = useChatAPI();

  const [showFileModal, setShowFileModal] = useState(false);

  useEffect(() => {
    if (chat.messages.length === 0) {
      setTimeout(() => {
        chat.addBotMessage(`¡Hola! 👋 Soy el Asistente de Archivo de REVISAR.IA.

Puedo ayudarte a dar de alta nuevos **clientes** o **proveedores** de forma inteligente.

**¿Cómo funciona?**
1. 📁 Sube los documentos que tengas (contratos, facturas, CSF, etc.)
2. 📧 Dame un email de contacto
3. 🔍 Analizaré los documentos y buscaré datos faltantes en internet
4. ✅ Confirmas y creamos el registro automáticamente

**¿Qué quieres dar de alta hoy?**`, {
          agent: 'ARCHIVO',
          suggestions: [
            { text: 'Registrar cliente', value: 'cliente' },
            { text: 'Registrar proveedor', value: 'proveedor' },
          ],
        });
        steps.setCurrentStep('select_type');
      }, 500);
    }
  }, []);

  const handleSelectEntityType = useCallback((tipo) => {
    steps.selectEntityType(tipo);
    steps.setIntelligentMode(true);
    chat.addUserMessage(`Quiero dar de alta un ${tipo}`);
    
    setTimeout(() => {
      if (tipo === 'cliente') {
        chat.addBotMessage(`Perfecto, vamos a dar de alta un nuevo **cliente**.

Para clientes los requisitos son mínimos. Puedes:

📝 **Opción 1: Datos básicos**
Simplemente dime el nombre de la empresa y un email de contacto.

📁 **Opción 2: Con documentos** (opcional)
Si tienes contratos u otros documentos, súbelos y extraeré los datos automáticamente.

*El RFC y CSF no son obligatorios para clientes.*

¿Cómo prefieres continuar?`, { agent: 'ARCHIVO' });
      } else {
        chat.addBotMessage(`Perfecto, vamos a dar de alta un nuevo **proveedor**.

⚠️ **Para proveedores se requiere validación fiscal completa:**

📋 **Documentos OBLIGATORIOS:**
1. **Acta Constitutiva** - Para verificar el objeto social vs lo que facturan
2. **Constancia de Situación Fiscal (CSF)** - Para validar régimen fiscal
3. **Opinión de Cumplimiento del SAT** - Para verificar que esté al corriente

📁 **Documentos opcionales:**
- Contratos de servicio
- Facturas de muestra
- Identificación del representante legal

Sube los documentos y analizaré que todo sea congruente.`, { agent: 'ARCHIVO' });
      }
      steps.setCurrentStep('upload_docs');
    }, 500);
  }, [chat, steps]);

  const handleSendMessage = useCallback(async (content) => {
    chat.addUserMessage(content);

    if (steps.currentStep === 'select_type') {
      if (content.toLowerCase().includes('cliente')) {
        handleSelectEntityType('cliente');
        return;
      } else if (content.toLowerCase().includes('proveedor')) {
        handleSelectEntityType('proveedor');
        return;
      }
    }

    if (steps.currentStep === 'request_email') {
      const emailMatch = content.match(/[^\s@]+@[^\s@]+\.[^\s@]+/);
      if (emailMatch) {
        steps.setEmailContacto(emailMatch[0]);
        chat.addBotMessage(`✅ Email registrado: ${emailMatch[0]}`, { agent: 'ARCHIVO' });
        showConfirmation();
      } else {
        chat.addBotMessage('⚠️ No encontré un email válido. Por favor proporciona un email como ejemplo@empresa.com', { agent: 'ARCHIVO' });
      }
      return;
    }

    if (steps.currentStep === 'awaiting_data') {
      const nuevosDatos = { ...(steps.extractedData || {}) };
      
      if (!nuevosDatos.nombre && !nuevosDatos.razon_social) {
        nuevosDatos.nombre = content;
        nuevosDatos.razon_social = content;
      }
      
      const rfcMatch = content.match(/[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}/i);
      if (rfcMatch) nuevosDatos.rfc = rfcMatch[0].toUpperCase();
      
      const emailMatch = content.match(/[^\s@]+@[^\s@]+\.[^\s@]+/);
      if (emailMatch) {
        nuevosDatos.email = emailMatch[0];
        steps.setEmailContacto(emailMatch[0]);
      }
      
      steps.mergeExtractedData(nuevosDatos);
      
      if (!nuevosDatos.email && !steps.emailContacto) {
        requestEmail();
      } else {
        showConfirmation();
      }
      return;
    }

    if (api.useRealAI) {
      chat.setTyping(true);
      try {
        chat.startStreaming({ agent: 'ARCHIVO' });
        
        await api.sendToClaudeAPI({
          message: content,
          conversationHistory: chat.conversationHistory,
          companyContext: steps.collectedData,
          stream: true,
          onStreamChunk: (chunk) => chat.updateStreamingMessage(chunk),
        });
        
        chat.finalizeStreamingMessage();
      } catch (error) {
        chat.cancelStreaming();
        chat.addSystemMessage(`Error: ${error.message}`, 'error');
      }
      chat.setTyping(false);
    }
  }, [chat, steps, api, handleSelectEntityType]);

  const handleSuggestionClick = useCallback((suggestion) => {
    const value = typeof suggestion === 'string' ? suggestion : suggestion.value || suggestion.text;
    
    if (value === 'cliente' || value === 'proveedor') {
      handleSelectEntityType(value);
    } else {
      handleSendMessage(value);
    }
  }, [handleSelectEntityType, handleSendMessage]);

  async function handleFileAnalysisComplete(results) {
    if (results.length === 0) return;

    const allExtractedData = {};
    results.forEach(result => {
      if (result.extracted_data || result.extractedData) {
        Object.assign(allExtractedData, result.extracted_data || result.extractedData);
      }
    });

    if (Object.keys(allExtractedData).length > 0) {
      steps.mergeExtractedData(allExtractedData);

      // Show user what data was extracted
      const datosExtraidos = [];
      if (allExtractedData.rfc) datosExtraidos.push(`• **RFC:** ${allExtractedData.rfc}`);
      if (allExtractedData.razon_social) datosExtraidos.push(`• **Razón Social:** ${allExtractedData.razon_social}`);
      if (allExtractedData.nombre) datosExtraidos.push(`• **Nombre:** ${allExtractedData.nombre}`);
      if (allExtractedData.regimen_fiscal) datosExtraidos.push(`• **Régimen Fiscal:** ${allExtractedData.regimen_fiscal}`);
      if (allExtractedData.direccion) datosExtraidos.push(`• **Dirección:** ${allExtractedData.direccion}`);
      if (allExtractedData.codigo_postal) datosExtraidos.push(`• **C.P.:** ${allExtractedData.codigo_postal}`);
      if (allExtractedData.email) datosExtraidos.push(`• **Email:** ${allExtractedData.email}`);
      if (allExtractedData.telefono) datosExtraidos.push(`• **Teléfono:** ${allExtractedData.telefono}`);

      if (datosExtraidos.length > 0) {
        chat.addBotMessage(`📊 **Datos extraídos automáticamente:**

${datosExtraidos.join('\n')}

🔍 *Revisa que la información sea correcta.*`, { agent: 'ARCHIVO' });
      }
    } else {
      chat.addBotMessage(`📊 **Análisis completado**

He analizado ${results.length} documento(s). No se detectaron datos estructurados automáticamente, pero puedes ingresarlos manualmente.`, { agent: 'ARCHIVO' });
    }

    if (!allExtractedData.email && !steps.emailContacto) {
      requestEmail();
    } else {
      showConfirmation();
    }
  }

  const handleFilesSelected = useCallback(async (selectedFiles) => {
    const fileArray = Array.from(selectedFiles);
    await files.handleFileSelect(fileArray);
    
    chat.addUserMessage(`📎 Subiendo ${fileArray.length} archivo(s): ${fileArray.map(f => f.name).join(', ')}`);
    
    const analyzingMsgId = `analyzing-${Date.now()}`;
    chat.addBotMessage('🔍 Analizando documentos con IA...', { agent: 'ARCHIVO', id: analyzingMsgId });

    const filesToAnalyze = fileArray.map((file, index) => ({
      id: `file-${Date.now()}-${index}`,
      file,
      name: file.name,
    }));
    
    try {
      const results = await files.analyzeFiles(filesToAnalyze);
      
      chat.removeMessage(analyzingMsgId);
      
      const successCount = results.filter(r => r.success).length;
      const errorCount = results.filter(r => !r.success).length;
      
      if (errorCount > 0) {
        const errorFiles = results.filter(r => !r.success).map(r => r.fileName || r.file_name).join(', ');
        chat.addBotMessage(`⚠️ Algunos archivos no pudieron analizarse: ${errorFiles}. Puedes continuar con los datos que tenemos o intentar subir nuevamente.`, { agent: 'ARCHIVO' });
      }
      
      if (successCount > 0) {
        // Mostrar detalles de lo que se analizó para dar confianza al usuario
        const successResults = results.filter(r => r.success);
        let detallesAnalisis = successResults.map(r => {
          const nombre = r.fileName || r.file_name || 'Documento';
          const clasificacion = r.classification || 'documento';
          const tipoDoc = clasificacion === 'csf' ? 'Constancia de Situación Fiscal' :
                         clasificacion === 'contrato' ? 'Contrato' :
                         clasificacion === 'factura' ? 'Factura' :
                         clasificacion === 'identificacion' ? 'Identificación' :
                         clasificacion === 'acta_constitutiva' ? 'Acta Constitutiva' :
                         clasificacion === 'poder_notarial' ? 'Poder Notarial' :
                         'Documento General';
          const palabras = r.word_count || (r.extracted_text ? r.extracted_text.split(' ').length : 0);
          return `• **${nombre}** → ${tipoDoc} (${palabras} palabras extraídas)`;
        }).join('\n');

        chat.addBotMessage(`✅ **Análisis completado - ${successCount} archivo(s):**

${detallesAnalisis}

📋 Listo para extraer la información de tus documentos.`, { agent: 'ARCHIVO' });
      } else if (errorCount > 0 && successCount === 0) {
        chat.addBotMessage(`❌ No se pudo analizar ningún archivo. Intenta con otro formato (PDF, DOCX) o ingresa los datos manualmente.`, { agent: 'ARCHIVO' });
      }
    } catch (err) {
      console.error('Error analizando archivos:', err);
      chat.removeMessage(analyzingMsgId);
      chat.addBotMessage(`❌ Error al analizar documentos: ${err.message || 'Error desconocido'}. Puedes intentar nuevamente o ingresar los datos manualmente.`, { agent: 'ARCHIVO' });
    }
    
    setShowFileModal(false);
  }, [files, chat]);

  const requestEmail = useCallback(() => {
    steps.setCurrentStep('request_email');
    chat.addBotMessage(`📧 **¿Cuál es el email de contacto del ${steps.entityType || 'cliente'}?**

Este email se usará para:
- Enviar notificaciones
- Comunicaciones del sistema
- Solicitar documentos adicionales`, { agent: 'ARCHIVO' });
  }, [steps, chat]);

  const showConfirmation = useCallback(() => {
    steps.setShowConfirmation(true);
    chat.addBotMessage('✅ **¡Listo! He recopilado la siguiente información.** Revisa los datos y confirma para crear el registro.', { agent: 'ARCHIVO' });
  }, [steps, chat]);

  const handleConfirmData = useCallback(async () => {
    steps.confirmExtractedData();
    steps.setOnboardingStatus('loading');
    
    chat.addBotMessage(`📋 Creando ${steps.entityType || 'cliente'}...`, { agent: 'ARCHIVO' });

    try {
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        throw new Error('No estás autenticado. Por favor, inicia sesión primero.');
      }

      const response = await fetch('/api/archivo/crear-entidad', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          tipo: steps.entityType || 'cliente',
          datos: steps.extractedData,
          email_contacto: steps.emailContacto || steps.extractedData?.email || '',
          archivos_ids: []
        })
      });

      // Leer como text primero para evitar "Body is disturbed or locked"
      const responseText = await response.text();
      let data;
      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch (parseErr) {
        console.error('[ChatbotArchivo] JSON parse error:', parseErr, 'Response:', responseText.substring(0, 200));
        throw new Error(`Respuesta inválida del servidor: ${responseText.substring(0, 100)}`);
      }

      if (!response.ok) {
        throw new Error(data.detail || `Error del servidor (${response.status})`);
      }

      steps.setOnboardingStatus('completed');
      steps.setShowConfirmation(false);

      chat.addBotMessage(`🎉 **¡${steps.entityType === 'proveedor' ? 'Proveedor' : 'Cliente'} creado exitosamente!**

**${steps.extractedData?.nombre || steps.extractedData?.razon_social}**
RFC: ${steps.extractedData?.rfc || 'N/A'}

✅ Registro creado en el sistema
✅ Documentos guardados en su expediente
${steps.emailContacto ? `✅ Se enviará email de bienvenida a ${steps.emailContacto}` : ''}

Puedes editar este ${steps.entityType || 'cliente'} desde el **Panel de Administración**.`, {
        agent: 'ARCHIVO',
        suggestions: [
          { text: 'Dar de alta otro', value: 'nuevo' },
          { text: 'Ir al Dashboard', value: 'dashboard' },
        ],
      });

    } catch (error) {
      steps.setOnboardingStatus('error');
      chat.addBotMessage(`⚠️ Error creando ${steps.entityType || 'cliente'}: ${error.message}`, { agent: 'ARCHIVO' });
    }
  }, [steps, chat]);

  const handleResetOnboarding = useCallback(() => {
    steps.resetOnboarding();
    files.clearAllFiles();
    chat.clearMessages();
    
    setTimeout(() => {
      chat.addBotMessage(`¡Hola! 👋 ¿Qué quieres dar de alta hoy?`, {
        agent: 'ARCHIVO',
        suggestions: [
          { text: 'Registrar cliente', value: 'cliente' },
          { text: 'Registrar proveedor', value: 'proveedor' },
        ],
      });
      steps.setCurrentStep('select_type');
    }, 300);
  }, [steps, files, chat]);

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
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

          {steps.entityType && (
            <div className="mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
              <p className="text-sm text-gray-300">
                Registrando: <span className="font-semibold text-indigo-400">{steps.entityType === 'cliente' ? 'Cliente' : 'Proveedor'}</span>
              </p>
            </div>
          )}

          {typeof steps.currentStep === 'number' && (
            <ProgressIndicator
              steps={steps.steps}
              currentStep={steps.currentStep}
              onStepClick={steps.goToStep}
            />
          )}

          <button
            onClick={handleResetOnboarding}
            className="w-full mt-4 px-4 py-2 text-sm text-gray-400 hover:text-gray-200 hover:bg-white/10 rounded-lg transition-colors"
          >
            🔄 Empezar de nuevo
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col">
        <header className="lg:hidden bg-black/30 backdrop-blur-sm border-b border-white/10 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">📁</span>
            <h1 className="font-semibold text-gray-100">ARCHIVO</h1>
          </div>
          {steps.entityType && (
            <span className="text-sm text-indigo-400">
              {steps.entityType === 'cliente' ? 'Cliente' : 'Proveedor'}
            </span>
          )}
        </header>

        <MessageList
          messages={chat.messages}
          isTyping={chat.isTyping}
          currentAgent="ARCHIVO"
          onSuggestionClick={handleSuggestionClick}
          className="flex-1"
        />

        {(api.lastError || steps.onboardingError) && (
          <div className="px-4">
            <ErrorMessage
              message={api.lastError || steps.onboardingError}
              onDismiss={() => {
                api.clearError();
                steps.clearError();
              }}
            />
          </div>
        )}

        <ChatInput
          onSend={handleSendMessage}
          onAttach={() => setShowFileModal(true)}
          disabled={chat.isTyping || chat.isStreaming || api.isSearchingWeb}
          placeholder={
            steps.entityType
              ? `Escribe aquí para continuar con el registro del ${steps.entityType}...`
              : 'Escribe aquí para comenzar...'
          }
        />
      </main>

      <Modal
        isOpen={showFileModal}
        onClose={() => setShowFileModal(false)}
        title="Subir documentos"
        size="lg"
      >
        <FileUploadArea
          onFilesSelected={handleFilesSelected}
          uploadedFiles={files.uploadedFiles}
          isProcessing={files.isProcessingFile}
          onRemoveFile={files.removeFile}
        />

        {files.uploadedFiles.length > 0 && (
          <div className="mt-4 flex justify-end gap-3">
            <button
              onClick={() => setShowFileModal(false)}
              className="px-4 py-2 text-gray-300 hover:bg-white/10 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={async () => {
                await files.uploadFilesToCloud();
                setShowFileModal(false);
              }}
              disabled={files.isUploadingDocuments}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {files.isUploadingDocuments ? 'Subiendo...' : 'Confirmar'}
            </button>
          </div>
        )}
      </Modal>

      <Modal
        isOpen={steps.showConfirmation}
        onClose={() => steps.setShowConfirmation(false)}
        title="Confirmar información"
        size="lg"
      >
        <ConfirmationCard
          data={{ ...steps.collectedData, ...steps.extractedData, email: steps.emailContacto || steps.extractedData?.email }}
          onConfirm={handleConfirmData}
          onEdit={() => {
            steps.setShowConfirmation(false);
            chat.addBotMessage('¿Qué datos necesitas corregir?', { agent: 'ARCHIVO' });
          }}
          onCancel={() => steps.setShowConfirmation(false)}
          isLoading={steps.onboardingStatus === 'loading'}
          fieldLabels={{
            rfc: 'RFC',
            razon_social: 'Razón Social',
            nombre: 'Nombre',
            nombreComercial: 'Nombre Comercial',
            regimenFiscal: 'Régimen Fiscal',
            domicilioFiscal: 'Domicilio Fiscal',
            direccion: 'Dirección',
            email: 'Email',
            telefono: 'Teléfono',
            giro: 'Giro',
          }}
        />
      </Modal>
    </div>
  );
};

export default ChatbotArchivo;
