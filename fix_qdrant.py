# Run this script ONCE to fix Qdrant
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()

# Connect to Qdrant
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

collection_name = os.getenv("QDRANT_COLLECTION", "iPDF")

# Delete old collection
try:
    client.delete_collection(collection_name)
    print(f"✅ Deleted old collection: {collection_name}")
except:
    print(f"Collection {collection_name} didn't exist")

# Create new collection with correct dimensions
client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(
        size=384,  # ✅ Match your embedding model!
        distance=Distance.COSINE
    )
)

print(f"✅ Created new collection: {collection_name} (384 dimensions)")
print("\nNow run your app - it will work!")
