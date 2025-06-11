import os
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_tavily import TavilySearch
from langchain.tools.retriever import create_retriever_tool
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain.chat_models import init_chat_model
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langgraph.checkpoint.postgres import PostgresSaver
from langchain.docstore.document import Document
from psycopg import Connection
import psycopg
from app.config import settings
from app.logging_config import logger
from app.utils.context import customer_id_context

# Environment variables
os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
os.environ["LANGCHAIN_TRACING"] = settings.langchain_tracing
os.environ["TAVILY_API_KEY"] = settings.tavily_api_key
os.environ["LANGSMITH_TRACING_V2"] = settings.langsmith_tracing_v2
os.environ["LANGSMITH_TRACING"] = settings.langsmith_tracing
os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Database setup
connection_kwargs = {"autocommit": True, "prepare_threshold": 0}
try:
    conn = Connection.connect(settings.db_uri, **connection_kwargs)
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    logger.info("Database setup completed successfully.")
except Exception as e:
    logger.error(f"Database setup failed: {e}")
    raise

def get_documents_from_pgvector():
    """
    Retrieves documents from the PGVector collection and returns a list of Document objects.
    Adjust the SQL query and column indices based on your actual schema.
    """
    try:
        with psycopg.connect(settings.db_uri) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, cmetadata, document FROM langchain_pg_embedding
                """)
                rows = cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching documents from PGVector: {e}")
        return []
    documents = []
    for row in rows:
        try:
            documents.append(Document(id=row[0], metadata=row[1], page_content=row[2]))
        except Exception as e:
            logger.error(f"Error processing row {row}: {e}")
    return documents

def init_workflow():
    """
    Initializes the workflow graph using documents that have been already
    ingested and embedded into the 'my_docs' vector store.
    """
    try:
        # Retrieve the vector store containing pre-embedded documents.
        try:
            vector_store = PGVector(
                embeddings=OpenAIEmbeddings(api_key=settings.openai_api_key),
                collection_name=settings.vector_collection_name,
                connection=settings.db_uri,
                use_jsonb=True,
            )
            logger.info("PGVector initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing PGVector: {e}")
            raise

        # Build a similarity retriever to handle document queries.
        try:
            similarity_retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            logger.info("Similarity retriever created successfully.")
        except Exception as e:
            logger.error(f"Error creating similarity retriever: {e}")
            raise

        # Initialize a BM25 retriever.
        try:
            documents = get_documents_from_pgvector()
            if documents:
                bm25_retriever = BM25Retriever.from_documents(documents=documents, k=5)
                logger.info("BM25 retriever initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing BM25 retriever: {e}")
            raise

        # Combine both retrievers using an ensemble.
        try:
            if documents:
                ensemble_retriever = EnsembleRetriever(
                    retrievers=[bm25_retriever, similarity_retriever],
                    weights=[0.3, 0.7]
                )
                logger.info("Ensemble retriever created successfully.")
            else:
                ensemble_retriever = EnsembleRetriever(
                    retrievers=[similarity_retriever],
                    weights=[1]
                )
                logger.info("Ensemble retriever created successfully without BM25.")
        except Exception as e:
            logger.error(f"Error creating ensemble retriever: {e}")
            raise

        # Use a cross-encoder reranker to compress the retrieved context.
        try:
            model_dir = "app/models/bge-reranker-v2-m3"
            reranker = HuggingFaceCrossEncoder(model_name=model_dir)
            reranker_compressor = CrossEncoderReranker(model=reranker, top_n=5)
            final_retriever = ContextualCompressionRetriever(
                base_compressor=reranker_compressor,
                base_retriever=ensemble_retriever
            )
            logger.info("Contextual compression retriever set up successfully.")
        except Exception as e:
            logger.error(f"Error setting up cross-encoder reranker: {e}")
            raise

        # Create a tool for the research agent to retrieve information.
        try:
            retriever_tool = create_retriever_tool(
                final_retriever,
                "retrieve_about_us",
                "Search and return information about the company",
            )
            logger.info("Retriever tool created successfully.")
        except Exception as e:
            logger.error(f"Error creating retriever tool: {e}")
            raise

        # Set up a web search tool as an additional resource.
        try:
            web_search = TavilySearch(max_results=3)
            logger.info("Web search tool initialized successfully.")
        except Exception as e:
            logger.error(f"Error creating web search tool: {e}")
            raise

        # Initialize the research agent.
        try:
            research_agent = create_react_agent(
                model=init_chat_model("gpt-4.1-nano-2025-04-14", temperature=0.3),
                tools=[retriever_tool, web_search],
                prompt=(
                    "You are a research agent.\n\n"
                    "INSTRUCTIONS:\n"
                    "- Assist ONLY with research-related tasks, DO NOT do any appointment or booking related tasks\n"
                    "- You can answer all types of general questions"
                    "- You have access to retriever_tool to look into database and do web search using the web_search tool\n"
                    "- After you're done with your tasks, respond to the supervisor directly\n"
                    "- Respond ONLY with the results of your work, do NOT include ANY other text."
                ),
                name="research_agent",
            )
            logger.info("Research agent initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing research agent: {e}")
            raise

        # Define appointment tools.
        def findCurrentTime():
            """
            Get the current date and time in a formatted string.
            Returns:
                str: The current date and time formatted as "YYYY-MM-DD HH:MM".
            """
            try:
                now = datetime.now()
                return f"The current time is: {now.strftime('%Y-%m-%d %H:%M')}"
            except Exception as e:
                logger.error(f"Error fetching current time: {e}")
                return "Unable to retrieve current time."

        def getSlots(date: str):
            """
            Returns a list of available 30-minute time slots for the specified date.

            Args:
                date (str): The date in 'YYYY-MM-DD' format.

            Returns:
                list[str]: Available time slots in 'HH:MM' format, sorted chronologically.
                If no slots are available, returns "No slots found".
            """
            try:
                with psycopg.connect(settings.db_uri) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT DISTINCT time_slot FROM appointments
                            WHERE date = %s AND booked = FALSE
                            ORDER BY time_slot
                        """, (date,))
                        slots = [row[0].strftime("%H:%M") for row in cur.fetchall()]
                logger.info(f"Fetched available slots for {date}.")
                return slots if slots else "No slots found"
            except Exception as e:
                logger.error(f"Error getting slots for date {date}: {e}")
                return "Error retrieving slots"

        def bookSlot(date: str, time_slot: str, mode: str = None):
            """
            Books the first available appointment slot for a given date and time.

            Args:
                customer_id (str): UUID formatted string.
                date (str): The date in 'YYYY-MM-DD' format.
                time_slot (str): The time slot in 'HH:MM' format.
                mode (str): The mode of appointment ('virtual', 'telephonic' or 'in-person').

            Returns:
                str: Success message with agent ID and appointment time if booked.
                    If all matching slots are booked or not found, returns a failure message.
            """
            try:
                if not mode:
                    logger.warning("Mode not provided. Please specify 'virtual', 'telephonic' or 'in-person'.")
                    return "Mode not specified. Please provide 'virtual', 'telephonic' or 'in-person'."
                if mode not in ["virtual", "telephonic", "in-person"]:
                    logger.warning(f"Invalid mode provided: {mode}. Must be 'virtual', 'telephonic' or 'in-person'.")
                    return "Invalid mode. Please choose either 'virtual', 'telephonic' or 'in-person'."
                customer_id = customer_id_context.get()
                with psycopg.connect(settings.db_uri) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT id, agent_id, booked FROM appointments
                            WHERE date = %s AND time_slot = %s
                        """, (date, time_slot))
                        results = cur.fetchall()

                        if not results:
                            logger.warning(f"No slots found for {date} at {time_slot}.")
                            return "No slots found for that date and time."

                        available_slot = next((row for row in results if not row[2]), None)
                        if available_slot:
                            appointment_id, agent_id, _ = available_slot
                            cur.execute("""
                                UPDATE appointments
                                SET customer_id = %s, booked = TRUE, mode = %s
                                WHERE id = %s
                            """, (customer_id, mode, appointment_id))
                            conn.commit()
                            logger.info(f"Slot booked for customer {customer_id} at {time_slot} on {date}.")
                            return f"Slot booked with Agent {agent_id} at {time_slot} on {date}."
                        else:
                            logger.warning(f"All slots already booked for {date} at {time_slot}.")
                            return "All slots at this time are already booked."
            except Exception as e:
                logger.error(f"Error booking slot for customer {customer_id} on {date} at {time_slot}: {e}")
                return "Error booking slot"

        # Initialize the appointment agent.
        try:
            appointment_agent = create_react_agent(
                model=init_chat_model("gpt-4.1-nano-2025-04-14", temperature=0.1),
                tools=[findCurrentTime, getSlots, bookSlot],
                prompt = (
                    "- You are an appointment scheduling assistant and must handle ONLY appointment-related queries. Do not assist with any other type of query.\n"
                    "- You are strictly prohibited from making parallel tool calls. Always complete one tool call before initiating another.\n"
                    "- If the user requests to schedule an appointment, always ask for the specific **day** and **time** they prefer.\n"
                    "- You have access to the following tools: `findCurrentTime`, `getSlots`, and `bookSlot`. Use only these tools for appointment-related tasks.\n"
                    "- You are NOT allowed to infer or assume the meaning of time-related words such as 'today', 'tomorrow', 'tonight', or 'this evening'. You MUST call the `findCurrentTime` tool whenever any such term is present in the user's input."
                    "- After retrieving the current date/time, use the `getSlots` tool to retrieve available appointment slots for that date.\n"
                    "- Even if the user provides a date and/or time, always use the `getSlots` tool for that date to check availability before confirmation.\n"
                    "- Always confirm the selected date and time with the user before proceeding to the next steps.\n"
                    "- After date and time confirmation, ask the user for their preferred **mode of appointment** ('virtual', 'telephonic' or 'in-person') if it hasn't been provided.\n"
                    "- Never book an appointment without knowing the mode of appointment.\n"
                    "- Strictly use bookSlot for booking the appointment.\n"
                    "- Respond in a clear, concise, and professional manner. Do not speculate or invent information. Stick strictly to appointment handling.\n"
                    "- Failure to follow any of the above instructions will result in incorrect behavior and is strictly prohibited."
                ),
                name="appointment_agent",
            )
            logger.info("Appointment agent initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing appointment agent: {e}")
            raise

        # Create a supervisor to manage both agents.
        try:
            workflow = create_supervisor(
                model=init_chat_model("gpt-4.1-mini-2025-04-14", temperature=0.7),
                agents=[research_agent, appointment_agent],
                prompt=(
                    "- You are a supervisor having access to multiple agents.\n"
                    "- You are good at understanding natural language.\n"
                    "- You always look into history to extract past information and you can avoid unnecessary tool calls\n"
                    "- You should carefully assess the user's intent and route the query to the appropriate agent.\n"
                    "- If the user asks for general information, route to research_agent.\n"
                    "- If the user asks to schedule an appointment, route to appointment_agent.\n"
                    "- You should carefully assess the agent's response and route the query to the appropriate agent or respond to the user accordingly.\n"
                    "- You should never ask the user to repeat the question, instead you should look into the history and extract the information from there.\n"
                    "- You should never disclose your internal workings or the agent, tool names to the user.\n"
                    "- You should never disclose any PII (Personally Identifiable Information) to the user.\n"
                    "- Respond in a natural and conversational tone\n\n"
                ),
                add_handoff_back_messages=True,
                output_mode="full_history",
            )
            logger.info("Supervisor initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing supervisor: {e}")
            raise

        # Compile the workflow.
        try:
            graph = workflow.compile(checkpointer=checkpointer)
            logger.info("Workflow graph compiled successfully.")
            return graph
        except Exception as e:
            logger.error(f"Error compiling workflow graph: {e}")
            raise
    except Exception as overall_error:
        logger.error(f"Error in init_workflow: {overall_error}")
        raise

# Initialize the workflow graph once.
try:
    workflow_graph = init_workflow()
except Exception as e:
    logger.error(f"Failed to initialize workflow_graph at module load time: {e}")
    workflow_graph = None

def get_workflow_graph():
    return workflow_graph

def refresh_workflow():
    """
    Reinitializes the workflow graph to pick up newly uploaded documents.
    Returns:
        Updated workflow graph.
    """
    global workflow_graph
    try:
        workflow_graph = init_workflow()
        logger.info("Workflow refreshed successfully.")
    except Exception as e:
        logger.error(f"Workflow refresh failed: {e}")
        raise
    return workflow_graph