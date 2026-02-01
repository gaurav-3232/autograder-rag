from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import get_settings
from app.services.embeddings import embedding_service
import uuid

settings = get_settings()


class RAGService:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        self.collection_name = settings.qdrant_collection
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            # Get vector dimension from embedding model
            sample_embedding = embedding_service.embed_text("sample")
            vector_size = len(sample_embedding)
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
    
    def index_document(self, assignment_id: int, text: str, metadata: dict = None):
        """Chunk and index a reference document."""
        # Chunk the text
        chunks = embedding_service.chunk_text(text)
        
        # Generate embeddings
        embeddings = embedding_service.embed_batch(chunks)
        
        # Create points for Qdrant
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            payload = {
                "assignment_id": assignment_id,
                "chunk_index": idx,
                "text": chunk,
                **(metadata or {})
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))
        
        # Upsert to Qdrant
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        
        return len(points)
    
    def search_relevant_chunks(self, assignment_id: int, query: str, top_k: int = 5):
        """Search for relevant chunks for a given query."""
        # Generate query embedding
        query_embedding = embedding_service.embed_text(query)
        
        # Search in Qdrant
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter={
                "must": [
                    {"key": "assignment_id", "match": {"value": assignment_id}}
                ]
            },
            limit=top_k
        )
        
        # Extract results
        results = []
        for result in search_results:
            results.append({
                "text": result.payload.get("text", ""),
                "score": result.score,
                "metadata": {k: v for k, v in result.payload.items() if k != "text"}
            })
        
        return results
    
    def delete_assignment_documents(self, assignment_id: int):
        """Delete all documents for an assignment."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector={
                "filter": {
                    "must": [
                        {"key": "assignment_id", "match": {"value": assignment_id}}
                    ]
                }
            }
        )


rag_service = RAGService()
