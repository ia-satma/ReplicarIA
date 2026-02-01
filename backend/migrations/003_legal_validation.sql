-- ============================================================
-- REVISAR.IA - Migración: Sistema de Validación Legal
-- ============================================================
-- Tablas para almacenar resultados de validación legal
-- basado en LISR 27, CFF 69-B, CFF 5-A, LIVA 5, Anexo 20
-- ============================================================

-- Tabla principal de evaluaciones de operaciones
CREATE TABLE IF NOT EXISTS legal_evaluaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID REFERENCES empresas(id),
    operacion_id VARCHAR(100) NOT NULL,
    proveedor_rfc VARCHAR(13) NOT NULL,
    proveedor_nombre VARCHAR(255),
    monto DECIMAL(18, 2) NOT NULL,
    tipo_servicio VARCHAR(50) NOT NULL,

    -- Resultado de validación
    nivel_riesgo VARCHAR(20) NOT NULL CHECK (nivel_riesgo IN ('verde', 'amarillo', 'rojo')),
    score_total DECIMAL(5, 2) NOT NULL,
    score_formal DECIMAL(5, 2) NOT NULL,
    score_materialidad DECIMAL(5, 2) NOT NULL,
    score_razon_negocios DECIMAL(5, 2) NOT NULL,

    -- Flags de validación
    es_parte_relacionada BOOLEAN DEFAULT FALSE,
    proveedor_en_69b BOOLEAN DEFAULT FALSE,
    cfdi_validado BOOLEAN DEFAULT TRUE,
    tiene_opinion_32d BOOLEAN DEFAULT FALSE,

    -- Resumen y acciones
    resumen TEXT,
    acciones_correctivas JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,

    -- Índices para búsqueda
    CONSTRAINT uk_legal_eval_operacion UNIQUE (empresa_id, operacion_id)
);

-- Tabla de resultados por regla
CREATE TABLE IF NOT EXISTS legal_resultados_regla (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluacion_id UUID NOT NULL REFERENCES legal_evaluaciones(id) ON DELETE CASCADE,
    regla_id VARCHAR(50) NOT NULL,
    regla_nombre VARCHAR(100) NOT NULL,
    capa VARCHAR(30) NOT NULL,

    -- Resultado
    cumple BOOLEAN NOT NULL,
    nivel_cumplimiento DECIMAL(5, 4) NOT NULL,

    -- Evidencias
    evidencias_presentes JSONB DEFAULT '[]'::jsonb,
    evidencias_faltantes JSONB DEFAULT '[]'::jsonb,

    -- Detalles
    observaciones TEXT,
    recomendaciones JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de evidencias documentales asociadas a operaciones
CREATE TABLE IF NOT EXISTS legal_evidencias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluacion_id UUID REFERENCES legal_evaluaciones(id) ON DELETE CASCADE,
    operacion_id VARCHAR(100) NOT NULL,
    empresa_id UUID REFERENCES empresas(id),

    -- Tipo y descripción
    tipo_evidencia VARCHAR(50) NOT NULL,
    descripcion TEXT,

    -- Archivo asociado
    archivo_id UUID,
    archivo_nombre VARCHAR(255),
    archivo_url TEXT,

    -- Metadata
    fecha_documento DATE,
    verificado BOOLEAN DEFAULT FALSE,
    verificado_por UUID,
    verificado_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de consultas a listas SAT (69-B, 32-D, etc.)
CREATE TABLE IF NOT EXISTS legal_consultas_sat (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID REFERENCES empresas(id),
    proveedor_rfc VARCHAR(13) NOT NULL,

    -- Tipo de consulta
    tipo_consulta VARCHAR(30) NOT NULL CHECK (tipo_consulta IN ('lista_69b', 'opinion_32d', 'validacion_cfdi', 'situacion_fiscal')),

    -- Resultado
    resultado VARCHAR(50) NOT NULL,
    en_lista_negativa BOOLEAN DEFAULT FALSE,
    detalles JSONB,

    -- Vigencia
    fecha_consulta TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    vigente_hasta DATE,

    -- Comprobante
    evidencia_archivo_id UUID,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para rendimiento
CREATE INDEX IF NOT EXISTS idx_legal_eval_empresa ON legal_evaluaciones(empresa_id);
CREATE INDEX IF NOT EXISTS idx_legal_eval_proveedor ON legal_evaluaciones(proveedor_rfc);
CREATE INDEX IF NOT EXISTS idx_legal_eval_riesgo ON legal_evaluaciones(nivel_riesgo);
CREATE INDEX IF NOT EXISTS idx_legal_eval_fecha ON legal_evaluaciones(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_legal_eval_tipo ON legal_evaluaciones(tipo_servicio);

CREATE INDEX IF NOT EXISTS idx_legal_result_eval ON legal_resultados_regla(evaluacion_id);
CREATE INDEX IF NOT EXISTS idx_legal_result_regla ON legal_resultados_regla(regla_id);
CREATE INDEX IF NOT EXISTS idx_legal_result_cumple ON legal_resultados_regla(cumple);

CREATE INDEX IF NOT EXISTS idx_legal_evid_eval ON legal_evidencias(evaluacion_id);
CREATE INDEX IF NOT EXISTS idx_legal_evid_tipo ON legal_evidencias(tipo_evidencia);
CREATE INDEX IF NOT EXISTS idx_legal_evid_empresa ON legal_evidencias(empresa_id);

CREATE INDEX IF NOT EXISTS idx_legal_sat_rfc ON legal_consultas_sat(proveedor_rfc);
CREATE INDEX IF NOT EXISTS idx_legal_sat_tipo ON legal_consultas_sat(tipo_consulta);
CREATE INDEX IF NOT EXISTS idx_legal_sat_empresa ON legal_consultas_sat(empresa_id);

-- Vista para dashboard de riesgo
CREATE OR REPLACE VIEW v_legal_dashboard AS
SELECT
    e.empresa_id,
    COUNT(*) as total_evaluaciones,
    COUNT(*) FILTER (WHERE nivel_riesgo = 'verde') as evaluaciones_verde,
    COUNT(*) FILTER (WHERE nivel_riesgo = 'amarillo') as evaluaciones_amarillo,
    COUNT(*) FILTER (WHERE nivel_riesgo = 'rojo') as evaluaciones_rojo,
    AVG(score_total) as score_promedio,
    AVG(score_formal) as score_formal_promedio,
    AVG(score_materialidad) as score_materialidad_promedio,
    AVG(score_razon_negocios) as score_razon_promedio,
    SUM(monto) FILTER (WHERE nivel_riesgo = 'verde') as monto_bajo_riesgo,
    SUM(monto) FILTER (WHERE nivel_riesgo = 'amarillo') as monto_riesgo_medio,
    SUM(monto) FILTER (WHERE nivel_riesgo = 'rojo') as monto_alto_riesgo,
    COUNT(*) FILTER (WHERE proveedor_en_69b = TRUE) as proveedores_69b,
    MAX(e.created_at) as ultima_evaluacion
FROM legal_evaluaciones e
GROUP BY e.empresa_id;

-- Vista para alertas de riesgo
CREATE OR REPLACE VIEW v_legal_alertas AS
SELECT
    e.id,
    e.empresa_id,
    e.operacion_id,
    e.proveedor_rfc,
    e.proveedor_nombre,
    e.monto,
    e.nivel_riesgo,
    e.score_total,
    e.resumen,
    e.acciones_correctivas,
    e.created_at,
    CASE
        WHEN e.proveedor_en_69b THEN 'CRITICO: Proveedor en lista 69-B'
        WHEN e.nivel_riesgo = 'rojo' THEN 'ALTO: Operación con riesgo elevado'
        WHEN e.nivel_riesgo = 'amarillo' THEN 'MEDIO: Revisar documentación'
        ELSE NULL
    END as tipo_alerta
FROM legal_evaluaciones e
WHERE e.nivel_riesgo IN ('amarillo', 'rojo')
ORDER BY
    CASE e.nivel_riesgo
        WHEN 'rojo' THEN 1
        WHEN 'amarillo' THEN 2
        ELSE 3
    END,
    e.monto DESC;

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_legal_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_legal_eval_updated ON legal_evaluaciones;
CREATE TRIGGER tr_legal_eval_updated
    BEFORE UPDATE ON legal_evaluaciones
    FOR EACH ROW
    EXECUTE FUNCTION update_legal_updated_at();

DROP TRIGGER IF EXISTS tr_legal_evid_updated ON legal_evidencias;
CREATE TRIGGER tr_legal_evid_updated
    BEFORE UPDATE ON legal_evidencias
    FOR EACH ROW
    EXECUTE FUNCTION update_legal_updated_at();

-- Comentarios para documentación
COMMENT ON TABLE legal_evaluaciones IS 'Evaluaciones de riesgo legal de operaciones según LISR 27, CFF 69-B, 5-A, LIVA 5';
COMMENT ON TABLE legal_resultados_regla IS 'Resultados detallados por regla de validación';
COMMENT ON TABLE legal_evidencias IS 'Evidencias documentales asociadas a operaciones evaluadas';
COMMENT ON TABLE legal_consultas_sat IS 'Histórico de consultas a servicios SAT (69-B, 32-D, etc.)';
COMMENT ON VIEW v_legal_dashboard IS 'Vista consolidada para dashboard de riesgo legal por empresa';
COMMENT ON VIEW v_legal_alertas IS 'Vista de alertas activas por riesgo legal';
