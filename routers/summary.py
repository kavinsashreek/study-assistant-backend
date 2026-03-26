from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.vector_store import get_all_chunks
from services.claude_service import generate_summary

router = APIRouter(prefix="/api", tags=["summary"])


class SummaryRequest(BaseModel):
    collection_name: str
    document_name: str = "Uploaded Document"


@router.post("/summarize")
async def summarize_document(request: SummaryRequest):
    try:
        chunks = get_all_chunks(request.collection_name)

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No content found. Please upload a document first!"
            )

        print(f"📝 Generating summary for {len(chunks)} chunks...")

        result = generate_summary(
            chunks=chunks,
            document_name=request.document_name
        )

        return {
            "success": True,
            "summary": result["summary"],
            "document_name": request.document_name,
            "total_chunks_analyzed": result["chunks_analyzed"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )
