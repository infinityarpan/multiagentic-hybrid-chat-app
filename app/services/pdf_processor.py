from docling.datamodel.base_models import InputFormat  
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_openai import ChatOpenAI
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

def generate_chunk_context(document, chunk):

    chunk_process_prompt = """You are an AI assistant specializing in document
                              analysis. Your task is to provide brief,
                              relevant context for a chunk of text based on the
                              following document.

                              Here is the document:
                              <document>
                              {document}
                              </document>

                              Here is the chunk we want to situate within the whole
                              document:
                              <chunk>
                              {chunk}
                              </chunk>

                              Provide a concise context (3-4 sentences max) for this
                              chunk, considering the following guidelines:

                              - Give a short succinct context to situate this chunk
                                within the overall document for the purposes of
                                improving search retrieval of the chunk.
                              - Answer only with the succinct context and nothing
                                else.
                              - Context should be mentioned like 'Focuses on ....'
                                do not mention 'this chunk or section focuses on...'

                              Context:
                           """

    prompt_template = ChatPromptTemplate.from_template(chunk_process_prompt)
    agentic_chunk_chain = (prompt_template
                                |
                            chatgpt
                                |
                            StrOutputParser())
    context = agentic_chunk_chain.invoke({'document': document, 'chunk': chunk})
    return context

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