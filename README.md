# FastAPI Application

This project is a FastAPI application designed to handle customer interactions and manage document processing efficiently. It leverages advanced parsing strategies, Retrieval-Augmented Generation (RAG), and a supervisor-based orchestration of tools to provide robust functionality.

---

## Project Highlights

### Parsing Strategy
The application uses the `docling` library to process uploaded PDF documents. The parsing pipeline includes:
- **OCR with Tesseract**: Extracts text from scanned PDFs.
- **Markdown Conversion**: Converts the extracted text into Markdown format for structured processing.
- **Header-Based Splitting**: Splits the Markdown content into smaller chunks using headers for better embedding and retrieval.

### RAG Strategy
The application implements a Retrieval-Augmented Generation (RAG) approach:
- **Vector Store**: Uses `PGVector` to store document embeddings in a PostgreSQL database.
- **Retrievers**:
  - **Similarity Retriever**: Retrieves documents based on vector similarity.
  - **BM25 Retriever**: Retrieves documents using BM25 ranking for keyword-based search.
- **Ensemble Retriever**: Combines the similarity and BM25 retrievers with weighted scores.
- **Cross-Encoder Reranker**: Refines the retrieved results using a Hugging Face cross-encoder model.

### Supervisor and Tools Orchestration
The application orchestrates multiple tools using a supervisor:
- **Research Agent**: Handles research-related tasks using document retrieval and web search tools.
- **Appointment Agent**: Manages appointment scheduling tasks, including finding available slots and booking appointments.
- **Supervisor**: Coordinates the agents, ensuring tasks are assigned to the appropriate agent and responses are managed effectively.

---

## Dependencies

The application requires the following dependencies, as listed in [`requirements.txt`](requirements.txt):
- **FastAPI**: For building the web application.
- **LangChain and LangGraph**: For RAG and workflow orchestration.
- **PGVector**: For vector-based document storage.
- **Tesseract OCR**: For text extraction from scanned PDFs.
- **Hugging Face Transformers**: For cross-encoder reranking.
- **PostgreSQL**: For storing vector embeddings and application data.

---

## Database Information

### PostgreSQL
The application uses a PostgreSQL database to store:
- **Vector Embeddings**: Stored in the `langchain_pg_embedding` table for document retrieval.
- **agents**: Stores information about the agents used in the application.
- **appointments**: Manages customer appointment data, including scheduling and availability.
- **checkpoint_blobs, checkpoint_migrations, checkpoint_writes, checkpoints**: Used for managing application checkpoints and migrations.
- **customers**: Stores customer-related data, such as profiles and interactions.
- **langchain_pg_collection**: Contains metadata about document collections for retrieval.
- **langchain_pg_embedding**: Stores vector embeddings for documents to enable similarity-based retrieval.

Ensure the database is set up with the appropriate schema before running the application.

---

## Installation and Setup

Follow these steps to set up and run the application:

### 1. Clone the Repository
```bash
git clone <repository-url>
cd fastapi-app
```

### 2. Set Up the Environment
- Create a virtual environment (optional but recommended):
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows use `venv\Scripts\activate`
  ```
- Install the required dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### 3. Configure the Environment Variables
- Update the `.env` file with your API keys, database URI, and other configurations:
  ```env
  OPENAI_API_KEY=<your-openai-api-key>
  DB_URI=postgresql://<username>:<password>@<host>:<port>/<database>
  VECTOR_COLLECTION_NAME=my_docs
  ```

### 4. Set Up the Database and Reranker
- Ensure PostgreSQL is running and accessible.
- Create the necessary tables for vector embeddings and appointments.
- Download the BAAI/bge-reranker-v2-m3 reranker
- Run the database setup script to create the necessary tables:
  ```bash
  python app/setup_scripts/create_agents.py
  python app/setup_scripts/create_customers.py
  python app/setup_scripts/create_appointments.py
  python app/setup_scripts/download_reranker.py
  ```

### 5. Run the Application
- Start the FastAPI application:
  ```bash
  uvicorn app.main:app --port 8000 --reload
  ```
- The server will be available at `http://127.0.0.1:8000`.

---

## API Endpoints

### Process Customer Query
- **Endpoint:** `/api/customer/query`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "customer_id": "string",
    "thread_id": "string",
    "user_query": "string"
  }
  ```

### Upload PDF Document
- **Endpoint:** `/api/documents/upload_pdf`
- **Method:** `POST`
- **Request Body:** Form data with a file upload.

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

---

## License

This project is licensed under the MIT License. See the LICENSE file for more details.