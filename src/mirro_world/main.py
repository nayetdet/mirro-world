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

    github_client: GithubClient = GithubClient()
    github_repos: List[Repository] = github_client.get_owned_repos()
    if not github_repos:
        logger.info("No repositories found.")
        return

    logger.info("Found {} repositories to mirror.", len(github_repos))
    gitlab_client: GitlabClient = GitlabClient()
    gitlab_namespace: Namespace = gitlab_client.get_namespace()
    for github_repo in github_repos:
        logger.info("Mirroring {}", github_repo.full_name)
        local_mirror_path: str = RepositoryUtils.get_repo_path(github_repo, full_name=True)
        gitlab_project_path: str = RepositoryUtils.get_repo_path(github_repo)
        gitlab_project: Project = gitlab_client.get_project(github_repo, gitlab_project_path, gitlab_namespace)
        Mirror.sync(github_repo, local_mirror_path, gitlab_project)

if __name__ == "__main__":
    setup_logging()
    main()
