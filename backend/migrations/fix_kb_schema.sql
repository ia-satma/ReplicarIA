-- Migration: Fix Knowledge Base Schema
-- Habilitar pgvector y corregir empresa_id para usar UUID

-- 1. Habilitar extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Verificar y modificar empresa_id en kb_documentos
-- Primero verificamos el tipo actual
DO $$
BEGIN
    -- Si empresa_id es INTEGER, lo cambiamos a UUID
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'kb_documentos'
        AND column_name = 'empresa_id'
        AND data_type = 'integer'
    ) THEN
        -- Eliminar la restricción si existe
        ALTER TABLE kb_documentos DROP CONSTRAINT IF EXISTS kb_documentos_empresa_id_fkey;

        -- Cambiar el tipo de columna
        ALTER TABLE kb_documentos
        ALTER COLUMN empresa_id TYPE UUID USING NULL;

        RAISE NOTICE 'empresa_id cambiado a UUID';
    ELSIF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'kb_documentos'
        AND column_name = 'empresa_id'
    ) THEN
        -- Si no existe la columna, la creamos
        ALTER TABLE kb_documentos ADD COLUMN empresa_id UUID;
        RAISE NOTICE 'empresa_id agregado como UUID';
    ELSE
        RAISE NOTICE 'empresa_id ya es del tipo correcto o no requiere cambios';
    END IF;
END $$;

-- 3. Asegurar que kb_chunks tenga la columna contenido_embedding como vector
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'kb_chunks'
        AND column_name = 'contenido_embedding'
    ) THEN
        ALTER TABLE kb_chunks ADD COLUMN contenido_embedding vector(1536);
        RAISE NOTICE 'contenido_embedding agregado';
    END IF;
END $$;

-- 4. Crear índice para búsqueda vectorial si no existe
CREATE INDEX IF NOT EXISTS kb_chunks_embedding_idx
ON kb_chunks USING ivfflat (contenido_embedding vector_cosine_ops)
WITH (lists = 100);

-- 5. Crear índice para empresa_id si no existe
CREATE INDEX IF NOT EXISTS kb_documentos_empresa_id_idx
ON kb_documentos (empresa_id);

-- 6. Verificar resultado
SELECT
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE table_name IN ('kb_documentos', 'kb_chunks')
AND column_name IN ('empresa_id', 'contenido_embedding')
ORDER BY table_name, column_name;
