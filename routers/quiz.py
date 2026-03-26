from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.vector_store import get_all_chunks
from services.claude_service import generate_quiz

router = APIRouter(prefix="/api", tags=["quiz"])


class QuizRequest(BaseModel):
    collection_name: str
    document_name: str = "Uploaded Document"
    difficulty: str = "medium"


@router.post("/quiz")
async def create_quiz(request: QuizRequest):
    try:
        chunks = get_all_chunks(request.collection_name)

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No content found. Please upload a document first!"
            )

        print(f"📝 Generating quiz from {len(chunks)} chunks...")

        result = generate_quiz(
            chunks=chunks,
            document_name=request.document_name,
            difficulty=request.difficulty
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "quiz": result["quiz"],
            "total_questions": result["total_questions"],
            "difficulty": result["difficulty"],
            "document_name": request.document_name
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating quiz: {str(e)}"
        )