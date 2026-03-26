import json
import os
from datetime import datetime

# File where we save document info
STORE_FILE = "./document_store.json"


def load_documents() -> list[dict]:
    """
    Loads all previously uploaded documents from the JSON file.
    If the file doesn't exist yet, returns empty list.
    """
    if not os.path.exists(STORE_FILE):
        return []

    try:
        with open(STORE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("documents", [])
    except Exception as e:
        print(f"Error loading documents: {e}")
        return []


def save_document(document_info: dict) -> bool:
    """
    Saves a new document's metadata to the JSON file.
    Called every time a new PDF/TXT is uploaded.
    """
    try:
        # Load existing documents
        documents = load_documents()

        # Check if document already exists
        existing = next(
            (d for d in documents
             if d["collection_name"] == document_info["collection_name"]),
            None
        )

        if not existing:
            # Add upload timestamp
            document_info["uploaded_at"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
            documents.append(document_info)

            # Save back to file
            with open(STORE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"documents": documents}, f, indent=2)

            print(f"✅ Document saved to store: {document_info['document_name']}")

        return True

    except Exception as e:
        print(f"Error saving document: {e}")
        return False


def delete_document(collection_name: str) -> bool:
    """
    Removes a document from the JSON store.
    Called when user deletes a document.
    """
    try:
        documents = load_documents()

        # Filter out the deleted document
        updated = [
            d for d in documents
            if d["collection_name"] != collection_name
        ]

        # Save updated list
        with open(STORE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"documents": updated}, f, indent=2)

        print(f"✅ Document deleted from store: {collection_name}")
        return True

    except Exception as e:
        print(f"Error deleting document: {e}")
        return False


def get_document(collection_name: str) -> dict:
    """
    Gets a single document's metadata by collection name.
    """
    documents = load_documents()
    return next(
        (d for d in documents
         if d["collection_name"] == collection_name),
        None
    )