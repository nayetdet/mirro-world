from pathlib import Path
from typing import Dict
from git import Repo
from github.Repository import Repository
from gitlab.v4.objects import Project
from loguru import logger
from yarl import URL
from mirro_world.settings import settings
from mirro_world.utils.repository_utils import RepositoryUtils
from mirro_world.utils.url_utils import UrlUtils

class Mirror:
    @classmethod
    def sync(cls, source_repo: Repository, local_mirror_path: str, target_project: Project) -> None:
        source_url: URL = UrlUtils.get_url_with_credentials(
            url=source_repo.clone_url,
            user="x-access-token",
            password=settings.GITHUB_TOKEN.get_secret_value()
        )

        target_url: URL = UrlUtils.get_url_with_credentials(
            url=target_project.http_url_to_repo,
            user="oauth2",
            password=settings.GITLAB_TOKEN.get_secret_value()
        )

        local_repo_path: Path = settings.MIRRORS_PATH / f"{local_mirror_path}.git"
        cls.validate_target_refs(
            source_repo,
            local_repo_path,
            str(source_url),
            str(target_url),
            target_project
        )

        local_repo: Repo = cls.clone_or_update(local_repo_path, source_url=str(source_url))
        logger.info("Pushing mirror to GitLab...")
        local_repo.git.push("--mirror", str(target_url))

    @staticmethod
    def clone_or_update(local_repo_path: Path, source_url: str) -> Repo:
        if local_repo_path.exists():
            logger.info("Updating local mirror clone...")
            local_repo = Repo(local_repo_path)
            local_repo.remote("origin").set_url(source_url)
            local_repo.git.fetch("origin", "--force", "--prune", "--prune-tags", "+refs/*:refs/*")
            return local_repo

        logger.info("Cloning mirror from GitHub...")
        return Repo.clone_from(source_url, local_repo_path, mirror=True)

    @staticmethod
    def validate_target_refs(
        source_repo: Repository,
        local_repo_path: Path,
        source_url: str,
        target_url: str,
        target_project: Project
    ) -> None:
        if settings.MIRRORS_OVERRIDE:
            logger.warning("MIRRORS_OVERRIDE is enabled. Skipping target refs safety check for {}.", target_project.path_with_namespace)
            return

        target_refs: Dict[str, str] = RepositoryUtils.get_repo_refs(target_url, remote=True)
        if getattr(target_project, "empty_repo", False) or not target_refs:
            return

        expected_refs: Dict[str, str] = RepositoryUtils.get_repo_refs(str(local_repo_path), remote=False) if local_repo_path.exists() else RepositoryUtils.get_repo_refs(source_url, remote=True)
        if target_refs == expected_refs:
            return

        raise RuntimeError(f"Refusing to mirror {source_repo.full_name} into {target_project.path_with_namespace}: target refs do not match expected refs.")
