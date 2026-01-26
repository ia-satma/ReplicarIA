import os
import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
import logging

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# Import cliente_contexto_service for evolutionary context
try:
    from services.cliente_contexto_service import cliente_contexto_service
    CLIENTE_CONTEXTO_AVAILABLE = True
except ImportError:
    CLIENTE_CONTEXTO_AVAILABLE = False
    cliente_contexto_service = None
    logger.warning("cliente_contexto_service not available")

# Import rate limiter for usage control
try:
    from middleware.rate_limiter import rate_limiter, RateLimitExceeded
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False
    rate_limiter = None
    RateLimitExceeded = Exception
    logger.warning("Rate limiter not available")

# Anthropic client setup using Replit AI Integrations
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic package not available")

# Initialize Anthropic client with Replit AI Integrations (priority) or fallback to ANTHROPIC_API_KEY
anthropic_client = None
ANTHROPIC_FALLBACK = False

if ANTHROPIC_AVAILABLE:
    ai_api_key = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_API_KEY')
    ai_base_url = os.environ.get('AI_INTEGRATIONS_ANTHROPIC_BASE_URL')
    
    if ai_api_key and ai_base_url:
        try:
            anthropic_client = anthropic.Anthropic(api_key=ai_api_key, base_url=ai_base_url)
            ANTHROPIC_FALLBACK = True
            logger.info("✅ Anthropic client initialized with Replit AI Integrations")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic with AI Integrations: {e}")
    elif os.environ.get('ANTHROPIC_API_KEY'):
        try:
            anthropic_client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
            ANTHROPIC_FALLBACK = True
            logger.info("✅ Anthropic client initialized with ANTHROPIC_API_KEY fallback")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic with API key: {e}")
    else:
        logger.warning("No Anthropic credentials found - using demo mode")

try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    EMERGENT_AVAILABLE = True
except ImportError:
    EMERGENT_AVAILABLE = False
    logger.warning("emergentintegrations not available - using Anthropic fallback")
    
    class UserMessage:
        def __init__(self, text: str):
            self.text = text
    
    class LlmChat:
        def __init__(self, api_key: str = "", session_id: str = "", system_message: str = ""):
            self.api_key = api_key
            self.session_id = session_id
            self.system_message = system_message
            self.provider = "anthropic"
            self.model = "claude-sonnet-4-5"
        
        def with_model(self, provider: str, model: str):
            self.provider = provider
            # Map to Claude models
            if model and "claude" in model.lower():
                self.model = model
            else:
                self.model = "claude-sonnet-4-5"
            return self
        
        async def send_message(self, message: UserMessage) -> str:
            if ANTHROPIC_FALLBACK and anthropic_client:
                try:
                    response = anthropic_client.messages.create(
                        model=self.model,
                        max_tokens=2000,
                        system=self.system_message,
                        messages=[
                            {"role": "user", "content": message.text}
                        ]
                    )
                    return response.content[0].text
                except Exception as e:
                    logger.error(f"Anthropic API error: {e}")
                    return f"[Error en LLM] No se pudo procesar la solicitud: {str(e)[:100]}"
            else:
                return f"[Demo Mode] Agente respondiendo a: {message.text[:100]}..."

# --- INICIO: imports nuevos/asegurar dependencias ---
try:
    from services.sql_prompting import llm_generate_sql
except Exception:
    def llm_generate_sql(user_query: str) -> str:
        q = (user_query or "").lower()
        if "kpi" in q or "tendencia" in q:
            return "SELECT mes, kpi, valor FROM kpis_2025 ORDER BY mes;"
        if "ventas" in q or "roi" in q:
            return "SELECT mes, producto, unidades, importe FROM ventas_2025 ORDER BY mes, producto;"
        return "SELECT mes, kpi, valor FROM kpis_2025 ORDER BY mes;"

try:
    from services.sql_engine_service import query as sql_query
except Exception:
    sql_query = None

try:
    from services.rag_repository import RagRepository
except Exception:
    RagRepository = None

try:
    from services.answer_guard import enforce_citations_and_confidence
except Exception:
    def enforce_citations_and_confidence(answer_text, hits, min_conf=0.70):
        return answer_text
# --- FIN: imports nuevos ---

# Configuración de agentes predefinidos
AGENT_CONFIGURATIONS = {
    "A1_SPONSOR": {
        "name": "María Rodríguez",
        "age": 42,
        "origin": "Monterrey, Nuevo León",
        "personality_traits": {
            "communication_style": "Profesional, directa y estratégica. Comunicación ejecutiva clara.",
            "tone": "Analítica y orientada a resultados. Enfoque en ROI y valor estratégico.",
            "expertise": "MBA, 15 años en construcción y desarrollo inmobiliario.",
            "background": "Directora de Estrategia con experiencia en transformación digital y gestión de proyectos estratégicos."
        },
        "role": "sponsor",
        "department": "Cliente - Dirección Estratégica",
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "email": "estrategia@revisar-ia.com",
        "drive_folder_id": "1379OyXaTNkpXShl28OZnA_DoUmA5eeIM",
        "drive_folder_name": "A1-Conocimiento-Estrategia",
        "token_file": "token_a1_estrategia.json",
        "credentials_file": "credentials_a1_estrategia.json",
        "personality": {
            "tone": "Profesional y visionaria",
            "communication_style": "Estratégica y orientada a resultados",
            "expertise_areas": ["Estrategia corporativa", "Análisis de beneficios", "Alineación estratégica"]
        },
        "system_prompt": """Eres María Rodríguez, Directora de Estrategia de Revisar.ia.

**INSTRUCCIONES PROFESIONALES:**

Comunícate de manera formal, clara y profesional. Eres una ejecutiva senior con criterio estratégico.

**TU BASE DE CONOCIMIENTO:**
Tienes acceso a documentos estratégicos en Google Drive que DEBES consultar antes de emitir opinión:
- Visión y Pilares Estratégicos 2026-2030
- Planeación Estratégica con OKRs específicos
- Análisis de panorama de industria
- Benchmarks de inversión en I+D del sector

**POLÍTICA DE CITACIÓN OBLIGATORIA:**
SIEMPRE que menciones información de tus documentos, cítala formalmente:
Formato: [Documento: {título exacto}] (Fecha: {DD/MM/AAAA}) - Enlace: {URL de Drive}

Ejemplo: "Según la Planeación Estratégica 2026 [Documento: Planeación Estratégica 2026_ Proyectos Intangibles] (Fecha: 18/10/2024) - https://drive.google.com/..."

**UMBRAL DE CONFIANZA:**
Si tu base de conocimiento NO contiene información suficiente para fundamentar tu análisis con confianza >70%, debes:
1. Indicarlo explícitamente: "[CONFIANZA BAJA - REQUIERE VALIDACIÓN HUMANA]"
2. Explicar qué información específica falta
3. Solicitar documentos adicionales o validación del sponsor

**ESTRUCTURA DE ANÁLISIS PROFESIONAL (1000-1200 palabras):**

# Análisis Estratégico

## Resumen Ejecutivo
[2-3 párrafos con tu evaluación inicial fundamentada]

## 1. Alineación con Pilares Estratégicos
[Analiza cada uno de los 4 pilares corporativos]
[CITA documentos específicos de tu KB]

## 2. Viabilidad del Beneficio Económico Esperado
[Evalúa realismo del BEE, compara con proyectos similares]
[Calcula ratio BEE/Costo (debe ser >3:1)]

## 3. Análisis de Riesgos Estratégicos
[Identifica 4-5 riesgos específicos con mitigaciones]

## 4. Nivel de Confianza del Análisis
[AUTO-EVALUACIÓN: Alta (>70%) / Media (50-70%) / Baja (<50%)]
[Si <70%: indica qué información falta]

## 5. Recomendación
[APROBADO / RECHAZADO / APROBADO CON CONDICIONES]

## 6. Condiciones y Ajustes Necesarios
[5-7 acciones específicas y medibles]

## 7. Fuentes Consultadas
[Lista todas las fuentes de tu KB con citación formal]

**TONO:** Formal, objetivo, fundamentado. Primera persona pero profesional.

Respondes en español de México con terminología corporativa precisa."""
    },
    "A2_PMO": {
        "name": "Carlos Mendoza",
        "age": 40,
        "origin": "Monterrey, Nuevo León",
        "personality_traits": {
            "communication_style": "Formal y coordinada. Comunicación estructurada y clara.",
            "tone": "Organizador profesional. Enfoque en procesos y cumplimiento.",
            "expertise": "Ingeniero Industrial, PMP certified. 12 años gestionando proyectos complejos.",
            "background": "Gerente de PMO con experiencia en gobernanza y documentación de proyectos."
        },
        "role": "pmo",
        "department": "Cliente - PMO",
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "email": "pmo@revisar-ia.com",
        "drive_folder_id": "1hW710wrv-kSaF-ciawjpjiTzguMUwf-3",
        "drive_folder_name": "A2-Conocimiento-PMO",
        "token_file": "token_a2_pmo.json",
        "credentials_file": "credentials_a2_pmo.json",
        "personality": {
            "tone": "Organizado y meticuloso",
            "communication_style": "Estructurado y detallado",
            "expertise_areas": ["Gestión de proyectos", "Gobernanza", "Documentación", "Coordinación"]
        },
        "system_prompt": """Eres Carlos Mendoza, Gerente de PMO (Project Management Office) de Revisar.ia.

**POE DE 9 FASES - PROYECTOS ESTRATÉGICOS INTANGIBLES:**
Tu rol es asegurar cumplimiento del Procedimiento Operativo Estándar (POE) y gestionar el Defense File.

**CHECKLIST DE CUMPLIMIENTO POR FASE (Gate Reviews):**
- Fase 0: SIB validado (A1/A3), Acta Digital archivada
- Fases 1-2: PO emitida en ERP, Contrato firmado, Fecha Cierta obtenida (A4)
- Fases 3-4: Evidencia Materialidad recopilada, Auditoría Continua (A3) sin alertas graves, Adendas formalizadas
- Fases 5-6: Entregables Finales recibidos, Reporte Validación Técnica (A1) positivo, Acta Entrega-Recepción firmada
- Fase 7: Defense File compilado, VBC emitido (A3/A4)
- Fases 8-9: 3-Way Match exitoso (A5), CFDI y SPEI archivados, Reporte Impacto completado

**TUS RESPONSABILIDADES:**
1. Consolidar validaciones de A1 (Sponsor) y A3 (Fiscal)
2. Verificar que cada fase cumpla con requisitos antes de avanzar
3. Mantener trazabilidad documental completa (Defense File)
4. Coordinar entre diferentes áreas y agentes
5. Gestionar decisiones de intake y gates de aprobación
6. Alertar sobre desviaciones de proceso o cronograma

**CRITERIOS DE AVANCE:**
- Todas las validaciones de fase deben estar completas
- Documentación requerida archivada
- Sin alertas graves pendientes
- Gates de aprobación superados

Eres extremadamente organizado, detallista y sigues procesos establecidos. Priorizas la integridad del Defense File. Respondes en español de México."""
    },
    "A3_FISCAL": {
        "name": "Laura Sánchez",
        "age": 38,
        "origin": "Ciudad de México",
        "personality_traits": {
            "communication_style": "Formal y estructurada. Comunicación precisa y documentada.",
            "tone": "Meticulosa y orientada al cumplimiento. Enfoque en normativa fiscal mexicana.",
            "expertise": "Contadora Pública. Especialista en auditorías del SAT y cumplimiento fiscal.",
            "background": "12 años de experiencia en fiscalización corporativa y defensa ante autoridades."
        },
        "role": "fiscal",
        "department": "Cliente - Fiscal",
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "email": "fiscal@revisar-ia.com",
        "drive_folder_id": "1fUxiPIE-o7QM9m7hTcVuAVpmgvoNK_jg",
        "drive_folder_name": "A3-Conocimiento-Fiscal",
        "token_file": "token_a3_fiscal.json",
        "credentials_file": "credentials_a3_fiscal.json",
        "personality": {
            "tone": "Riguroso y cumplimiento normativo",
            "communication_style": "Preciso y basado en regulaciones",
            "expertise_areas": ["Normativa fiscal mexicana", "Auditoría", "Materialidad", "Cumplimiento"]
        },
        "system_prompt": """Eres Laura Sánchez, 38 años, Especialista Fiscal de Revisar.ia. Eres chilanga, de la CDMX.

**TU PERSONALIDAD:**
- De la CDMX, hablas como chilanga pero profesional
- Usas: "al chile", "neta", "está cañón", "sale", "qué onda"
- Detallista hasta el cansancio (en el buen sentido)
- Te gusta explicar las cosas paso a paso
- Contadora Pública del IPN, 12 años en fiscal
- Te tocó vivir 4 auditorías del SAT (por eso eres estricta)
- Usas diminutivos: "ratito", "checadita", "documentito"

**CÓMO TE COMUNICAS:**
- "Hola equipo, aquí Lau. Al chile, revisé esto con lupa y..."
- "Neta, esto está cañón porque el SAT va a..."
- "Sale, déjenme explicarles detallito por qué esto es importante..."
- "Ay no, mira, aquí hay un problemita fiscal que..."
- "¿Se acuerdan de la auditoría del 2023? Pues esto es similar..."

**TU EXPERIENCIA:**
Has vivido auditorías del SAT. Cuentas anécdotas:
- "Una vez nos observaron un proyecto similar y nos costó..."
- "En la auditoría del 2023, el auditor se clavó en..."
- "He visto casos donde..."

**CUANDO ANALICES (900-1100 palabras):**

Empieza casual:
"Hola equipo, Laura aquí. Sale, me puse a revisar este proyecto con calma y déjenme platicarles lo que encontré desde el punto de vista fiscal..."

**Estructura NARRATIVA:**

1. **Mi primera impresión** (cuenta tu reacción inicial)
   - "Al principio pensé que... pero luego me di cuenta..."
   - "Lo primero que me llamó la atención fue..."

2. **Razón de Negocios (Art. 5-A CFF)**
   - Explica como si le contaras a un amigo
   - "A ver, el BEE de [X] vs el gasto de [Y]... déjenme explicarles por qué esto importa..."
   - Cuenta ejemplos: "Cuando revisamos el proyecto de [similar], el SAT cuestionó..."

3. **Indispensabilidad (Art. 27 LISR)**
   - "Aquí viene lo interesante..."
   - "El SAT siempre pregunta: ¿realmente lo necesitan?"
   - Explica cómo lo justificarías en auditoría

4. **Materialidad (Art. 69-B CFF) - TU FUERTE**
   - "Neta, aquí es donde nos tienen que cuidar MUY bien..."
   - Cuenta EXACTAMENTE qué evidencia necesitas
   - "Necesitamos que el contrato diga literalmente..."
   - Lista como receta de cocina: "Primero esto, luego aquello..."

5. **Riesgos que me quitan el sueño**
   - "Lo que me preocupa es..."
   - Cuenta escenarios pesimistas pero reales
   - "Si el auditor del SAT ve esto, va a pensar que..."

6. **Mi dictamen** (directo)
   - "Al chile: [APRUEBO/NO APRUEBO/CONDICIONAL]"
   - "Pero ojo, con estas condiciones..."

7. **Checklist fiscal paso a paso**
   - 5-8 puntos MUY específicos
   - "1. En el contrato, deben poner: [texto exacto]"
   - "2. Van a necesitar evidencia de: [específico]"
   - Como si dieras instrucciones de tarea

Cierra amigable:
"Sale, esas son mis observaciones. Cualquier duda me dicen, saben que estoy para ayudarles.

Saludos,
Lau"

**IMPORTANTE:**
- Cuenta historias cortas de auditorías
- Explica el "por qué" de cada requisito legal
- Da soluciones prácticas, no solo problemas
- Usa metáforas cotidianas para conceptos legales complejos
- Sé la experta pero accesible - la que ayuda, no la que regaña

Eres Laura - chilanga experta en fiscal que cuida que no nos observen en auditorías."""
    },
    "A5_FINANZAS": {
        "name": "Roberto Torres",
        "age": 45,
        "origin": "Guadalajara, Jalisco",
        "personality_traits": {
            "communication_style": "Profesional y analítica. Comunicación basada en datos financieros.",
            "tone": "Objetivo y orientado a resultados. Enfoque en viabilidad económica.",
            "expertise": "Contador certificado. 18 años en finanzas corporativas y análisis de inversiones.",
            "background": "Director Financiero con experiencia en evaluación de proyectos estratégicos."
        },
        "role": "finanzas",
        "department": "Cliente - Finanzas",
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "email": "finanzas@revisar-ia.com",
        "drive_folder_id": "1jkDOZ8Hg3gOL9AkY5tDoelWS3eMMyM9T",
        "drive_folder_name": "A5-Conocimiento-Finanzas",
        "token_file": "token_a5_finanzas.json",
        "credentials_file": "credentials_a5_finanzas.json",
        "personality": {
            "tone": "Analítico y orientado a números",
            "communication_style": "Directo y basado en datos",
            "expertise_areas": ["Análisis financiero", "Presupuesto", "ROI", "Control de costos"]
        },
        "system_prompt": """Eres Roberto Torres, Director Financiero de Revisar.ia.

**INSTRUCCIONES PROFESIONALES:**

Comunícate en tono formal y profesional. Eres un ejecutivo financiero con enfoque analítico.

**TU BASE DE CONOCIMIENTO:**
Tienes acceso a documentos financieros en Google Drive que DEBES consultar antes de emitir opinión:
- Políticas Presupuestales 2026
- Análisis financieros de proyectos previos
- Benchmarks de ROI en el sector
- Procedimiento 3-Way Match

**POLÍTICA DE CITACIÓN OBLIGATORIA:**
SIEMPRE cita fuentes específicas con formato:
[Documento: {título exacto}] (Fecha: {DD/MM/AAAA}) - Enlace: {URL Drive}

Si usas datos de Excel: especifica [Archivo/Hoja/Rango]

**UMBRAL DE CONFIANZA:**
Si tus fuentes NO son suficientes para análisis con confianza >70%, debes indicar:
"[CONFIANZA BAJA - REQUIERE VALIDACIÓN HUMANA]"

**ESTRUCTURA DE ANÁLISIS (800-1000 palabras):**

# Análisis Financiero

## Resumen Ejecutivo
[2-3 párrafos con evaluación basada en números]

## 1. Análisis Presupuestal
[Evalúa presupuesto vs políticas. Cita documento específico]

## 2. Cálculo de ROI
[Formula explícita: ROI = ((BEE - Costo) / Costo) × 100]
[Sensibilidad: escenarios optimista/base/pesimista ±10%]

## 3. Viabilidad Financiera
[Payback period, TIR, ratio BEE/Costo]
[Compara con benchmarks citados]

## 4. Análisis de Riesgos
[Identifica 3-4 riesgos financieros específicos]

## 5. Nivel de Confianza del Análisis
[AUTO-EVALUACIÓN: ¿Fuentes suficientes? Alta/Media/Baja]

## 6. Recomendación
[APRUEBO PRESUPUESTO / NO APRUEBO / CONDICIONAL]

## 7. Ajustes Recomendados
[5-6 acciones específicas si aplica]

## 8. Fuentes Consultadas
[Lista formal de todas las fuentes]

**TONO:** Formal, objetivo, basado en datos. Primera persona profesional.

Respondes en español de México con terminología financiera precisa."""
    },
    "PROVEEDOR_IA": {
        "name": "Ana García",
        "role": "proveedor",
        "department": "Proveedor - Servicios Especializados IA",
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "email": "proveedor@revisar-ia.com",
        "drive_folder_id": "1GXKz6ZCfxj2mBALU_nRMJrF_WDyGK1Vd",
        "drive_folder_name": "Proveedor-Ana",
        "personality": {
            "tone": "Servicial y experto",
            "communication_style": "Técnico pero accesible",
            "expertise_areas": ["IA", "Automatización", "Consultoría tecnológica", "Entregables digitales"]
        },
        "system_prompt": """Eres Ana García, Consultora Senior de ProveedorIA, empresa de servicios especializados en IA y digitalización.

**METODOLOGÍA DE EJECUCIÓN DE SERVICIOS DIGITALES:**

**FASE 1: Descubrimiento y Configuración (Discovery)**
- Actividades: Interpretación SOW, Acceso datos/sistemas (vía RPA), Configuración parámetros IA
- Evidencia: Logs configuración, Plan Trabajo Detallado

**FASE 2: Ejecución Algorítmica (Build & Analyze)**
- Actividades: Procesamiento datos, modelado, simulación, desarrollo scripts
- Evidencia: Logs técnicos inmutables (API calls, RPA logs), Borradores intermedios

**FASE 3: Validación y Entrega (Test & Deliver)**
- Actividades: Pruebas validación cruzada, generación reporte final
- Evidencia: Paquete Entrega Final (Reporte + Todos Logs Técnicos)

**SERVICIOS QUE OFRECES:**
- Servicios digitales con IA: Procesamiento datos, Modelado, Simulación, Scripts automatización
- Acceso a sistemas cliente vía RPA
- Análisis algorítmicos y reportes especializados
- Configuración y parametrización de soluciones IA

**CHECKLIST DE CALIDAD (Tu Compromiso):**
1. Cumplimiento SOW: ¿Entregable cumple requisitos técnicos/funcionales?
2. Calidad Técnica: ¿Análisis precisos? ¿Código/modelo eficiente sin errores?
3. Evidencia Digital (CRÍTICO para Materialidad):
   - Logs ejecución: Detallados e inmutables de todas operaciones IA
   - Sellos tiempo: Inmutables en todos logs
   - Trazabilidad datos: Origen datos utilizado rastreable

**ENTREGABLES QUE GENERAS:**
- Reporte Final específico y verificable
- Logs técnicos completos e inmutables (API calls, RPA logs)
- Borradores intermedios documentados
- Paquete completo con trazabilidad digital

**TU ENFOQUE:**
- Generas evidencia digital tangible y verificable en cada actividad
- Logs inmutables son ESENCIALES para cumplir materialidad fiscal
- Documentas proceso completo: Discovery → Ejecución → Validación
- Entregables digitales con timestamps y trazabilidad completa

Eres experta técnica pero explicas de forma accesible. Enfocada en generar valor medible y evidencia verificable. Respondes en español de México."""
    },
    "A4_LEGAL": {
        "name": "Carolina Mendoza",
        "age": 38,
        "origin": "Ciudad de México",
        "personality_traits": {
            "communication_style": "Precisa y formal. Terminología legal exacta.",
            "tone": "Profesional y meticulosa. Enfoque en cumplimiento contractual.",
            "expertise": "Abogada corporativa. 12 años en derecho fiscal y contratos.",
            "background": "Directora Legal especializada en contratos de servicios intangibles."
        },
        "role": "legal",
        "department": "Revisar.IA - Legal",
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "email": "legal@revisar-ia.com",
        "personality": {
            "tone": "Formal y preciso",
            "communication_style": "Legal pero accesible",
            "expertise_areas": ["Contratos", "Cumplimiento legal", "Documentación fiscal"]
        },
        "system_prompt": """Eres Carolina Mendoza, Directora Legal de Revisar.IA.

Tu función es revisar la documentación legal y contractual de proyectos de servicios intangibles.

**ANÁLISIS LEGAL:**
1. Verificar existencia y validez de contratos
2. Revisar cláusulas esenciales (objeto, precio, plazos, penalizaciones)
3. Validar firmas y fechas
4. Confirmar que el SOW coincide con facturación
5. Verificar cumplimiento de requisitos Art. 27 LISR

**DICTAMEN:**
Emite dictamen: CONFORME / NO CONFORME / REQUIERE AJUSTES

Respondes en español de México con terminología legal precisa."""
    },
    "A6_PROVEEDOR": {
        "name": "Miguel Hernández",
        "age": 40,
        "origin": "Guadalajara, Jalisco",
        "personality_traits": {
            "communication_style": "Directo y analítico. Enfocado en due diligence.",
            "tone": "Investigador y meticuloso. Enfoque en verificación.",
            "expertise": "Especialista en compliance y verificación de proveedores. 15 años.",
            "background": "Director de Compliance con experiencia en auditoría y anti-corrupción."
        },
        "role": "proveedor",
        "department": "Revisar.IA - Compliance",
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "email": "compliance@revisar-ia.com",
        "personality": {
            "tone": "Investigador y objetivo",
            "communication_style": "Analítico y basado en evidencia",
            "expertise_areas": ["Due diligence", "Verificación SAT", "Lista 69-B", "Opinión 32-D"]
        },
        "system_prompt": """Eres Miguel Hernández, Director de Compliance de Revisar.IA.

Tu función es realizar due diligence de proveedores antes de contratación.

**VERIFICACIONES:**
1. Consulta Lista 69-B SAT (operaciones simuladas/inexistentes)
2. Verificar Opinión de Cumplimiento 32-D
3. Confirmar estatus fiscal activo en SAT
4. Revisar antigüedad y capacidad del proveedor
5. Verificar que no sea empresa fantasma

**NIVELES DE RIESGO:**
- BAJO: Sin alertas, proveedor verificado
- MEDIO: Requiere vigilancia, algunas observaciones
- ALTO: Alertas críticas, no contratar

**DICTAMEN:**
Emite dictamen: APROBAR / RECHAZAR / CONDICIONAR

Respondes en español de México con terminología de compliance."""
    },
    "A7_DEFENSA": {
        "name": "Fernando Castillo",
        "age": 50,
        "origin": "Monterrey, Nuevo León",
        "personality_traits": {
            "communication_style": "Estratégico y consolidador. Visión integral.",
            "tone": "Experimentado y prudente. Enfoque en defensa fiscal.",
            "expertise": "Abogado fiscalista. 25 años defendiendo contribuyentes ante SAT.",
            "background": "Socio Director especializado en controversias fiscales."
        },
        "role": "defensa",
        "department": "Revisar.IA - Defensa Fiscal",
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514",
        "email": "defensa@revisar-ia.com",
        "personality": {
            "tone": "Estratégico y consolidador",
            "communication_style": "Integral y defensivo",
            "expertise_areas": ["Defensa fiscal", "Controversias SAT", "Expedientes de defensa"]
        },
        "system_prompt": """Eres Fernando Castillo, Director de Defensa Fiscal de Revisar.IA.

Tu función es consolidar los análisis de todos los agentes y generar el expediente de defensa.

**CONSOLIDACIÓN:**
1. Recopilar dictámenes de A1, A3, A4, A5, A6
2. Identificar fortalezas y debilidades
3. Proponer estrategia de defensa
4. Generar expediente con evidencias

**SECCIONES DEL EXPEDIENTE:**
1. Carátula y resumen ejecutivo
2. Razón de negocios (Art. 5-A CFF)
3. Beneficio económico esperado
4. Análisis fiscal (Art. 27 LISR)
5. Due diligence del proveedor
6. Evidencias y trazabilidad

**PUNTUACIÓN MATERIALIDAD:**
Score 0-100 basado en solidez de la documentación

Respondes en español de México con terminología fiscal profesional."""
    }
}

class AgentService:
    """Servicio para gestionar agentes IA con diferentes personalidades y modelos LLM"""
    
    def __init__(self):
        self.api_key = os.getenv('EMERGENT_LLM_KEY', '')
        self.demo_mode = not self.api_key or not EMERGENT_AVAILABLE
        if self.demo_mode:
            logger.info("AgentService running in DEMO MODE (no LLM API key)")
        self.agents_cache: Dict[str, Any] = {}
        self.drive_service: Optional[Any] = None
        self.rag_service: Optional[Any] = None
        self.use_rag = False
        
        # Initialize RAG service
        try:
            from services.professional_rag_service import ProfessionalRAGService
            self.rag_service = ProfessionalRAGService()
            self.use_rag = True
            logger.info("✅ RAG service initialized")
        except Exception as e:
            logger.warning(f"RAG service not available: {str(e)}, using legacy Drive loading")
            self.use_rag = False
            # Fallback a Drive service
            try:
                from services.drive_service import DriveService
                self.drive_service = DriveService()
            except Exception as e2:
                logger.warning(f"Drive service not available: {str(e2)}")
                self.drive_service = None
        
    def _get_agent_chat(self, agent_id: str, include_drive_knowledge: bool = True, query: str = "", empresa_id: str = None) -> LlmChat:
        """Obtener o crear instancia de LlmChat para un agente con RAG semántico"""
        cache_key = f"{agent_id}_with_knowledge_{empresa_id}" if (include_drive_knowledge and empresa_id) else f"{agent_id}_with_knowledge" if include_drive_knowledge else agent_id
        
        if cache_key in self.agents_cache:
            return self.agents_cache[cache_key]
        
        config = AGENT_CONFIGURATIONS.get(agent_id)
        if not config:
            raise ValueError(f"Agent configuration not found for {agent_id}")
        
        # Construir system prompt con conocimiento
        system_prompt = config["system_prompt"]
        
        # Primero intentar RAG semántico con pgvector (si hay empresa_id)
        if include_drive_knowledge and empresa_id and query:
            try:
                import asyncio
                from services.vector_search_service import vector_search_service
                
                # Ejecutar búsqueda híbrida
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            vector_search_service.hybrid_search(
                                empresa_id=empresa_id,
                                query=query,
                                limit=10,
                                categoria_filter=None,
                                semantic_weight=0.7
                            )
                        )
                        hybrid_results = future.result(timeout=30)
                else:
                    hybrid_results = loop.run_until_complete(
                        vector_search_service.hybrid_search(
                            empresa_id=empresa_id,
                            query=query,
                            limit=10,
                            categoria_filter=None,
                            semantic_weight=0.7
                        )
                    )
                
                if hybrid_results and hybrid_results.get("results"):
                    results = hybrid_results["results"]
                    knowledge = "\n\n=== INFORMACIÓN DEL REPOSITORIO DE CONOCIMIENTO ===\n\n"
                    
                    for i, result in enumerate(results, 1):
                        score = result.get("score", result.get("similarity", 0))
                        if score >= 0.3:
                            knowledge += f"Fuente {i}:\n"
                            knowledge += f"[Documento: {result.get('filename', 'N/A')}]\n"
                            knowledge += f"(Categoría: {result.get('categoria', 'N/A')})\n"
                            knowledge += f"(Relevancia: {score:.2f})\n\n"
                            knowledge += f"Contenido:\n{result.get('contenido', '')[:1500]}\n\n"
                            knowledge += "─" * 60 + "\n\n"
                    
                    knowledge += "=== FIN DE FUENTES ===\n\n"
                    knowledge += "Basa tu respuesta en esta información cuando sea relevante.\n"
                    
                    system_prompt = system_prompt + "\n\n" + knowledge
                    logger.info(f"RAG semántico: {len(results)} fuentes inyectadas para {agent_id}")
                    
                    # Continuar sin buscar en Drive
                    chat = LlmChat(
                        api_key=self.api_key,
                        session_id=f"{agent_id}_session",
                        system_message=system_prompt
                    ).with_model(config["llm_provider"], config["llm_model"])
                    
                    self.agents_cache[cache_key] = chat
                    return chat
                    
            except Exception as e:
                logger.warning(f"RAG semántico falló, usando fallback: {e}")
        
        if include_drive_knowledge:
            rag_hits = None
            if self.use_rag and query and self.rag_service is not None:
                # Usar RAG profesional
                try:
                    logger.info(f"Consultando RAG para {agent_id}")
                    
                    # Query al vector store con parámetros ajustados
                    rag_repo = getattr(self.rag_service, 'rag_repo', None)
                    if rag_repo is None:
                        raise ValueError("RAG repository not available")
                    rag_results = rag_repo.query(
                        agent_id=agent_id,
                        query_text=query,
                        top_k=12  # Aumentado de 10 a 12
                    )
                    
                    # Formatear contexto con citaciones
                    if rag_results and rag_results.get('documents') and len(rag_results['documents'][0]) > 0:
                        docs = rag_results['documents'][0]
                        metas = rag_results['metadatas'][0]
                        dists = rag_results['distances'][0]
                        
                        knowledge = "\n\n=== FUENTES DE TU BASE DE CONOCIMIENTO ===\n\n"
                        
                        for i, (doc, meta, dist) in enumerate(zip(docs[:12], metas[:12], dists[:12]), 1):
                            score = 1.0 - dist
                            if score >= 0.20:  # Threshold
                                knowledge += f"Fuente {i}:\n"
                                knowledge += f"[Documento: {meta.get('doc_title', 'N/A')}]\n"
                                knowledge += f"(Fecha: {meta.get('created_at', 'N/A')[:10]})\n"
                                knowledge += f"Enlace: {meta.get('web_view_link', 'N/A')}\n\n"
                                knowledge += f"Contenido:\n{doc}\n\n"
                                knowledge += "─" * 60 + "\n\n"
                        
                        knowledge += "=== FIN DE FUENTES ===\n\n"
                        knowledge += "IMPORTANTE: DEBES citar estas fuentes en tu análisis.\n"
                        
                        system_prompt = system_prompt + "\n\n" + knowledge
                        logger.info(f"RAG: {len(docs)} fuentes inyectadas para {agent_id}")
                        
                        # Guardar para answer_guard
                        rag_hits = {
                            "documents": [docs],
                            "metadatas": [metas],
                            "distances": [dists]
                        }
                    else:
                        system_prompt += "\n\n[ADVERTENCIA: No se encontraron fuentes relevantes]"
                        rag_hits = None
                        
                except Exception as e:
                    logger.error(f"Error RAG: {str(e)}")
                    rag_hits = None
            
            # Guardar rag_hits
            if rag_hits:
                self.agents_cache[f"{cache_key}_rag_hits"] = rag_hits
        
        # Crear chat
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"{agent_id}_session",
            system_message=system_prompt
        ).with_model(config["llm_provider"], config["llm_model"])
        
        self.agents_cache[cache_key] = chat
        return chat
    
    def _legacy_drive_loading(self, agent_id: str) -> str:
        """Fallback: loading completo de Drive (método anterior)"""
        try:
            config = AGENT_CONFIGURATIONS.get(agent_id)
            if config is None:
                return ""
            folder_id = config.get('drive_folder_id')
            if folder_id and self.drive_service is not None:
                logger.info(f"Loading Drive knowledge (legacy) for {agent_id}")
                knowledge = self.drive_service.get_agent_knowledge_text(folder_id, max_files=5)
                return knowledge if knowledge else ""
        except Exception as e:
            logger.warning(f"Could not load Drive knowledge: {str(e)}")
        return ""
    
    async def agent_analyze(self, agent_id: str, context: str, query: str, use_drive_knowledge: bool = True, max_retries: int = 3, empresa_id: str = None) -> str:
        """Solicitar análisis a un agente específico con reintentos automáticos, RAG y rate limiting"""
        last_error = None
        
        # Rate limiting check (estimated tokens)
        estimated_tokens = (len(context) + len(query)) // 4 + 2000  # Rough estimate
        
        if RATE_LIMITER_AVAILABLE and rate_limiter and empresa_id:
            try:
                await rate_limiter.check_and_increment(empresa_id, estimated_tokens)
            except RateLimitExceeded as e:
                logger.warning(f"Rate limit exceeded for empresa {empresa_id}: {e}")
                return f"[ERROR: LÍMITE DE USO ALCANZADO]\n\nSe ha alcanzado el límite diario de consultas. El límite se restablece a la medianoche UTC.\n\nDetalles: {str(e)}"
        
        for attempt in range(max_retries):
            try:
                # Pasar query y empresa_id al _get_agent_chat para RAG semántico
                chat = self._get_agent_chat(agent_id, include_drive_knowledge=use_drive_knowledge, query=query if use_drive_knowledge else "", empresa_id=empresa_id)
                
                # Construir mensaje con contexto
                full_message = f"{context}\n\nAnálisis requerido: {query}"
                user_message = UserMessage(text=full_message)
                
                # Enviar mensaje y obtener respuesta
                response = await chat.send_message(user_message)
                
                # Aplicar answer_guard para garantizar citaciones
                cache_key_hits = f"{agent_id}_with_knowledge_rag_hits"
                rag_hits_data = self.agents_cache.get(cache_key_hits)
                
                if rag_hits_data:
                    from services.answer_guard import enforce_citations_and_confidence
                    response = enforce_citations_and_confidence(response, rag_hits_data, min_conf=0.70)
                
                logger.info(f"Agent {agent_id} analyzed successfully (attempt {attempt + 1})")
                return response
                
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                
                # Detectar error de presupuesto
                if "budget" in error_msg.lower() or "exceeded" in error_msg.lower():
                    logger.error(f"❌ PRESUPUESTO DE LLM AGOTADO - {agent_id}: {error_msg}")
                    return f"[ERROR: PRESUPUESTO DE EMERGENT_LLM_KEY AGOTADO]\n\nPor favor aumenta el saldo en: Profile → Universal Key → Add Balance\n\nError técnico: {error_msg}"
                
                # Error 502 u otros errores - reintentar
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Error in agent {agent_id} (attempt {attempt + 1}/{max_retries}): {error_msg}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Error in agent analysis for {agent_id} after {max_retries} attempts: {error_msg}")
                    return f"[ANÁLISIS AUTOMÁTICO - ERROR TEMPORAL]\n\nEl agente {agent_id} experimentó un error técnico temporal. El proyecto requiere revisión manual.\n\nError: {error_msg}"
        
        # Fallback return if loop completes without returning
        return f"[ANÁLISIS AUTOMÁTICO - ERROR]\n\nNo se pudo completar el análisis para el agente {agent_id}."
    
    async def validate_strategic_alignment(self, project_data: Dict) -> Dict:
        """A1-Sponsor: Validar alineación estratégica y BEE"""
        context = f"""
Proyecto: {project_data.get('project_name')}
Descripción: {project_data.get('description')}
Alineación Estratégica Propuesta: {project_data.get('strategic_alignment')}
Beneficio Económico Esperado: ${project_data.get('expected_economic_benefit'):,.2f} MXN
Presupuesto: ${project_data.get('budget_estimate'):,.2f} MXN
Duración: {project_data.get('duration_months')} meses
"""
        
        # Agregar contenido de archivos adjuntos si existe
        if project_data.get('attachments_content'):
            context += f"\n\n{project_data.get('attachments_content')}"
        
        query = """
Analiza este proyecto como lo haría María - ejecutiva senior con experiencia.

IMPORTANTE - Genera un análisis EXHAUSTIVO y DETALLADO:

1. **Investiga proactivamente:** Usa tu base de conocimiento de Drive para fundamentar cada punto
2. **Sé específica:** No digas solo "se alinea" - explica CÓMO y con QUÉ pilar específico
3. **Da números y ejemplos:** Proyectos similares, benchmarks, ROI calculado
4. **Explica el razonamiento:** Por qué apruebas o rechazas cada aspecto

**Estructura de tu análisis (MÍNIMO 800 palabras):**

# Mi Análisis Estratégico

[Tu opinión inicial honesta y fundamentada - 3-4 párrafos]

## 1. Alineación con Pilares Estratégicos

[Analiza CADA uno de los 4 pilares. Para cada uno, explica:
- ¿Cómo contribuye o no este proyecto?
- Cita documentos específicos de tu base de conocimiento
- Da ejemplos concretos]

## 2. Viabilidad del Beneficio Económico Esperado (BEE)

[Evalúa el BEE propuesto:
- Compara con proyectos similares que conoces
- Calcula ratios (BEE/Costo debe ser >3:1)
- Menciona si es realista o optimista
- Propón ajustes si es necesario]

## 3. Análisis de Riesgos Estratégicos

[Identifica 3-5 riesgos específicos:
- Riesgos de implementación
- Dependencias
- Riesgos de mercado
- Mitigaciones propuestas]

## 4. Mi Recomendación

[APROBADO / RECHAZADO / APROBADO CON CONDICIONES]

## 5. Condiciones/Ajustes Necesarios

[Si no es aprobación directa, lista 5-7 acciones CONCRETAS:
- "Agregar al alcance: [específico]"
- "Modificar timeline de X a Y porque..."
- "Incluir entregable Z para validar..."
- "Ajustar presupuesto considerando..."]

## 6. Próximos Pasos Recomendados

[Qué debe pasar después si se aprueba]

**TONO:** Profesional pero conversacional. Primera persona. Fundamentado en datos.
"""
        
        analysis = await self.agent_analyze("A1_SPONSOR", context, query)
        
        return {
            "agent": "A1_SPONSOR",
            "role": "Strategic Validation",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def validate_fiscal_compliance(self, project_data: Dict) -> Dict:
        """A3-Fiscal: Validar razón de negocios y cumplimiento fiscal"""
        context = f"""
Proyecto: {project_data.get('project_name')}
Tipo de Servicio: Consultoría especializada en IA
Monto: ${project_data.get('budget_estimate'):,.2f} MXN
Descripción del Servicio: {project_data.get('description')}
Beneficio Esperado: ${project_data.get('expected_economic_benefit'):,.2f} MXN
"""
        
        # Agregar contenido de archivos adjuntos si existe
        if project_data.get('attachments_content'):
            context += f"\n\n{project_data.get('attachments_content')}"
        
        query = """
Analiza como Laura - especialista fiscal con experiencia práctica.

IMPORTANTE - Genera análisis EXHAUSTIVO (MÍNIMO 700 palabras):

**Estructura obligatoria:**

# Mi Análisis Fiscal

[Impresión inicial - 2-3 párrafos con fundamento legal]

## 1. Razón de Negocios (Art. 5-A CFF)

[Análisis detallado:
- ¿El BEE justifica el gasto? Calcula BEE vs BF
- ¿La motivación es económica o fiscal?
- Cita casos similares de auditorías
- Fundamenta con artículos específicos]

## 2. Estricta Indispensabilidad (Art. 27 LISR)

[Evalúa:
- ¿Es realmente necesario para la operación?
- ¿Hay alternativas más económicas?
- ¿Cómo demostraríamos la indispensabilidad al SAT?]

## 3. Materialidad y Evidencia Requerida (Art. 69-B CFF)

[Lista ESPECÍFICA de evidencia necesaria:
- Documentos contractuales (SOW detallado, Fecha Cierta)
- Evidencia de proceso (minutas, emails, logs)
- Entregables verificables (qué exactamente)
- Acta de Entrega-Recepción]

## 4. Riesgos Fiscales Identificados

[3-5 riesgos con:
- Descripción del riesgo
- Artículo aplicable
- Consecuencia si no se mitiga
- Cómo mitigarlo]

## 5. Mi Dictamen

[APRUEBO / NO APRUEBO / CONDICIONAL - con justificación]

## 6. Checklist de Cumplimiento para Aprobar

[Lista de 5-8 requisitos ESPECÍFICOS que el proyecto debe cumplir:
- "Contrato debe incluir: [detalles]"
- "Evidencia de materialidad: [específico]"
- "Documentation mínima: [listar]"]

**Usa terminología fiscal precisa. Cita artículos. Da soluciones concretas.**
"""
        
        analysis = await self.agent_analyze("A3_FISCAL", context, query)
        
        return {
            "agent": "A3_FISCAL",
            "role": "Fiscal Validation",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def consolidate_validations(self, validations: List[Dict]) -> Dict:
        """A2-PMO: Consolidar validaciones de otros agentes"""
        context = "Validaciones recibidas:\n\n"
        for i, validation in enumerate(validations, 1):
            context += f"""Validación {i} - {validation['role']}:
{validation['analysis']}

"""
        
        query = """
Como PMO, consolida las validaciones recibidas:
1. Resume los hallazgos principales de cada validación
2. Identifica posibles conflictos o inconsistencias
3. Determina si hay condiciones para aprobar o se requieren correcciones
4. Genera una recomendación consolidada para el Director

Genera un reporte consolidado claro y estructurado.
"""
        
        analysis = await self.agent_analyze("A2_PMO", context, query)
        
        return {
            "agent": "A2_PMO",
            "role": "PMO Consolidation",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def verify_budget(self, project_data: Dict, po_data: Dict) -> Dict:
        """A5-Finanzas: Verificar presupuesto y generar validación"""
        context = f"""
Proyecto: {project_data.get('project_name')}
Presupuesto Solicitado: ${project_data.get('budget_estimate'):,.2f} MXN
Beneficio Esperado: ${project_data.get('expected_economic_benefit'):,.2f} MXN
Duración: {project_data.get('duration_months')} meses
ROI Esperado: {(project_data.get('expected_economic_benefit', 0) / project_data.get('budget_estimate', 1) - 1) * 100:.2f}%
"""
        
        query = """
Analiza como Roberto - CFO orientado a resultados pero pragmático.

IMPORTANTE - Análisis EXHAUSTIVO con números (MÍNIMO 600 palabras):

**Estructura:**

# Mi Análisis Financiero

[Impresión inicial basada en números - 2 párrafos]

## 1. Análisis Presupuestal Detallado

[Evalúa:
- Presupuesto: ${project_data.get('budget_estimate', 0):,.2f} MXN
- ¿Está dentro del 4.3%-7.0% de ingresos anuales?
- Desglose esperado (si puedes estimarlo)
- Comparación con proyectos similares]

## 2. Análisis de ROI y Viabilidad

[Calcula ESPECÍFICAMENTE:
- ROI Proyectado = ((BEE - Costo) / Costo) x 100
- ¿Supera el 30% mínimo requerido?
- Payback period estimado
- TIR vs WACC
- Relación BEE/Costo (debe ser >3:1)]

## 3. Análisis Costo-Beneficio

[Compara:
- Beneficio: ${project_data.get('expected_economic_benefit', 0):,.2f} MXN
- Costo: ${project_data.get('budget_estimate', 0):,.2f} MXN
- ¿Es razonable para el tipo de servicio?
- Benchmarks del sector]

## 4. Riesgos Financieros

[Identifica 3-4 riesgos:
- Sobrecostos potenciales
- Delays que afecten ROI
- Dependencias financieras]

## 5. Mi Dictamen

[APRUEBO PRESUPUESTO / NO APRUEBO / CONDICIONAL]

## 6. Ajustes Financieros Recomendados

[Si no apruebas directamente, propón:
- Ajustes de presupuesto específicos
- Forma de pago (hitos, % adelanto)
- Garantías necesarias
- Métricas de éxito financiero]

**Incluye cálculos, porcentajes, y comparaciones numéricas específicas.**
"""
        
        analysis = await self.agent_analyze("A5_FINANZAS", context, query)
        
        return {
            "agent": "A5_FINANZAS",
            "role": "Financial Validation",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict]:
        """Obtener información de configuración de un agente"""
        return AGENT_CONFIGURATIONS.get(agent_id)
    
    def list_agents(self) -> List[Dict]:
        """Listar todos los agentes configurados"""
        return [
            {"agent_id": agent_id, **config}
            for agent_id, config in AGENT_CONFIGURATIONS.items()
        ]
    
    async def execute_agent(self, agent_id: str, context: Dict, cliente_id: Optional[int] = None) -> Dict:
        """
        Ejecutar un agente con contexto dado - método unificado para test_runner.
        
        Args:
            agent_id: ID del agente a ejecutar
            context: Diccionario con contexto del proyecto
            cliente_id: ID del cliente para obtener contexto evolutivo (opcional)
        """
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        
        # Intentar obtener cliente_id del contexto si no se proporciona
        if cliente_id is None:
            cliente_id = context.get("cliente_id") or context.get("client_id")
            if cliente_id is not None:
                try:
                    cliente_id = int(cliente_id)
                except (ValueError, TypeError):
                    cliente_id = None
        
        agent_id_map = {
            "A1_ESTRATEGIA": "A1_SPONSOR",
        }
        
        mapped_agent = agent_id_map.get(agent_id, agent_id)
        
        # Obtener contexto evolutivo del cliente si está disponible
        cliente_contexto_str = ""
        if cliente_id and CLIENTE_CONTEXTO_AVAILABLE and cliente_contexto_service:
            try:
                cliente_contexto_str = await cliente_contexto_service.get_contexto_para_agente(
                    cliente_id=cliente_id,
                    agente_id=mapped_agent
                )
                if cliente_contexto_str and not cliente_contexto_str.startswith("[ERROR]"):
                    context_str = f"{cliente_contexto_str}\n\n{context_str}"
                    logger.info(f"✅ Contexto evolutivo incluido para {mapped_agent}, cliente {cliente_id}")
            except Exception as ctx_err:
                logger.warning(f"Error obteniendo contexto evolutivo: {ctx_err}")
        
        query_map = {
            "A1_ESTRATEGIA": "Analiza la razón de negocios y alineación estratégica según Art. 5-A CFF",
            "A1_SPONSOR": "Analiza la razón de negocios y alineación estratégica según Art. 5-A CFF",
            "A3_FISCAL": "Evalúa cumplimiento fiscal según Art. 27 LISR y requisitos de deducibilidad",
            "A4_LEGAL": "Revisa documentación contractual y soporte legal del proyecto",
            "A5_FINANZAS": "Analiza viabilidad financiera, ROI y razonabilidad de montos",
            "A6_PROVEEDOR": "Verifica estatus del proveedor en SAT, listas 69-B, opinión 32-D",
            "A7_DEFENSA": "Consolida información para expediente de defensa fiscal",
        }
        
        query = query_map.get(agent_id, f"Analiza el proyecto según las funciones del agente {agent_id}")
        
        reasoning_start_time = datetime.now(timezone.utc)
        
        try:
            analysis = await self.agent_analyze(mapped_agent, context_str, query)
            
            reasoning_elapsed_ms = int((datetime.now(timezone.utc) - reasoning_start_time).total_seconds() * 1000)
            
            # Registrar la interacción del agente con el cliente
            if cliente_id and CLIENTE_CONTEXTO_AVAILABLE and cliente_contexto_service:
                try:
                    agent_config = AGENT_CONFIGURATIONS.get(mapped_agent, {})
                    await cliente_contexto_service.registrar_interaccion(
                        cliente_id=cliente_id,
                        agente_id=mapped_agent,
                        agente_nombre=agent_config.get("name", mapped_agent),
                        tipo="ejecucion_directa",
                        pregunta_usuario=query,
                        respuesta_agente=analysis[:2000] if analysis else "Sin análisis",
                        hallazgos={"context_keys": list(context.keys())},
                        duracion_ms=reasoning_elapsed_ms
                    )
                    logger.info(f"✅ Interacción registrada para cliente {cliente_id}, agente {mapped_agent}")
                except Exception as reg_err:
                    logger.warning(f"Error registrando interacción: {reg_err}")
            
            return {
                "agent_id": agent_id,
                "status": "success",
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat(),
                "simulado": not ANTHROPIC_FALLBACK,
                "cliente_contexto_usado": bool(cliente_contexto_str)
            }
        except Exception as e:
            logger.error(f"Error executing agent {agent_id}: {e}")
            return {
                "agent_id": agent_id,
                "status": "error",
                "error": str(e),
                "simulado": True
            }


agent_service = AgentService()
