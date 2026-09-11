from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://integration:integration_dev@localhost:5432/integration"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    webhook_secret: str = "local-demo-secret"
    demo_mode: bool = True
    outbox_poll_interval: float = 0.25
    max_delivery_attempts: int = 3
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
