-- ============================================================
-- REVISAR.IA - Migración: Abogado del Diablo
-- ============================================================
-- Módulo de control interno y aprendizaje organizacional.
-- ACCESO: Solo administradores.
--
-- ADVERTENCIA: Esta información es altamente sensible.
-- Debe tratarse como herramienta interna de compliance.
-- ============================================================

-- Tabla de industrias (catálogo)
CREATE TABLE IF NOT EXISTS catalogo_industrias (
    id VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

INSERT INTO catalogo_industrias (id, nombre, descripcion) VALUES
('retail', 'Retail', 'Comercio minorista'),
('manufactura', 'Manufactura', 'Industria manufacturera'),
('servicios_financieros', 'Servicios Financieros', 'Bancos, aseguradoras, fintechs'),
('tecnologia', 'Tecnología', 'TI, software, telecomunicaciones'),
('salud', 'Salud', 'Hospitales, laboratorios, farma'),
('construccion', 'Construcción', 'Construcción e inmobiliaria'),
('alimentos', 'Alimentos', 'Producción y distribución de alimentos'),
('energia', 'Energía', 'Petróleo, gas, electricidad, renovables'),
('transporte', 'Transporte', 'Logística y transporte'),
('educacion', 'Educación', 'Instituciones educativas'),
('comercio_exterior', 'Comercio Exterior', 'Importación/exportación'),
('inmobiliario', 'Inmobiliario', 'Desarrollo y administración inmobiliaria'),
('otro', 'Otro', 'Otras industrias')
ON CONFLICT (id) DO NOTHING;

-- Tabla principal de huellas de revisión
CREATE TABLE IF NOT EXISTS abogado_diablo_huellas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proyecto_id UUID NOT NULL,
    empresa_id UUID REFERENCES empresas(id),

    -- Clasificación
    industria VARCHAR(50) NOT NULL REFERENCES catalogo_industrias(id),
    tipo_servicio VARCHAR(50) NOT NULL,
    monto DECIMAL(18, 2) NOT NULL,
    proveedor_rfc VARCHAR(13),

    -- Timeline
    fecha_inicio TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    fecha_cierre TIMESTAMP WITH TIME ZONE,
    resultado_final VARCHAR(20) DEFAULT 'en_proceso'
        CHECK (resultado_final IN ('en_proceso', 'aprobado', 'rechazado', 'cancelado')),

    -- Scores consolidados por fase (JSONB para flexibilidad)
    scores_por_fase JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,

    CONSTRAINT uk_huella_proyecto UNIQUE (proyecto_id)
);

-- Tabla de cambios de semáforo
CREATE TABLE IF NOT EXISTS abogado_diablo_cambios_semaforo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    huella_id UUID NOT NULL REFERENCES abogado_diablo_huellas(id) ON DELETE CASCADE,

    -- Cambio
    fase VARCHAR(10) NOT NULL CHECK (fase IN ('F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9')),
    color_anterior VARCHAR(20) NOT NULL,
    color_nuevo VARCHAR(20) NOT NULL,
    score_anterior DECIMAL(5, 2),
    score_nuevo DECIMAL(5, 2),

    -- Contexto
    agente_responsable VARCHAR(50),
    version_entregable VARCHAR(50),
    justificacion TEXT,

    -- Evidencias que cambiaron el resultado
    evidencia_que_cambio JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de evidencias clave
CREATE TABLE IF NOT EXISTS abogado_diablo_evidencias_clave (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    huella_id UUID NOT NULL REFERENCES abogado_diablo_huellas(id) ON DELETE CASCADE,

    -- Evidencia
    tipo_evidencia VARCHAR(100) NOT NULL,
    descripcion TEXT,
    norma_acreditada VARCHAR(50),  -- LISR_27, CFF_69B, CFF_5A, LIVA_5, NOM_151
    impacto VARCHAR(50),  -- amarillo_a_verde, rojo_a_verde, rechazo_a_aprobado

    -- Reusabilidad
    reusable BOOLEAN DEFAULT TRUE,
    notas TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de preguntas incómodas respondidas
CREATE TABLE IF NOT EXISTS abogado_diablo_preguntas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    huella_id UUID NOT NULL REFERENCES abogado_diablo_huellas(id) ON DELETE CASCADE,

    -- Pregunta
    categoria VARCHAR(50) NOT NULL,  -- materialidad, razon_negocios, formal, proveedor
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,

    -- Soporte
    evidencia_soporte JSONB DEFAULT '[]'::jsonb,
    norma_relacionada VARCHAR(50),

    -- Efectividad
    efectiva BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de riesgos residuales aceptados
CREATE TABLE IF NOT EXISTS abogado_diablo_riesgos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    huella_id UUID NOT NULL REFERENCES abogado_diablo_huellas(id) ON DELETE CASCADE,

    -- Riesgo
    descripcion TEXT NOT NULL,
    nivel VARCHAR(20) NOT NULL CHECK (nivel IN ('ninguno', 'bajo', 'medio', 'alto', 'critico')),
    justificacion TEXT NOT NULL,
    mitigacion_propuesta TEXT,

    -- Exposición
    monto_exposicion DECIMAL(18, 2) DEFAULT 0,

    -- Aprobación
    aprobado_por UUID,
    fecha_aprobacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de perfiles de riesgo dinámico (aprendizaje)
CREATE TABLE IF NOT EXISTS abogado_diablo_perfiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Clave del perfil
    industria VARCHAR(50) NOT NULL REFERENCES catalogo_industrias(id),
    tipo_servicio VARCHAR(50) NOT NULL,
    rango_monto VARCHAR(20) NOT NULL,  -- <500k, 500k-2M, >2M

    -- Estadísticas
    total_casos INTEGER DEFAULT 0,
    casos_aprobados INTEGER DEFAULT 0,
    casos_rechazados INTEGER DEFAULT 0,
    score_promedio_aprobados DECIMAL(5, 2) DEFAULT 0,

    -- Aprendizaje
    evidencias_minimas JSONB DEFAULT '[]'::jsonb,
    objeciones_frecuentes JSONB DEFAULT '[]'::jsonb,
    patrones_exito JSONB DEFAULT '[]'::jsonb,
    alertas JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uk_perfil UNIQUE (industria, tipo_servicio, rango_monto)
);

-- Tabla de lecciones aprendidas
CREATE TABLE IF NOT EXISTS abogado_diablo_lecciones (
    id VARCHAR(100) PRIMARY KEY,

    -- Identificación
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,

    -- Clasificación
    industria VARCHAR(50) REFERENCES catalogo_industrias(id),
    tipo_servicio VARCHAR(50),
    categoria VARCHAR(50),  -- materialidad, razon_negocios, formal, proveedor
    norma_relacionada VARCHAR(50),

    -- Contenido
    contexto TEXT,
    problema_detectado TEXT,
    solucion_aplicada TEXT,

    -- Aplicabilidad
    aplicable_cuando JSONB DEFAULT '[]'::jsonb,
    no_aplicable_cuando JSONB DEFAULT '[]'::jsonb,

    -- Efectividad
    veces_aplicada INTEGER DEFAULT 0,
    veces_exitosa INTEGER DEFAULT 0,

    -- Origen
    origen VARCHAR(50) DEFAULT 'automatico',  -- automatico, manual
    registrado_por UUID,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de incidentes SAT (post-aprobación)
CREATE TABLE IF NOT EXISTS abogado_diablo_incidentes_sat (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proyecto_id UUID NOT NULL,
    huella_id UUID REFERENCES abogado_diablo_huellas(id) ON DELETE SET NULL,
    empresa_id UUID REFERENCES empresas(id),

    -- Incidente
    descripcion TEXT NOT NULL,
    tipo_acto VARCHAR(50) NOT NULL,  -- revision, visita, negativa, etc.
    monto_cuestionado DECIMAL(18, 2),
    fecha_incidente DATE NOT NULL,

    -- Resultado (si ya se conoce)
    resultado VARCHAR(50),  -- favorable, desfavorable, parcial, pendiente
    monto_ajustado DECIMAL(18, 2),
    fecha_resolucion DATE,
    notas_resolucion TEXT,

    -- Registro
    registrado_por UUID,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de preguntas incómodas (catálogo legacy)
CREATE TABLE IF NOT EXISTS catalogo_preguntas_incomodas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    categoria VARCHAR(50) NOT NULL,
    pregunta TEXT NOT NULL,
    tipo_servicio VARCHAR(50) DEFAULT 'todos',
    norma_relacionada VARCHAR(50),
    activa BOOLEAN DEFAULT TRUE,
    orden INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- TABLA DE PREGUNTAS ESTRUCTURADAS (25 PREGUNTAS CON SEVERIDAD)
-- ============================================================
CREATE TABLE IF NOT EXISTS catalogo_preguntas_estructuradas (
    id VARCHAR(50) PRIMARY KEY,  -- P01_DESCRIPCION_SERVICIO, etc.
    bloque VARCHAR(50) NOT NULL,  -- B1_hechos_objeto, B2_materialidad, etc.
    numero INTEGER NOT NULL,
    pregunta TEXT NOT NULL,
    descripcion TEXT,

    -- Clasificación
    severidad VARCHAR(20) NOT NULL CHECK (severidad IN ('critico', 'importante', 'informativo')),
    tipo_respuesta VARCHAR(30) NOT NULL CHECK (tipo_respuesta IN (
        'texto_corto', 'texto_largo', 'seleccion_simple',
        'seleccion_multiple', 'escala', 'porcentaje', 'monto'
    )),
    norma_relacionada VARCHAR(50),

    -- Acciones
    accion_si_negativo VARCHAR(30) NOT NULL CHECK (accion_si_negativo IN (
        'forzar_revision', 'bandera_roja', 'alerta', 'solo_aprendizaje'
    )),
    accion_si_incompleto VARCHAR(30) NOT NULL CHECK (accion_si_incompleto IN (
        'forzar_revision', 'bandera_roja', 'alerta', 'solo_aprendizaje'
    )),

    -- Opciones y umbrales
    opciones JSONB DEFAULT '[]'::jsonb,
    umbral_critico INTEGER,
    umbral_alerta INTEGER,

    -- Aplicabilidad
    aplica_a_servicios JSONB DEFAULT '["todos"]'::jsonb,
    obligatoria BOOLEAN DEFAULT TRUE,
    activa BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- INSERTAR LAS 25 PREGUNTAS ESTRUCTURADAS
-- ============================================================

-- BLOQUE 1: HECHOS Y OBJETO DEL SERVICIO (P01-P04)
INSERT INTO catalogo_preguntas_estructuradas (
    id, bloque, numero, pregunta, descripcion, severidad, tipo_respuesta,
    norma_relacionada, accion_si_negativo, accion_si_incompleto, opciones, obligatoria
) VALUES
('P01_DESCRIPCION_SERVICIO', 'B1_hechos_objeto', 1,
 '¿Puedes describir el servicio exactamente como lo entendería un auditor que no sabe nada del negocio?',
 'Verificar que la descripción del servicio sea clara, específica y comprensible para un tercero sin contexto previo.',
 'importante', 'texto_largo', 'CFF_69B', 'alerta', 'forzar_revision', '[]'::jsonb, TRUE),

('P02_ENTREGABLE_CONCRETO', 'B1_hechos_objeto', 2,
 '¿Cuál es el entregable físico o digital concreto que generó este servicio?',
 'Identificar evidencia tangible del resultado del servicio.',
 'critico', 'texto_corto', 'CFF_69B', 'bandera_roja', 'forzar_revision', '[]'::jsonb, TRUE),

('P03_EVIDENCIA_EJECUCION', 'B1_hechos_objeto', 3,
 '¿Cómo demostrarías que el servicio se prestó entre las fechas del contrato y la factura?',
 'Verificar correspondencia temporal entre documentos y ejecución real.',
 'critico', 'texto_largo', 'CFF_28_30', 'bandera_roja', 'forzar_revision', '[]'::jsonb, TRUE),

('P04_TESTIGO_INDEPENDIENTE', 'B1_hechos_objeto', 4,
 '¿Hay algún testigo, correo o registro de terceros que corrobore la ejecución?',
 'Buscar evidencia independiente que refuerce la materialidad.',
 'importante', 'seleccion_simple', 'CFF_69B', 'alerta', 'solo_aprendizaje',
 '["Sí, existe evidencia de terceros", "No, solo evidencia bilateral", "Parcialmente"]'::jsonb, TRUE)
ON CONFLICT (id) DO UPDATE SET
    pregunta = EXCLUDED.pregunta,
    descripcion = EXCLUDED.descripcion,
    severidad = EXCLUDED.severidad,
    updated_at = NOW();

-- BLOQUE 2: MATERIALIDAD / CFF 69-B (P05-P08)
INSERT INTO catalogo_preguntas_estructuradas (
    id, bloque, numero, pregunta, descripcion, severidad, tipo_respuesta,
    norma_relacionada, accion_si_negativo, accion_si_incompleto, opciones, umbral_critico, obligatoria
) VALUES
('P05_CAPACIDAD_PROVEEDOR', 'B2_materialidad', 5,
 '¿El proveedor tiene la capacidad material, humana y técnica demostrable para prestar este servicio?',
 'Evaluar si el proveedor podría razonablemente haber prestado el servicio según su estructura.',
 'critico', 'escala', 'CFF_69B', 'bandera_roja', 'forzar_revision',
 '["Alta capacidad demostrada", "Capacidad parcial/inferida", "Capacidad dudosa", "Sin evidencia de capacidad"]'::jsonb, 2, TRUE),

('P06_DOMICILIO_VERIFICABLE', 'B2_materialidad', 6,
 '¿El domicilio fiscal del proveedor es verificable y congruente con su actividad?',
 'Verificar que el domicilio fiscal exista y sea apropiado para la operación declarada.',
 'critico', 'seleccion_simple', 'CFF_69B', 'bandera_roja', 'forzar_revision',
 '["Verificado y congruente", "Verificado pero cuestionable", "No verificable", "No localizable"]'::jsonb, NULL, TRUE),

('P07_RASTRO_DIGITAL', 'B2_materialidad', 7,
 '¿Existe un rastro digital independiente y verificable de la prestación del servicio?',
 'Identificar evidencia digital que no pueda ser fabricada unilateralmente.',
 'importante', 'seleccion_multiple', 'NOM_151', 'alerta', 'solo_aprendizaje',
 '["Correos con timestamps", "Plataformas de gestión de proyectos", "Métricas de terceros", "Logs de sistemas", "Ninguno de los anteriores"]'::jsonb, NULL, TRUE),

('P08_FABRICACION_POSTERIOR', 'B2_materialidad', 8,
 '¿La evidencia presentada podría haber sido fabricada o generada después de los hechos?',
 'Evaluar el riesgo de que la documentación haya sido creada ex post facto.',
 'critico', 'escala', 'CFF_69B', 'bandera_roja', 'forzar_revision',
 '["Imposible de fabricar (sellos/terceros)", "Difícil de fabricar", "Posible fabricación", "Alta probabilidad de fabricación"]'::jsonb, 2, TRUE)
ON CONFLICT (id) DO UPDATE SET
    pregunta = EXCLUDED.pregunta,
    descripcion = EXCLUDED.descripcion,
    severidad = EXCLUDED.severidad,
    umbral_critico = EXCLUDED.umbral_critico,
    updated_at = NOW();

-- BLOQUE 3: RAZÓN DE NEGOCIOS / CFF 5-A (P09-P12)
INSERT INTO catalogo_preguntas_estructuradas (
    id, bloque, numero, pregunta, descripcion, severidad, tipo_respuesta,
    norma_relacionada, accion_si_negativo, accion_si_incompleto, opciones, umbral_critico, obligatoria
) VALUES
('P09_BENEFICIO_SIN_FISCAL', 'B3_razon_negocios', 9,
 '¿Qué beneficio económico concreto obtuvo la empresa, independientemente del efecto fiscal?',
 'Identificar el valor real del servicio más allá de la deducción.',
 'critico', 'texto_largo', 'CFF_5A', 'bandera_roja', 'forzar_revision', '[]'::jsonb, NULL, TRUE),

('P10_ALTERNATIVA_INTERNA', 'B3_razon_negocios', 10,
 '¿Por qué no se hizo internamente si la empresa tiene o podría tener la capacidad?',
 'Justificar la necesidad de externalizar vs. desarrollar internamente.',
 'importante', 'seleccion_simple', 'CFF_5A', 'alerta', 'solo_aprendizaje',
 '["Especialización técnica no disponible internamente", "Capacidad insuficiente (tiempo/recursos)", "Costo-beneficio favorable a tercerizar", "No se evaluó la alternativa interna"]'::jsonb, NULL, TRUE),

('P11_PRECIO_MERCADO', 'B3_razon_negocios', 11,
 '¿El precio pagado es congruente con referencias de mercado para servicios similares?',
 'Verificar que el precio no sea artificialmente alto o bajo.',
 'importante', 'escala', 'LISR_27', 'alerta', 'forzar_revision',
 '["Dentro de rango de mercado", "Ligeramente por arriba", "Significativamente elevado", "Sin referencia comparable"]'::jsonb, 2, TRUE),

('P12_RESULTADO_MEDIBLE', 'B3_razon_negocios', 12,
 '¿Se midió o evaluó el resultado del servicio? ¿Existe evidencia de la medición?',
 'Verificar que el servicio tuvo un impacto evaluable.',
 'informativo', 'seleccion_simple', 'CFF_5A', 'solo_aprendizaje', 'solo_aprendizaje',
 '["Sí, con métricas documentadas", "Sí, evaluación informal", "No se midió", "No aplica medición"]'::jsonb, NULL, FALSE)
ON CONFLICT (id) DO UPDATE SET
    pregunta = EXCLUDED.pregunta,
    descripcion = EXCLUDED.descripcion,
    severidad = EXCLUDED.severidad,
    umbral_critico = EXCLUDED.umbral_critico,
    updated_at = NOW();

-- BLOQUE 4: PROVEEDOR Y EFOS (P13-P16)
INSERT INTO catalogo_preguntas_estructuradas (
    id, bloque, numero, pregunta, descripcion, severidad, tipo_respuesta,
    norma_relacionada, accion_si_negativo, accion_si_incompleto, opciones, umbral_alerta, obligatoria
) VALUES
('P13_LISTA_69B', 'B4_proveedor_efos', 13,
 '¿Se verificó que el proveedor NO esté en lista 69-B antes de contratar y al momento de pagar?',
 'Verificación obligatoria en lista de operaciones simuladas del SAT.',
 'critico', 'seleccion_simple', 'CFF_69B', 'bandera_roja', 'bandera_roja',
 '["Verificado limpio en ambas fechas", "Solo verificado al contratar", "En lista 69-B", "No se verificó"]'::jsonb, NULL, TRUE),

('P14_OPINION_32D', 'B4_proveedor_efos', 14,
 '¿Se cuenta con opinión de cumplimiento 32-D positiva y vigente del proveedor?',
 'Verificar cumplimiento fiscal del proveedor mediante constancia oficial.',
 'importante', 'seleccion_simple', 'CFF_32D', 'alerta', 'alerta',
 '["Opinión positiva vigente", "Opinión vencida", "Opinión negativa", "No se solicitó"]'::jsonb, NULL, TRUE),

('P15_HISTORIAL_PROVEEDOR', 'B4_proveedor_efos', 15,
 '¿El proveedor tiene historial verificable de operaciones reales con otros clientes?',
 'Evaluar si el proveedor tiene trayectoria comercial legítima.',
 'importante', 'escala', 'CFF_69B', 'alerta', 'solo_aprendizaje',
 '["Historial amplio verificable", "Historial limitado pero real", "Historial no verificable", "Proveedor nuevo/desconocido"]'::jsonb, 2, TRUE),

('P16_EMPLEADOS_IMSS', 'B4_proveedor_efos', 16,
 '¿El proveedor tiene empleados registrados en IMSS congruentes con su operación?',
 'Verificar que el proveedor tenga estructura laboral real.',
 'importante', 'seleccion_simple', 'CFF_69B', 'alerta', 'solo_aprendizaje',
 '["Plantilla congruente verificada", "Plantilla mínima pero existente", "Sin empleados registrados", "No verificable"]'::jsonb, NULL, TRUE)
ON CONFLICT (id) DO UPDATE SET
    pregunta = EXCLUDED.pregunta,
    descripcion = EXCLUDED.descripcion,
    severidad = EXCLUDED.severidad,
    umbral_alerta = EXCLUDED.umbral_alerta,
    updated_at = NOW();

-- BLOQUE 5: REQUISITOS FISCALES FORMALES (P17-P21)
INSERT INTO catalogo_preguntas_estructuradas (
    id, bloque, numero, pregunta, descripcion, severidad, tipo_respuesta,
    norma_relacionada, accion_si_negativo, accion_si_incompleto, opciones, umbral_critico, obligatoria
) VALUES
('P17_CFDI_DETALLE', 'B5_formal_fiscal', 17,
 '¿El CFDI tiene descripción suficientemente detallada del servicio prestado?',
 'Verificar que el concepto del CFDI identifique claramente el servicio.',
 'critico', 'escala', 'CFF_29_29A', 'bandera_roja', 'forzar_revision',
 '["Descripción detallada y específica", "Descripción adecuada", "Descripción genérica", "Descripción insuficiente"]'::jsonb, 2, TRUE),

('P18_COINCIDENCIA_CONTRATO_CFDI', 'B5_formal_fiscal', 18,
 '¿Los datos del contrato coinciden exactamente con lo facturado en el CFDI?',
 'Verificar consistencia entre documentos contractuales y fiscales.',
 'critico', 'seleccion_simple', 'CFF_29_29A', 'bandera_roja', 'forzar_revision',
 '["Coincidencia exacta", "Diferencias menores explicables", "Diferencias significativas", "No hay contrato"]'::jsonb, NULL, TRUE),

('P19_PAGO_BANCARIZADO', 'B5_formal_fiscal', 19,
 '¿El pago se realizó por transferencia bancaria a cuenta del proveedor y está debidamente documentado?',
 'Verificar trazabilidad bancaria del pago.',
 'critico', 'seleccion_simple', 'LISR_27', 'bandera_roja', 'forzar_revision',
 '["Transferencia a cuenta del proveedor verificada", "Otro medio bancarizado documentado", "Pago en efectivo parcial", "Sin trazabilidad bancaria"]'::jsonb, NULL, TRUE),

('P20_CONGRUENCIA_FECHAS', 'B5_formal_fiscal', 20,
 '¿Hay congruencia lógica entre las fechas de contrato, servicio, factura y pago?',
 'Verificar que la secuencia temporal sea lógica y no presente inconsistencias.',
 'importante', 'seleccion_simple', 'CFF_28_30', 'alerta', 'forzar_revision',
 '["Secuencia lógica perfecta", "Pequeñas inconsistencias explicables", "Inconsistencias notables", "Secuencia ilógica"]'::jsonb, NULL, TRUE),

('P21_REGIMEN_CONGRUENTE', 'B5_formal_fiscal', 21,
 '¿El régimen fiscal del proveedor es congruente con el tipo de servicio prestado?',
 'Verificar que el proveedor pueda legalmente prestar el servicio según su régimen.',
 'importante', 'seleccion_simple', 'LISR_27', 'alerta', 'solo_aprendizaje',
 '["Régimen plenamente congruente", "Régimen aceptable", "Régimen cuestionable", "Régimen incompatible"]'::jsonb, NULL, TRUE)
ON CONFLICT (id) DO UPDATE SET
    pregunta = EXCLUDED.pregunta,
    descripcion = EXCLUDED.descripcion,
    severidad = EXCLUDED.severidad,
    umbral_critico = EXCLUDED.umbral_critico,
    updated_at = NOW();

-- BLOQUE 6: RIESGO RESIDUAL Y LECCIONES APRENDIDAS (P22-P25)
INSERT INTO catalogo_preguntas_estructuradas (
    id, bloque, numero, pregunta, descripcion, severidad, tipo_respuesta,
    norma_relacionada, accion_si_negativo, accion_si_incompleto, opciones, umbral_alerta, obligatoria
) VALUES
('P22_DEBILIDAD_PRINCIPAL', 'B6_riesgo_residual', 22,
 '¿Cuál es la debilidad más importante del expediente que podría explotar un auditor fiscal?',
 'Identificar el punto más vulnerable del caso para documentar el riesgo residual.',
 'informativo', 'texto_largo', 'general', 'solo_aprendizaje', 'solo_aprendizaje', '[]'::jsonb, NULL, TRUE),

('P23_MITIGACION_DEBILIDAD', 'B6_riesgo_residual', 23,
 '¿Qué se puede hacer para mitigar esta debilidad antes del cierre del expediente?',
 'Proponer acciones concretas para reducir el riesgo identificado.',
 'informativo', 'texto_largo', 'general', 'solo_aprendizaje', 'solo_aprendizaje', '[]'::jsonb, NULL, TRUE),

('P24_LECCION_PREVENCION', 'B6_riesgo_residual', 24,
 '¿Qué lección aprendida debería aplicarse en futuros casos similares?',
 'Capturar conocimiento para mejorar procesos futuros.',
 'informativo', 'texto_largo', 'general', 'solo_aprendizaje', 'solo_aprendizaje', '[]'::jsonb, NULL, FALSE),

('P25_RIESGO_ACEPTADO', 'B6_riesgo_residual', 25,
 'Si se aprueba con debilidades, ¿cuál es el nivel de riesgo residual que se está aceptando conscientemente?',
 'Documentar formalmente el riesgo residual aceptado y su justificación.',
 'importante', 'escala', 'general', 'alerta', 'forzar_revision',
 '["Ninguno - expediente sólido", "Bajo - riesgo menor documentado", "Medio - riesgo aceptable con justificación", "Alto - requiere aprobación especial"]'::jsonb, 2, TRUE)
ON CONFLICT (id) DO UPDATE SET
    pregunta = EXCLUDED.pregunta,
    descripcion = EXCLUDED.descripcion,
    severidad = EXCLUDED.severidad,
    umbral_alerta = EXCLUDED.umbral_alerta,
    updated_at = NOW();

-- ============================================================
-- TABLA DE RESPUESTAS A PREGUNTAS ESTRUCTURADAS
-- ============================================================
CREATE TABLE IF NOT EXISTS abogado_diablo_respuestas_estructuradas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    huella_id UUID NOT NULL REFERENCES abogado_diablo_huellas(id) ON DELETE CASCADE,
    pregunta_id VARCHAR(50) NOT NULL REFERENCES catalogo_preguntas_estructuradas(id),

    -- Respuesta
    respuesta_texto TEXT,
    indice_opcion INTEGER,  -- Para selección/escala
    opciones_seleccionadas JSONB DEFAULT '[]'::jsonb,  -- Para selección múltiple

    -- Evaluación automática
    accion_resultado VARCHAR(30),  -- forzar_revision, bandera_roja, alerta, solo_aprendizaje
    bandera_roja BOOLEAN DEFAULT FALSE,
    requiere_revision BOOLEAN DEFAULT FALSE,
    alertas JSONB DEFAULT '[]'::jsonb,

    -- Evidencia de soporte
    evidencia_soporte JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    respondido_por UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uk_respuesta_pregunta UNIQUE (huella_id, pregunta_id)
);

-- ============================================================
-- TABLA DE EVALUACIONES CONSOLIDADAS
-- ============================================================
CREATE TABLE IF NOT EXISTS abogado_diablo_evaluaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    huella_id UUID NOT NULL REFERENCES abogado_diablo_huellas(id) ON DELETE CASCADE,

    -- Scores
    score_total DECIMAL(5, 2),
    score_b1_hechos DECIMAL(5, 2),
    score_b2_materialidad DECIMAL(5, 2),
    score_b3_razon DECIMAL(5, 2),
    score_b4_proveedor DECIMAL(5, 2),
    score_b5_formal DECIMAL(5, 2),
    score_b6_residual DECIMAL(5, 2),

    -- Resultado
    semaforo VARCHAR(20) CHECK (semaforo IN ('verde', 'amarillo', 'rojo')),
    total_banderas_rojas INTEGER DEFAULT 0,
    total_alertas INTEGER DEFAULT 0,
    preguntas_respondidas INTEGER DEFAULT 0,

    -- Detalle
    banderas_rojas JSONB DEFAULT '[]'::jsonb,
    alertas JSONB DEFAULT '[]'::jsonb,
    requieren_revision JSONB DEFAULT '[]'::jsonb,
    recomendacion TEXT,

    -- Metadata
    evaluado_por UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uk_evaluacion_huella UNIQUE (huella_id)
);

-- Índices adicionales
CREATE INDEX IF NOT EXISTS idx_respuesta_huella ON abogado_diablo_respuestas_estructuradas(huella_id);
CREATE INDEX IF NOT EXISTS idx_respuesta_pregunta ON abogado_diablo_respuestas_estructuradas(pregunta_id);
CREATE INDEX IF NOT EXISTS idx_respuesta_bandera ON abogado_diablo_respuestas_estructuradas(bandera_roja) WHERE bandera_roja = TRUE;
CREATE INDEX IF NOT EXISTS idx_evaluacion_semaforo ON abogado_diablo_evaluaciones(semaforo);
CREATE INDEX IF NOT EXISTS idx_evaluacion_banderas ON abogado_diablo_evaluaciones(total_banderas_rojas);

-- Vista de preguntas críticas pendientes
CREATE OR REPLACE VIEW v_preguntas_criticas_sin_responder AS
SELECT
    h.id as huella_id,
    h.proyecto_id,
    p.id as pregunta_id,
    p.numero,
    p.bloque,
    p.pregunta,
    p.severidad
FROM abogado_diablo_huellas h
CROSS JOIN catalogo_preguntas_estructuradas p
LEFT JOIN abogado_diablo_respuestas_estructuradas r
    ON h.id = r.huella_id AND p.id = r.pregunta_id
WHERE h.resultado_final = 'en_proceso'
  AND p.severidad = 'critico'
  AND p.obligatoria = TRUE
  AND r.id IS NULL
ORDER BY h.proyecto_id, p.numero;

-- Vista de banderas rojas activas
CREATE OR REPLACE VIEW v_banderas_rojas_activas AS
SELECT
    h.id as huella_id,
    h.proyecto_id,
    h.empresa_id,
    h.industria,
    h.tipo_servicio,
    h.monto,
    r.pregunta_id,
    p.pregunta,
    p.bloque,
    r.respuesta_texto,
    r.alertas,
    r.created_at
FROM abogado_diablo_huellas h
JOIN abogado_diablo_respuestas_estructuradas r ON h.id = r.huella_id
JOIN catalogo_preguntas_estructuradas p ON r.pregunta_id = p.id
WHERE r.bandera_roja = TRUE
  AND h.resultado_final = 'en_proceso'
ORDER BY r.created_at DESC;

-- Comentarios
COMMENT ON TABLE catalogo_preguntas_estructuradas IS '25 preguntas del Abogado del Diablo organizadas en 6 bloques con niveles de severidad';
COMMENT ON TABLE abogado_diablo_respuestas_estructuradas IS 'Respuestas a las preguntas estructuradas con evaluación automática';
COMMENT ON TABLE abogado_diablo_evaluaciones IS 'Evaluaciones consolidadas por huella con scores por bloque';
COMMENT ON VIEW v_preguntas_criticas_sin_responder IS 'Preguntas críticas pendientes de responder por proyecto en proceso';
COMMENT ON VIEW v_banderas_rojas_activas IS 'Banderas rojas activas en proyectos en proceso';

-- Insertar preguntas legacy para compatibilidad
INSERT INTO catalogo_preguntas_incomodas (categoria, pregunta, tipo_servicio, norma_relacionada, orden) VALUES
-- Materialidad
('materialidad', '¿Qué pasa si el SAT dice que el proveedor no tenía capacidad para prestar el servicio?', 'todos', 'CFF_69B', 1),
('materialidad', '¿Cómo demostrarías que el servicio se prestó si el proveedor niega la operación?', 'todos', 'CFF_69B', 2),
('materialidad', '¿La evidencia documental es suficiente sin testigos o registros independientes?', 'todos', 'CFF_69B', 3),
('materialidad', '¿El proveedor tiene la infraestructura física/humana para prestar este servicio?', 'todos', 'CFF_69B', 4),
('materialidad', '¿Hay rastro digital verificable de la ejecución del servicio?', 'todos', 'CFF_69B', 5),
-- Razón de negocios
('razon_negocios', '¿Qué beneficio económico habría sin considerar el efecto fiscal?', 'todos', 'CFF_5A', 1),
('razon_negocios', '¿Por qué no se hizo internamente si la empresa tiene capacidad?', 'todos', 'CFF_5A', 2),
('razon_negocios', '¿El precio pagado es congruente con el mercado para este servicio?', 'todos', 'CFF_5A', 3),
('razon_negocios', '¿Cuál era el problema de negocio que este servicio resolvía?', 'todos', 'CFF_5A', 4),
-- Formal
('formal', '¿El CFDI tiene la descripción suficientemente detallada?', 'todos', 'CFF_29_29A', 1),
('formal', '¿Los datos del contrato coinciden exactamente con el CFDI?', 'todos', 'CFF_29_29A', 2),
('formal', '¿El pago se realizó por los canales y fechas correctos?', 'todos', 'LISR_27', 3),
-- Proveedor
('proveedor', '¿Se verificó que el proveedor no esté en lista 69-B antes de contratar?', 'todos', 'CFF_69B', 1),
('proveedor', '¿El proveedor tiene historial de operaciones reales?', 'todos', 'CFF_69B', 2),
('proveedor', '¿Hay indicios de que sea empresa de fachada o facturera?', 'todos', 'CFF_69B', 3),
-- Marketing específicas
('marketing_especifica', '¿Se puede demostrar que la campaña se publicó efectivamente?', 'marketing', 'CFF_69B', 1),
('marketing_especifica', '¿Hay métricas de terceros (Google, Meta) que validen los resultados?', 'marketing', 'CFF_69B', 2),
('marketing_especifica', '¿El alcance reportado es congruente con el monto pagado?', 'marketing', 'CFF_5A', 3),
('marketing_especifica', '¿Se pueden correlacionar los resultados con incremento real de ventas?', 'marketing', 'CFF_5A', 4),
-- Outsourcing específicas
('outsourcing_especifica', '¿El proveedor tiene registro REPSE vigente?', 'outsourcing', 'LISR_27', 1),
('outsourcing_especifica', '¿El personal tercerizado reporta al proveedor o al cliente?', 'outsourcing', 'LSS', 2),
('outsourcing_especifica', '¿Hay evidencia de que no es simulación de relación laboral?', 'outsourcing', 'LFT', 3),
('outsourcing_especifica', '¿El servicio es genuinamente especializado o es staffing genérico?', 'outsourcing', 'LISR_27', 4)
ON CONFLICT DO NOTHING;

-- Índices para rendimiento
CREATE INDEX IF NOT EXISTS idx_huella_proyecto ON abogado_diablo_huellas(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_huella_empresa ON abogado_diablo_huellas(empresa_id);
CREATE INDEX IF NOT EXISTS idx_huella_industria ON abogado_diablo_huellas(industria);
CREATE INDEX IF NOT EXISTS idx_huella_tipo ON abogado_diablo_huellas(tipo_servicio);
CREATE INDEX IF NOT EXISTS idx_huella_resultado ON abogado_diablo_huellas(resultado_final);
CREATE INDEX IF NOT EXISTS idx_huella_fecha ON abogado_diablo_huellas(fecha_inicio DESC);

CREATE INDEX IF NOT EXISTS idx_cambio_huella ON abogado_diablo_cambios_semaforo(huella_id);
CREATE INDEX IF NOT EXISTS idx_cambio_fase ON abogado_diablo_cambios_semaforo(fase);

CREATE INDEX IF NOT EXISTS idx_evidencia_huella ON abogado_diablo_evidencias_clave(huella_id);
CREATE INDEX IF NOT EXISTS idx_evidencia_norma ON abogado_diablo_evidencias_clave(norma_acreditada);

CREATE INDEX IF NOT EXISTS idx_pregunta_huella ON abogado_diablo_preguntas(huella_id);
CREATE INDEX IF NOT EXISTS idx_pregunta_categoria ON abogado_diablo_preguntas(categoria);

CREATE INDEX IF NOT EXISTS idx_riesgo_huella ON abogado_diablo_riesgos(huella_id);
CREATE INDEX IF NOT EXISTS idx_riesgo_nivel ON abogado_diablo_riesgos(nivel);

CREATE INDEX IF NOT EXISTS idx_perfil_industria ON abogado_diablo_perfiles(industria);
CREATE INDEX IF NOT EXISTS idx_perfil_servicio ON abogado_diablo_perfiles(tipo_servicio);

CREATE INDEX IF NOT EXISTS idx_leccion_industria ON abogado_diablo_lecciones(industria);
CREATE INDEX IF NOT EXISTS idx_leccion_servicio ON abogado_diablo_lecciones(tipo_servicio);

CREATE INDEX IF NOT EXISTS idx_incidente_proyecto ON abogado_diablo_incidentes_sat(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_incidente_empresa ON abogado_diablo_incidentes_sat(empresa_id);

-- Vista de resumen por industria/servicio
CREATE OR REPLACE VIEW v_abogado_diablo_resumen AS
SELECT
    h.industria,
    h.tipo_servicio,
    COUNT(*) as total_casos,
    COUNT(*) FILTER (WHERE h.resultado_final = 'aprobado') as casos_aprobados,
    COUNT(*) FILTER (WHERE h.resultado_final = 'rechazado') as casos_rechazados,
    AVG(h.monto) as monto_promedio,
    COUNT(DISTINCT r.id) FILTER (WHERE r.nivel IN ('alto', 'critico')) as riesgos_criticos,
    COUNT(DISTINCT i.id) as incidentes_sat,
    MAX(h.fecha_cierre) as ultimo_caso
FROM abogado_diablo_huellas h
LEFT JOIN abogado_diablo_riesgos r ON h.id = r.huella_id
LEFT JOIN abogado_diablo_incidentes_sat i ON h.proyecto_id = i.proyecto_id
GROUP BY h.industria, h.tipo_servicio;

-- Vista de alertas de riesgos críticos
CREATE OR REPLACE VIEW v_abogado_diablo_alertas AS
SELECT
    h.id as huella_id,
    h.proyecto_id,
    h.empresa_id,
    h.industria,
    h.tipo_servicio,
    h.monto,
    r.descripcion as riesgo,
    r.nivel,
    r.monto_exposicion,
    r.fecha_aprobacion,
    h.resultado_final
FROM abogado_diablo_huellas h
JOIN abogado_diablo_riesgos r ON h.id = r.huella_id
WHERE r.nivel IN ('alto', 'critico')
ORDER BY r.fecha_aprobacion DESC;

-- Vista de lecciones más efectivas
CREATE OR REPLACE VIEW v_abogado_diablo_lecciones_top AS
SELECT
    id,
    titulo,
    industria,
    tipo_servicio,
    categoria,
    veces_aplicada,
    veces_exitosa,
    CASE WHEN veces_aplicada > 0
         THEN ROUND((veces_exitosa::DECIMAL / veces_aplicada) * 100, 2)
         ELSE 0
    END as tasa_exito
FROM abogado_diablo_lecciones
WHERE veces_aplicada >= 3
ORDER BY tasa_exito DESC, veces_aplicada DESC;

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_abogado_diablo_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_huella_updated ON abogado_diablo_huellas;
CREATE TRIGGER tr_huella_updated
    BEFORE UPDATE ON abogado_diablo_huellas
    FOR EACH ROW
    EXECUTE FUNCTION update_abogado_diablo_updated_at();

DROP TRIGGER IF EXISTS tr_perfil_updated ON abogado_diablo_perfiles;
CREATE TRIGGER tr_perfil_updated
    BEFORE UPDATE ON abogado_diablo_perfiles
    FOR EACH ROW
    EXECUTE FUNCTION update_abogado_diablo_updated_at();

DROP TRIGGER IF EXISTS tr_leccion_updated ON abogado_diablo_lecciones;
CREATE TRIGGER tr_leccion_updated
    BEFORE UPDATE ON abogado_diablo_lecciones
    FOR EACH ROW
    EXECUTE FUNCTION update_abogado_diablo_updated_at();

DROP TRIGGER IF EXISTS tr_incidente_updated ON abogado_diablo_incidentes_sat;
CREATE TRIGGER tr_incidente_updated
    BEFORE UPDATE ON abogado_diablo_incidentes_sat
    FOR EACH ROW
    EXECUTE FUNCTION update_abogado_diablo_updated_at();

-- Comentarios para documentación
COMMENT ON TABLE abogado_diablo_huellas IS 'Huellas de revisión de proyectos - registro completo del proceso de aprobación';
COMMENT ON TABLE abogado_diablo_cambios_semaforo IS 'Registro de cambios de color en el semáforo de riesgo';
COMMENT ON TABLE abogado_diablo_evidencias_clave IS 'Evidencias que hicieron la diferencia en decisiones';
COMMENT ON TABLE abogado_diablo_preguntas IS 'Preguntas incómodas respondidas y sus argumentos';
COMMENT ON TABLE abogado_diablo_riesgos IS 'Riesgos residuales aceptados conscientemente';
COMMENT ON TABLE abogado_diablo_perfiles IS 'Perfiles de riesgo dinámico aprendidos por industria/servicio';
COMMENT ON TABLE abogado_diablo_lecciones IS 'Lecciones aprendidas de casos anteriores';
COMMENT ON TABLE abogado_diablo_incidentes_sat IS 'Incidentes posteriores con SAT sobre proyectos aprobados';
COMMENT ON TABLE catalogo_preguntas_incomodas IS 'Catálogo base de preguntas incómodas por categoría';
COMMENT ON VIEW v_abogado_diablo_resumen IS 'Resumen estadístico por industria y tipo de servicio';
COMMENT ON VIEW v_abogado_diablo_alertas IS 'Alertas de riesgos críticos aceptados';
COMMENT ON VIEW v_abogado_diablo_lecciones_top IS 'Lecciones más efectivas basadas en tasa de éxito';
