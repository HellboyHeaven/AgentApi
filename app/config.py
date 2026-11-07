from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_base_url: str
    llm_api_key: str
    llm_model: str

    # Base URL of the RagDocsApi service, used by the document search tool
    rag_api_url: str = "http://localhost:8000"

    # Hard limit on model/tool round trips, protects against infinite loops
    max_agent_steps: int = 6

    # extra="ignore": the copied .env contains variables from the other project
    # (DATABASE_URL, CHUNK_SIZE, ...) and would otherwise raise a validation error
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    tool_timeout_s: float = 10.0
    max_tool_output_chars: int = 4000

settings = Settings()