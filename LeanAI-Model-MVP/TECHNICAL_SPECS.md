# LeanAI Model MVP - Technical Specifications

## 🔧 System Architecture

### Application Stack
```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                   │
│  • Custom CSS Styling                                  │
│  • Lottie Animations                                   │
│  • Responsive UI Components                            │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                  Python Application Layer               │
│  • Session State Management                            │
│  • File Processing Engine                              │
│  • AI Integration Layer                                │
│  • Vector Operations                                   │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                    External Services                    │
│  • Supabase (Database + Auth)                          │
│  • Gemini API (Chat + Embeddings)                      │
│  • pgvector (Vector Storage)                           │
└─────────────────────────────────────────────────────────┘
```

## 📊 Database Schema

### Core Tables

#### subjects
```sql
CREATE TABLE subjects (
    subject_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_id TEXT UNIQUE NOT NULL,                    -- LC-YYYY-SUBJ-XXXX
    subject_name TEXT NOT NULL,
    input_conversation TEXT[] DEFAULT '{}',             -- User inputs
    output_conversation TEXT[] DEFAULT '{}',            -- AI responses
    interaction_embeddings FLOAT8[][] DEFAULT '{}',     -- Vector embeddings
    interaction_metadata JSONB[] DEFAULT '{}',          -- Structured metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);
```

#### subject_documents
```sql
CREATE TABLE subject_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES subjects(subject_id) ON DELETE CASCADE,
    content TEXT NOT NULL,                              -- Chunked content
    embedding FLOAT8[] NOT NULL,                        -- 768-dim vector
    metadata JSONB DEFAULT '{}',                        -- File info, chunk data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Indexes & Performance
```sql
CREATE INDEX idx_subjects_display_id ON subjects(display_id);
CREATE INDEX idx_subjects_created_by ON subjects(created_by);
CREATE INDEX idx_subject_documents_subject_id ON subject_documents(subject_id);
```

### RPC Functions
```sql
-- Vector similarity search for interactions
CREATE OR REPLACE FUNCTION match_subject_interactions(
    query_embedding FLOAT8[],
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.5,
    filter JSONB DEFAULT '{}'
)

-- Vector similarity search for documents
CREATE OR REPLACE FUNCTION match_subject_documents(
    query_embedding FLOAT8[],
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.5,
    subject_filter UUID DEFAULT NULL
)
```

## 🤖 AI Integration

### Gemini API Integration

#### Chat Completion
```python
def gemini_chat(messages):
    """Call Gemini chat API with OpenAI-style messages."""
    GEMINI_CHAT_URL = f'https://generativelanguage.googleapis.com/v1/models/{GEMINI_CHAT_MODEL}:generateContent'
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    # Returns generated text response
```

#### Embeddings Generation
```python
def gemini_embed(text):
    """Generate 768-dimensional embeddings using Gemini."""
    GEMINI_EMBED_URL = f'https://generativelanguage.googleapis.com/v1/models/{GEMINI_EMBED_MODEL}:embedContent'
    payload = {
        "content": {
            "parts": [{"text": text}]
        }
    }
    # Returns 768-dimensional float array
```

### Vector Operations
```python
def cosine_similarity(embedding1, embedding2):
    """Calculate cosine similarity between two embeddings."""
    return np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )
```

## 📄 Document Processing

### File Format Support
| Format | Library | Max Size | Chunking |
|--------|---------|----------|----------|
| PDF | PyPDF2 | 200MB | ✅ |
| TXT | Built-in | 200MB | ✅ |
| DOCX | python-docx | 200MB | ✅ |

### Chunking Algorithm
```python
def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200):
    """
    Sentence-based chunking with configurable overlap.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Character overlap between chunks
        
    Returns:
        List of text chunks with preserved context
    """
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Start new chunk with overlap
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + " " + sentence
            else:
                current_chunk = sentence
        else:
            current_chunk += (". " if current_chunk else "") + sentence
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks
```

## 🔍 RAG Implementation

### Multi-Source Retrieval
```python
def retrieve_relevant_subject_interactions(subject_id: str, query: str, top_k: int = 3):
    """
    Retrieve relevant content from multiple sources:
    1. Subject interaction history (input/output pairs)
    2. Document chunks with embeddings
    
    Returns ranked results with similarity scores
    """
    query_embedding = gemini_embed(query)
    
    # Search interaction history
    interactions = search_interaction_embeddings(subject_id, query_embedding, top_k)
    
    # Search document chunks
    documents = search_document_chunks(subject_id, query_embedding, top_k)
    
    # Combine and rank results
    return combine_and_rank_results(interactions, documents)
```

### Narrative Generation Pipeline
```python
def generate_narrative(subject_id: str, focus: str = None):
    """
    1. Retrieve relevant context from all sources
    2. Build structured prompt with context
    3. Generate one-page narrative using AI
    4. Return formatted result with sources
    """
    # Retrieve context
    relevant_interactions = retrieve_relevant_subject_interactions(subject_id, query, 5)
    relevant_documents = retrieve_relevant_document_chunks(subject_id, query, 5)
    
    # Build context
    context = build_narrative_context(relevant_interactions, relevant_documents)
    
    # Generate narrative
    system_prompt = """You are LeanAI MVP Narrator. Produce a single page narrative:
    1. Purpose and Scope
    2. Key Facts and Constraints  
    3. Open Questions and Assumptions
    4. Next Steps
    Keep to ≤400–600 words."""
    
    narrative = gemini_chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}"}
    ])
    
    return narrative, relevant_interactions, relevant_documents
```

## 🎨 UI Components

### Streamlit Architecture
```python
# Session State Management
if 'leanai_view' not in st.session_state:
    st.session_state.leanai_view = None

# Module Navigation
if st.session_state.leanai_view is None:
    # Dashboard with module selection
elif st.session_state.leanai_view == 'create':
    render_subject_creation_ui_tab(user_id)
elif st.session_state.leanai_view == 'manage':
    render_manage_subject_ui(user_id)
elif st.session_state.leanai_view == 'rag':
    render_subject_rag_ui(user_id)
```

### Custom CSS Styling
```css
/* Modern card-based layout */
.feature-box {
    background-color: #ffffff;
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

/* Primary buttons */
button[kind="primary"] {
    background-color: #1e73c4;
    border-radius: 10px;
    padding: 12px 20px;
    font-weight: bold;
}
```

## 🔒 Security Architecture

### Authentication Flow
```python
def sign_in(email, password):
    """Supabase Auth integration with session management."""
    response = supabase_client.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    if response and response.user:
        st.session_state.authenticated = True
        st.session_state.user = response.user
```

### Row Level Security (RLS)
```sql
-- Users can only access their own subjects
CREATE POLICY "Users can view their own subjects" ON subjects
    FOR SELECT USING (auth.uid() = created_by);

-- Cascading security for documents
CREATE POLICY "Users can view documents of their subjects" ON subject_documents
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM subjects s 
            WHERE s.subject_id = subject_documents.subject_id 
            AND s.created_by = auth.uid()
        )
    );
```

## ⚡ Performance Specifications

### Response Time Targets
| Operation | Target | Typical | Max Acceptable |
|-----------|--------|---------|----------------|
| Subject Creation | <30s | 25s | 45s |
| Document Upload (10MB) | <2min | 90s | 3min |
| Narrative Generation | <45s | 35s | 60s |
| RAG Retrieval | <10s | 5s | 15s |
| Vector Search | <5s | 2s | 8s |

### Scalability Limits
| Resource | Current Limit | Scaling Strategy |
|----------|---------------|------------------|
| File Upload | 200MB | Configurable via config.toml |
| Concurrent Users | 50+ | Supabase auto-scaling |
| Database Size | 100GB+ | Supabase handles scaling |
| Vector Dimensions | 768 | Fixed by Gemini model |
| Chunks per Document | 1000+ | Memory-efficient processing |

## 🔧 Configuration Management

### Environment Variables
```bash
# Required Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres
GEMINI_API_KEY=your_gemini_api_key

# Optional Tuning
LLM_PROVIDER=gemini                    # AI provider selection
GEMINI_CHAT_MODEL=gemini-2.5-flash    # Chat model version
GEMINI_EMBED_MODEL=text-embedding-004  # Embedding model
MAX_UPLOAD_MB=200                      # File upload limit
SUBJECT_RAG_TOP_K=5                    # RAG result count
CHUNK_SIZE=1500                        # Characters per chunk
CHUNK_OVERLAP=200                      # Overlap between chunks
```

### Streamlit Configuration
```toml
# .streamlit/config.toml
[server]
maxUploadSize = 200        # MB
headless = false
runOnSave = true

[theme]
primaryColor = "#1e73c4"
backgroundColor = "#f5f7fa"
secondaryBackgroundColor = "#ffffff"
textColor = "#333333"
```

## 🧪 Testing Framework

### Automated Testing
```python
# demo_test.py - System validation
def test_supabase_connection():
    """Verify database connectivity and table access."""
    
def test_gemini_api():
    """Verify AI API connectivity and response."""
    
def test_subject_creation():
    """Test core CRUD operations."""
```

### Manual Testing Procedures
1. **Authentication Flow**: Sign up → Email confirmation → Login
2. **Subject Creation**: Input → AI generation → Review → Confirm
3. **Document Processing**: Upload → Chunking → Embedding → Storage
4. **RAG Generation**: Query → Retrieval → Context building → Narrative

## 📈 Monitoring & Observability

### Key Metrics to Track
```python
# Performance Metrics
- Response times per operation
- File processing throughput
- Vector search latency
- API call success rates

# Usage Metrics
- Subjects created per user
- Documents processed per day
- Narratives generated
- User session duration

# Error Metrics
- Failed uploads by file type
- API timeout rates
- Database connection errors
- Authentication failures
```

### Logging Strategy
```python
# Structured logging for key operations
logger.info("Subject created", {
    "subject_id": subject_id,
    "user_id": user_id,
    "processing_time": elapsed_time
})
```

## 🚀 Deployment Specifications

### Minimum System Requirements
- **Python**: 3.9+
- **RAM**: 4GB (8GB recommended for large files)
- **Storage**: 10GB (plus document storage)
- **Network**: Stable internet for API calls

### Production Deployment
```bash
# Docker deployment (future enhancement)
FROM python:3.9-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "leanai_model.py"]
```

### Environment-Specific Configurations
| Environment | Configuration | Considerations |
|-------------|---------------|----------------|
| Development | Local SQLite + Mock APIs | Fast iteration |
| Staging | Supabase + Real APIs | Full feature testing |
| Production | Supabase + Monitoring | Performance optimization |

---

**Technical Specifications Version**: 1.0  
**Last Updated**: October 2, 2024  
**Compatibility**: Python 3.9+, Streamlit 1.28+, Supabase 2.0+
