from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.vector_store import get_all_chunks
from services.claude_service import generate_flashcards

router = APIRouter(prefix="/api", tags=["flashcards"])


class FlashcardRequest(BaseModel):
    collection_name: str
    document_name: str = "Uploaded Document"


@router.post("/flashcards")
async def create_flashcards(request: FlashcardRequest):
    try:
        chunks = get_all_chunks(request.collection_name)

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No content found. Please upload a document first!"
            )

        print(f"🃏 Generating flashcards from {len(chunks)} chunks...")

        result = generate_flashcards(
            chunks=chunks,
            document_name=request.document_name
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "flashcards": result["flashcards"],
            "total_cards": result["total_cards"],
            "document_name": request.document_name
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating flashcards: {str(e)}"
        )
