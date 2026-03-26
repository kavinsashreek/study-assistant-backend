from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.vector_store import search_similar_chunks
from services.claude_service import answer_question_with_rag

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    collection_name: str
    document_name: str = "Uploaded Document"


@router.post("/chat")
async def chat_with_document(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty!")

    if not request.collection_name:
        raise HTTPException(status_code=400, detail="Please upload a document first!")

    try:
        print(f"🔍 Searching for: '{request.question}'")

        relevant_chunks = search_similar_chunks(
            collection_name=request.collection_name,
            query=request.question,
            n_results=5
        )

        print(f"📚 Found {len(relevant_chunks)} relevant chunks")

        result = answer_question_with_rag(
            question=request.question,
            relevant_chunks=relevant_chunks,
            document_name=request.document_name
        )

        return {
            "success": True,
            "question": request.question,
            "answer": result["answer"],
            "sources_found": result["sources_used"],
            "relevant_excerpts": [
                {
                    "text": chunk["text"][:200] + "...",
                    "score": round(chunk["similarity_score"], 3)
                }
                for chunk in relevant_chunks[:3]
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error answering question: {str(e)}"
        )
