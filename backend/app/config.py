from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../backend.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Geidi AI Spend Manager"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    # Database
    database_url: str

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # OpenAI
    openai_admin_api_key: str = ""
    openai_org_id: str = ""
    openai_billing_enabled: bool = False
    openai_costs_base_url: str = "https://api.openai.com/v1"

    # Anthropic
    anthropic_admin_api_key: str = ""
    anthropic_org_id: str = ""
    anthropic_billing_enabled: bool = False
    anthropic_api_base_url: str = "https://api.anthropic.com/v1"

    # Invoice ingestion
    invoice_upload_enabled: bool = True
    max_upload_size_mb: int = 10
    allowed_upload_extensions: str = "pdf,csv"
    invoice_storage_path: str = "./storage/invoices"

    # Billing / reporting
    default_currency: str = "USD"
    reporting_timezone: str = "Asia/Manila"
    billing_sync_enabled: bool = False
    billing_sync_cron: str = "0 2 * * *"
    billing_history_months: int = 12
    reconciliation_enabled: bool = True

    # FX
    fx_conversion_enabled: bool = False
    fx_rate_provider: str = ""
    fx_api_key: str = ""

    # Xero (optional)
    xero_integration_enabled: bool = False
    xero_client_id: str = ""
    xero_client_secret: str = ""
    xero_tenant_id: str = ""

    # AI assistant (OpenAI-compatible chat completions API, e.g. NVIDIA)
    nvidia_api_key: str = ""
    assistant_enabled: bool = False
    assistant_base_url: str = "https://integrate.api.nvidia.com/v1"
    assistant_model: str = "deepseek-ai/deepseek-v4.1-flash"
    assistant_vision_model: str = ""  # empty = use assistant_model for images too
    assistant_timeout_seconds: int = 120
    assistant_max_history: int = 12
    assistant_max_tokens: int = 3000  # reasoning models spend ~2-3k tokens thinking before they answer
    assistant_upload_extensions: str = "pdf,csv,png,jpg,jpeg,webp"

    # Logging
    log_level: str = "INFO"
    audit_log_enabled: bool = True

    @field_validator("jwt_secret_key")
    @classmethod
    def jwt_secret_must_be_set(cls, v: str) -> str:
        if not v or v == "REPLACE_WITH_STRONG_RANDOM_SECRET":
            raise ValueError("JWT_SECRET_KEY must be set to a real secret before startup")
        return v

    @property
    def allowed_extensions(self) -> list[str]:
        return [e.strip().lower() for e in self.allowed_upload_extensions.split(",")]

    @property
    def assistant_extensions(self) -> list[str]:
        return [e.strip().lower() for e in self.assistant_upload_extensions.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
