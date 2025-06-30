-- Create function for customer similarity search
CREATE OR REPLACE FUNCTION match_customers (
    query_embedding vector(1536),
    filter jsonb DEFAULT '{}'::jsonb,
    match_count int DEFAULT 5,
    match_threshold float DEFAULT 0.5
) RETURNS TABLE (
    id UUID,
    entity_type TEXT,
    entity_name TEXT,
    company TEXT,
    contact TEXT,
    industry TEXT,
    region TEXT,
    status TEXT,
    priority TEXT,
    notes TEXT,
    tags TEXT[],
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        customers.id,
        customers.entity_type,
        customers.entity_name,
        customers.company,
        customers.contact,
        customers.industry,
        customers.region,
        customers.status,
        customers.priority,
        customers.notes,
        customers.tags,
        1 - (customers.embedding <=> query_embedding) as similarity
    FROM customers
    WHERE 
        customers.embedding IS NOT NULL
        AND 1 - (customers.embedding <=> query_embedding) > match_threshold
        AND customers.metadata @> filter
    ORDER BY customers.embedding <=> query_embedding
    LIMIT match_count;
END;
$$; 