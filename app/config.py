from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    langchain_tracing_v2: str = "true"
    langchain_tracing: str = "true"
    tavily_api_key: str
    langsmith_tracing_v2: str = "true"
    langsmith_tracing: str = "true"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str
    langsmith_project: str = "project-x"
    openai_api_key: str
    db_uri: str
    vector_collection_name: str

    class Config:
        # Adjust the path below if your .env is not at the project root.
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()