import chromadb
from chromadb.config import Settings
import os
from dotenv import load_dotenv
from services.embeddings import create_embeddings, create_single_embedding
import uuid

load_dotenv()

PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
TOP_K = int(os.getenv("TOP_K_RESULTS", "5"))

chroma_client = chromadb.PersistentClient(
    path=PERSIST_DIRECTORY,
    settings=Settings(anonymized_telemetry=False)
)

print(f"✅ ChromaDB initialized at: {PERSIST_DIRECTORY}")


def get_or_create_collection(collection_name: str):
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Study material embeddings"}
    )
    return collection


def store_chunks(collection_name: str, chunks: list[str], document_name: str) -> dict:
    print(f"🔄 Creating embeddings for {len(chunks)} chunks...")
    embeddings = create_embeddings(chunks)
    chunk_ids = [f"{document_name}_chunk_{i}_{str(uuid.uuid4())[:8]}"
                 for i in range(len(chunks))]
    metadatas = [
        {
            "document": document_name,
            "chunk_index": i,
            "chunk_total": len(chunks)
        }
        for i in range(len(chunks))
    ]
    collection = get_or_create_collection(collection_name)
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=chunk_ids,
        metadatas=metadatas
    )
    print(f"✅ Stored {len(chunks)} chunks in ChromaDB")
    return {
        "collection_name": collection_name,
        "chunks_stored": len(chunks),
        "document_name": document_name
    }


def search_similar_chunks(collection_name: str, query: str, n_results: int = None) -> list[dict]:
    if n_results is None:
        n_results = TOP_K
    query_embedding = create_single_embedding(query)
    collection = get_or_create_collection(collection_name)
    if collection.count() == 0:
        return []
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"]
    )
    formatted_results = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            formatted_results.append({
                "text": doc,
                "metadata": results["metadatas"][0][i],
                "similarity_score": 1 - results["distances"][0][i]
            })
    return formatted_results


def list_collections() -> list[str]:
    collections = chroma_client.list_collections()
    return [col.name for col in collections]


def delete_collection(collection_name: str) -> bool:
    try:
        chroma_client.delete_collection(collection_name)
        return True
    except Exception:
        return False


def get_all_chunks(collection_name: str) -> list[str]:
    collection = get_or_create_collection(collection_name)
    if collection.count() == 0:
        return []
    results = collection.get(include=["documents"])
    return results["documents"] if results["documents"] else []
