from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

print("🔄 Loading embedding model...")
embedding_model = SentenceTransformer(MODEL_NAME)
print("✅ Embedding model loaded!")


def create_embeddings(texts: list[str]) -> list[list[float]]:
    embeddings = embedding_model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    return embeddings.tolist()


def create_single_embedding(text: str) -> list[float]:
    embedding = embedding_model.encode([text], convert_to_numpy=True)
    return embedding[0].tolist()
