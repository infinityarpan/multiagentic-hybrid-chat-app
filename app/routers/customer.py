from fastapi import APIRouter
from pydantic import BaseModel
from app.services.workflow import get_workflow_graph

router = APIRouter()

class QueryRequest(BaseModel):
    customer_id: str
    thread_id: str
    user_query: str

@router.post("/query")
def query_endpoint(request: QueryRequest):
    graph = get_workflow_graph()  # Get the precompiled workflow graph
    message = {
        "role": "user",
        "content": f"User Details: customer_id = {request.customer_id}, User's Query: {request.user_query}"
    }
    config = {"configurable": {"thread_id": request.thread_id}}
    responses = []
    for chunk in graph.stream({"messages": [message]}, config):
        responses.append(chunk)
    return {"response": responses[-1]["supervisor"]["messages"][-1].content}