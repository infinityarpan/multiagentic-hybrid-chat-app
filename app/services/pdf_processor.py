from docling.datamodel.base_models import InputFormat  
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from app.config import settings

# Update your DB connection string as needed.
def process_document(file_path: str) -> str:
    ocr_options = TesseractCliOcrOptions(lang=["auto"])
    pipeline_options = PdfPipelineOptions(do_ocr=True, ocr_options=ocr_options)
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    doc = converter.convert(file_path).document
    md = doc.export_to_markdown()
    return md

def add_document_to_vector_store(markdown_content: str, headers_to_split_on):
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(markdown_content)
    collection_name = settings.vector_collection_name
    vector_store = PGVector(
        embeddings=OpenAIEmbeddings(),
        collection_name=collection_name,
        connection=settings.db_uri,
        use_jsonb=True,
    )
    vector_store.add_documents(md_header_splits)