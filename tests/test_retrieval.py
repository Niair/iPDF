#!/usr/bin/env python3
"""
Test script to verify retrieval is working
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up environment variables
os.environ.setdefault('QDRANT_URL', 'https://8ecd1fc4-4111-49d5-bc66-8471ae2ac4a2.europe-west3-0.gcp.cloud.qdrant.io:6333')
os.environ.setdefault('QDRANT_API_KEY', 'your_api_key_here')  # Set this to your actual API key
os.environ.setdefault('QDRANT_COLLECTION', 'iPDF')

def test_retrieval():
    """Test the retrieval system"""
    try:
        from services.query_service import QueryService
        from services.chat_service import ChatService
        
        print("Testing Query Service...")
        query_service = QueryService()
        
        # Test with a simple query
        test_query = "attention mechanism"
        print(f"Testing query: '{test_query}'")
        
        results = query_service.search(
            query=test_query,
            limit=5,
            filename="attention_is_all_you_need.pdf"
        )
        
        print(f"Found {len(results)} results")
        for i, result in enumerate(results):
            payload = result['payload']
            score = result['score']
            content_preview = payload.get('content', '')[:100] + "..." if len(payload.get('content', '')) > 100 else payload.get('content', '')
            print(f"  {i+1}. Score: {score:.4f}, Page: {payload.get('page_number', '?')}, Content: {content_preview}")
        
        # Test Chat Service
        print("\nTesting Chat Service...")
        chat_service = ChatService()
        
        # Test with a simple query
        chat_query = "What is this document about?"
        print(f"Testing chat query: '{chat_query}'")
        
        response = chat_service.chat(
            query=chat_query,
            filename="attention_is_all_you_need.pdf"
        )
        
        print(f"Response: {response.answer[:200]}...")
        print(f"Sources: {len(response.sources)}")
        print(f"Processing time: {response.processing_time:.2f}s")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()