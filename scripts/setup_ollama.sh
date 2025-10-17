#!/bin/bash
# Setup Ollama and download required models

echo "🚀 Setting up Ollama..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed"
    echo "Please install from: https://ollama.ai/download"
    exit 1
fi

echo "✅ Ollama is installed"

# Pull LLM model
echo "📦 Pulling Llama 3.2 model..."
ollama pull llama3.2

# Pull embedding model
echo "📦 Pulling nomic-embed-text model..."
ollama pull nomic-embed-text

echo "✅ All models downloaded!"
echo ""
echo "Test with:"
echo "  ollama run llama3.2"
