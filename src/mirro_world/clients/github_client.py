from datetime import datetime, timezone
from typing import List
from github import Auth, Github, PaginatedList
from github.Repository import Repository
from mirro_world.settings import settings

class GithubClient:
    def __init__(self) -> None:
        self.__client: Github = Github(auth=Auth.Token(settings.GITHUB_TOKEN.get_secret_value()))

    def get_owned_repos(self) -> List[Repository]:
        repos: PaginatedList[Repository] = self.__client.get_user().get_repos(affiliation="owner")
        filtered_repos: List[Repository] = [repo for repo in repos if (settings.MIRRORS_INCLUDE_FORKS or not repo.fork) and (settings.MIRRORS_INCLUDE_ARCHIVED or not repo.archived)]
        return sorted(filtered_repos, key=lambda repo: repo.pushed_at or repo.updated_at or datetime.min.replace(tzinfo=timezone.utc))
