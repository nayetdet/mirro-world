from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # GitHub
    GITHUB_USERNAME: str
    GITHUB_TOKEN: SecretStr

    # GitLab
    GITLAB_TOKEN: SecretStr
    GITLAB_URL: str = "https://gitlab.com"
    GITLAB_NAMESPACE: str
    GITLAB_NAMESPACE_ID: int

    # Mirrors
    MIRRORS_INCLUDE_FORKS: bool = True
    MIRRORS_INCLUDE_ARCHIVED: bool = True

    # Paths
    ROOT_PATH: Path = Path(__file__).resolve().parents[2]
    DATA_PATH: Path = ROOT_PATH / "data"
    LOGS_PATH: Path = DATA_PATH / "logs"
    MIRRORS_PATH: Path = DATA_PATH / "mirrors"

    def ensure_paths(self) -> None:
        for path in (self.DATA_PATH, self.LOGS_PATH, self.MIRRORS_PATH):
            path.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_paths()
