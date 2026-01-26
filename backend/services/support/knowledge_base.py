"""
Knowledge Base for Revisar.IA Support Chatbot
Contains detailed information about the platform, features, and common questions.
"""

SOPORTE_KNOWLEDGE_BASE = """
# BASE DE CONOCIMIENTO - REVISAR.IA

## ¿Qué es Revisar.IA?

Revisar.IA es una **plataforma de auditoría fiscal inteligente** diseñada para empresas mexicanas. 
Utiliza inteligencia artificial avanzada para analizar y validar operaciones con proveedores de servicios intangibles,
asegurando el cumplimiento fiscal antes de que el SAT realice una auditoría.

La plataforma ayuda a las empresas a:
- Validar la materialidad y sustancia de operaciones con proveedores
- Detectar riesgos fiscales potenciales relacionados con el Artículo 69-B del CFF
- Generar expedientes de defensa sólidos
- Automatizar el análisis de contratos, facturas y evidencias
- Obtener una puntuación de riesgo para cada proveedor y operación

## Funcionalidades Principales

### 1. Dashboard
Panel central que muestra:
- Proyectos activos y su estado
- Estadísticas de aprobación/rechazo
- Alertas de riesgo fiscal
- Acceso rápido a todas las funciones

### 2. Registro de Empresa
- Dar de alta tu empresa con RFC y datos fiscales
- Configurar preferencias y usuarios
- Establecer políticas internas de cumplimiento

### 3. Gestión de Proveedores
- Agregar y administrar proveedores
- Cargar documentos (contratos, facturas, CFDIs)
- Verificar estatus en listas del SAT (69-B)
- Análisis OCR automático de documentos

### 4. Diagnóstico Fiscal
Sistema de 8 fases para analizar operaciones:
- F0: Recepción y clasificación inicial
- F1: Análisis de tipología del servicio
- F2: Verificación de sustancia económica
- F3: Validación de materialidad
- F4: Análisis financiero y razonabilidad
- F5: Revisión legal de contratos
- F6: Validación de evidencias de proveedor
- F7: Generación del expediente de defensa

### 5. Defense File (Expediente de Defensa)
Documento integral que incluye:
- Análisis de cada agente especializado
- Evidencias organizadas
- Justificación fiscal detallada
- Recomendaciones de mejora
- Historial de versiones

### 6. Templates y Plantillas
- Contratos tipo para diferentes servicios
- Checklists de evidencias requeridas
- Formatos de actas de trabajo
- Plantillas para minutas

## Agentes de IA Especializados

### A1 - Agente de Estrategia (Sponsor)
Valida la alineación estratégica de contrataciones con objetivos corporativos.
Evalúa razón de negocio y beneficio económico real.

### A3 - Agente Fiscal
Especialista en normativa fiscal mexicana (CFF, LISR, LIVA).
Analiza cumplimiento con artículos 5-A, 69-B y criterios del SAT.

### A5 - Agente Financiero
Valida razonabilidad de montos, precios de mercado y ROI.
Realiza análisis de three-way-match (contrato-factura-evidencia).

### A6 - Agente de Proveedor
Valida la existencia y capacidad real del proveedor.
Verifica entregables y evidencias de ejecución.

### A7 - Agente de Defensa
Genera el expediente de defensa final.
Consolida análisis de todos los agentes.

### A4 - Agente Legal
Revisa contratos y documentación legal.
Valida cláusulas de materialidad y alcance.

## Cómo Usar la Plataforma

### Primer Acceso
1. Ingresa a revisar.ia
2. Regístrate con tu correo empresarial
3. Recibirás un código de verificación por email
4. Completa tu perfil con datos de la empresa

### Registrar Empresa
1. Ve a "Onboarding" desde el menú
2. Ingresa razón social y RFC
3. Proporciona datos de industria y facturación
4. Opcionalmente sube documentos de muestra
5. El sistema configurará tu cuenta

### Agregar Proveedor
1. Accede a "Proveedores" en el menú
2. Haz clic en "Nuevo Proveedor"
3. Ingresa RFC y datos básicos
4. Sube contratos y facturas relacionadas
5. El sistema verificará automáticamente contra listas SAT

### Crear Proyecto de Auditoría
1. Desde el Dashboard, clic en "Nuevo Proyecto"
2. Selecciona empresa y proveedor
3. Define tipo de servicio y monto
4. Adjunta documentos relevantes
5. El sistema iniciará el diagnóstico automático

### Revisar Resultados
1. Accede al proyecto desde el Dashboard
2. Revisa el scoring de riesgo
3. Lee los análisis de cada agente
4. Descarga el expediente de defensa
5. Implementa recomendaciones si es necesario

## Preguntas Frecuentes (FAQs)

### ¿Qué documentos necesito para el análisis?
- Contrato de servicios vigente
- CFDIs/Facturas relacionadas
- Evidencias de entregables (reportes, minutas, correos)
- Datos del proveedor (constancia de situación fiscal)

### ¿Cuánto tiempo tarda el análisis?
- Análisis inicial: 5-10 minutos
- Diagnóstico completo: 15-30 minutos
- Expediente de defensa: 1-2 horas (dependiendo complejidad)

### ¿Qué significa el score de riesgo?
- 0-30: Riesgo Alto (requiere atención inmediata)
- 31-60: Riesgo Medio (mejoras recomendadas)
- 61-80: Riesgo Bajo (operación razonable)
- 81-100: Riesgo Muy Bajo (operación bien documentada)

### ¿Qué es el Artículo 69-B del CFF?
Es la disposición que permite al SAT detectar y publicar empresas que facturan operaciones simuladas (EFOS).
Revisar.IA te ayuda a validar que tus proveedores no estén en estas listas y que tus operaciones tengan sustancia real.

### ¿Puedo exportar los reportes?
Sí, todos los reportes se pueden descargar en formato PDF.
Los expedientes de defensa incluyen todos los análisis y evidencias organizadas.

### ¿Es segura mi información?
- Toda la información se maneja de forma confidencial
- Usamos encriptación para datos sensibles
- No compartimos información con terceros
- Cumplimos con regulaciones de protección de datos

## Errores Comunes y Soluciones

### "No se pudo cargar el documento"
- Verifica que el archivo sea PDF, DOCX o imagen
- El tamaño máximo es 10MB
- Intenta con un archivo de menor resolución

### "RFC inválido"
- Verifica que el RFC tenga el formato correcto (12-13 caracteres)
- Personas morales: 3 letras + 6 dígitos + 3 caracteres
- Personas físicas: 4 letras + 6 dígitos + 3 caracteres

### "Sesión expirada"
- Por seguridad, la sesión expira después de inactividad
- Vuelve a iniciar sesión con tu correo
- Usa "Recordar sesión" para mayor comodidad

### "Error al procesar factura"
- Verifica que el XML o PDF sea válido
- Asegúrate de que sea un CFDI 4.0 vigente
- Intenta subirlo nuevamente

### "Proveedor no encontrado en SAT"
- Verifica que el RFC esté correcto
- El proveedor puede ser nuevo y aún no estar en listados
- Procede con precaución y documenta exhaustivamente

## Información de Contacto

### Soporte Técnico
📧 Email: soporte@revisar.ia
📞 Horario: Lunes a Viernes, 9:00 - 18:00 (CDMX)

### Ventas y Demos
📧 Email: ventas@revisar.ia
💼 Solicita una demostración personalizada

### Facturación
📧 Email: facturacion@revisar.ia

## Actualizaciones Recientes

- **Enero 2026**: Nueva interfaz de Dashboard
- **Diciembre 2025**: Integración con SAT para consulta de CFDIs
- **Noviembre 2025**: Agente A7 de Defensa mejorado
- **Octubre 2025**: Templates RAG para diferentes tipologías

---
Para más información, visita nuestra documentación completa o contacta a soporte.

## ESCALACIÓN A SOPORTE HUMANO

Cuando el usuario pide hablar con una persona/humano, dice que no le ayudaste, tiene problema muy complejo, menciona urgencia extrema, está frustrado o pide contacto directo, debes incluir [WHATSAPP_BUTTON] en tu respuesta.

Ejemplo:
"Entiendo que necesitas atención personalizada. 👤

Te conecto con nuestro equipo de soporte humano por WhatsApp:

[WHATSAPP_BUTTON]

Un asesor te atenderá lo antes posible."
"""
