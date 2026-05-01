from pathlib import Path
from git import GitCommandError, Repo
from github.Repository import Repository
from gitlab.v4.objects import Project
from loguru import logger
from yarl import URL
from mirro_world.settings import settings
from mirro_world.utils.url_utils import UrlUtils

class Mirror:
    @classmethod
    def sync(cls, github_repository: Repository, local_mirror_path: str, gitlab_project: Project) -> None:
        github_repository_source_url: URL = UrlUtils.get_url_with_credentials(
            url=github_repository.clone_url,
            user="x-access-token",
            password=settings.GITHUB_TOKEN.get_secret_value()
        )

        gitlab_project_target_url: URL = UrlUtils.get_url_with_credentials(
            url=gitlab_project.http_url_to_repo,
            user="oauth2",
            password=settings.GITLAB_TOKEN.get_secret_value()
        )

        try:
            local_repository_path: Path = settings.MIRRORS_PATH / f"{local_mirror_path}.git"
            local_repository: Repo = cls.clone_or_update(local_repository_path, github_repository_source_url=str(github_repository_source_url))
            logger.info("Pushing mirror to GitLab...")
            local_repository.git.push("--mirror", str(gitlab_project_target_url))
        except GitCommandError as error:
            logger.error(str(error))
            raise SystemExit(error.status) from error

    @staticmethod
    def clone_or_update(local_repository_path: Path, github_repository_source_url: str) -> Repo:
        if local_repository_path.exists():
            logger.info("Updating local mirror clone...")
            local_repository = Repo(local_repository_path)
            local_repository.remote("origin").set_url(github_repository_source_url)
            local_repository.remote("origin").update(prune=True)
            return local_repository

        logger.info("Cloning mirror from GitHub...")
        return Repo.clone_from(github_repository_source_url, local_repository_path, mirror=True)
