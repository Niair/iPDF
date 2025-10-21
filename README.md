# iPDF - Intelligent PDF Assistant

![iPDF Logo](https://via.placeholder.com/150?text=iPDF) <!-- Replace with your logo if available -->

An AI-powered document companion that reads, understands, and highlights insights, risks, and key takeaways from your PDFs. Beyond reading PDFs — it analyzes, explains, and flags what matters most using AI. Simply upload your PDFs and let iPDF explain, summarize, and check for insights with a sleek, user-friendly interface.

- **Deployed App**: [Try iPDF Live](https://niair-ipdf-srcuiapp-jrucow.streamlit.app/) <!-- Update with your live app link -->
- **Video Demo**: [Watch the Demo](https://www.youtube.com/watch?v=placeholder) <!-- Replace with your video link when available -->

## ✨ Features

- 📄 **Chat with Multiple PDFs**: Upload and query multiple documents seamlessly.
- 🔍 **Semantic Search**: Find relevant information across all uploaded documents using advanced retrieval techniques.
- 📊 **Extract Tables**: Automatically detect and extract tables for easy analysis.
- 🖼️ **Handle Images**: Process PDF images (feature in development).
- ⚡ **Fast & Free**: Powered by Ollama (local) and Qdrant (free cloud tier) for 100% free usage.
- 🎨 **Beautiful UI**: Enjoy a split-screen interface with an integrated PDF viewer.

## 🛠️ Technology Stack

- **LLM**: Ollama (Llama 3.2) - 100% FREE, runs locally.
- **Embeddings**: nomic-embed-text - 100% FREE via Ollama.
- **Vector DB**: Qdrant Cloud - FREE tier (no credit card required).
- **UI**: Streamlit for an interactive and responsive interface.
- **PDF Processing**: pdfplumber and PyMuPDF for robust document handling.

## 📋 Prerequisites

1. **Python 3.9+**
2. **Ollama** - Download and install from [Ollama](https://ollama.ai/).
3. **Qdrant Cloud Account** - Sign up for free at [Qdrant Cloud](https://cloud.qdrant.io/).

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/Niair/iPDF.git
cd iPDF

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Ollama

```bash
# Pull required models
ollama pull llama3.2
ollama pull nomic-embed-text

# Test
ollama run llama3.2
```

### 3. Setup Qdrant

1. Go to [Qdrant Cloud](https://cloud.qdrant.io/).
2. Sign up (FREE - no credit card).
3. Create a cluster (Free tier: 1GB).
4. Copy the URL and API key.

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Qdrant credentials
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
```

### 5. Test Services

```bash
python scripts/test_all_services.py
```

You should see:
```
✅ Ollama Embeddings: WORKING
✅ Ollama LLM: WORKING
✅ Qdrant: WORKING
```

### 6. Run Application

```bash
streamlit run src/ui/app.py
```

Open your browser to `http://localhost:8501`.

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test
pytest tests/test_embeddings.py -v
```

## 📁 Project Structure

```
ipdf/
├── src/                  # Source code
│   ├── core/             # Core logic (embeddings, LLM, vector store)
│   ├── services/         # Application services
│   ├── models/           # Data models
│   ├── utils/            # Utilities
│   └── ui/               # Streamlit UI
├── tests/                # Comprehensive test suite
├── config/               # Configuration files
├── data/                 # Data storage
└── scripts/              # Setup scripts
```

## 🎯 Usage

1. **Upload PDFs**: Click "Upload PDFs" in the sidebar.
2. **Process**: Click "Process Documents" to analyze the files.
3. **Chat**: Ask questions about your documents in the chat interface.
4. **View PDF**: Click the PDF name to view it on the left side.
5. **Copy**: Use copy buttons to copy responses.

## 🆓 Cost Breakdown

| Service           | Cost | Notes                  |
|-------------------|------|-------------------------|
| Ollama LLM        | $0   | Runs locally            |
| Ollama Embeddings | $0   | Runs locally            |
| Qdrant Cloud      | $0   | Free tier: 1GB storage  |
| **TOTAL**         | **$0** | **100% FREE!**          |

## 🐛 Troubleshooting

- **Ollama not connecting**:
  - Ensure Ollama is running: `ollama serve` when you want to run locally
  - Test: `ollama run llama3.2`
- **Qdrant not connecting**:
  - Check your `.env` file has the correct URL and API key.
  - Test with: `python scripts/test_all_services.py`
- **PDF not processing**:
  - Ensure the PDF is text-based (not a scanned image).
  - Enable OCR in settings for scanned PDFs.

## 📝 License

This project is licensed under the [MIT License](LICENSE).

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss your ideas or bug fixes.

## 📧 Contact

- **Nihal** - [nihalk2180@outlook.com](mailto:nihalk2180@outlook.com)

## 🎉 Complete Codebase Ready!

All files have been created with:
- ✅ Clean directory structure (no `ipdf/ipdf` nesting)
- ✅ 100% FREE services (Ollama + Qdrant free tier)
- ✅ Comprehensive tests for every service
- ✅ Production-ready, modular code
- ✅ Complete documentation

### Next Steps
1. Create the directory structure.
2. Copy all code files.
3. Run `python scripts/test_all_services.py`.
4. Start the application!

## About iPDF

iPDF is designed to revolutionize how you interact with PDF documents. Leveraging the power of Retrieval-Augmented Generation (RAG), it combines local language models (via Ollama) with a free vector database (Qdrant Cloud) to provide deep insights into your documents. Whether you're summarizing research papers, extracting data from reports, or exploring visual content, iPDF offers a fast, free, and intuitive solution. The project is built with a focus on accessibility, using open-source tools to ensure it remains cost-free for all users.

### Project Vision
- Enhance document understanding with AI-driven analysis.
- Support multiple file formats and multimodal content (text, tables, images).
- Provide a scalable, community-driven platform for knowledge extraction.

### Future Enhancements
- Full image processing support.
- Integration with additional LLM models.
- Advanced semantic search capabilities.

Stay tuned for updates, and feel free to contribute to make iPDF even better!
