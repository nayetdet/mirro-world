from gitlab import Gitlab
from gitlab.exceptions import GitlabGetError
from github.Repository import Repository
from gitlab.v4.objects import Namespace, Project
from loguru import logger
from mirro_world.settings import settings

class GitlabClient:
    def __init__(self) -> None:
        self.__client: Gitlab = Gitlab(url=settings.GITLAB_URL.rstrip("/"), private_token=settings.GITLAB_TOKEN.get_secret_value())
        self.__client.auth()

    def get_namespace(self) -> Namespace:
        return self.__client.namespaces.get(settings.GITLAB_NAMESPACE_ID)

    def get_project(self, github_repository: Repository, gitlab_project_path: str, gitlab_namespace: Namespace) -> Project:
        try:
            gitlab_project_full_path: str = f"{gitlab_namespace.full_path}/{gitlab_project_path}"
            gitlab_project: Project = self.__client.projects.get(gitlab_project_full_path)
            logger.info("GitLab project already exists: {}", gitlab_project.path_with_namespace)
            return gitlab_project
        except GitlabGetError as error:
            if error.response_code != 404:
                raise
        return self.create_project(github_repository, gitlab_project_path, gitlab_namespace)

    def create_project(self, github_repository: Repository, gitlab_project_path: str, gitlab_namespace: Namespace) -> Project:
        logger.info("Creating GitLab project...")
        return self.__client.projects.create(
            {
                "name": github_repository.name,
                "path": gitlab_project_path,
                "visibility": "private" if github_repository.private else "public",
                "namespace_id": gitlab_namespace.id
            }
        )
