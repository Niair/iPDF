# 📚 iPDF - AI-Powered PDF Chat Application

<div align="center">

![iPDF Banner](https://img.shields.io/badge/iPDF-AI%20Document%20Companion-blue?style=for-the-badge)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**An AI-powered document companion that reads, understands, and highlights insights, risks, and key takeaways from your PDFs.**

Beyond reading PDFs — it analyzes, explains, and flags what matters most using AI. Just upload your PDFs and let AI explain, summarize, and check for insights!

### 🚀 [**Try Live Demo**](https://niair-ipdf-srcuiapp-jrucow.streamlit.app/) | [📖 Documentation](#installation)

</div>

---

## 🎥 Demo Video

> **Add your demo video here:**

<!-- Replace with your video embed -->
```
[![iPDF Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)
```

<!-- Or use this format for other video platforms -->
```html
<video src="your-demo-video.mp4" controls></video>
```

---

## ✨ Features

### 🎯 Core Capabilities
- **📄 Multi-PDF Chat** - Upload and query multiple documents simultaneously
- **🔍 Semantic Search** - Find relevant information across all your documents using advanced AI embeddings
- **📊 Table Extraction** - Automatic detection and extraction of tables from PDFs
- **🖼️ Image Processing** - Handle PDF images and visual content *(coming soon)*
- **💬 Intelligent Q&A** - Ask natural language questions and get contextual answers
- **📝 Summarization** - Get instant summaries of lengthy documents
- **⚠️ Risk Detection** - Automatically identifies potential risks and important clauses
- **💡 Key Insights** - Highlights the most important takeaways from your documents

### 🎨 User Experience
- **Split-Screen Interface** - View PDFs alongside your chat
- **Beautiful UI** - Modern, intuitive Streamlit interface
- **Copy Responses** - Easy copy buttons for all AI responses
- **Fast Processing** - Efficient document processing and retrieval
- **100% FREE** - No API costs, runs locally with free cloud vector DB

---

## 🛠️ Tech Stack

| Component | Technology | Cost |
|-----------|------------|------|
| **LLM** | Ollama (Llama 3.2) | 🆓 FREE - Runs Locally |
| **Embeddings** | nomic-embed-text via Ollama | 🆓 FREE - Runs Locally |
| **Vector Database** | Qdrant Cloud | 🆓 FREE Tier (1GB) |
| **Frontend** | Streamlit | 🆓 Open Source |
| **PDF Processing** | pdfplumber, PyMuPDF | 🆓 Open Source |
| **Language** | Python 3.9+ | 🆓 Open Source |

### Architecture
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Streamlit  │ ───> │   Ollama     │ ───> │   Qdrant    │
│     UI      │      │  (Local AI)  │      │  (Cloud DB) │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     │                      │
       └─────────────────────┴──────────────────────┘
              Retrieval Augmented Generation (RAG)
```

---

## 📋 Prerequisites

Before you begin, ensure you have:
- **Python 3.9+** installed
- **Ollama** - [Download here](https://ollama.ai/download)
- **Qdrant Cloud Account** - [Sign up FREE](https://cloud.qdrant.io/) (no credit card required)

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Niair/iPDF.git
cd iPDF
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Ollama
```bash
# Install Ollama from https://ollama.ai/download

# Pull required models
ollama pull llama3.2
ollama pull nomic-embed-text

# Test Ollama (optional)
ollama run llama3.2
```

### 5. Setup Qdrant Cloud
1. Go to [https://cloud.qdrant.io/](https://cloud.qdrant.io/)
2. Sign up for FREE (no credit card required)
3. Create a cluster (Free tier: 1GB storage)
4. Copy your cluster URL and API key

### 6. Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your credentials
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key-here
```

### 7. Test Your Setup
```bash
python scripts/test_all_services.py
```

You should see:
```
✅ Ollama Embeddings: WORKING
✅ Ollama LLM: WORKING
✅ Qdrant: WORKING
```

### 8. Run the Application
```bash
streamlit run src/ui/app.py
```

Open your browser to **http://localhost:8501** 🎉

---

## 📖 Usage Guide

### Basic Workflow

1. **Upload PDFs**
   - Click "Upload PDFs" in the sidebar
   - Select one or multiple PDF files
   - Wait for upload confirmation

2. **Process Documents**
   - Click "Process Documents" button
   - AI will extract text, create embeddings, and store in vector database
   - Processing time depends on document size

3. **Start Chatting**
   - Type your question in the chat input
   - AI will retrieve relevant context and generate answers
   - View sources and confidence scores

4. **View PDFs**
   - Click on any PDF name in the sidebar
   - PDF appears in the left panel
   - Chat continues in the right panel

5. **Copy Responses**
   - Use the copy button next to any response
   - Share insights with your team

### Example Questions

- "What are the key points in this contract?"
- "Summarize the main findings from all documents"
- "Are there any risks mentioned in these PDFs?"
- "What does section 5 say about payment terms?"
- "Compare the methodologies across these research papers"

---

## 📁 Project Structure

```
iPDF/
├── src/                    # Source code
│   ├── core/              # Core logic
│   │   ├── embeddings.py  # Embedding generation
│   │   ├── llm.py         # LLM integration
│   │   └── vector_store.py # Vector database
│   ├── services/          # Application services
│   │   ├── pdf_processor.py
│   │   └── chat_service.py
│   ├── models/            # Data models
│   ├── utils/             # Utility functions
│   └── ui/                # Streamlit UI
│       └── app.py         # Main application
├── tests/                 # Test suite
│   ├── test_embeddings.py
│   ├── test_llm.py
│   └── test_vector_store.py
├── config/                # Configuration files
├── data/                  # Data storage
├── scripts/               # Setup and utility scripts
│   └── test_all_services.py
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

---

## 🧪 Testing

Run the full test suite:
```bash
pytest tests/ -v
```

With coverage report:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

Test specific components:
```bash
pytest tests/test_embeddings.py -v
pytest tests/test_llm.py -v
pytest tests/test_vector_store.py -v
```

---

## 🐛 Troubleshooting

### Ollama Not Connecting
```bash
# Make sure Ollama is running
ollama serve

# Test connection
ollama run llama3.2
```

### Qdrant Not Connecting
- Verify your `.env` file has correct URL and API key
- Check your internet connection
- Test with: `python scripts/test_all_services.py`

### PDF Not Processing
- Ensure PDF is text-based (not a scanned image)
- Enable OCR in settings for scanned PDFs
- Check if PDF is password-protected

### Slow Performance
- Reduce the number of documents processed at once
- Consider using a smaller LLM model
- Check your internet connection (for Qdrant)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

Please open an issue first to discuss major changes.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests before committing
pytest tests/ -v
```

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

**Nihal** - [nihalk2180@outlook.com](mailto:nihalk2180@outlook.com)

**Project Link:** [https://github.com/Niair/iPDF](https://github.com/Niair/iPDF)

**Live Demo:** [https://niair-ipdf-srcuiapp-jrucow.streamlit.app/](https://niair-ipdf-srcuiapp-jrucow.streamlit.app/)

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - For providing free local LLM inference
- [Qdrant](https://qdrant.tech/) - For the excellent vector database
- [Streamlit](https://streamlit.io/) - For the amazing web framework
- [LangChain](https://langchain.com/) - For RAG framework inspiration

---

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/Niair/iPDF?style=social)
![GitHub forks](https://img.shields.io/github/forks/Niair/iPDF?style=social)
![GitHub issues](https://img.shields.io/github/issues/Niair/iPDF)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Niair/iPDF)

---

<div align="center">

**Made with by Nihal**

⭐ **Star this repo if you find it helpful!** ⭐

</div>
