-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for created_at to improve time-based filtering performance
CREATE INDEX IF NOT EXISTS documents_created_at_idx ON documents (created_at);

-- Create function for similarity search
CREATE OR REPLACE FUNCTION match_documents (
    query_embedding vector(1536),
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