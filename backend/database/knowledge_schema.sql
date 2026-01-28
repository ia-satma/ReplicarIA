-- Knowledge Repository Schema
-- Tables for corporate knowledge management

-- Folders table
CREATE TABLE IF NOT EXISTS knowledge_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL,
    path VARCHAR(1024) NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_path VARCHAR(1024) NOT NULL DEFAULT '/',
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_folder_path UNIQUE (empresa_id, path)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_knowledge_folders_empresa ON knowledge_folders(empresa_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_folders_parent ON knowledge_folders(empresa_id, parent_path);

-- Documents table
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL,
    path VARCHAR(1024) NOT NULL DEFAULT '/',
    filename VARCHAR(512) NOT NULL,
    mime_type VARCHAR(255),
    size_bytes BIGINT,
    checksum_sha256 VARCHAR(64),
    status VARCHAR(50) DEFAULT 'uploaded',
    extracted_text TEXT,
    metadata JSONB DEFAULT '{}',
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for documents
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_empresa ON knowledge_documents(empresa_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_path ON knowledge_documents(empresa_id, path);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status ON knowledge_documents(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_checksum ON knowledge_documents(checksum_sha256);

-- Document chunks for RAG
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    empresa_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    tokens INTEGER,
    embedding JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_chunk UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_empresa ON knowledge_chunks(empresa_id);

-- Audit log for document operations
CREATE TABLE IF NOT EXISTS knowledge_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    user_id UUID,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_audit_entity ON knowledge_audit_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_audit_user ON knowledge_audit_log(user_id);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS knowledge_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL,
    document_id UUID REFERENCES knowledge_documents(id) ON DELETE SET NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_knowledge_jobs_empresa ON knowledge_jobs(empresa_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_jobs_status ON knowledge_jobs(status);
