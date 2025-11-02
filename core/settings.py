from logging import config as logging_config

from async_fastapi_jwt_auth import AuthJWT
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

from core.logger import LOGGING

# Apply logging settings
logging_config.dictConfig(LOGGING)


class PostgresSettings(BaseSettings):
    """Postgres settings."""

    echo_database: bool = False
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_app_user: str
    postgres_app_password: str
    postgres_migrate_user: str
    postgres_migrate_password: str

    @property
    def pg_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_app_user,
            password=self.postgres_app_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )

    @property
    def migrate_pg_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_migrate_user,
            password=self.postgres_migrate_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )


class Settings(PostgresSettings):
    # General settings
    project_name: str = "Order Service"
    debug: bool = False
    show_traceback: bool = False

    # Redis settings
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379

    # AuthJWT settings
    authjwt_secret_key: str = "secret"

    # Telemetry settings
    jaeger_trace: bool = True
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831

    timezone: str = "Australia/Melbourne"


@AuthJWT.load_config
def get_config():
    return Settings()


settings = Settings()
