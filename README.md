# Agent Network System - Trazabilidad de Servicios Intangibles

Sistema completo de red de agentes IA para trazabilidad de servicios intangibles y consultorías especializadas, implementando un flujo de 5 etapas con múltiples agentes que interactúan entre sí.

## 🎯 Descripción del Sistema

Este sistema simula una red de agentes IA con personalidades únicas que colaboran para gestionar proyectos de consultoría especializada, proporcionando trazabilidad completa desde la iniciativa hasta el cierre.

### Agentes Configurados

1. **María Rodríguez (A1-Sponsor)** - GPT-5
   - Directora de Estrategia
   - Validación estratégica y BEE
   - Email: maria.rodriguez@revisar.ia

2. **Carlos Mendoza (A2-PMO)** - Claude Sonnet 4
   - Gerente de PMO
   - Consolidación y gestión documental
   - Email: carlos.mendoza@revisar.ia

3. **Laura Sánchez (A3-Fiscal)** - Claude Sonnet 4
   - Especialista Fiscal
   - Análisis de cumplimiento normativo mexicano
   - Email: laura.sanchez@revisar.ia

4. **Roberto Torres (A5-Finanzas)** - GPT-5
   - Director Financiero
   - Verificación presupuestal y 3-Way Match
   - Email: roberto.torres@revisar.ia

5. **Ana García (PROVEEDOR_IA)** - GPT-5
   - Consultora Senior de ProveedorIA
   - Ejecución de servicios especializados
   - Email: ana.garcia@proveedoria.com

## 📋 Flujo de 5 Etapas

### Etapa 1: INTAKE Y VALIDACIÓN ESTRATÉGICA (Fase 0)
- Recepción de Strategic Initiative Brief (SIB)
- Validación estratégica (A1-Sponsor)
- Validación fiscal (A3-Fiscal)
- Consolidación (A2-PMO)
- Aprobación directiva

### Etapa 2: FORMALIZACIÓN LEGAL Y FINANCIERA (Fases 1 y 2)
- Selección de proveedor
- Verificación presupuestal (A5-Finanzas)
- Generación de PO (Purchase Order)
- Generación contractual (requiere intervención humana)
- Firma y validación

### Etapa 3: EJECUCIÓN Y MONITOREO (Fases 3 y 4)
- Ejecución del servicio (Proveedor)
- Monitoreo de materialidad (A3-Fiscal)
- Gestión de cronograma (A2-PMO)
- Generación de evidencia digital

### Etapa 4: ENTREGA Y AUDITORÍA (Fases 5, 6 y 7)
- Recepción de entregables
- Validación técnica (A1-Sponsor)
- Auditoría de cumplimiento (A3-Fiscal)
- Generación de VBC (Visto Bueno de Cumplimiento)

### Etapa 5: CIERRE Y MEDICIÓN DE IMPACTO (Fases 8 y 9)
- 3-Way Match (A5-Finanzas)
- Proceso de pago
- Medición de impacto real vs. esperado
- Validación de trazabilidad posterior
- Cierre del proyecto

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web asíncrono
- **MongoDB**: Base de datos para proyectos, agentes e interacciones
- **Emergent LLM Key**: Llave universal para GPT-5 y Claude Sonnet 4
- **Google APIs**: Gmail API y Drive API (preparados para integración)
- **Wufoo API**: Integración de formularios (preparado)

### Frontend
- **React 19**: Interfaz de usuario moderna
- **Tailwind CSS**: Diseño responsivo
- **Axios**: Cliente HTTP
- **React Router**: Navegación

## 🚀 API Endpoints

### Webhooks (Integración Wufoo)
- `POST /api/webhooks/wufoo` - **Webhook principal para recibir formularios de Wufoo automáticamente**
- `GET /api/webhooks/wufoo/test` - Verificar que el webhook está activo
- `POST /api/webhooks/wufoo/simulate` - Simular una submisión de Wufoo (para pruebas)

### Proyectos
- `POST /api/projects/submit` - Enviar nuevo proyecto (Stage 1)
- `POST /api/projects/{project_id}/stage2` - Ejecutar Stage 2
- `POST /api/projects/{project_id}/stage3` - Ejecutar Stage 3
- `POST /api/projects/{project_id}/stage4` - Ejecutar Stage 4
- `POST /api/projects/{project_id}/stage5` - Ejecutar Stage 5
- `GET /api/projects/{project_id}/status` - Obtener estado del proyecto
- `GET /api/projects/` - Listar todos los proyectos

### Agentes
- `GET /api/agents/` - Listar todos los agentes
- `GET /api/agents/{agent_id}` - Información de un agente
- `POST /api/agents/{agent_id}/analyze` - Solicitar análisis a un agente
- `GET /api/agents/interactions/recent` - Interacciones recientes

## 🔗 Integración Automática con Wufoo

El sistema está configurado para **iniciar automáticamente el flujo** cuando se envía un formulario en Wufoo:

1. Usuario completa formulario SIB en Wufoo
2. Wufoo envía webhook → `POST /api/webhooks/wufoo`
3. Sistema inicia automáticamente Stage 1 (validaciones)
4. Proyecto aparece en el dashboard con interacciones de agentes

**Ver instrucciones completas:** [WUFOO_SETUP.md](/app/WUFOO_SETUP.md)

**URL del Webhook:** `https://enterprise-ai-agents-2.preview.emergentagent.com/api/webhooks/wufoo`

## 📊 Dashboard Frontend

Accede al dashboard en: `https://enterprise-ai-agents-2.preview.emergentagent.com`

Documentación API: `https://enterprise-ai-agents-2.preview.emergentagent.com/docs`
