# iPDF - Intelligent PDF Assistant

🚀 An **multimodal** PDF chat application with **RAG (Retrieval Augmented Generation)**. An AI-powered document companion that reads, understands, and highlights insights, risks, and key takeaways from your PDFs. Beyond reading PDFs — it analyzes, explains, and flags what matters most using AI, just upload your PDFs and let AI explain, summarize, and check for insights.

## ✨ Features

- 📄 **Chat with multiple PDFs** - Upload and query multiple documents
- 🔍 **Semantic search** - Find relevant information across all documents
- 📊 **Extract tables** - Automatic table detection and extraction
- 🖼️ **Handle images** - Process PDF images (coming soon)
- ⚡ **Fast & Free** - Uses Ollama (local) + Qdrant (free cloud tier)
- 🎨 **Beautiful UI** - Split-screen interface with PDF viewer

## 🛠️ Technology Stack

- **LLM**: Ollama (Llama 3.2) - 100% FREE, runs locally
- **Embeddings**: nomic-embed-text - 100% FREE via Ollama
- **Vector DB**: Qdrant Cloud - FREE tier (no credit card)
- **UI**: Streamlit
- **PDF Processing**: pdfplumber, PyMuPDF

## 📋 Prerequisites

1. **Python 3.9+**
2. **Ollama** - [Download](https://ollama.ai/download)
3. **Qdrant Cloud Account** - [Sign up FREE](https://cloud.qdrant.io/)

## 🚀 Quick Start

### 1. Clone and Setup

\`\`\`bash
git clone <your-repo>
cd ipdf

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\\Scripts\\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
\`\`\`

### 2. Setup Ollama

\`\`\`bash
# Install Ollama from https://ollama.ai/download

# Pull required models
ollama pull llama3.2
ollama pull nomic-embed-text

# Test
ollama run llama3.2
\`\`\`

### 3. Setup Qdrant

1. Go to https://cloud.qdrant.io/
2. Sign up (FREE - no credit card)
3. Create a cluster (Free tier: 1GB)
4. Copy URL and API key

### 4. Configure Environment

\`\`\`bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Qdrant credentials
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
\`\`\`

### 5. Test Services

\`\`\`bash
python scripts/test_all_services.py
\`\`\`

You should see:
\`\`\`
✅ Ollama Embeddings: WORKING
✅ Ollama LLM: WORKING
✅ Qdrant: WORKING
\`\`\`

### 6. Run Application

\`\`\`bash
streamlit run src/ui/app.py
\`\`\`

Open browser to `http://localhost:8501`

## 🧪 Running Tests

\`\`\`bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test
pytest tests/test_embeddings.py -v
\`\`\`

## 📁 Project Structure

\`\`\`
ipdf/
├── src/                    # Source code
│   ├── core/              # Core logic (embeddings, LLM, vector store)
│   ├── services/          # Application services
│   ├── models/            # Data models
│   ├── utils/             # Utilities
│   └── ui/                # Streamlit UI
├── tests/                 # Comprehensive test suite
├── config/                # Configuration files
├── data/                  # Data storage
└── scripts/               # Setup scripts
\`\`\`

## 🎯 Usage

1. **Upload PDFs** - Click "Upload PDFs" in sidebar
2. **Process** - Click "Process Documents"
3. **Chat** - Ask questions about your documents
4. **View PDF** - Click PDF name to view on left side
5. **Copy** - Use copy buttons to copy responses

## 🆓 Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| Ollama LLM | $0 | Runs locally |
| Ollama Embeddings | $0 | Runs locally |
| Qdrant Cloud | $0 | Free tier: 1GB storage |
| **TOTAL** | **$0** | **100% FREE!** |

## 🐛 Troubleshooting

**Ollama not connecting:**
- Make sure Ollama is running: `ollama serve`
- Test: `ollama run llama3.2`

**Qdrant not connecting:**
- Check your .env file has correct URL and API key
- Test with: `python scripts/test_all_services.py`

**PDF not processing:**
- Make sure PDF is text-based (not scanned image)
- Enable OCR in settings for scanned PDFs

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue first.

## 📧 Contact

Nihal - nihalk2180@outlook.com
\`\`\`

---

## 🎉 COMPLETE CODEBASE READY!

All files have been created with:
1. ✅ Clean directory structure (no ipdf/ipdf nesting)
2. ✅ 100% FREE services (Ollama + Qdrant free tier)
3. ✅ Comprehensive tests for every service
4. ✅ Production-ready, modular code
5. ✅ Complete documentation

**Next steps:**
1. Create the directory structure
2. Copy all code files
3. Run `python scripts/test_all_services.py`
4. Start the application!
