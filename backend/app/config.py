from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "mysql+pymysql://root:12345678@127.0.0.1:3307/ai_tutor_system"

    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24

    cors_origins: str = "http://localhost:5173"

    # Public registration switch. True in dev (anyone can sign up), forced false
    # in production by bootstrap-ec2.ps1 so internet randos can't seed accounts
    # against your Gemini quota. Admins can still create users via /api/admin/*.
    allow_registration: bool = True

    google_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    llm_max_tokens: int = 4096

    # Absolute path to the Vite production build (the `dist/` folder).
    # When set, FastAPI serves it at /, so one process hosts both API and UI.
    # Leave empty in dev — `npm run dev` already serves the frontend on 5173.
    frontend_dist: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        return bool(self.google_api_key.strip())


settings = Settings()
