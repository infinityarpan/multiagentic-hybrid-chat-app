from pydantic import BaseModel

class QueryRequest(BaseModel):
    customer_id: str
    thread_id: str
    user_query: str

class QueryResponse(BaseModel):
    response: str