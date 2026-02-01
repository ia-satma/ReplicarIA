-- ============================================================
-- REVISAR.IA - Migración: Sistema de Modo Defensa
-- ============================================================
-- Tablas para gestionar expedientes cuando existe un acto de
-- autoridad fiscal (revisión, visita, negativa, etc.)
-- ============================================================

-- Tabla principal de expedientes de defensa
CREATE TABLE IF NOT EXISTS expedientes_defensa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID REFERENCES empresas(id),

    -- Estado del expediente
    estado VARCHAR(50) NOT NULL DEFAULT 'recibido'
        CHECK (estado IN ('recibido', 'en_analisis', 'recopilando', 'elaborando_respuesta',
                          'listo_para_presentar', 'presentado', 'en_espera_resolucion',
                          'resuelto_favorable', 'resuelto_parcial', 'resuelto_desfavorable', 'en_impugnacion')),

    -- Datos del acto de autoridad
    tipo_acto VARCHAR(50) NOT NULL
        CHECK (tipo_acto IN ('revision_electronica', 'visita_domiciliaria', 'revision_gabinete',
                             'negativa_devolucion', 'oficio_observaciones', 'carta_invitacion', 'resolucion_provisional')),
    numero_oficio VARCHAR(100) NOT NULL,
    fecha_notificacion DATE NOT NULL,
    autoridad_emisora VARCHAR(255) NOT NULL,
    ejercicio_revisado INTEGER NOT NULL,

    -- Plazos
    plazo_dias_habiles INTEGER NOT NULL,
    fecha_limite DATE NOT NULL,

    -- Montos
    monto_total_cuestionado DECIMAL(18, 2) NOT NULL DEFAULT 0,

    -- Contenido del Defense File
    narrativa_hechos TEXT,
    argumentacion_juridica JSONB DEFAULT '{}'::jsonb,
    conclusion_operativa TEXT,

    -- Estrategia
    medio_defensa_recomendado VARCHAR(50)
        CHECK (medio_defensa_recomendado IN ('respuesta_requerimiento', 'recurso_revocacion',
                                              'juicio_nulidad', 'acuerdo_conclusivo', 'autocorreccion')),
    probabilidad_exito_estimada DECIMAL(5, 2) DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,

    CONSTRAINT uk_expediente_oficio UNIQUE (empresa_id, numero_oficio)
);

-- Tabla de operaciones cuestionadas dentro de un expediente
CREATE TABLE IF NOT EXISTS operaciones_cuestionadas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expediente_id UUID NOT NULL REFERENCES expedientes_defensa(id) ON DELETE CASCADE,

    -- Datos de la operación
    operacion_id VARCHAR(100) NOT NULL,
    proveedor_rfc VARCHAR(13) NOT NULL,
    proveedor_nombre VARCHAR(255),
    monto DECIMAL(18, 2) NOT NULL,
    tipo_servicio VARCHAR(50) NOT NULL,
    cfdi_folio VARCHAR(100),
    fecha_operacion DATE,

    -- Cuestionamiento
    motivo_cuestionamiento TEXT NOT NULL,

    -- Evaluación (resultado del LegalValidationService)
    evaluacion_id UUID REFERENCES legal_evaluaciones(id),
    nivel_riesgo VARCHAR(20),
    score_evaluacion DECIMAL(5, 2),

    -- Argumentación generada
    argumentacion_generada TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de documentos del expediente de defensa
CREATE TABLE IF NOT EXISTS documentos_expediente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expediente_id UUID NOT NULL REFERENCES expedientes_defensa(id) ON DELETE CASCADE,
    operacion_cuestionada_id UUID REFERENCES operaciones_cuestionadas(id) ON DELETE SET NULL,

    -- Identificación del documento
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL,

    -- Prioridad y descripción
    prioridad VARCHAR(20) NOT NULL DEFAULT 'media'
        CHECK (prioridad IN ('critica', 'alta', 'media', 'baja')),
    descripcion TEXT,
    fundamento_legal VARCHAR(255),

    -- Estado
    disponible BOOLEAN DEFAULT FALSE,
    fecha_obtencion DATE,

    -- Archivo asociado
    archivo_id UUID,
    archivo_nombre VARCHAR(255),
    archivo_url TEXT,

    -- Notas
    notas TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de historial de cambios del expediente
CREATE TABLE IF NOT EXISTS historial_expediente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expediente_id UUID NOT NULL REFERENCES expedientes_defensa(id) ON DELETE CASCADE,

    -- Cambio
    tipo_evento VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    estado_anterior VARCHAR(50),
    estado_nuevo VARCHAR(50),

    -- Usuario
    usuario_id UUID,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de plazos procesales (catálogo)
CREATE TABLE IF NOT EXISTS catalogo_plazos_procesales (
    id VARCHAR(50) PRIMARY KEY,
    tipo_acto VARCHAR(50) NOT NULL,
    plazo_respuesta INTEGER NOT NULL,
    unidad VARCHAR(20) NOT NULL DEFAULT 'dias_habiles',
    fundamento VARCHAR(100),
    prorroga_posible BOOLEAN DEFAULT FALSE,
    dias_prorroga INTEGER DEFAULT 0,
    notas TEXT
);

-- Insertar catálogo de plazos
INSERT INTO catalogo_plazos_procesales (id, tipo_acto, plazo_respuesta, unidad, fundamento, prorroga_posible, dias_prorroga, notas) VALUES
('PLAZO_REV_ELECT', 'revision_electronica', 15, 'dias_habiles', 'CFF Art. 53-B', TRUE, 10, 'Se puede solicitar prórroga por una sola vez'),
('PLAZO_VISITA', 'visita_domiciliaria', 20, 'dias_habiles', 'CFF Art. 46', TRUE, 15, 'Plazo para desvirtuar última acta parcial'),
('PLAZO_GABINETE', 'revision_gabinete', 20, 'dias_habiles', 'CFF Art. 48', TRUE, 15, 'Mismo tratamiento que visita domiciliaria'),
('PLAZO_NEG_DEV', 'negativa_devolucion', 30, 'dias_habiles', 'CFF Art. 22', FALSE, 0, 'Plazo para recurso de revocación'),
('PLAZO_OBS', 'oficio_observaciones', 20, 'dias_habiles', 'CFF Art. 48 Frac. VI', TRUE, 15, 'Momento crítico para desvirtuar'),
('PLAZO_CARTA', 'carta_invitacion', 15, 'dias_habiles', 'No vinculante legalmente', FALSE, 0, 'Aunque no es obligatoria, conviene atender'),
('PLAZO_RES_PROV', 'resolucion_provisional', 45, 'dias_habiles', 'CFF Art. 117', FALSE, 0, 'Plazo para interponer recurso de revocación')
ON CONFLICT (id) DO NOTHING;

-- Índices para rendimiento
CREATE INDEX IF NOT EXISTS idx_exp_def_empresa ON expedientes_defensa(empresa_id);
CREATE INDEX IF NOT EXISTS idx_exp_def_estado ON expedientes_defensa(estado);
CREATE INDEX IF NOT EXISTS idx_exp_def_tipo ON expedientes_defensa(tipo_acto);
CREATE INDEX IF NOT EXISTS idx_exp_def_fecha_limite ON expedientes_defensa(fecha_limite);
CREATE INDEX IF NOT EXISTS idx_exp_def_ejercicio ON expedientes_defensa(ejercicio_revisado);

CREATE INDEX IF NOT EXISTS idx_op_cuest_expediente ON operaciones_cuestionadas(expediente_id);
CREATE INDEX IF NOT EXISTS idx_op_cuest_proveedor ON operaciones_cuestionadas(proveedor_rfc);
CREATE INDEX IF NOT EXISTS idx_op_cuest_tipo ON operaciones_cuestionadas(tipo_servicio);

CREATE INDEX IF NOT EXISTS idx_doc_exp_expediente ON documentos_expediente(expediente_id);
CREATE INDEX IF NOT EXISTS idx_doc_exp_prioridad ON documentos_expediente(prioridad);
CREATE INDEX IF NOT EXISTS idx_doc_exp_disponible ON documentos_expediente(disponible);

CREATE INDEX IF NOT EXISTS idx_hist_expediente ON historial_expediente(expediente_id);
CREATE INDEX IF NOT EXISTS idx_hist_fecha ON historial_expediente(created_at DESC);

-- Vista de expedientes con alertas de plazo
CREATE OR REPLACE VIEW v_expedientes_alertas AS
SELECT
    e.id,
    e.empresa_id,
    e.estado,
    e.tipo_acto,
    e.numero_oficio,
    e.autoridad_emisora,
    e.fecha_limite,
    e.monto_total_cuestionado,
    e.probabilidad_exito_estimada,
    e.medio_defensa_recomendado,
    (e.fecha_limite - CURRENT_DATE) as dias_restantes,
    CASE
        WHEN (e.fecha_limite - CURRENT_DATE) <= 3 THEN 'CRITICA'
        WHEN (e.fecha_limite - CURRENT_DATE) <= 7 THEN 'ALTA'
        WHEN (e.fecha_limite - CURRENT_DATE) <= 15 THEN 'MEDIA'
        ELSE 'NORMAL'
    END as urgencia,
    (SELECT COUNT(*) FROM operaciones_cuestionadas oc WHERE oc.expediente_id = e.id) as num_operaciones,
    (SELECT COUNT(*) FROM documentos_expediente de WHERE de.expediente_id = e.id AND de.disponible = TRUE) as docs_listos,
    (SELECT COUNT(*) FROM documentos_expediente de WHERE de.expediente_id = e.id) as docs_total
FROM expedientes_defensa e
WHERE e.estado NOT IN ('resuelto_favorable', 'resuelto_parcial', 'resuelto_desfavorable')
ORDER BY
    CASE
        WHEN (e.fecha_limite - CURRENT_DATE) <= 3 THEN 1
        WHEN (e.fecha_limite - CURRENT_DATE) <= 7 THEN 2
        WHEN (e.fecha_limite - CURRENT_DATE) <= 15 THEN 3
        ELSE 4
    END,
    e.monto_total_cuestionado DESC;

-- Vista de documentos pendientes críticos
CREATE OR REPLACE VIEW v_documentos_pendientes_criticos AS
SELECT
    de.id,
    de.expediente_id,
    de.codigo,
    de.nombre,
    de.prioridad,
    de.fundamento_legal,
    e.numero_oficio,
    e.fecha_limite,
    (e.fecha_limite - CURRENT_DATE) as dias_restantes
FROM documentos_expediente de
JOIN expedientes_defensa e ON de.expediente_id = e.id
WHERE de.disponible = FALSE
  AND de.prioridad IN ('critica', 'alta')
  AND e.estado NOT IN ('resuelto_favorable', 'resuelto_parcial', 'resuelto_desfavorable')
ORDER BY
    CASE de.prioridad
        WHEN 'critica' THEN 1
        WHEN 'alta' THEN 2
        ELSE 3
    END,
    e.fecha_limite;

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_expediente_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_expediente_updated ON expedientes_defensa;
CREATE TRIGGER tr_expediente_updated
    BEFORE UPDATE ON expedientes_defensa
    FOR EACH ROW
    EXECUTE FUNCTION update_expediente_updated_at();

DROP TRIGGER IF EXISTS tr_doc_expediente_updated ON documentos_expediente;
CREATE TRIGGER tr_doc_expediente_updated
    BEFORE UPDATE ON documentos_expediente
    FOR EACH ROW
    EXECUTE FUNCTION update_expediente_updated_at();

-- Trigger para registrar cambios de estado en historial
CREATE OR REPLACE FUNCTION registrar_cambio_estado_expediente()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN
        INSERT INTO historial_expediente (expediente_id, tipo_evento, descripcion, estado_anterior, estado_nuevo)
        VALUES (NEW.id, 'cambio_estado', 'Cambio de estado del expediente', OLD.estado, NEW.estado);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_expediente_cambio_estado ON expedientes_defensa;
CREATE TRIGGER tr_expediente_cambio_estado
    AFTER UPDATE ON expedientes_defensa
    FOR EACH ROW
    EXECUTE FUNCTION registrar_cambio_estado_expediente();

-- Comentarios para documentación
COMMENT ON TABLE expedientes_defensa IS 'Expedientes de defensa cuando existe un acto de autoridad fiscal';
COMMENT ON TABLE operaciones_cuestionadas IS 'Operaciones individuales cuestionadas dentro de un expediente';
COMMENT ON TABLE documentos_expediente IS 'Documentos requeridos y disponibles para el expediente de defensa';
COMMENT ON TABLE historial_expediente IS 'Historial de cambios y eventos del expediente';
COMMENT ON TABLE catalogo_plazos_procesales IS 'Catálogo de plazos procesales por tipo de acto';
COMMENT ON VIEW v_expedientes_alertas IS 'Vista de expedientes activos con alertas de plazo';
COMMENT ON VIEW v_documentos_pendientes_criticos IS 'Vista de documentos críticos pendientes de obtener';
