from sentence_transformers import SentenceTransformer
from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)
    
    def embed_text(self, text: str) -> list:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def embed_batch(self, texts: list) -> list:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts)
        return [emb.tolist() for emb in embeddings]
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks


embedding_service = EmbeddingService()
