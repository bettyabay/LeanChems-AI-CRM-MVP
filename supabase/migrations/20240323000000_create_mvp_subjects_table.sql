-- Create MVP subjects table for LeanAI Model
CREATE TABLE IF NOT EXISTS mvp_subjects (
    id BIGSERIAL PRIMARY KEY,
    mvp_id TEXT UNIQUE NOT NULL,
    display_id TEXT UNIQUE NOT NULL,
    subject_name TEXT NOT NULL,
    narration TEXT,
    file_name TEXT,
    file_content TEXT,
    grok_analysis TEXT,
    input_conversation TEXT[],
    output_conversation TEXT[],
    interaction_metadata JSONB[],
    interaction_embeddings VECTOR(768)[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by TEXT,
    user_id TEXT
);

-- Create index for faster searches
CREATE INDEX IF NOT EXISTS idx_mvp_subjects_subject_name ON mvp_subjects USING GIN (to_tsvector('english', subject_name));
CREATE INDEX IF NOT EXISTS idx_mvp_subjects_display_id ON mvp_subjects (display_id);
CREATE INDEX IF NOT EXISTS idx_mvp_subjects_created_by ON mvp_subjects (created_by);
CREATE INDEX IF NOT EXISTS idx_mvp_subjects_user_id ON mvp_subjects (user_id);

-- Enable RLS (Row Level Security)
ALTER TABLE mvp_subjects ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view their own MVP subjects" ON mvp_subjects
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own MVP subjects" ON mvp_subjects
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own MVP subjects" ON mvp_subjects
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own MVP subjects" ON mvp_subjects
    FOR DELETE USING (auth.uid()::text = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_mvp_subjects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_update_mvp_subjects_updated_at
    BEFORE UPDATE ON mvp_subjects
    FOR EACH ROW
    EXECUTE FUNCTION update_mvp_subjects_updated_at();

-- Create function for MVP subject search with vector similarity
CREATE OR REPLACE FUNCTION search_mvp_subjects(
    query_embedding VECTOR(768),
    match_count INTEGER DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    mvp_id TEXT,
    subject_name TEXT,
    display_id TEXT,
    narration TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ms.mvp_id,
        ms.subject_name,
        ms.display_id,
        ms.narration,
        1 - (ms.interaction_embeddings <-> query_embedding) AS similarity
    FROM mvp_subjects ms
    WHERE 1 - (ms.interaction_embeddings <-> query_embedding) > match_threshold
    ORDER BY ms.interaction_embeddings <-> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
