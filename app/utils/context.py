from contextvars import ContextVar

# Define a ContextVar to store customer_id
customer_id_context: ContextVar[str] = ContextVar("customer_id_context")