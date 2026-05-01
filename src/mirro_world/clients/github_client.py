from typing import List
from github import Auth, Github, PaginatedList
from github.Repository import Repository
from mirro_world.settings import settings

class GithubClient:
    def __init__(self) -> None:
        self.__client: Github = Github(auth=Auth.Token(settings.GITHUB_TOKEN.get_secret_value()))

    def get_owned_repos(self) -> List[Repository]:
        github_repositories: PaginatedList[Repository] = self.__client.get_user().get_repos(affiliation="owner")
        return [github_repository for github_repository in github_repositories if (settings.MIRRORS_INCLUDE_FORKS or not github_repository.fork) and (settings.MIRRORS_INCLUDE_ARCHIVED or not github_repository.archived)]
