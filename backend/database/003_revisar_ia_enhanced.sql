-- ============================================================================
-- MIGRACIÓN 003: Sistema Mejorado REVISAR.IA
-- Implementa: Base Jurídica, Matriz Materialidad F0-F9, Defense File Mejorado,
--             3-Way Match, Plantillas SIB/SOW/Actas
-- Fecha: 2026-01-31
-- Basado en: Recomendaciones del Agente Especializado
-- ============================================================================

-- ============================================================================
-- 1. BASE JURÍDICA - Fundamentación Legal SCJN
-- ============================================================================

CREATE TABLE IF NOT EXISTS legal_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID,  -- NULL = contenido global del sistema

    -- Clasificación
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN (
        'articulo_cff',        -- Artículos del CFF (5-A, 69-B, etc.)
        'articulo_lisr',       -- Artículos LISR (27, etc.)
        'norma_oficial',       -- NOM-151, etc.
        'jurisprudencia',      -- Tesis SCJN/TFJA
        'criterio_sat',        -- Criterios normativos SAT
        'resolucion_tfja',     -- Resoluciones TFJA
        'circular',            -- Circulares
        'criterio_interno'     -- Criterios internos de la plataforma
    )),
    categoria VARCHAR(100),  -- 'razon_negocios', 'materialidad', 'bee', 'trazabilidad', 'efos'

    -- Contenido
    titulo VARCHAR(500) NOT NULL,
    subtitulo VARCHAR(500),
    numero_referencia VARCHAR(100),  -- Ej: "II.2o.C. J/1 K (12a.)", "Art. 5-A CFF"
    registro_digital VARCHAR(50),     -- Ej: "2031639"

    contenido_completo TEXT NOT NULL,
    resumen_ejecutivo TEXT,

    -- Aplicabilidad
    aplica_a_tipologias JSONB DEFAULT '[]',  -- ['CONSULTORIA', 'INTRAGRUPO', etc.]
    aplica_a_fases JSONB DEFAULT '[]',       -- ['F0', 'F2', 'F6', 'F8']
    aplica_a_pilares JSONB DEFAULT '[]',     -- ['razon_negocios', 'bee', 'materialidad', 'trazabilidad']

    -- Vigencia
    fecha_publicacion DATE,
    fecha_vigencia_inicio DATE,
    fecha_vigencia_fin DATE,  -- NULL = vigente
    es_vigente BOOLEAN DEFAULT TRUE,

    -- Metadata
    fuente VARCHAR(500),       -- URL o referencia
    keywords JSONB DEFAULT '[]',
    orden_display INT DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_legal_base_tipo ON legal_base(tipo);
CREATE INDEX IF NOT EXISTS idx_legal_base_categoria ON legal_base(categoria);
CREATE INDEX IF NOT EXISTS idx_legal_base_vigente ON legal_base(es_vigente);
CREATE INDEX IF NOT EXISTS idx_legal_base_empresa ON legal_base(empresa_id);

-- ============================================================================
-- 2. FAQ FISCAL/LEGAL
-- ============================================================================

CREATE TABLE IF NOT EXISTS faqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID,  -- NULL = FAQ global

    categoria VARCHAR(100) NOT NULL,  -- 'fiscal', 'legal', 'uso_ia', 'materialidad', 'defensa'
    subcategoria VARCHAR(100),

    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    respuesta_corta VARCHAR(500),  -- Para previews

    -- Referencias cruzadas
    referencias_legales JSONB DEFAULT '[]',  -- Array de IDs de legal_base
    referencias_externas JSONB DEFAULT '[]', -- URLs externas

    -- Metadata
    orden INT DEFAULT 0,
    visitas INT DEFAULT 0,
    es_destacada BOOLEAN DEFAULT FALSE,
    es_activa BOOLEAN DEFAULT TRUE,

    -- Para búsqueda
    keywords JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_faqs_categoria ON faqs(categoria);
CREATE INDEX IF NOT EXISTS idx_faqs_activa ON faqs(es_activa);

-- ============================================================================
-- 3. MATRIZ DE MATERIALIDAD MEJORADA (Por Fase F0-F9)
-- ============================================================================

CREATE TABLE IF NOT EXISTS materialidad_matriz (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proyecto_id UUID NOT NULL,
    empresa_id UUID NOT NULL,

    -- Fase del flujo POE
    fase VARCHAR(10) NOT NULL CHECK (fase IN ('F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9')),
    nombre_fase VARCHAR(100),

    -- Evaluación por pilar (0-100)
    score_razon_negocios DECIMAL(5,2) DEFAULT 0,
    score_bee DECIMAL(5,2) DEFAULT 0,
    score_materialidad DECIMAL(5,2) DEFAULT 0,
    score_trazabilidad DECIMAL(5,2) DEFAULT 0,
    score_total DECIMAL(5,2) GENERATED ALWAYS AS (
        (score_razon_negocios + score_bee + score_materialidad + score_trazabilidad) / 4
    ) STORED,

    -- Documentos requeridos vs presentes
    documentos_requeridos JSONB DEFAULT '[]',
    documentos_presentes JSONB DEFAULT '[]',
    documentos_faltantes JSONB DEFAULT '[]',
    porcentaje_completitud DECIMAL(5,2) DEFAULT 0,

    -- Checklist específico de la fase
    checklist_items JSONB DEFAULT '[]',  -- [{item, requerido, cumplido, evidencia_id}]
    checklist_completitud DECIMAL(5,2) DEFAULT 0,

    -- Evaluación humana
    evaluado_por UUID,  -- user_id del evaluador
    evaluado_por_nombre VARCHAR(200),
    fecha_evaluacion TIMESTAMPTZ,
    notas_evaluacion TEXT,

    -- Candados (F2, F6, F8)
    es_candado BOOLEAN DEFAULT FALSE,
    candado_liberado BOOLEAN DEFAULT FALSE,
    candado_liberado_por UUID,
    candado_liberado_fecha TIMESTAMPTZ,
    candado_condiciones TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_materialidad_proyecto ON materialidad_matriz(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_materialidad_fase ON materialidad_matriz(fase);
CREATE INDEX IF NOT EXISTS idx_materialidad_empresa ON materialidad_matriz(empresa_id);

-- ============================================================================
-- 4. DEFENSE FILE MEJORADO (Estructura por Secciones)
-- ============================================================================

CREATE TABLE IF NOT EXISTS defense_files_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proyecto_id UUID NOT NULL,
    empresa_id UUID NOT NULL,

    -- Metadata del expediente
    folio_defensa VARCHAR(50) UNIQUE,
    titulo VARCHAR(500) NOT NULL,
    descripcion TEXT,

    -- Estado
    estado VARCHAR(50) DEFAULT 'borrador' CHECK (estado IN (
        'borrador', 'en_construccion', 'revision_interna',
        'aprobado', 'presentado', 'archivado'
    )),

    -- Índice de Defendibilidad (0-100)
    indice_defendibilidad DECIMAL(5,2) DEFAULT 0,

    -- Desglose por criterio TFJA
    score_razon_negocios DECIMAL(5,2) DEFAULT 0,
    score_bee DECIMAL(5,2) DEFAULT 0,
    score_materialidad DECIMAL(5,2) DEFAULT 0,
    score_trazabilidad DECIMAL(5,2) DEFAULT 0,
    score_coherencia_documental DECIMAL(5,2) DEFAULT 0,

    -- Secciones del expediente (5 secciones según documento)
    seccion_1_contexto JSONB DEFAULT '{}',       -- Contexto estratégico y razón de negocios
    seccion_2_contractual JSONB DEFAULT '{}',    -- Marco contractual (SOW, contratos)
    seccion_3_ejecucion JSONB DEFAULT '{}',      -- Evidencia de ejecución
    seccion_4_financiero JSONB DEFAULT '{}',     -- Aspecto financiero (CFDI, pagos, 3-way)
    seccion_5_cierre JSONB DEFAULT '{}',         -- Cierre y BEE post-implementación

    -- Documentos vinculados
    documentos_ids JSONB DEFAULT '[]',

    -- Deliberaciones y decisiones
    deliberaciones_ids JSONB DEFAULT '[]',
    decisiones_clave JSONB DEFAULT '[]',

    -- Aprobaciones requeridas
    aprobacion_fiscal BOOLEAN DEFAULT FALSE,
    aprobacion_fiscal_fecha TIMESTAMPTZ,
    aprobacion_fiscal_por UUID,

    aprobacion_legal BOOLEAN DEFAULT FALSE,
    aprobacion_legal_fecha TIMESTAMPTZ,
    aprobacion_legal_por UUID,

    aprobacion_finanzas BOOLEAN DEFAULT FALSE,
    aprobacion_finanzas_fecha TIMESTAMPTZ,
    aprobacion_finanzas_por UUID,

    -- Hash de integridad
    hash_contenido VARCHAR(64),
    fecha_hash TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

CREATE INDEX IF NOT EXISTS idx_defense_v2_proyecto ON defense_files_v2(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_defense_v2_empresa ON defense_files_v2(empresa_id);
CREATE INDEX IF NOT EXISTS idx_defense_v2_estado ON defense_files_v2(estado);
CREATE INDEX IF NOT EXISTS idx_defense_v2_folio ON defense_files_v2(folio_defensa);

-- ============================================================================
-- 5. 3-WAY MATCH (Contrato = CFDI = Pago)
-- ============================================================================

CREATE TABLE IF NOT EXISTS three_way_match (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proyecto_id UUID NOT NULL,
    empresa_id UUID NOT NULL,

    -- Referencia del match
    match_id VARCHAR(50) UNIQUE,  -- TWM-YYYYMMDD-XXX

    -- Componente 1: Contrato
    contrato_id UUID,
    contrato_monto DECIMAL(18,2),
    contrato_concepto TEXT,
    contrato_fecha DATE,
    contrato_documento_id UUID,  -- Referencia al documento

    -- Componente 2: CFDI
    cfdi_uuid VARCHAR(36),
    cfdi_folio VARCHAR(50),
    cfdi_monto DECIMAL(18,2),
    cfdi_concepto TEXT,
    cfdi_fecha DATE,
    cfdi_rfc_emisor VARCHAR(20),
    cfdi_rfc_receptor VARCHAR(20),
    cfdi_documento_id UUID,
    cfdi_es_generico BOOLEAN DEFAULT FALSE,  -- Alerta si es genérico

    -- Componente 3: Pago
    pago_id UUID,
    pago_monto DECIMAL(18,2),
    pago_fecha DATE,
    pago_referencia VARCHAR(100),
    pago_banco VARCHAR(100),
    pago_documento_id UUID,  -- Comprobante

    -- Resultado del match
    match_status VARCHAR(50) DEFAULT 'pendiente' CHECK (match_status IN (
        'pendiente', 'parcial', 'completo', 'discrepancia', 'excepcion_aprobada'
    )),

    -- Discrepancias detectadas
    discrepancia_monto BOOLEAN DEFAULT FALSE,
    discrepancia_monto_detalle JSONB,
    discrepancia_concepto BOOLEAN DEFAULT FALSE,
    discrepancia_concepto_detalle TEXT,
    discrepancia_fecha BOOLEAN DEFAULT FALSE,
    discrepancia_fecha_detalle TEXT,

    -- Tolerancias
    tolerancia_monto_aplicada DECIMAL(18,2) DEFAULT 0,
    tolerancia_porcentaje DECIMAL(5,2) DEFAULT 0,

    -- Aprobación de excepción (si hay discrepancia)
    excepcion_aprobada BOOLEAN DEFAULT FALSE,
    excepcion_motivo TEXT,
    excepcion_aprobada_por UUID,
    excepcion_fecha TIMESTAMPTZ,

    -- Vinculación a Defense File
    defense_file_id UUID REFERENCES defense_files_v2(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_3way_proyecto ON three_way_match(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_3way_empresa ON three_way_match(empresa_id);
CREATE INDEX IF NOT EXISTS idx_3way_status ON three_way_match(match_status);
CREATE INDEX IF NOT EXISTS idx_3way_cfdi ON three_way_match(cfdi_uuid);

-- ============================================================================
-- 6. PLANTILLAS SIB/SOW/ACTAS
-- ============================================================================

CREATE TABLE IF NOT EXISTS plantillas_documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID,  -- NULL = plantillas del sistema

    -- Tipo de plantilla
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN (
        'SIB',           -- Service Initiation Brief
        'SOW',           -- Statement of Work
        'ACTA_KICKOFF',  -- Acta de arranque
        'ACTA_ACEPTACION', -- Acta de aceptación técnica
        'ACTA_ENTREGA',  -- Acta de entrega
        'MINUTA',        -- Minuta de reunión
        'VBC_FISCAL',    -- Visto Bueno Fiscal
        'VBC_LEGAL',     -- Visto Bueno Legal
        'MATRIZ_BEE',    -- Matriz de BEE
        'CONTRATO_MARCO',-- Contrato marco
        'ANEXO_TECNICO'  -- Anexo técnico
    )),

    -- Metadata
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    version VARCHAR(20) DEFAULT '1.0',

    -- Aplicabilidad
    tipologias_servicio JSONB DEFAULT '[]',  -- A qué tipos de servicio aplica
    fases_aplicables JSONB DEFAULT '[]',     -- En qué fases se usa

    -- Contenido
    estructura_json JSONB NOT NULL,  -- Estructura de campos requeridos
    contenido_html TEXT,             -- Template HTML
    contenido_markdown TEXT,         -- Template Markdown

    -- Campos dinámicos
    campos_requeridos JSONB DEFAULT '[]',    -- [{nombre, tipo, requerido, placeholder}]
    campos_calculados JSONB DEFAULT '[]',    -- [{nombre, formula}]

    -- Validaciones
    validaciones JSONB DEFAULT '[]',  -- Reglas de validación

    -- Estado
    es_activa BOOLEAN DEFAULT TRUE,
    es_sistema BOOLEAN DEFAULT FALSE,  -- TRUE = no editable por usuarios

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_plantillas_tipo ON plantillas_documentos(tipo);
CREATE INDEX IF NOT EXISTS idx_plantillas_empresa ON plantillas_documentos(empresa_id);
CREATE INDEX IF NOT EXISTS idx_plantillas_activa ON plantillas_documentos(es_activa);

-- ============================================================================
-- 7. DOCUMENTOS GENERADOS (Instancias de plantillas)
-- ============================================================================

CREATE TABLE IF NOT EXISTS documentos_generados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plantilla_id UUID REFERENCES plantillas_documentos(id),
    proyecto_id UUID NOT NULL,
    empresa_id UUID NOT NULL,

    -- Tipo heredado
    tipo VARCHAR(50) NOT NULL,

    -- Contenido
    titulo VARCHAR(500) NOT NULL,
    contenido_json JSONB NOT NULL,  -- Datos del formulario
    contenido_renderizado TEXT,      -- HTML/Markdown generado

    -- Archivo generado
    archivo_url VARCHAR(1000),
    archivo_hash VARCHAR(64),

    -- Firmas digitales
    firmado BOOLEAN DEFAULT FALSE,
    firmas JSONB DEFAULT '[]',  -- [{usuario_id, nombre, fecha, rol}]

    -- Vinculación
    fase VARCHAR(10),
    defense_file_id UUID,

    -- Estado
    estado VARCHAR(50) DEFAULT 'borrador',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_docs_gen_proyecto ON documentos_generados(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_docs_gen_tipo ON documentos_generados(tipo);
CREATE INDEX IF NOT EXISTS idx_docs_gen_plantilla ON documentos_generados(plantilla_id);

-- ============================================================================
-- 8. TIPOLOGÍAS DE SERVICIO (Expandido según documentos)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tipologias_servicio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificación
    codigo VARCHAR(50) UNIQUE NOT NULL,  -- CONSULTORIA_MACRO_MERCADO, INTRAGRUPO_MANAGEMENT_FEE, etc.
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,

    -- Clasificación de riesgo
    riesgo_inherente VARCHAR(20) CHECK (riesgo_inherente IN ('BAJO', 'MEDIO', 'ALTO', 'MUY_ALTO', 'CRITICO')),
    score_riesgo_base INT DEFAULT 0,  -- 0-100

    -- Documentos mínimos requeridos por fase
    docs_f0 JSONB DEFAULT '[]',  -- Documentos para F0
    docs_f1 JSONB DEFAULT '[]',  -- Documentos para F1 (SOW/Contrato)
    docs_f2 JSONB DEFAULT '[]',  -- Documentos para F2 (Candado inicio)
    docs_f3_f4 JSONB DEFAULT '[]', -- Documentos ejecución
    docs_f5 JSONB DEFAULT '[]',  -- Documentos entrega
    docs_f6 JSONB DEFAULT '[]',  -- Documentos VBC (Candado fiscal)
    docs_f7 JSONB DEFAULT '[]',  -- Documentos auditoría
    docs_f8 JSONB DEFAULT '[]',  -- Documentos pago (Candado pago)
    docs_f9 JSONB DEFAULT '[]',  -- Documentos post-implementación

    -- Checklist por pilar
    checklist_razon_negocios JSONB DEFAULT '[]',
    checklist_bee JSONB DEFAULT '[]',
    checklist_materialidad JSONB DEFAULT '[]',
    checklist_trazabilidad JSONB DEFAULT '[]',

    -- Criterios especiales
    requiere_precios_transferencia BOOLEAN DEFAULT FALSE,
    requiere_estudio_comparabilidad BOOLEAN DEFAULT FALSE,
    requiere_opinion_fiscal_externa BOOLEAN DEFAULT FALSE,

    -- Agentes responsables
    agentes_evaluadores JSONB DEFAULT '["A1_ESTRATEGIA", "A3_FISCAL"]',

    -- Metadata
    es_activa BOOLEAN DEFAULT TRUE,
    orden_display INT DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tipologias_codigo ON tipologias_servicio(codigo);
CREATE INDEX IF NOT EXISTS idx_tipologias_riesgo ON tipologias_servicio(riesgo_inherente);

-- ============================================================================
-- 9. INSERTAR DATOS INICIALES - BASE JURÍDICA
-- ============================================================================

INSERT INTO legal_base (tipo, categoria, titulo, numero_referencia, registro_digital, contenido_completo, resumen_ejecutivo, aplica_a_pilares, es_vigente) VALUES

-- Artículo 5-A CFF - Razón de Negocios
('articulo_cff', 'razon_negocios',
'Artículo 5-A CFF - Razón de Negocios',
'Art. 5-A CFF',
NULL,
'Los actos jurídicos que carezcan de una razón de negocios y que generen un beneficio fiscal directo o indirecto, tendrán los efectos fiscales que correspondan a los que se habrían realizado para la obtención del beneficio económico razonablemente esperado por el contribuyente.

Se considera que no existe una razón de negocios, cuando el beneficio económico cuantificable razonablemente esperado, sea menor al beneficio fiscal.

La autoridad fiscal sólo podrá presumir que no existe una razón de negocios, cuando el contribuyente haya elegido una forma jurídica que implique que el beneficio fiscal supere el beneficio económico razonablemente esperado, valorando las operaciones del contribuyente como un todo, considerando sus elementos relevantes.',
'Establece el principio de razón de negocios: los actos jurídicos deben tener un propósito económico real más allá del beneficio fiscal. El BEE (Beneficio Económico Esperado) debe ser mayor o igual al beneficio fiscal obtenido.',
'["razon_negocios", "bee"]',
TRUE),

-- Artículo 27 LISR - Estricta Indispensabilidad
('articulo_lisr', 'razon_negocios',
'Artículo 27 LISR - Requisitos de Deducciones',
'Art. 27 LISR',
NULL,
'Las deducciones autorizadas en este Título deberán reunir los siguientes requisitos:

I. Ser estrictamente indispensables para los fines de la actividad del contribuyente, salvo que se trate de donativos...

La estricta indispensabilidad se refiere a que los gastos deben ser necesarios para la generación de ingresos o para mantener la fuente de riqueza del contribuyente.',
'Los gastos deducibles deben ser ESTRICTAMENTE INDISPENSABLES para la actividad del contribuyente. Debe existir vinculación directa entre el gasto y la generación de ingresos.',
'["razon_negocios"]',
TRUE),

-- Artículo 69-B CFF - Materialidad (EFOS)
('articulo_cff', 'materialidad',
'Artículo 69-B CFF - Operaciones Inexistentes (EFOS)',
'Art. 69-B CFF',
NULL,
'Cuando la autoridad fiscal detecte que un contribuyente ha estado emitiendo comprobantes sin contar con los activos, personal, infraestructura o capacidad material, directa o indirectamente, para prestar los servicios o producir, comercializar o entregar los bienes que amparan tales comprobantes...

El contribuyente podrá manifestar ante la autoridad fiscal lo que a su derecho convenga y aportar la documentación e información que considere pertinente para desvirtuar los hechos que llevaron a la autoridad a notificarlo.',
'Establece el procedimiento para detectar y publicar contribuyentes que emiten comprobantes de operaciones inexistentes (EFOS). Requiere demostrar MATERIALIDAD: que las operaciones realmente existieron y fueron prestadas.',
'["materialidad"]',
TRUE),

-- NOM-151-SCFI-2016 - Trazabilidad
('norma_oficial', 'trazabilidad',
'NOM-151-SCFI-2016 - Conservación de Mensajes de Datos',
'NOM-151-SCFI-2016',
NULL,
'Esta Norma Oficial Mexicana establece los requisitos que deben observarse para la conservación de mensajes de datos y digitalización de documentos.

Los prestadores de servicios de certificación que deseen obtener la acreditación para conservar mensajes de datos deberán garantizar:
- Integridad del documento
- Autenticidad del documento
- Fecha cierta de existencia
- No repudio',
'Establece requisitos para conservación de documentos digitales con valor probatorio. Garantiza integridad, autenticidad, fecha cierta y no repudio de los documentos.',
'["trazabilidad"]',
TRUE),

-- Jurisprudencia SCJN - Uso de IA
('jurisprudencia', 'uso_ia',
'Jurisprudencia sobre Uso de Inteligencia Artificial',
'II.2o.C. J/1 K (12a.)',
'2031639',
'INTELIGENCIA ARTIFICIAL. SU USO COMO HERRAMIENTA EN EL CÁLCULO DE GARANTÍAS EN EL JUICIO DE AMPARO.

El uso de herramientas de inteligencia artificial para el cálculo de montos de garantías en juicios de amparo es válido y recomendable, siempre que se utilice como herramienta auxiliar y no sustituya la función jurisdiccional.

La IA aporta beneficios como:
- Reducción de errores humanos en cálculos complejos
- Transparencia y trazabilidad en los resultados
- Consistencia y estandarización de criterios
- Eficiencia, liberando tiempo para análisis sustantivo

El núcleo decisorio permanece siempre en la persona juzgadora, quien valida y aprueba los resultados generados por la herramienta tecnológica.',
'La SCJN avala el uso de IA como herramienta auxiliar en procesos jurídicos. La IA reduce errores, aporta transparencia y estandariza criterios, sin sustituir la decisión humana.',
'["uso_ia"]',
TRUE)

ON CONFLICT DO NOTHING;

-- ============================================================================
-- 10. INSERTAR DATOS INICIALES - TIPOLOGÍAS DE SERVICIO
-- ============================================================================

INSERT INTO tipologias_servicio (codigo, nombre, descripcion, riesgo_inherente, score_riesgo_base, docs_f0, docs_f1, docs_f6, checklist_razon_negocios, checklist_materialidad) VALUES

('CONSULTORIA_ESTRATEGICA',
'Consultoría Estratégica',
'Servicios de consultoría para definición de estrategia, planeación, transformación organizacional',
'MEDIO',
40,
'["ficha_proyecto", "justificacion_estrategica", "matriz_bee"]',
'["contrato_servicios", "sow_detallado", "alcance_entregables"]',
'["informe_final", "matriz_materialidad", "acta_aceptacion", "vbc_fiscal", "vbc_legal"]',
'["Vinculación con plan estratégico", "Objetivo de negocio definido", "BEE cuantificable"]',
'["Contrato específico", "Entregables documentados", "Minutas de seguimiento", "Informe final"]'),

('CONSULTORIA_MACRO_MERCADO',
'Consultoría Macro/Mercado',
'Estudios macroeconómicos, análisis de mercado, prospectiva sectorial',
'MEDIO',
35,
'["ficha_proyecto", "contexto_necesidad", "matriz_bee"]',
'["contrato_servicios", "sow_metodologia", "cronograma"]',
'["estudio_completo", "modelo_parametrico", "manual_metodologico", "matriz_materialidad"]',
'["Decisiones de inversión dependientes", "Contexto sectorial documentado", "Horizonte temporal definido"]',
'["Metodología clara", "Fuentes verificables", "Modelo entregado", "Presentación a dirección"]'),

('SOFTWARE_DESARROLLO',
'Desarrollo de Software',
'Desarrollo de aplicaciones, sistemas, plataformas tecnológicas',
'MEDIO',
45,
'["ficha_proyecto", "requerimientos_funcionales", "caso_negocio"]',
'["contrato_desarrollo", "especificaciones_tecnicas", "cronograma_sprints"]',
'["codigo_fuente", "documentacion_tecnica", "pruebas_qa", "acta_aceptacion"]',
'["Problema de negocio resuelto", "Capacidades inexistentes internamente", "ROI proyectado"]',
'["Código entregado", "Documentación técnica", "Ambiente productivo", "Capacitación"]'),

('MARKETING_BRANDING',
'Marketing y Branding',
'Servicios de marketing, publicidad, branding, comunicación',
'ALTO',
55,
'["brief_creativo", "objetivos_campana", "matriz_bee"]',
'["contrato_servicios", "alcance_creativo", "entregables_definidos"]',
'["materiales_entregados", "metricas_campana", "reportes_resultados"]',
'["Objetivo medible", "Público objetivo definido", "KPIs de performance"]',
'["Materiales creativos", "Reportes de métricas", "Evidencia de publicación", "Resultados vs objetivos"]'),

('INTRAGRUPO_MANAGEMENT_FEE',
'Servicios Intragrupo / Management Fee',
'Servicios entre partes relacionadas, cuotas de administración',
'MUY_ALTO',
75,
'["justificacion_servicio", "analisis_comparabilidad", "matriz_bee"]',
'["contrato_intercompany", "estudio_precios_transferencia", "base_asignacion"]',
'["reportes_periodicos", "evidencia_servicios", "conciliacion_bases", "estudio_pt_vigente"]',
'["Servicios realmente prestados", "Base de asignación justificada", "Beneficio para receptora"]',
'["Estudio PT vigente", "Reportes mensuales/trimestrales", "Evidencia de prestación", "Contratos formales"]'),

('ESG_CUMPLIMIENTO',
'ESG y Cumplimiento',
'Servicios de sustentabilidad, compliance, certificaciones',
'BAJO',
25,
'["requerimiento_regulatorio", "gap_analysis", "plan_implementacion"]',
'["contrato_servicios", "alcance_certificacion", "cronograma"]',
'["certificacion_obtenida", "reportes_cumplimiento", "evidencias_implementacion"]',
'["Obligación regulatoria o de mercado", "Beneficio reputacional cuantificable", "Riesgos mitigados"]',
'["Plan de trabajo", "Avances documentados", "Certificación/validación", "Evidencia de uso"]'),

('REESTRUCTURA_CORPORATIVA',
'Reestructura Corporativa',
'Fusiones, escisiones, reorganizaciones societarias',
'CRITICO',
85,
'["dictamen_necesidad", "analisis_opciones", "opinion_fiscal_previa"]',
'["protocolo_reestructura", "valuaciones", "estudios_fiscales"]',
'["actas_asamblea", "escrituras", "declaraciones_fiscales", "dictamen_fiscal"]',
'["Razón de negocios más allá de fiscal", "Beneficio económico medible", "Sustancia operativa post-reestructura"]',
'["Valuaciones independientes", "Opiniones fiscales", "Documentación corporativa completa"]')

ON CONFLICT (codigo) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    riesgo_inherente = EXCLUDED.riesgo_inherente,
    score_riesgo_base = EXCLUDED.score_riesgo_base,
    updated_at = NOW();

-- ============================================================================
-- 11. INSERTAR DATOS INICIALES - FAQ
-- ============================================================================

INSERT INTO faqs (categoria, pregunta, respuesta, respuesta_corta, orden, es_destacada) VALUES

('uso_ia',
'¿Revisar-IA sustituye al abogado fiscal o al contador?',
'No. La plataforma utiliza inteligencia artificial como herramienta de apoyo, pero las decisiones con consecuencias jurídicas y fiscales (celebrar contratos, autorizar pagos, determinar deducciones, definir postura ante SAT/TFJA) las toman siempre personas: Dirección, Fiscal, Legal, Finanzas.

Revisar-IA se encarga de:
- Aplicar checklists objetivos (5-A CFF, 27 LISR, 69-B CFF, NOM-151)
- Calcular risk_scores reproducibles
- Organizar Defense Files
- Señalar brechas (falta contrato, falta evidencia, CFDI genérico, riesgo EFOS, etc.)

La función de Fiscal/Legal no desaparece; se fortalece con mejor información y mejor documentación.',
'No. La IA auxilia, pero las decisiones legales/fiscales siempre las toman personas.',
1, TRUE),

('uso_ia',
'¿El SAT puede rechazar un gasto "porque lo revisó una IA"?',
'No hay base legal para eso. El SAT puede rechazar deducciones si:
- No hubo servicio real
- No hay contrato/SOW adecuado
- No hay entregables ni evidencia de ejecución
- El CFDI es genérico o no corresponde a la realidad
- No hay razón de negocios ni estricta indispensabilidad
- Se detecta que el proveedor es EFOS (69-B CFF) o la operación es simulada

Lo que la autoridad no hace es calificar el gasto por el software utilizado, sino por la realidad de los hechos y la calidad de las pruebas.

Revisar-IA está diseñada justamente para detectar esos problemas antes.',
'No. El SAT evalúa hechos y pruebas, no el software usado para documentarlos.',
2, TRUE),

('uso_ia',
'¿Qué aval tiene el uso de IA desde el punto de vista jurídico?',
'Hay dos planos:

1. La ley fiscal mexicana NO PROHÍBE el uso de sistemas automatizados o IA para control interno, checklists, cálculos o preparación de expedientes.

2. Existe jurisprudencia federal (Registro 2031639) que reconoce que la inteligencia artificial puede utilizarse válidamente en procesos judiciales para tareas auxiliares, siempre que no sustituya la función de la persona juzgadora.

La jurisprudencia destaca que la IA:
- Reduce errores humanos en cálculos complejos
- Aporta transparencia y trazabilidad
- Genera consistencia y estandarización
- Mejora la eficiencia

Revisar-IA aplica exactamente esta lógica: la IA no dicta sentencias ni firma contratos; se usa para calcular, organizar y documentar.',
'La ley no lo prohíbe y existe jurisprudencia SCJN que avala el uso de IA como herramienta auxiliar.',
3, TRUE),

('materialidad',
'¿Qué hace Revisar-IA respecto de la materialidad (Art. 69-B CFF)?',
'La plataforma obliga a construir una Matriz de Materialidad por proyecto, donde cada HECHO (contratación, ejecución, entrega, pago) se liga a EVIDENCIAS concretas (contrato, SOW, minutas, borradores, informes, modelos, logs, CFDI, transferencias).

Además:
- Mide el porcentaje de completitud de materialidad
- No permite declarar F6 como completada (ni emitir VBC Fiscal/Legal) si no se alcanza un umbral mínimo de evidencia o faltan documentos críticos

El objetivo es obligar internamente a que no se considere "cerrado" un servicio sin soporte suficiente.',
'Construye matriz de materialidad con evidencias específicas y bloquea avance sin documentación suficiente.',
4, TRUE),

('materialidad',
'¿Qué pasa con servicios intra-grupo y management fees?',
'En esas tipologías (INTRAGRUPO_MANAGEMENT_FEE), Revisar-IA:
- Marca riesgo inherente MUY ALTO
- Exige como mínimos:
  * Estudio de precios de transferencia vigente
  * Contrato con desglose de servicios
  * Base clara de asignación del fee
  * Reportes periódicos de servicios prestados
  * Evidencia de capacidad operativa del prestador

En estas operaciones, la revisión humana de Fiscal y Legal es SIEMPRE obligatoria, sin depender solo del análisis automatizado.',
'Riesgo MUY ALTO. Requiere estudio PT, contratos detallados, reportes periódicos y revisión humana obligatoria.',
5, TRUE),

('defensa',
'¿Revisar-IA garantiza que nunca habrá ajustes del SAT?',
'No. Ninguna herramienta puede garantizar eso.

Lo que hace es:
1. Reducir la probabilidad de ajustes por errores evitables:
   - Falta de contrato
   - CFDI genéricos
   - Ausencia de entregables
   - Inexistencia de BEE
   - Mala documentación de servicios intra-grupo o marketing

2. Si aún así hubiera un ajuste, te permite tener:
   - Un Defense File ordenado y completo
   - Mejores argumentos
   - Mayor claridad de qué se hizo bien o mal, para ajustar políticas futuras',
'No garantiza cero ajustes, pero reduce riesgos evitables y mejora capacidad de defensa.',
6, FALSE),

('razon_negocios',
'¿Qué hace Revisar-IA en materia de razón de negocios (Art. 5-A CFF)?',
'La plataforma exige que cada servicio relevante tenga:

1. Un SIB/BEE (Service Initiation Brief) donde se explique:
   - El objetivo de negocio del servicio
   - El tipo de beneficio económico esperado (ingresos, ahorros, mitigación de riesgo, cumplimiento)
   - El horizonte de tiempo
   - Los KPIs con los que se evaluará el resultado

2. Una vinculación explícita con:
   - Los pilares estratégicos de la empresa
   - Los OKRs del año

Los agentes Fiscal (A3) y Estrategia (A1) utilizan esa información para determinar si hay una razón de negocios real, si el BEE es razonable, y que no se trate solo de una operación "para deducir".',
'Exige documentar objetivo, BEE, horizonte y KPIs, vinculándolos con estrategia empresarial.',
7, FALSE)

ON CONFLICT DO NOTHING;

-- ============================================================================
-- 12. INSERTAR PLANTILLAS BASE
-- ============================================================================

INSERT INTO plantillas_documentos (tipo, nombre, descripcion, version, es_sistema, estructura_json, campos_requeridos) VALUES

('SIB', 'Service Initiation Brief - Estándar',
'Plantilla estándar para justificación de servicios',
'1.0', TRUE,
'{
  "secciones": [
    {"id": "contexto", "titulo": "Contexto y Necesidad", "descripcion": "¿Por qué se necesita este servicio?"},
    {"id": "objetivo", "titulo": "Objetivo de Negocio", "descripcion": "¿Qué problema resuelve o qué oportunidad captura?"},
    {"id": "bee", "titulo": "Beneficio Económico Esperado", "descripcion": "Cuantificación del beneficio"},
    {"id": "alineacion", "titulo": "Alineación Estratégica", "descripcion": "Vinculación con pilares y OKRs"},
    {"id": "alternativas", "titulo": "Alternativas Consideradas", "descripcion": "¿Por qué esta opción y no otra?"},
    {"id": "riesgos", "titulo": "Riesgos Identificados", "descripcion": "Riesgos de hacer y de no hacer"}
  ]
}',
'[
  {"nombre": "nombre_proyecto", "tipo": "text", "requerido": true},
  {"nombre": "monto_estimado", "tipo": "currency", "requerido": true},
  {"nombre": "area_solicitante", "tipo": "text", "requerido": true},
  {"nombre": "tipo_beneficio", "tipo": "select", "opciones": ["Ingresos adicionales", "Ahorros de costos", "Mitigación de riesgos", "Cumplimiento regulatorio"], "requerido": true},
  {"nombre": "horizonte_beneficio", "tipo": "select", "opciones": ["6 meses", "12 meses", "24 meses", "36 meses", "Más de 36 meses"], "requerido": true},
  {"nombre": "cuantificacion_bee", "tipo": "text", "requerido": true},
  {"nombre": "pilar_estrategico", "tipo": "text", "requerido": true},
  {"nombre": "okr_vinculado", "tipo": "text", "requerido": false}
]'),

('SOW', 'Statement of Work - Estándar',
'Plantilla estándar para alcance de servicios',
'1.0', TRUE,
'{
  "secciones": [
    {"id": "partes", "titulo": "Partes Contratantes"},
    {"id": "objeto", "titulo": "Objeto del Servicio"},
    {"id": "alcance", "titulo": "Alcance Detallado"},
    {"id": "entregables", "titulo": "Lista de Entregables"},
    {"id": "cronograma", "titulo": "Cronograma de Ejecución"},
    {"id": "honorarios", "titulo": "Esquema de Honorarios"},
    {"id": "criterios_aceptacion", "titulo": "Criterios de Aceptación"},
    {"id": "exclusiones", "titulo": "Exclusiones"}
  ]
}',
'[
  {"nombre": "proveedor", "tipo": "text", "requerido": true},
  {"nombre": "rfc_proveedor", "tipo": "text", "requerido": true},
  {"nombre": "objeto_servicio", "tipo": "textarea", "requerido": true},
  {"nombre": "entregables", "tipo": "array", "requerido": true},
  {"nombre": "fecha_inicio", "tipo": "date", "requerido": true},
  {"nombre": "fecha_fin", "tipo": "date", "requerido": true},
  {"nombre": "monto_total", "tipo": "currency", "requerido": true},
  {"nombre": "forma_pago", "tipo": "text", "requerido": true}
]'),

('ACTA_ACEPTACION', 'Acta de Aceptación Técnica',
'Plantilla para formalizar la aceptación de entregables',
'1.0', TRUE,
'{
  "secciones": [
    {"id": "datos_proyecto", "titulo": "Datos del Proyecto"},
    {"id": "entregables_recibidos", "titulo": "Entregables Recibidos"},
    {"id": "verificacion", "titulo": "Verificación de Criterios"},
    {"id": "observaciones", "titulo": "Observaciones"},
    {"id": "aceptacion", "titulo": "Declaración de Aceptación"},
    {"id": "firmas", "titulo": "Firmas"}
  ]
}',
'[
  {"nombre": "proyecto_nombre", "tipo": "text", "requerido": true},
  {"nombre": "folio_proyecto", "tipo": "text", "requerido": true},
  {"nombre": "proveedor", "tipo": "text", "requerido": true},
  {"nombre": "fecha_recepcion", "tipo": "date", "requerido": true},
  {"nombre": "entregables_verificados", "tipo": "array", "requerido": true},
  {"nombre": "cumple_criterios", "tipo": "boolean", "requerido": true},
  {"nombre": "observaciones", "tipo": "textarea", "requerido": false},
  {"nombre": "responsable_area", "tipo": "text", "requerido": true}
]'),

('VBC_FISCAL', 'Visto Bueno Fiscal',
'Plantilla para aprobación del área fiscal',
'1.0', TRUE,
'{
  "secciones": [
    {"id": "datos_operacion", "titulo": "Datos de la Operación"},
    {"id": "evaluacion_5a", "titulo": "Evaluación Art. 5-A CFF (Razón de Negocios)"},
    {"id": "evaluacion_27", "titulo": "Evaluación Art. 27 LISR (Estricta Indispensabilidad)"},
    {"id": "evaluacion_69b", "titulo": "Evaluación Art. 69-B CFF (Materialidad)"},
    {"id": "riesgo", "titulo": "Evaluación de Riesgo Fiscal"},
    {"id": "dictamen", "titulo": "Dictamen"},
    {"id": "condiciones", "titulo": "Condiciones (si aplica)"}
  ]
}',
'[
  {"nombre": "folio_proyecto", "tipo": "text", "requerido": true},
  {"nombre": "monto_operacion", "tipo": "currency", "requerido": true},
  {"nombre": "tiene_razon_negocios", "tipo": "boolean", "requerido": true},
  {"nombre": "razon_negocios_detalle", "tipo": "textarea", "requerido": true},
  {"nombre": "es_estrictamente_indispensable", "tipo": "boolean", "requerido": true},
  {"nombre": "materialidad_score", "tipo": "number", "requerido": true},
  {"nombre": "risk_score", "tipo": "number", "requerido": true},
  {"nombre": "dictamen", "tipo": "select", "opciones": ["APROBAR", "APROBAR_CONDICIONES", "RECHAZAR", "ESCALAR"], "requerido": true},
  {"nombre": "condiciones", "tipo": "textarea", "requerido": false},
  {"nombre": "responsable_fiscal", "tipo": "text", "requerido": true}
]'),

('MATRIZ_BEE', 'Matriz de Beneficio Económico Esperado',
'Plantilla para documentar y cuantificar el BEE',
'1.0', TRUE,
'{
  "secciones": [
    {"id": "proyecto", "titulo": "Identificación del Proyecto"},
    {"id": "tipo_beneficio", "titulo": "Tipo de Beneficio"},
    {"id": "cuantificacion", "titulo": "Cuantificación del Beneficio"},
    {"id": "horizonte", "titulo": "Horizonte Temporal"},
    {"id": "supuestos", "titulo": "Supuestos Clave"},
    {"id": "kpis", "titulo": "KPIs de Medición"},
    {"id": "seguimiento", "titulo": "Plan de Seguimiento"}
  ]
}',
'[
  {"nombre": "proyecto_nombre", "tipo": "text", "requerido": true},
  {"nombre": "tipo_beneficio", "tipo": "select", "opciones": ["Ingresos adicionales", "Ahorro de costos", "Mitigación de riesgos", "Cumplimiento", "Combinado"], "requerido": true},
  {"nombre": "monto_beneficio_estimado", "tipo": "currency", "requerido": true},
  {"nombre": "horizonte_meses", "tipo": "number", "requerido": true},
  {"nombre": "supuestos", "tipo": "array", "requerido": true},
  {"nombre": "kpis", "tipo": "array", "requerido": true},
  {"nombre": "fecha_primera_revision", "tipo": "date", "requerido": true}
]')

ON CONFLICT DO NOTHING;

-- ============================================================================
-- 13. FUNCIONES AUXILIARES
-- ============================================================================

-- Función para calcular score de materialidad por fase
CREATE OR REPLACE FUNCTION calcular_materialidad_score(
    p_docs_requeridos JSONB,
    p_docs_presentes JSONB
) RETURNS DECIMAL AS $$
DECLARE
    total_requeridos INT;
    total_presentes INT;
BEGIN
    total_requeridos := jsonb_array_length(COALESCE(p_docs_requeridos, '[]'::JSONB));
    total_presentes := jsonb_array_length(COALESCE(p_docs_presentes, '[]'::JSONB));

    IF total_requeridos = 0 THEN
        RETURN 100;
    END IF;

    RETURN ROUND((total_presentes::DECIMAL / total_requeridos::DECIMAL) * 100, 2);
END;
$$ LANGUAGE plpgsql;

-- Función para generar folio de Defense File
CREATE OR REPLACE FUNCTION generar_folio_defensa() RETURNS VARCHAR AS $$
DECLARE
    v_year VARCHAR(4);
    v_seq INT;
    v_folio VARCHAR(50);
BEGIN
    v_year := TO_CHAR(CURRENT_DATE, 'YYYY');

    SELECT COALESCE(MAX(
        CAST(SUBSTRING(folio_defensa FROM 'DF-' || v_year || '-(\d+)') AS INT)
    ), 0) + 1
    INTO v_seq
    FROM defense_files_v2
    WHERE folio_defensa LIKE 'DF-' || v_year || '-%';

    v_folio := 'DF-' || v_year || '-' || LPAD(v_seq::TEXT, 5, '0');

    RETURN v_folio;
END;
$$ LANGUAGE plpgsql;

-- Función para generar ID de 3-way match
CREATE OR REPLACE FUNCTION generar_match_id() RETURNS VARCHAR AS $$
DECLARE
    v_date VARCHAR(8);
    v_seq INT;
BEGIN
    v_date := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');

    SELECT COALESCE(MAX(
        CAST(SUBSTRING(match_id FROM 'TWM-' || v_date || '-(\d+)') AS INT)
    ), 0) + 1
    INTO v_seq
    FROM three_way_match
    WHERE match_id LIKE 'TWM-' || v_date || '-%';

    RETURN 'TWM-' || v_date || '-' || LPAD(v_seq::TEXT, 3, '0');
END;
$$ LANGUAGE plpgsql;

-- Trigger para auto-generar folio de Defense File
CREATE OR REPLACE FUNCTION trigger_generar_folio_defensa()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.folio_defensa IS NULL THEN
        NEW.folio_defensa := generar_folio_defensa();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_defense_folio ON defense_files_v2;
CREATE TRIGGER trg_defense_folio
    BEFORE INSERT ON defense_files_v2
    FOR EACH ROW
    EXECUTE FUNCTION trigger_generar_folio_defensa();

-- Trigger para auto-generar match_id
CREATE OR REPLACE FUNCTION trigger_generar_match_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.match_id IS NULL THEN
        NEW.match_id := generar_match_id();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_3way_match_id ON three_way_match;
CREATE TRIGGER trg_3way_match_id
    BEFORE INSERT ON three_way_match
    FOR EACH ROW
    EXECUTE FUNCTION trigger_generar_match_id();

-- ============================================================================
-- FIN DE MIGRACIÓN 003
-- ============================================================================

COMMENT ON TABLE legal_base IS 'Base jurídica y normativa para fundamentación legal del sistema';
COMMENT ON TABLE faqs IS 'Preguntas frecuentes fiscal/legal para usuarios';
COMMENT ON TABLE materialidad_matriz IS 'Matriz de materialidad por fase del flujo F0-F9';
COMMENT ON TABLE defense_files_v2 IS 'Expedientes de defensa estructurados con 5 secciones';
COMMENT ON TABLE three_way_match IS 'Validación 3-way match: Contrato = CFDI = Pago';
COMMENT ON TABLE plantillas_documentos IS 'Plantillas maestras SIB, SOW, Actas, VBC';
COMMENT ON TABLE documentos_generados IS 'Documentos generados a partir de plantillas';
COMMENT ON TABLE tipologias_servicio IS 'Catálogo de tipos de servicio con checklists por fase';
