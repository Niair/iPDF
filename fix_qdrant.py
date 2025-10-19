# Run this to clear Qdrant and start fresh
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Delete collection
collection_name = os.getenv("QDRANT_COLLECTION", "iPDF")
try:
    client.delete_collection(collection_name)
    print(f"✅ Deleted {collection_name}")
except:
    print("Collection didn't exist")

# Recreate
from qdrant_client.models import Distance, VectorParams
client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)
print(f"✅ Created fresh {collection_name}")
