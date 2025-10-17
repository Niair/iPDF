#!/bin/bash
# Setup Qdrant (instructions)

echo "🗄️  Setting up Qdrant Vector Database"
echo "======================================"
echo ""
echo "Option 1: Qdrant Cloud (Recommended - 100% FREE)"
echo "  1. Go to: https://cloud.qdrant.io/"
echo "  2. Sign up (NO credit card required)"
echo "  3. Create a new cluster (Free tier: 1GB)"
echo "  4. Copy your cluster URL and API key"
echo "  5. Add to .env file:"
echo "     QDRANT_URL=https://your-cluster.qdrant.io"
echo "     QDRANT_API_KEY=your-api-key"
echo ""
echo "Option 2: Local Docker"
echo "  docker run -p 6333:6333 qdrant/qdrant"
echo ""
