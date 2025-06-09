from fastapi import APIRouter
from pydantic import BaseModel
from app.services.workflow import get_workflow_graph
from app.schemas.models import QueryRequest
from app.utils.context import customer_id_context

router = APIRouter()

@router.post("/query")
def query_endpoint(request: QueryRequest):
    customer_id_context.set(request.customer_id)
    graph = get_workflow_graph()  # Get the precompiled workflow graph
    message = {
        "role": "user",
        "content": f"User's Query: {request.user_query}"
    }
    config = {"configurable": {"thread_id": request.thread_id}}
    responses = []
    for chunk in graph.stream({"messages": [message]}, config):
        responses.append(chunk)
    return {"response": responses[-1]["supervisor"]["messages"][-1].content}