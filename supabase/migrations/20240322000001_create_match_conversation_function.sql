-- Create function for conversation similarity search with 768 dimensions
CREATE OR REPLACE FUNCTION match_conversation (
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
        conversation.id,
        conversation.content,
        conversation.metadata,
        1 - (conversation.embedding <=> query_embedding) as similarity,
        conversation.created_at
    FROM conversation
    WHERE 
        conversation.embedding IS NOT NULL
        AND 1 - (conversation.embedding <=> query_embedding) > match_threshold
        AND (
            filter->>'created_at' IS NULL 
            OR conversation.created_at >= (filter->>'created_at')::timestamp with time zone
        )
    ORDER BY 
        conversation.embedding <=> query_embedding,
        conversation.created_at DESC
    LIMIT match_count;
END;
$$; 