import shutil
from typing import List
from github.Repository import Repository
from gitlab.v4.objects import Namespace, Project
from loguru import logger
from mirro_world.clients.github_client import GithubClient
from mirro_world.clients.gitlab_client import GitlabClient
from mirro_world.core.mirror import Mirror
from mirro_world.logging import setup_logging
from mirro_world.utils.repository_utils import RepositoryUtils

def main() -> None:
    if shutil.which("git") is None:
        logger.error("Required program not found in PATH: git")
        raise SystemExit(1)

    source_client: GithubClient = GithubClient()
    source_repos: List[Repository] = source_client.get_owned_repos()
    if not source_repos:
        logger.info("No repositories found.")
        return

    logger.info("Found {} repositories to mirror.", len(source_repos))
    target_client: GitlabClient = GitlabClient()
    target_namespace: Namespace = target_client.get_namespace()

    failed: int = 0
    succeeded: int = 0
    for source_repo in source_repos:
        try:
            logger.info("Mirroring {}", source_repo.full_name)
            local_mirror_path: str = RepositoryUtils.get_repo_path(source_repo, full_name=True)
            target_project_path: str = RepositoryUtils.get_repo_path(source_repo)
            target_project: Project = target_client.get_project(target_project_path, source_repo, target_namespace)
            Mirror.sync(source_repo, local_mirror_path, target_project)
            succeeded += 1
        except Exception as error:
            failed += 1
            logger.error("Skipping {} after failure: {}", source_repo.full_name, " | ".join(str(error).splitlines()))
    logger.info("Mirroring finished: {} total, {} succeeded, {} failed.", len(source_repos), succeeded, failed)
    if failed > 0:
        raise SystemExit(1)

if __name__ == "__main__":
    setup_logging()
    main()
