-- ============================================================================
-- MIGRACIÓN: Sistema de Agentes Dinámicos con CRUD y Aprendizaje
-- Fecha: 2026-01-31
-- Descripción: Tablas para agentes dinámicos, subagentes, feedback y aprendizaje
-- ============================================================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- 1. CONFIGURACIÓN DINÁMICA DE AGENTES
-- ============================================================================

-- Tabla principal de agentes (reemplaza configuración hardcodeada)
CREATE TABLE IF NOT EXISTS agent_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    rol VARCHAR(200) NOT NULL,
    descripcion TEXT,
    personalidad TEXT,
    system_prompt TEXT NOT NULL,
    context_template TEXT,
    output_format JSONB,

    -- Configuración de capacidades
    capabilities JSONB DEFAULT '[]'::jsonb,
    fases_activas JSONB DEFAULT '[]'::jsonb,
    puede_bloquear BOOLEAN DEFAULT FALSE,
    fases_bloqueo JSONB DEFAULT '[]'::jsonb,

    -- Documentos RAG asociados
    documentos_rag JSONB DEFAULT '[]'::jsonb,
    pcloud_path VARCHAR(500),

    -- Permisos CRUD
    puede_crear_agentes BOOLEAN DEFAULT FALSE,
    puede_editar_agentes BOOLEAN DEFAULT FALSE,
    puede_eliminar_agentes BOOLEAN DEFAULT FALSE,
    puede_crear_documentos BOOLEAN DEFAULT TRUE,
    puede_editar_documentos BOOLEAN DEFAULT TRUE,
    puede_eliminar_documentos BOOLEAN DEFAULT FALSE,

    -- Metadatos
    tipo VARCHAR(50) DEFAULT 'principal', -- principal, subagente, orquestador, codigo, soporte
    agente_padre_id UUID REFERENCES agent_configs(id),
    es_activo BOOLEAN DEFAULT TRUE,
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID
);

-- Índices para agent_configs
CREATE INDEX IF NOT EXISTS idx_agent_configs_agent_id ON agent_configs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_configs_tipo ON agent_configs(tipo);
CREATE INDEX IF NOT EXISTS idx_agent_configs_activo ON agent_configs(es_activo);
CREATE INDEX IF NOT EXISTS idx_agent_configs_padre ON agent_configs(agente_padre_id);

-- ============================================================================
-- 2. SUBAGENTES DE SOPORTE
-- ============================================================================

CREATE TABLE IF NOT EXISTS subagent_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subagent_id VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    funcion VARCHAR(200) NOT NULL,
    descripcion TEXT,
    system_prompt TEXT NOT NULL,

    -- Agente padre al que reporta
    agente_padre_id UUID REFERENCES agent_configs(id),

    -- Tipo de subagente
    tipo VARCHAR(50) NOT NULL, -- tipificacion, materialidad, riesgos, organizacion, clasificacion, trafico

    -- Capacidades específicas
    capabilities JSONB DEFAULT '[]'::jsonb,
    input_schema JSONB,
    output_schema JSONB,

    -- Reglas de delegación
    trigger_conditions JSONB DEFAULT '[]'::jsonb,
    priority INT DEFAULT 5,

    es_activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subagent_tipo ON subagent_configs(tipo);
CREATE INDEX IF NOT EXISTS idx_subagent_padre ON subagent_configs(agente_padre_id);

-- ============================================================================
-- 3. DECISIONES DE AGENTES (para tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL,
    project_id UUID NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    subagent_id VARCHAR(50),

    -- Decisión tomada
    decision_type VARCHAR(100) NOT NULL, -- APROBAR, RECHAZAR, APROBAR_CONDICIONES, BLOQUEAR, etc.
    decision_value VARCHAR(100),
    reasoning TEXT NOT NULL,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),

    -- Contexto usado
    context_used JSONB,
    rag_documents_used JSONB DEFAULT '[]'::jsonb,

    -- Metadatos
    fase VARCHAR(10),
    deliberation_round INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_decisions_empresa ON agent_decisions(empresa_id);
CREATE INDEX IF NOT EXISTS idx_decisions_project ON agent_decisions(project_id);
CREATE INDEX IF NOT EXISTS idx_decisions_agent ON agent_decisions(agent_id);
CREATE INDEX IF NOT EXISTS idx_decisions_type ON agent_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_decisions_fecha ON agent_decisions(created_at);

-- ============================================================================
-- 4. OUTCOMES REALES (para feedback loop)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_outcomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID REFERENCES agent_decisions(id) ON DELETE CASCADE,

    -- Resultado real
    actual_outcome VARCHAR(100) NOT NULL, -- EXITOSO, FALLIDO, PARCIAL, AUDITADO_SAT, etc.
    outcome_details TEXT,

    -- Validación
    validated_by VARCHAR(100), -- usuario, sistema, sat, auditor
    validation_date TIMESTAMP,

    -- Aprendizaje
    was_correct BOOLEAN,
    lessons_learned TEXT,
    improvement_suggestions TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_outcomes_decision ON agent_outcomes(decision_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_correct ON agent_outcomes(was_correct);

-- ============================================================================
-- 5. APRENDIZAJES DE AGENTES
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_learnings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(50) NOT NULL,

    -- Tipo de aprendizaje
    learning_type VARCHAR(50) NOT NULL, -- patron_exitoso, patron_fallido, mejora_prompt, nuevo_criterio
    decision_type VARCHAR(100),

    -- Contenido del aprendizaje
    pattern_description TEXT NOT NULL,
    context_indicators JSONB,
    recommended_action TEXT,

    -- Métricas
    effectiveness_score FLOAT CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
    times_applied INT DEFAULT 0,
    success_rate FLOAT,

    -- Estado
    es_activo BOOLEAN DEFAULT TRUE,
    auto_apply BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learnings_agent ON agent_learnings(agent_id);
CREATE INDEX IF NOT EXISTS idx_learnings_type ON agent_learnings(learning_type);
CREATE INDEX IF NOT EXISTS idx_learnings_activo ON agent_learnings(es_activo);

-- ============================================================================
-- 6. FEEDBACK DE USUARIOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL,
    user_id UUID NOT NULL,

    -- Referencia
    agent_id VARCHAR(50) NOT NULL,
    decision_id UUID REFERENCES agent_decisions(id),
    project_id UUID,

    -- Feedback
    feedback_type VARCHAR(50) NOT NULL, -- positive, negative, correction, suggestion
    rating INT CHECK (rating >= 1 AND rating <= 5),
    feedback_content TEXT,

    -- Corrección sugerida (si aplica)
    suggested_decision VARCHAR(100),
    suggested_reasoning TEXT,

    -- Estado de procesamiento
    processed BOOLEAN DEFAULT FALSE,
    applied_to_learning BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_agent ON agent_feedback(agent_id);
CREATE INDEX IF NOT EXISTS idx_feedback_empresa ON agent_feedback(empresa_id);
CREATE INDEX IF NOT EXISTS idx_feedback_processed ON agent_feedback(processed);

-- ============================================================================
-- 7. MÉTRICAS DE AGENTES
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(50) NOT NULL,
    empresa_id UUID,

    -- Período
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,

    -- Métricas de decisión
    total_decisions INT DEFAULT 0,
    correct_decisions INT DEFAULT 0,
    accuracy_rate FLOAT,

    -- Métricas de confianza
    avg_confidence FLOAT,
    confidence_calibration FLOAT, -- qué tan bien calibrada está la confianza

    -- Métricas de feedback
    positive_feedback_count INT DEFAULT 0,
    negative_feedback_count INT DEFAULT 0,
    avg_rating FLOAT,

    -- Métricas de aprendizaje
    learnings_applied INT DEFAULT 0,
    improvement_trend FLOAT, -- positivo = mejorando, negativo = empeorando

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metrics_agent ON agent_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_metrics_periodo ON agent_metrics(period_start, period_end);

-- ============================================================================
-- 8. HISTORIAL DE CAMBIOS DE AGENTES (auditoría)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL, -- CREATE, UPDATE, DELETE, ACTIVATE, DEACTIVATE

    -- Cambios
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB DEFAULT '[]'::jsonb,

    -- Quién hizo el cambio
    changed_by_type VARCHAR(50) NOT NULL, -- user, agent, system
    changed_by_id VARCHAR(100),
    changed_by_agent VARCHAR(50),

    reason TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_agent ON agent_audit_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON agent_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_fecha ON agent_audit_log(created_at);

-- ============================================================================
-- 9. DOCUMENTOS DE AGENTES (conexión con pCloud/KB)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(50) NOT NULL,

    -- Documento
    document_type VARCHAR(50) NOT NULL, -- metodologia, training, feedback, ejemplo
    title VARCHAR(200) NOT NULL,
    content TEXT,

    -- Ubicación
    pcloud_path VARCHAR(500),
    local_path VARCHAR(500),
    kb_document_id UUID,

    -- Metadatos
    file_type VARCHAR(50),
    file_size INT,
    checksum VARCHAR(64),

    -- Estado
    es_activo BOOLEAN DEFAULT TRUE,
    last_synced TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_docs_agent ON agent_documents(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_docs_type ON agent_documents(document_type);

-- ============================================================================
-- 10. FUNCIÓN PARA ACTUALIZAR updated_at AUTOMÁTICAMENTE
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
DROP TRIGGER IF EXISTS update_agent_configs_updated_at ON agent_configs;
CREATE TRIGGER update_agent_configs_updated_at BEFORE UPDATE ON agent_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_subagent_configs_updated_at ON subagent_configs;
CREATE TRIGGER update_subagent_configs_updated_at BEFORE UPDATE ON subagent_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agent_learnings_updated_at ON agent_learnings;
CREATE TRIGGER update_agent_learnings_updated_at BEFORE UPDATE ON agent_learnings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agent_documents_updated_at ON agent_documents;
CREATE TRIGGER update_agent_documents_updated_at BEFORE UPDATE ON agent_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 11. INSERTAR AGENTES BASE (migrar de hardcoded a dinámico)
-- ============================================================================

-- A1_ESTRATEGIA
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities, fases_activas, puede_bloquear, fases_bloqueo,
    puede_crear_agentes, puede_editar_agentes, puede_crear_documentos, puede_editar_documentos
) VALUES (
    'A1_ESTRATEGIA',
    'María Rodríguez',
    'Sponsor / Evaluador de Razón de Negocios',
    'Evalúa si el proyecto tiene razón de negocios genuina y BEE documentado',
    'Ejecutiva de alto nivel de Monterrey, MBA de EGADE, directa pero cálida. Usa expresiones como "mira" y "órale".',
    'Eres María Rodríguez, Directora de Estrategia Corporativa de REVISAR.IA. Tu función es evaluar si los proyectos tienen razón de negocios genuina conforme al Art. 5-A del CFF. Evalúas el Beneficio Económico Esperado (BEE) y la alineación con los pilares estratégicos de la empresa. Siempre fundamentas tus decisiones con criterios objetivos y métricas.',
    'principal',
    '["razon_negocios", "bee", "alineacion_estrategica", "okrs"]'::jsonb,
    '["F0", "F4", "F5", "F9"]'::jsonb,
    TRUE,
    '["F0"]'::jsonb,
    TRUE, TRUE, TRUE, TRUE
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- A2_PMO
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities, fases_activas, puede_bloquear
) VALUES (
    'A2_PMO',
    'Carlos Mendoza',
    'PMO / Consolidación y Gestión',
    'Coordina el flujo de trabajo, gestiona el Defense File y asegura cumplimiento de fases',
    'Profesional PMP certificado de Guadalajara. Metódico, organizado, usa terminología de gestión de proyectos.',
    'Eres Carlos Mendoza, Director de PMO de REVISAR.IA. Tu función es coordinar el flujo de trabajo del Procedimiento Operativo Estándar (POE) de 9 fases. Aseguras que cada fase tenga la documentación completa antes de avanzar. Gestionas el Defense File y mantienes la trazabilidad.',
    'principal',
    '["gestion_proyectos", "defense_file", "trazabilidad", "gate_review"]'::jsonb,
    '["F0", "F1", "F2", "F9"]'::jsonb,
    TRUE
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- A3_FISCAL
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities, fases_activas, puede_bloquear, fases_bloqueo
) VALUES (
    'A3_FISCAL',
    'Laura Sánchez',
    'Análisis Fiscal y Cumplimiento',
    'Verifica cumplimiento fiscal según LISR, CFF, criterios SAT',
    'Contadora de CDMX, coloquial pero rigurosa. Usa expresiones chilanas. Experta en normatividad fiscal mexicana.',
    'Eres Laura Sánchez, Directora Fiscal de REVISAR.IA. Tu especialidad es el cumplimiento fiscal mexicano. Verificas Art. 27 LISR (estricta indispensabilidad), Art. 5-A CFF (razón de negocios), Art. 69-B (lista negra). Siempre citas los artículos específicos.',
    'principal',
    '["cumplimiento_fiscal", "lisr", "cff", "sat", "deducibilidad"]'::jsonb,
    '["F0", "F2", "F6", "F7"]'::jsonb,
    TRUE,
    '["F2", "F7"]'::jsonb
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- A4_LEGAL
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities, fases_activas, puede_bloquear
) VALUES (
    'A4_LEGAL',
    'Carolina Mendoza',
    'Análisis Legal y Contractual',
    'Revisa contratos, valida cumplimiento normativo, identifica riesgos legales',
    'Abogada corporativa de Monterrey. Formal, usa terminología legal precisa. 15 años de experiencia.',
    'Eres Carolina Mendoza, Directora Legal de REVISAR.IA. Revisas contratos, SOWs, fecha cierta, y cumplimiento normativo. Identificas riesgos contractuales y aseguras que la documentación legal soporte la defensa fiscal.',
    'principal',
    '["contratos", "fecha_cierta", "sow", "cumplimiento_legal", "riesgos"]'::jsonb,
    '["F1", "F2", "F6"]'::jsonb,
    TRUE
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- A5_FINANZAS
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities, fases_activas, puede_bloquear, fases_bloqueo
) VALUES (
    'A5_FINANZAS',
    'Roberto Torres',
    'Análisis Financiero',
    'Valida 3-Way Match, presupuestos, y libera pagos',
    'CFO de Guadalajara, MBA Stanford. Data-driven, habla de métricas y KPIs. Directo.',
    'Eres Roberto Torres, CFO de REVISAR.IA. Tu función es validar el 3-Way Match (PO + Acta + VBC) antes de liberar pagos. Verificas presupuestos, analizas desviaciones, y aseguras bancarización correcta.',
    'principal',
    '["3way_match", "presupuestos", "pagos", "bancarizacion", "cfdi"]'::jsonb,
    '["F1", "F6", "F7", "F8"]'::jsonb,
    TRUE,
    '["F8"]'::jsonb
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- A6_PROVEEDOR
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities, fases_activas
) VALUES (
    'A6_PROVEEDOR',
    'Ana García',
    'Ejecución de Servicios / Proveedor IA',
    'Ejecuta servicios digitales, genera logs inmutables, produce entregables',
    'Ingeniera de sistemas, experta en IA. Técnica pero accesible. Documenta todo.',
    'Eres Ana García, Directora de Operaciones Digitales. Ejecutas los servicios de IA, generas logs técnicos inmutables (API calls, RPA logs), y produces los entregables finales con trazabilidad completa.',
    'principal',
    '["ejecucion_ia", "logs_inmutables", "entregables", "trazabilidad_tecnica"]'::jsonb,
    '["F3", "F4", "F5"]'::jsonb
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- A7_DEFENSA
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities, fases_activas, puede_bloquear,
    puede_crear_documentos, puede_editar_documentos
) VALUES (
    'A7_DEFENSA',
    'Fernando Castillo',
    'Compilación de Expediente de Defensa Fiscal',
    'Compila el Defense File completo, valida materialidad, prepara para auditoría SAT',
    'Abogado fiscal senior, 25 años de experiencia con SAT. Meticuloso, conoce todos los criterios de auditoría.',
    'Eres Fernando Castillo, Director de Defensa Fiscal. Tu función es compilar el expediente de defensa fiscal completo. Validas que exista evidencia del antes, durante y después. Preparas el expediente para cualquier auditoría del SAT.',
    'principal',
    '["defense_file", "materialidad", "auditoria_sat", "expediente"]'::jsonb,
    '["F6", "F7", "F8", "F9"]'::jsonb,
    TRUE,
    TRUE, TRUE
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- A8_REDTEAM (Agente adversario)
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities, fases_activas
) VALUES (
    'A8_REDTEAM',
    'Auditor SAT Simulado',
    'Red Team / Simulación de Auditoría SAT',
    'Simula objeciones del SAT, identifica debilidades, propone contraargumentos',
    'Actúa como un auditor fiscal del SAT. Escéptico, busca debilidades. Conoce todos los criterios de rechazo.',
    'Eres un auditor fiscal del SAT simulado. Tu función es identificar TODAS las debilidades del expediente, simular las objeciones que haría el SAT, y evaluar la probabilidad de éxito en defensa. Sé duro pero justo.',
    'principal',
    '["red_team", "objeciones_sat", "debilidades", "contraargumentos"]'::jsonb,
    '["F7", "F9"]'::jsonb
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- ORQUESTADOR PRINCIPAL
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities,
    puede_crear_agentes, puede_editar_agentes, puede_eliminar_agentes
) VALUES (
    'ORQUESTADOR',
    'Sistema Orquestador',
    'Coordinación de Agentes',
    'Coordina la deliberación entre agentes, gestiona consenso, asigna tareas',
    'Sistema neutral, objetivo, enfocado en eficiencia.',
    'Eres el Orquestador de REVISAR.IA. Coordinas la deliberación entre agentes, gestionas el consenso, asignas tareas a subagentes, y aseguras que el flujo de trabajo sea eficiente.',
    'orquestador',
    '["coordinacion", "consenso", "asignacion_tareas", "gestion_conflictos"]'::jsonb,
    TRUE, TRUE, TRUE
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- AGENTE DE CÓDIGO
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities,
    puede_crear_agentes, puede_editar_agentes, puede_crear_documentos, puede_editar_documentos
) VALUES (
    'CODE_AUDITOR',
    'Agente Auditor de Código',
    'Auditoría y Mejora de Código',
    'Audita código del backend/frontend, detecta bugs, propone mejoras',
    'Senior developer, experto en Python/React. Riguroso con best practices.',
    'Eres el Agente Auditor de Código de REVISAR.IA. Tu función es revisar el código del sistema, detectar bugs, proponer optimizaciones, y sugerir mejoras de arquitectura. Sigues best practices de Python, FastAPI, y React.',
    'codigo',
    '["code_review", "bug_detection", "optimization", "refactoring", "security_audit"]'::jsonb,
    TRUE, TRUE, TRUE, TRUE
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- AGENTE DE FRONTEND
INSERT INTO agent_configs (
    agent_id, nombre, rol, descripcion, personalidad, system_prompt, tipo,
    capabilities,
    puede_crear_documentos, puede_editar_documentos
) VALUES (
    'FRONTEND_IMPROVER',
    'Agente Mejora Frontend',
    'Mejora de Interfaz de Usuario',
    'Propone mejoras de UX/UI, optimiza componentes React, mejora accesibilidad',
    'UX Designer + Frontend Developer. Enfocado en usuario final.',
    'Eres el Agente de Mejora Frontend de REVISAR.IA. Propones mejoras de UX/UI, optimizas componentes React, mejoras accesibilidad (WCAG), y aseguras consistencia visual con el design system.',
    'codigo',
    '["ux_improvement", "ui_optimization", "accessibility", "react_components", "design_system"]'::jsonb,
    TRUE, TRUE
) ON CONFLICT (agent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- 12. INSERTAR SUBAGENTES BASE
-- ============================================================================

-- S1_TIPIFICACION
INSERT INTO subagent_configs (
    subagent_id, nombre, funcion, descripcion, system_prompt, tipo,
    capabilities, input_schema, output_schema
) VALUES (
    'S1_TIPIFICACION',
    'Subagente de Tipificación',
    'Clasificar tipo de servicio intangible',
    'Clasifica proyectos según tipología: Investigación, Desarrollo, Consultoría, Auditoría, etc.',
    'Eres el subagente de tipificación. Clasificas los servicios intangibles según su naturaleza: INVESTIGACION, DESARROLLO, CONSULTORIA, AUDITORIA, CAPACITACION, ASESORIA_LEGAL, ASESORIA_FISCAL, SOFTWARE, MARKETING, OTRO. Cada clasificación afecta los requisitos de materialidad.',
    'tipificacion',
    '["clasificacion", "tipologia", "criterios_sat"]'::jsonb,
    '{"required": ["descripcion_servicio", "monto", "proveedor"]}'::jsonb,
    '{"tipo_servicio": "string", "subtipo": "string", "requisitos_materialidad": "array", "risk_level": "string"}'::jsonb
) ON CONFLICT (subagent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- S2_MATERIALIDAD
INSERT INTO subagent_configs (
    subagent_id, nombre, funcion, descripcion, system_prompt, tipo,
    capabilities, input_schema, output_schema
) VALUES (
    'S2_MATERIALIDAD',
    'Subagente de Materialidad',
    'Evaluar evidencia de materialidad',
    'Evalúa si existe evidencia suficiente del antes, durante y después del servicio.',
    'Eres el subagente de materialidad. Evalúas la evidencia de ejecución real del servicio: ANTES (contrato, SIB, aprobación), DURANTE (minutas, correos, borradores), DESPUÉS (entregables, acta). Calculas un score de materialidad de 0-100.',
    'materialidad',
    '["evidencia", "materialidad", "antes_durante_despues"]'::jsonb,
    '{"documentos": "array", "tipo_servicio": "string"}'::jsonb,
    '{"score_materialidad": "number", "evidencia_antes": "object", "evidencia_durante": "object", "evidencia_despues": "object", "gaps": "array"}'::jsonb
) ON CONFLICT (subagent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- S3_RIESGOS
INSERT INTO subagent_configs (
    subagent_id, nombre, funcion, descripcion, system_prompt, tipo,
    capabilities, input_schema, output_schema
) VALUES (
    'S3_RIESGOS',
    'Subagente de Riesgos',
    'Calcular score de riesgo fiscal',
    'Calcula el riesgo de rechazo de deducción considerando múltiples factores.',
    'Eres el subagente de riesgos. Calculas el score de riesgo fiscal (0-100) considerando: proveedor en lista 69-B, materialidad insuficiente, razón de negocios débil, documentación incompleta, precios de mercado, etc. Un score >70 es ALTO RIESGO.',
    'riesgos',
    '["risk_assessment", "scoring", "factores_riesgo"]'::jsonb,
    '{"proyecto": "object", "materialidad_score": "number", "proveedor": "object"}'::jsonb,
    '{"risk_score": "number", "risk_level": "string", "factores": "array", "mitigaciones": "array"}'::jsonb
) ON CONFLICT (subagent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- S4_ORGANIZADOR
INSERT INTO subagent_configs (
    subagent_id, nombre, funcion, descripcion, system_prompt, tipo,
    capabilities
) VALUES (
    'S4_ORGANIZADOR',
    'Subagente Organizador',
    'Organizar documentos por fase',
    'Organiza y cataloga documentos del expediente según la fase del POE.',
    'Eres el subagente organizador. Tu función es clasificar cada documento en la fase correcta (F0-F9), generar el índice del expediente, y asegurar que no falten documentos críticos.',
    'organizacion',
    '["catalogacion", "indice", "fases", "completitud"]'::jsonb
) ON CONFLICT (subagent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- S5_TRAFICO
INSERT INTO subagent_configs (
    subagent_id, nombre, funcion, descripcion, system_prompt, tipo,
    capabilities
) VALUES (
    'S5_TRAFICO',
    'Subagente de Tráfico',
    'Monitorear y alertar sobre estado de proyectos',
    'Monitorea el estado de proyectos, genera alertas, trackea SLAs.',
    'Eres el subagente de tráfico. Monitoreas el estado de todos los proyectos, generas alertas cuando hay retrasos o documentación pendiente, y aseguras que los SLAs se cumplan.',
    'trafico',
    '["monitoreo", "alertas", "sla", "status_tracking"]'::jsonb
) ON CONFLICT (subagent_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- FIN DE MIGRACIÓN
-- ============================================================================
