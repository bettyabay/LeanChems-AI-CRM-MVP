-- Fix documents table embedding dimension to match Gemini API (768 dimensions)
-- Drop existing indexes first
DROP INDEX IF EXISTS documents_embedding_idx;
DROP INDEX IF EXISTS documents_created_at_idx;

-- Alter the embedding column to use 768 dimensions
ALTER TABLE documents ALTER COLUMN embedding TYPE vector(768);

-- Recreate indexes for the new dimension
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS documents_created_at_idx ON documents (created_at);

-- Update the match_documents function to use 768 dimensions
CREATE OR REPLACE FUNCTION match_documents (
    query_embedding vector(768),
    filter jsonb DEFAULT '{}'::jsonb,
    match_count int DEFAULT 3,
    match_threshold float DEFAULT 0.5
) RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity float,
    created_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) as similarity,
        documents.created_at
    FROM documents
    WHERE 
        documents.embedding IS NOT NULL
        AND 1 - (documents.embedding <=> query_embedding) > match_threshold
        AND (
            filter->>'created_at' IS NULL 
            OR documents.created_at >= (filter->>'created_at')::timestamp with time zone
        )
    ORDER BY 
        documents.embedding <=> query_embedding,
        documents.created_at DESC
    LIMIT match_count;
END;
$$; 