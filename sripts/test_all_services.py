"""
Test All Services
Run this script to check if all services are working
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.logger import get_logger
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager
from core.llm_handler import LLMHandler

logger = get_logger(__name__)

def test_ollama_embeddings():
    """Test Ollama embeddings"""
    print("\n🔧 Testing Ollama Embeddings...")
    try:
        gen = EmbeddingGenerator()
        result = gen.test_connection()
        if result:
            print("✅ Ollama Embeddings: WORKING")
            return True
        else:
            print("❌ Ollama Embeddings: NOT WORKING")
            return False
    except Exception as e:
        print(f"❌ Ollama Embeddings: ERROR - {str(e)}")
        return False

def test_ollama_llm():
    """Test Ollama LLM"""
    print("\n🔧 Testing Ollama LLM...")
    try:
        llm = LLMHandler()
        result = llm.test_connection()
        if result:
            print("✅ Ollama LLM: WORKING")
            return True
        else:
            print("❌ Ollama LLM: NOT WORKING")
            return False
    except Exception as e:
        print(f"❌ Ollama LLM: ERROR - {str(e)}")
        return False

def test_qdrant():
    """Test Qdrant vector store"""
    print("\n🔧 Testing Qdrant Vector Store...")
    try:
        vector_store = VectorStoreManager()
        result = vector_store.test_connection()
        if result:
            print("✅ Qdrant: WORKING")
            return True
        else:
            print("❌ Qdrant: NOT WORKING")
            return False
    except Exception as e:
        print(f"❌ Qdrant: ERROR - {str(e)}")
        return False

def main():
    """Run all service tests"""
    print("="*70)
    print("🚀 iPDF - SERVICE STATUS CHECK")
    print("="*70)
    
    results = {
        "Ollama Embeddings": test_ollama_embeddings(),
        "Ollama LLM": test_ollama_llm(),
        "Qdrant": test_qdrant()
    }
    
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'WORKING' if status else 'FAILED'}")
    
    all_working = all(results.values())
    
    print("\n" + "="*70)
    if all_working:
        print("🎉 ALL SERVICES ARE WORKING!")
        print("You can now run the iPDF application.")
    else:
        print("⚠️  SOME SERVICES ARE NOT WORKING")
        print("\nSetup Instructions:")
        if not results["Ollama Embeddings"] or not results["Ollama LLM"]:
            print("\n📦 Ollama:")
            print("  1. Install Ollama: https://ollama.ai/download")
            print("  2. Pull models:")
            print("     ollama pull llama3.2")
            print("     ollama pull nomic-embed-text")
        
        if not results["Qdrant"]:
            print("\n🗄️  Qdrant:")
            print("  1. Sign up (FREE): https://cloud.qdrant.io/")
            print("  2. Create a cluster")
            print("  3. Add QDRANT_URL and QDRANT_API_KEY to .env file")
    
    print("="*70)

if __name__ == "__main__":
    main()
