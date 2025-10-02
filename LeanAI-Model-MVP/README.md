# LeanAI Model MVP

An AI-powered knowledge base management system that transforms documents and insights into structured, searchable knowledge using advanced RAG (Retrieval-Augmented Generation) capabilities.

## Features

### 🎯 Core Capabilities
- **Subject Matter Creation**: Initialize new knowledge domains with AI-generated profiles
- **Document Processing**: Upload and process large documents (up to 200MB) with intelligent chunking
- **Knowledge Management**: Build comprehensive knowledge bases with structured insights
- **RAG-Powered Narratives**: Generate one-page narratives grounded in your knowledge base
- **Vector Search**: Semantic search across all stored knowledge using embeddings

### 📚 Three Main Modules

#### 1. Create Subject Matter
- Generate unique subject IDs (LC-YYYY-SUBJ-XXXX format)
- AI-powered profile generation for new subjects
- Fuzzy matching to prevent duplicates
- Structured knowledge initialization

#### 2. Manage MVP
- Select and manage existing subjects
- Upload documents (PDF, TXT, DOCX) with automatic chunking
- Add insights and observations with AI analysis
- View interaction history and knowledge entries
- Delete entries and subjects with confirmation

#### 3. RAG for MVP
- Generate comprehensive one-page narratives
- Retrieve relevant knowledge using vector similarity
- Optional document upload for immediate integration
- Focus-driven narrative generation
- Export narratives as text files

## Technical Architecture

### Backend
- **Database**: Supabase with PostgreSQL
- **Vector Storage**: pgvector for embeddings
- **Authentication**: Supabase Auth with RLS policies
- **LLM Provider**: Gemini API (configurable)
- **Embeddings**: Gemini text-embedding-004

### Frontend
- **Framework**: Streamlit with custom CSS
- **File Processing**: PyPDF2, python-docx
- **Vector Operations**: NumPy for similarity calculations
- **UI Components**: Collapsible cards, tabs, forms

### Data Models

#### Subjects Table
```sql
subjects (
    subject_id UUID PRIMARY KEY,
    display_id TEXT UNIQUE,
    subject_name TEXT,
    input_conversation TEXT[],
    output_conversation TEXT[],
    interaction_embeddings FLOAT8[][],
    interaction_metadata JSONB[],
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    created_by UUID
)
```

#### Subject Documents Table
```sql
subject_documents (
    id UUID PRIMARY KEY,
    subject_id UUID REFERENCES subjects(subject_id),
    content TEXT,
    embedding FLOAT8[],
    metadata JSONB,
    created_at TIMESTAMP
)
```

## Configuration

### Environment Variables
```bash
# Required
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
DATABASE_URL=your_supabase_connection_string
GEMINI_API_KEY=your_gemini_api_key

# Optional
LLM_PROVIDER=gemini
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBED_MODEL=text-embedding-004
MAX_UPLOAD_MB=200
SUBJECT_RAG_TOP_K=5
CHUNK_SIZE=1500
CHUNK_OVERLAP=200
```

### Streamlit Configuration
The app includes a `.streamlit/config.toml` file with:
- Maximum upload size: 200MB
- Custom theme colors
- UI optimizations

## Installation

1. **Clone and Setup**
   ```bash
   cd LeanAI-Model-MVP
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Run the migration to create tables
   # Apply supabase/migrations/20241002000000_create_subjects_table.sql
   ```

3. **Environment Configuration**
   ```bash
   # Copy .env.example to .env and fill in your credentials
   cp .env.example .env
   ```

4. **Run the Application**
   ```bash
   streamlit run leanai_model.py
   ```

## Usage Guide

### Getting Started
1. **Sign Up/Login**: Create an account or login with existing credentials
2. **Create Subject**: Start with "Create Subject Matter" to initialize a new knowledge domain
3. **Add Knowledge**: Use "Manage MVP" to upload documents and add insights
4. **Generate Narratives**: Use "RAG for MVP" to create comprehensive summaries

### Document Processing
- **Supported Formats**: PDF, TXT, DOCX
- **Large Files**: Automatically chunked with configurable size and overlap
- **Embeddings**: Each chunk gets its own embedding for precise retrieval
- **Metadata**: Tracks filename, chunk index, user, and source

### RAG Capabilities
- **Semantic Search**: Vector similarity across all stored knowledge
- **Multi-Source**: Combines interaction history and document chunks
- **Relevance Scoring**: Shows similarity scores for transparency
- **Context Integration**: Seamlessly blends multiple sources

## API Functions

### Core Functions
- `generate_subject_profile()`: AI-powered subject analysis
- `chunk_text()`: Intelligent document chunking
- `process_uploaded_file_with_chunking()`: File processing pipeline
- `retrieve_relevant_subject_interactions()`: Vector-based retrieval
- `render_subject_rag_ui()`: One-page narrative generation

### Database Operations
- `create_new_subject()`: Subject creation workflow
- `update_subject_interaction()`: Knowledge entry storage
- `delete_subject()`: Complete subject removal
- RPC functions for vector similarity search

## Security Features
- **Row Level Security**: Users can only access their own subjects
- **Authentication**: Supabase Auth integration
- **Data Isolation**: Complete user data separation
- **Input Validation**: Comprehensive error handling

## Performance Optimizations
- **Caching**: Streamlit resource caching for API clients
- **Retry Logic**: Exponential backoff for API calls
- **Chunking**: Efficient processing of large documents
- **Indexing**: Database indexes for fast queries

## Customization

### Prompts
The system uses specialized prompts for:
- Subject profile generation
- Knowledge analysis
- One-page narrative creation
- Document summarization

### UI Themes
Custom CSS provides:
- Modern card-based layouts
- Dark mode support
- Responsive design
- Professional styling

## Troubleshooting

### Common Issues
1. **Upload Limits**: Check `server.maxUploadSize` in config.toml
2. **API Errors**: Verify Gemini API key and quotas
3. **Database Issues**: Check Supabase connection and RLS policies
4. **Memory Issues**: Reduce chunk size for very large documents

### Debug Mode
Enable debug logging by setting environment variables:
```bash
STREAMLIT_LOGGER_LEVEL=debug
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License
This project is licensed under the MIT License.

## Support
For issues and questions:
1. Check the troubleshooting section
2. Review the configuration guide
3. Open an issue on GitHub
4. Contact the development team

---

**LeanAI Model MVP** - Transform your documents into intelligent, searchable knowledge bases with AI-powered insights and narrative generation.
