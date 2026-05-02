from http import HTTPStatus
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

    def get_project(self, path: str, source_repo: Repository, namespace: Namespace) -> Project:
        try:
            project_full_path: str = f"{namespace.full_path}/{path}"
            project: Project = self.__client.projects.get(project_full_path)
            logger.info("GitLab project already exists: {}", project.path_with_namespace)
            return project
        except GitlabGetError as error:
            if error.response_code != HTTPStatus.NOT_FOUND:
                raise
        return self.create_project(path, source_repo, namespace)

    def create_project(self, path: str, source_repo: Repository, namespace: Namespace) -> Project:
        logger.info("Creating GitLab project...")
        return self.__client.projects.create(
            {
                "name": source_repo.name,
                "path": path,
                "visibility": "private" if source_repo.private else "public",
                "namespace_id": namespace.id
            }
        )
