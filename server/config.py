from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITEE_CLIENT_ID: str = ""
    GITEE_CLIENT_SECRET: str = ""

    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str | None = None

    MODEL_DICT_PREPROCESS: str = "gpt-3.5-turbo"
    MODEL_QUICK_ANSWER: str = "gpt-3.5-turbo"
    MODEL_DEEP_THINK: str = "gpt-4o"

    APP_BASE_URL: str = "http://localhost:5173"
    JWT_SECRET: str = ""
    DB_PATH: str = "../db/data.db"

    QUOTA_USER_DAILY: int = 50
    QUOTA_GUEST_DAILY: int = 50  # Total Pool

    def __init__(self):
        super().__init__()
        if not self.LLM_API_KEY:
            raise ValueError("API_KEY must be set in .env")


settings = Settings()
