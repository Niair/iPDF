# iPDF Pro - Enhanced Intelligent PDF Assistant

🚀 **Advanced PDF analysis with AI-powered insights, confidence scoring, and intelligent Q&A.**

An enhanced version of the original iPDF project with significant improvements in text extraction, response quality, and user experience.

## 🆕 What's New

### Major Improvements
- ✅ **Enhanced OCR Integration** - Robust fallback for scanned documents
- ✅ **Confidence Scoring** - Quality assessment for extracted content and answers
- ✅ **Better Error Handling** - Comprehensive error messages and recovery mechanisms
- ✅ **Improved RAG System** - Enhanced retrieval and response generation
- ✅ **Document Summaries** - Automatic comprehensive analysis
- ✅ **Source Attribution** - Clear indication of answer origins
- ✅ **Performance Optimizations** - Faster processing and better memory management

### Bug Fixes
- ✅ Fixed missing OCR implementation
- ✅ Resolved inconsistent LLM configurations
- ✅ Improved text chunking strategies
- ✅ Enhanced prompt engineering
- ✅ Better metadata handling

## ✨ Key Features

### 📄 Advanced Document Processing
- **Multi-PDF Support**: Process multiple documents simultaneously
- **Intelligent Text Extraction**: pdfplumber + OCR fallback
- **Table Detection**: Automatic table extraction and formatting
- **Confidence Scoring**: Quality assessment for all extracted content

### 🧠 Enhanced AI Capabilities
- **Dual LLM Support**: Groq (cloud) or Ollama (local)
- **Advanced RAG**: Improved retrieval with relevance scoring
- **Smart Chunking**: Intelligent text segmentation
- **Context Awareness**: Better understanding of document structure

### 💬 Intelligent Q&A
- **Source Attribution**: Clear indication of answer origins
- **Confidence Levels**: High/Medium/Low confidence indicators
- **Response Quality**: Comprehensive answer formatting
- **Chat History**: Persistent conversation memory

### 📊 Analysis & Summaries
- **Document Statistics**: Processing metrics and quality scores
- **Automatic Summaries**: Comprehensive document analysis
- **Metadata Extraction**: Author, title, and document properties
- **Performance Tracking**: Processing time and efficiency metrics

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Tesseract OCR (optional, for scanned documents)
- Groq API key (for cloud LLM)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd ipdf-pro
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements_improved.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Install Tesseract OCR** (optional)
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

6. **Configure Ollama** (optional, for local LLM)
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2
ollama pull nomic-embed-text
```

## 🚀 Usage

### Running the Application
```bash
streamlit run ipdf_improved.py
```

### Uploading Documents
1. Click "Browse files" in the sidebar
2. Select one or more PDF files
3. Choose processing options (LLM type, OCR)
4. Click "Process Documents"

### Asking Questions
1. Switch to the "Chat" tab
2. Type your question in the input field
3. View responses with confidence scores and sources
4. Use the "Analysis" tab to view document statistics

### Generating Summaries
1. Process documents first
2. Click "Generate Summaries" in the sidebar
3. View summaries in the "Analysis" tab

## 📋 Configuration

### Environment Variables
```env
# Required for Groq LLM
GROQ_API_KEY=your_groq_api_key

# Optional: Tesseract path (if not in PATH)
TESSERACT_PATH=/usr/bin/tesseract

# Optional: Custom model configurations
OLLAMA_MODEL=llama3.2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Processing Options
- **LLM Selection**: Choose between Groq (fast cloud) or Ollama (local)
- **OCR Fallback**: Enable for scanned documents
- **Chunk Size**: Configurable text segmentation (default: 1500 chars)
- **Confidence Threshold**: Minimum quality score for answers

## 🔧 Advanced Configuration

### Custom Prompts
The system uses enhanced prompts for better responses. You can customize these in the `RAGEngine` class:

- **Main Q&A Prompt**: Located in `create_conversation_chain()`
- **Summary Prompt**: Located in `SummaryGenerator.generate_summary()`

### Embedding Models
Default embedding model can be changed in the `setup_embeddings()` method:

```python
# For different HuggingFace models
model_name="sentence-transformers/all-mpnet-base-v2"

# For Ollama embeddings (requires Ollama)
model_name="nomic-embed-text"
```

## 📊 Performance Tips

### For Better Accuracy
- Use high-quality, text-based PDFs when possible
- Enable OCR for scanned documents
- Use Groq for faster processing
- Process documents in smaller batches

### For Faster Processing
- Disable OCR if documents are text-based
- Use smaller chunk sizes for large documents
- Process fewer documents at once
- Use local Ollama for offline processing

### For Scanned Documents
- Ensure good scan quality (300+ DPI)
- Enable OCR fallback
- Use appropriate OCR language settings
- Consider preprocessing images

## 🐛 Troubleshooting

### Common Issues

**"No text extracted" error**
- Enable OCR fallback in settings
- Check PDF quality and permissions
- Verify Tesseract installation

**Slow processing**
- Reduce number of concurrent documents
- Disable OCR for text-based PDFs
- Use smaller chunk sizes

**Poor answer quality**
- Check document relevance to questions
- Increase chunk overlap settings
- Verify embedding model compatibility

**OCR not working**
- Install Tesseract OCR
- Set correct Tesseract path in environment
- Check image quality in PDFs

### Debug Mode
Enable verbose logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your improvements
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Original iPDF project by Niair
- LangChain community for excellent tools
- Groq for fast LLM inference
- HuggingFace for embedding models
- Streamlit for the UI framework

## 📞 Support

For issues, feature requests, or questions:
1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with detailed information
4. Include error logs and system specifications

---

**iPDF Pro** - Bringing intelligence to your PDF documents with confidence and clarity.