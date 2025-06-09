import os
import uuid
from fastapi import APIRouter, UploadFile, File
from app.services.pdf_processor import process_document, add_document_to_vector_store
from app.services.workflow import refresh_workflow
from app.logging_config import logger

router = APIRouter()

@router.post("/upload_pdf")
def upload_pdf(file: UploadFile = File(...)):
    temp_filename = f"temp_{uuid.uuid4()}.pdf"
    with open(temp_filename, "wb") as f:
        content = file.file.read()
        f.write(content)

    try:
        markdown_content = process_document(temp_filename)
        headers_to_split_on = [("##", "Header 1")]
        add_document_to_vector_store(markdown_content, headers_to_split_on)
    finally:
        os.remove(temp_filename)

    # Refresh the workflow to include newly embedded documents
    try:
        refresh_workflow()
        logger.info("Workflow graph refreshed after PDF upload.")
    except Exception as e:
        logger.error(f"Failed to refresh workflow after PDF upload: {e}")
        raise HTTPException(status_code=500, detail=f"Document added, but failed to refresh workflow: {str(e)}")

    return {"detail": "PDF processed, data stored, and workflow refreshed successfully."}
