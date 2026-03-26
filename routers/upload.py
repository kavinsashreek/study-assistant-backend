from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
from services.pdf_processor import process_pdf, chunk_text
from services.vector_store import store_chunks, list_collections, delete_collection
from services.document_store import save_document, load_documents, delete_document

router = APIRouter(prefix="/api", tags=["upload"])

UPLOAD_DIR = "./temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Form(None)
):
    filename = file.filename.lower()
    if not (filename.endswith('.pdf') or filename.endswith('.txt')):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported!"
        )

    if not collection_name:
        clean_name = os.path.splitext(file.filename)[0]
        clean_name = "".join(c if c.isalnum() else "_" for c in clean_name)
        collection_name = f"{clean_name}_{str(uuid.uuid4())[:8]}"

    temp_file_path = os.path.join(UPLOAD_DIR, f"{collection_name}_{file.filename}")

    try:
        file_content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(file_content)

        print(f"📁 File saved temporarily: {temp_file_path}")

        if filename.endswith('.pdf'):
            result = process_pdf(temp_file_path)
        else:
            with open(temp_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
            chunks = chunk_text(text_content)
            result = {
                "full_text": text_content,
                "chunks": chunks,
                "total_characters": len(text_content),
                "total_chunks": len(chunks)
            }

        store_chunks(
            collection_name=collection_name,
            chunks=result["chunks"],
            document_name=file.filename
        )

        # Build the document info
        document_info = {
            "success": True,
            "message": f"Successfully processed '{file.filename}'!",
            "collection_name": collection_name,
            "document_name": file.filename,
            "stats": {
                "total_characters": result["total_characters"],
                "total_chunks": result["total_chunks"],
                "pages_or_sections": result["total_chunks"]
            }
        }

        # Save to persistent store!
        save_document({
            "collection_name": collection_name,
            "document_name": file.filename,
            "stats": document_info["stats"]
        })

        return JSONResponse(content=document_info)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"🗑️ Cleaned up temp file")


@router.get("/documents")
async def get_all_documents():
    """
    Returns all previously uploaded documents
    loaded from the persistent JSON store!
    """
    try:
        # Load from our persistent store
        documents = load_documents()

        return {
            "success": True,
            "documents": documents,
            "total": len(documents)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching documents: {str(e)}"
        )


@router.delete("/documents/{collection_name}")
async def delete_document_endpoint(collection_name: str):
    """
    Deletes a document from both ChromaDB and the persistent store.
    """
    try:
        # Delete from ChromaDB
        delete_collection(collection_name)

        # Delete from persistent store
        delete_document(collection_name)

        return {
            "success": True,
            "message": "Document deleted successfully!"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )