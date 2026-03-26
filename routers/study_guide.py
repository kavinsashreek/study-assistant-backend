from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.vector_store import get_all_chunks
from services.claude_service import generate_study_guide

router = APIRouter(prefix="/api", tags=["study-guide"])


class StudyGuideRequest(BaseModel):
    collection_name: str
    document_name: str = "Uploaded Document"


@router.post("/study-guide")
async def create_study_guide(request: StudyGuideRequest):
    try:
        chunks = get_all_chunks(request.collection_name)

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No content found. Please upload a document first!"
            )

        print(f"📅 Generating study guide from {len(chunks)} chunks...")

        result = generate_study_guide(
            chunks=chunks,
            document_name=request.document_name
        )

        return {
            "success": True,
            "study_guide": result["study_guide"],
            "document_name": request.document_name
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating study guide: {str(e)}"
        )
